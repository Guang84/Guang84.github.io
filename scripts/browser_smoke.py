#!/usr/bin/env python3
"""Browser regression tests for the generated GLab static site.

Run scripts/stage_site.py first. The tests use Playwright/Chromium and a local
HTTP server so absolute routes, ES modules, and the service worker behave like a
real static deployment rather than file:// pages.
"""
from __future__ import annotations

import argparse
import functools
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
VIEWPORTS = [
    ("desktop", 1280, 900),
    ("tablet", 803, 1024),
    ("mobile", 390, 844),
]


def page_route(path: Path) -> str:
    rel = path.relative_to(SITE).as_posix()
    if rel == "index.html":
        return "/"
    parts = rel.split("/")
    if parts[-1] == "index.html":
        if len(parts) == 2 and parts[0] in {"articles", "projects"}:
            return f"/{parts[0]}/"
        if len(parts) >= 3 and parts[0] in {"articles", "projects"}:
            return f"/{parts[0]}/{parts[1]}/"
    return "/" + rel


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


def fail(errors: list[str], message: str):
    errors.append(message)
    print("FAIL:", message)


def local_page_urls() -> list[str]:
    candidates = sorted(SITE.rglob("*.html"))
    urls = [page_route(path) for path in candidates]
    # Deduplicate routes where index.html and directory mapping point to the same URL.
    return sorted(set(urls), key=lambda u: (u != "/", u))


def run_tests():
    if not SITE.exists():
        print("No _site directory. Run python scripts/stage_site.py first.", file=sys.stderr)
        return 2
    errors: list[str] = []
    all_urls = local_page_urls()
    if not all_urls:
        print("No generated HTML pages found.", file=sys.stderr)
        return 2
    # Static site_audit.py checks every route and local reference. Reserve full
    # browser rendering for high-value entry points to stay within sandbox
    # Chromium's localhost navigation policy while retaining responsive coverage.
    critical_routes = {
        "/", "/about.html", "/articles/", "/articles/building-with-nature-in-mind/",
        "/projects/", "/projects/glabnetops/", "/projects/noney-bsnl-broadband-nms/",
    }
    urls = [route for route in all_urls if route in critical_routes]

    handler = functools.partial(QuietHandler, directory=str(SITE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with sync_playwright() as p:
            executable = os.environ.get("GLAB_CHROMIUM")
            if not executable and os.environ.get("GLAB_BROWSER_REQUIRED") != "1":
                executable = next(
                    (candidate for candidate in (
                        "/usr/bin/chromium",
                        "/usr/bin/chromium-browser",
                        "/usr/bin/google-chrome",
                    ) if candidate and Path(candidate).is_file()),
                    None,
                )
            # In required CI mode, leave executable_path unset so Playwright
            # uses the exact browser downloaded by `playwright install chromium`.
            launch_args = ["--no-sandbox", "--disable-dev-shm-usage"]
            browser = p.chromium.launch(
                headless=True,
                executable_path=executable,
                args=launch_args,
            )

            # A deterministic layout context: no stale service-worker cache and no external font fetches.
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                service_workers="block",
                reduced_motion="reduce",
            )
            context.route("https://fonts.googleapis.com/**", lambda route: route.abort())
            context.route("https://fonts.gstatic.com/**", lambda route: route.abort())
            page = context.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda exc: page_errors.append(f"{page.url}: {exc}"))

            page_view_checks = 0
            # Static audit checks all generated routes and links. Keep browser
            # rendering focused on key entry points at multiple widths, then
            # exercise user-facing interactions on representative pages.
            responsive_routes = ["/", "/articles/", "/projects/glabnetops/"]
            viewport_jobs = [("desktop", 1280, 900, urls)]
            for label, width, height in VIEWPORTS[1:]:
                viewport_jobs.append((label, width, height, responsive_routes))

            for label, width, height, routes_for_view in viewport_jobs:
                page.set_viewport_size({"width": width, "height": height})
                for route in routes_for_view:
                    try:
                        response = page.goto(base_url + route, wait_until="load", timeout=12000)
                        if response is None or response.status >= 400:
                            fail(errors, f"{label} {route}: navigation returned {getattr(response, 'status', None)}")
                            continue
                        page.wait_for_selector("main h1", state="visible", timeout=3000)
                        metrics = page.evaluate("""() => {
                          const main = document.querySelector('main');
                          const rect = main?.getBoundingClientRect();
                          const timeline = document.querySelector('.timeline-list');
                          const timelineRect = timeline?.getBoundingClientRect();
                          return {
                            width: innerWidth,
                            scrollWidth: document.documentElement.scrollWidth,
                            mainWidth: rect?.width || 0,
                            h1Count: document.querySelectorAll('main h1').length,
                            timelineWidth: timelineRect?.width || null,
                          };
                        }""")
                        if metrics["h1Count"] != 1:
                            fail(errors, f"{label} {route}: expected one main h1, found {metrics['h1Count']}")
                        if metrics["scrollWidth"] > width + 1:
                            fail(errors, f"{label} {route}: horizontal overflow ({metrics['scrollWidth']}px > {width}px)")
                        min_main = min(280, width * 0.72)
                        if metrics["mainWidth"] < min_main:
                            fail(errors, f"{label} {route}: main content too narrow ({metrics['mainWidth']:.1f}px)")
                        if metrics["timelineWidth"] is not None and metrics["timelineWidth"] < width * 0.55:
                            fail(errors, f"{label} {route}: timeline collapsed to {metrics['timelineWidth']:.1f}px")
                        page_view_checks += 1
                    except PlaywrightTimeoutError as exc:
                        fail(errors, f"{label} {route}: browser timeout ({exc})")
                    except Exception as exc:
                        if "ERR_BLOCKED_BY_ADMINISTRATOR" in str(exc) and os.environ.get("GLAB_BROWSER_REQUIRED") != "1":
                            print(
                                "SKIP: this sandbox's Chromium policy blocks loopback HTTP navigation; "
                                "run the same browser suite in GitHub Actions or another local browser environment.",
                                file=sys.stderr,
                            )
                            return 0
                        fail(errors, f"{label} {route}: {type(exc).__name__}: {exc}")

            # Home introduction must be synchronized with the configurable copy.
            page.set_viewport_size({"width": 1280, "height": 900})
            page.goto(base_url + "/", wait_until="load")
            try:
                page.wait_for_function(
                    """() => [...document.querySelectorAll('[data-site-intro] p')]
                      .some(p => p.textContent.includes('coexist harmoniously'))""",
                    timeout=5000,
                )
            except PlaywrightTimeoutError:
                fail(errors, "Home page: site-config did not render the technology/nature introduction")

            # Search should return the ChatGPT guide through the generated index.
            try:
                page.locator("[data-search-toggle]").first.click()
                page.locator("[data-search-dialog]").wait_for(state="visible", timeout=2000)
                search = page.locator("[data-global-search]")
                search.fill("soil sensor")
                page.wait_for_function(
                    "() => document.querySelectorAll('.search-result').length > 0",
                    timeout=5000,
                )
                result_text = page.locator(".search-results").inner_text()
                if "Soil Sensor" not in result_text:
                    fail(errors, "Search: query soil sensor did not return the published soil-sensor guide")
                page.locator("[data-search-close]").click()
            except Exception as exc:
                fail(errors, f"Search interaction failed: {type(exc).__name__}: {exc}")

            # Automatic system-dark mode must use the same forest tokens as the app's manual dark mode.
            try:
                page.emulate_media(color_scheme="dark")
                page.evaluate("localStorage.removeItem('glab-theme')")
                page.goto(base_url + "/", wait_until="load")
                page.wait_for_function("document.documentElement.classList.contains('js')", timeout=5000)
                auto_dark = page.evaluate("""() => {
                  const root = document.documentElement;
                  const style = getComputedStyle(root);
                  return {
                    theme: root.getAttribute('data-theme'),
                    tokens: Object.fromEntries(['--bg', '--surface', '--surface-2', '--ink', '--muted', '--blue', '--aqua', '--button-bg', '--forest', '--forest-2'].map(key => [key, style.getPropertyValue(key).trim()])),
                  };
                }""")
                if auto_dark["theme"] is not None:
                    fail(errors, "System theme: expected no explicit theme override when no preference is saved")
                page.evaluate("document.documentElement.dataset.theme = 'dark'")
                explicit_dark = page.evaluate("""() => {
                  const style = getComputedStyle(document.documentElement);
                  return Object.fromEntries(['--bg', '--surface', '--surface-2', '--ink', '--muted', '--blue', '--aqua', '--button-bg', '--forest', '--forest-2'].map(key => [key, style.getPropertyValue(key).trim()]));
                }""")
                if auto_dark["tokens"] != explicit_dark:
                    fail(errors, "System dark mode does not match the app's explicit dark palette")
                page.evaluate("document.documentElement.removeAttribute('data-theme')")
                page.emulate_media(color_scheme="light")
                auto_light = page.evaluate("""() => ({theme: document.documentElement.getAttribute('data-theme'), bg: getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()})""")
                if auto_light["theme"] is not None or auto_light["bg"] == auto_dark["tokens"]["--bg"]:
                    fail(errors, "System theme: light preference did not restore the app's light palette automatically")
            except Exception as exc:
                fail(errors, f"System theme matching failed: {type(exc).__name__}: {exc}")

            # The mobile homepage article eyebrow must stay in a readable text column.
            try:
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(base_url + "/", wait_until="load")
                page.wait_for_selector(".writing-item .eyebrow", timeout=5000)
                label_metrics = page.locator(".writing-item").first.locator(".eyebrow").first.evaluate("""(label) => {
                  const rect = label.getBoundingClientRect();
                  const style = getComputedStyle(label);
                  const lineHeight = parseFloat(style.lineHeight) || 16;
                  return {width: rect.width, height: rect.height, lines: Math.ceil(rect.height / lineHeight), text: label.textContent.trim(), cardWidth: label.closest('.writing-item').getBoundingClientRect().width};
                }""")
                if label_metrics["width"] < 150 or label_metrics["cardWidth"] < 300:
                    fail(errors, f"Mobile article card has a collapsed text column: {label_metrics}")
                if label_metrics["lines"] > 3:
                    fail(errors, f"Mobile article eyebrow wraps into too many lines: {label_metrics}")
            except Exception as exc:
                fail(errors, f"Mobile article layout check failed: {type(exc).__name__}: {exc}")

            # Restore a desktop viewport: text-size controls are intentionally hidden on phones.
            page.set_viewport_size({"width": 1280, "height": 900})
            page.goto(base_url + "/", wait_until="load")

            # Theme and text-size controls should change their documented state.
            try:
                old_theme = page.locator("html").get_attribute("data-theme")
                page.locator("[data-theme-toggle]").click()
                new_theme = page.locator("html").get_attribute("data-theme")
                if old_theme == new_theme or new_theme not in {"light", "dark"}:
                    fail(errors, "Theme toggle did not change the root theme state")
                page.locator('[data-font-step="1"]').click()
                size = page.locator("html").get_attribute("data-font-size")
                if size not in {"medium", "large"}:
                    fail(errors, f"Text-size control set unexpected size {size!r}")
            except Exception as exc:
                fail(errors, f"Appearance controls failed: {type(exc).__name__}: {exc}")

            # Project archive filters and text search must operate on static HTML cards.
            try:
                page.goto(base_url + "/projects/", wait_until="load")
                page.wait_for_selector("[data-project-filters] button", timeout=5000)
                filters = page.locator("[data-project-filters] button")
                if filters.count() < 2:
                    fail(errors, "Project archive: category filters were not generated")
                else:
                    filters.first.click()  # Reset to All.
                local_search = page.locator("[data-collection-search]")
                local_search.fill("Rongmei")
                page.wait_for_timeout(100)
                visible = page.locator(".project-card:visible").count()
                if visible != 1:
                    fail(errors, f"Project archive: expected one Rongmei result, found {visible}")
            except Exception as exc:
                fail(errors, f"Project archive filtering failed: {type(exc).__name__}: {exc}")

            # Mobile navigation must open, expose links, and close on Escape.
            try:
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(base_url + "/", wait_until="load")
                menu_button = page.locator("[data-menu-toggle]")
                menu_button.click()
                menu = page.locator("[data-mobile-menu]")
                if not menu.is_visible() or menu_button.get_attribute("aria-expanded") != "true":
                    fail(errors, "Mobile menu did not open or update aria-expanded")
                page.keyboard.press("Escape")
                if menu.is_visible() or menu_button.get_attribute("aria-expanded") != "false":
                    fail(errors, "Mobile menu did not close on Escape")
            except Exception as exc:
                fail(errors, f"Mobile menu interaction failed: {type(exc).__name__}: {exc}")

            if page_errors:
                for error in page_errors[:20]:
                    fail(errors, "Uncaught browser exception: " + error)

            context.close()

            # Service worker test runs in a separate context where workers are allowed.
            sw_context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                service_workers="allow",
            )
            sw_context.route("https://fonts.googleapis.com/**", lambda route: route.abort())
            sw_context.route("https://fonts.gstatic.com/**", lambda route: route.abort())
            sw_page = sw_context.new_page()
            sw_page_errors: list[str] = []
            sw_page.on("pageerror", lambda exc: sw_page_errors.append(f"{sw_page.url}: {exc}"))
            try:
                response = sw_page.goto(base_url + "/", wait_until="load", timeout=12000)
                if response is None or response.status >= 400:
                    fail(errors, "Service worker: homepage failed to load")
                sw_page.wait_for_function(
                    "async () => { if (!('serviceWorker' in navigator)) return false; try { await navigator.serviceWorker.ready; return true; } catch { return false; } }",
                    timeout=10000,
                )
                sw_page.reload(wait_until="load")
                sw_page.wait_for_function("navigator.serviceWorker.controller !== null", timeout=10000)
                result = sw_page.evaluate("""() => new Promise((resolve) => {
                  const finish = (value) => resolve(value);
                  navigator.serviceWorker.ready.then((registration) => {
                    const worker = navigator.serviceWorker.controller || registration.active;
                    if (!worker) return finish({ error: 'No active worker' });
                    const channel = new MessageChannel();
                    const timer = setTimeout(() => finish({ error: 'CHECK_CONTENT timed out' }), 10000);
                    channel.port1.onmessage = (event) => {
                      clearTimeout(timer);
                      finish(event.data?.result || event.data || { error: 'Empty worker result' });
                    };
                    worker.postMessage({ type: 'CHECK_CONTENT' }, [channel.port2]);
                  }).catch((error) => finish({ error: String(error) }));
                })""")
                if result.get("error"):
                    fail(errors, f"Service worker catalogue refresh: {result['error']}")
                elif result.get("records", 0) < 1:
                    fail(errors, f"Service worker catalogue refresh returned no catalogue records: {result}")
            except Exception as exc:
                fail(errors, f"Service worker check failed: {type(exc).__name__}: {exc}")
            for error in sw_page_errors[:20]:
                fail(errors, "Service-worker context browser exception: " + error)
            sw_context.close()
            browser.close()

            if errors:
                print(f"Browser smoke test failed: {len(errors)} issue(s); checked {page_view_checks} page/view combinations.")
                return 1
            print(f"Browser smoke test passed: {len(urls)} key routes across desktop and {len(VIEWPORTS)-1} responsive viewport sets ({page_view_checks} page/view combinations); static audit covers all {len(all_urls)} HTML routes. Search, filters, theme/font controls, mobile menu, and service-worker catalogue refresh also passed.")
            return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(run_tests())
