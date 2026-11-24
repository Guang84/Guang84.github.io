#!/usr/bin/env python3
"""Responsive and visual-quality diagnostics for the generated GLab website.

Run scripts/stage_site.py first. This is a browser-level companion to
browser_smoke.py: it renders every generated route at desktop size, exercises
representative templates around responsive breakpoints, and saves screenshots
and a JSON report for CI review. It deliberately does not rewrite site content
or CSS; it reports evidence so visual fixes can be reviewed rather than guessed.
"""
from __future__ import annotations

import json
import sys
import functools
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
ARTIFACTS = ROOT / "artifacts" / "ui-quality"

# Widths intentionally straddle the site's 600px and 860px CSS breakpoints.
RESPONSIVE_WIDTHS = (320, 375, 390, 600, 768, 860, 861, 1024, 1280, 1600, 1920, 2560)
RESPONSIVE_ROUTES = (
    "/", "/about.html", "/nature/", "/technology/", "/innovation/",
    "/articles/", "/articles/building-with-nature-in-mind/",
    "/projects/", "/projects/glabnetops/", "/services.html",
    "/contact.html", "/business/",
)
SCREENSHOT_ROUTES = {
    "/", "/about.html", "/articles/", "/projects/",
    "/services.html", "/contact.html",
}


def page_route(path: Path) -> str:
    rel = path.relative_to(SITE).as_posix()
    if rel == "index.html":
        return "/"
    parts = rel.split("/")
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/" if len(parts) > 1 else "/"
    return "/" + rel


def local_page_urls() -> list[str]:
    return sorted({page_route(path) for path in SITE.rglob("*.html")}, key=lambda item: (item != "/", item))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)
    print("FAIL:", message)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


def run() -> int:
    if not SITE.is_dir():
        print("No _site directory. Run python scripts/stage_site.py first.", file=sys.stderr)
        return 2

    urls = local_page_urls()
    if not urls:
        print("No generated HTML pages found.", file=sys.stderr)
        return 2

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    warnings: list[str] = []
    page_results: list[dict] = []
    responsive_results: list[dict] = []
    screenshots: list[str] = []
    browser_errors: list[str] = []

    # The responsive matrix includes only routes present in the generated site.
    responsive_routes = [route for route in RESPONSIVE_ROUTES if route in urls]
    if "/" not in responsive_routes:
        responsive_routes.insert(0, "/")

    handler = functools.partial(QuietHandler, directory=str(SITE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(
                viewport={"width": 1440, "height": 1000},
                service_workers="block",
                reduced_motion="reduce",
                device_scale_factor=1,
            )
            # Keep screenshots and measurements reproducible; local fonts and all
            # same-origin assets remain available.
            context.route("https://fonts.googleapis.com/**", lambda route: route.abort())
            context.route("https://fonts.gstatic.com/**", lambda route: route.abort())
            page = context.new_page()
            page.on("pageerror", lambda exc: browser_errors.append(f"{page.url}: {exc}"))

            # Pass 1: render every generated HTML route at a wide desktop viewport.
            page.set_viewport_size({"width": 1440, "height": 1000})
            for route in urls:
                try:
                    response = page.goto(base_url + route, wait_until="domcontentloaded", timeout=15000)
                    if response is None or response.status >= 400:
                        fail(errors, f"desktop {route}: navigation returned {getattr(response, 'status', None)}")
                        continue
                    page.wait_for_selector("main h1", state="visible", timeout=7000)
                    metrics = page.evaluate("""() => {
                      const visible = (el) => {
                        const s = getComputedStyle(el);
                        const r = el.getBoundingClientRect();
                        return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
                      };
                      const main = document.querySelector('main');
                      const h1 = main?.querySelector('h1');
                      const bodyStyle = getComputedStyle(document.body);
                      const h1Style = h1 ? getComputedStyle(h1) : null;
                      const mainRect = main?.getBoundingClientRect();
                      const h1Rect = h1?.getBoundingClientRect();
                      const images = [...document.images].map(img => ({
                        src: img.currentSrc || img.src,
                        complete: img.complete,
                        naturalWidth: img.naturalWidth,
                        loading: img.loading
                      }));
                      const controls = [...document.querySelectorAll('a,button,[role="button"]')].filter(visible);
                      const unnamed = controls.filter(el => {
                        const label = (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.innerText || el.textContent || '').trim();
                        const imageAlt = [...el.querySelectorAll('img[alt]')].map(img => img.alt).join(' ').trim();
                        return !label && !imageAlt;
                      }).map(el => ({tag: el.tagName.toLowerCase(), className: String(el.className || '').slice(0,100), href: el.getAttribute('href')}));
                      const undersized = controls.filter(el => {
                        const r = el.getBoundingClientRect();
                        return (el.matches('button,[role="button"],a[aria-label]') && (r.width < 24 || r.height < 24));
                      }).map(el => ({tag: el.tagName.toLowerCase(), className: String(el.className || '').slice(0,100), width: Math.round(el.getBoundingClientRect().width), height: Math.round(el.getBoundingClientRect().height)}));
                      const clipping = [...document.querySelectorAll('main h1,main h2,main h3,.project-card,.writing-item,.hero-panel,.profile-hero,.site-header')].filter(visible).filter(el => {
                        const s = getComputedStyle(el);
                        return (s.overflowX === 'hidden' || s.overflowX === 'clip') && el.scrollWidth > el.clientWidth + 2;
                      }).map(el => ({selector: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\\s+/).join('.') : ''), scrollWidth: el.scrollWidth, clientWidth: el.clientWidth}));
                      return {
                        viewportWidth: innerWidth,
                        documentWidth: document.documentElement.scrollWidth,
                        bodyWidth: document.body.scrollWidth,
                        mainWidth: mainRect?.width || 0,
                        h1Count: main?.querySelectorAll('h1').length || 0,
                        h1Width: h1Rect?.width || 0,
                        bodyFontSize: parseFloat(bodyStyle.fontSize) || 0,
                        bodyLineHeight: bodyStyle.lineHeight,
                        bodyFontFamily: bodyStyle.fontFamily,
                        h1FontSize: h1Style ? parseFloat(h1Style.fontSize) : 0,
                        h1LineHeight: h1Style?.lineHeight || '',
                        imageCount: images.length,
                        brokenImages: images.filter(img => img.complete && img.naturalWidth === 0),
                        pendingImages: images.filter(img => !img.complete),
                        unnamedControls: unnamed,
                        undersizedControls: undersized,
                        clippedComponents: clipping
                      };
                    }""")
                    route_result = {"route": route, **metrics}
                    page_results.append(route_result)

                    if metrics["h1Count"] != 1:
                        fail(errors, f"desktop {route}: expected exactly one main h1, found {metrics['h1Count']}")
                    if metrics["documentWidth"] > 1441 or metrics["bodyWidth"] > 1441:
                        fail(errors, f"desktop {route}: horizontal page overflow ({metrics['documentWidth']}px document, {metrics['bodyWidth']}px body)")
                    if metrics["mainWidth"] < 280:
                        fail(errors, f"desktop {route}: main content is unexpectedly narrow ({metrics['mainWidth']:.1f}px)")
                    if metrics["bodyFontSize"] < 14:
                        fail(errors, f"desktop {route}: body text is below 14px ({metrics['bodyFontSize']:.1f}px)")
                    if metrics["h1FontSize"] <= metrics["bodyFontSize"]:
                        warnings.append(f"{route}: main h1 is not larger than body text")
                    if metrics["brokenImages"]:
                        fail(errors, f"desktop {route}: broken image(s): " + ", ".join(img["src"] for img in metrics["brokenImages"][:5]))
                    if metrics["pendingImages"]:
                        warnings.append(f"{route}: {len(metrics['pendingImages'])} image(s) had not completed by the measurement point")
                    if metrics["unnamedControls"]:
                        warnings.append(f"{route}: {len(metrics['unnamedControls'])} visible link/button controls have no discernible text or accessible name")
                    if metrics["undersizedControls"]:
                        warnings.append(f"{route}: {len(metrics['undersizedControls'])} icon/button controls are smaller than 24×24 CSS px")
                    if metrics["clippedComponents"]:
                        fail(errors, f"desktop {route}: clipped content in {metrics['clippedComponents']}")
                    if route in SCREENSHOT_ROUTES:
                        name = "desktop-" + (route.strip("/").replace("/", "-") or "home") + ".png"
                        destination = ARTIFACTS / name
                        page.screenshot(path=str(destination), full_page=True, animations="disabled")
                        screenshots.append(str(destination.relative_to(ROOT)))

                except PlaywrightTimeoutError as exc:
                    fail(errors, f"desktop {route}: timed out waiting for visible main heading ({exc})")
                except Exception as exc:
                    fail(errors, f"desktop {route}: {type(exc).__name__}: {exc}")

            # Pass 2: representative page templates at all important width boundaries.
            for width in RESPONSIVE_WIDTHS:
                page.set_viewport_size({"width": width, "height": 900 if width > 600 else 780})
                for route in responsive_routes:
                    try:
                        response = page.goto(base_url + route, wait_until="domcontentloaded", timeout=12000)
                        if response is None or response.status >= 400:
                            fail(errors, f"responsive {width}px {route}: navigation returned {getattr(response, 'status', None)}")
                            continue
                        page.wait_for_selector("main h1", state="visible", timeout=6000)
                        metrics = page.evaluate("""() => {
                          const main = document.querySelector('main');
                          const header = document.querySelector('.site-header');
                          const menuButton = document.querySelector('[data-menu-toggle]');
                          const nav = document.querySelector('nav.nav');
                          const rect = main?.getBoundingClientRect();
                          const h1 = main?.querySelector('h1');
                          const h1Rect = h1?.getBoundingClientRect();
                          const style = h1 ? getComputedStyle(h1) : null;
                          return {
                            width: innerWidth,
                            documentWidth: document.documentElement.scrollWidth,
                            bodyWidth: document.body.scrollWidth,
                            mainWidth: rect?.width || 0,
                            h1Right: h1Rect?.right || 0,
                            h1Bottom: h1Rect?.bottom || 0,
                            h1FontSize: style ? parseFloat(style.fontSize) : 0,
                            headerVisible: !!header && getComputedStyle(header).display !== 'none',
                            desktopNavVisible: !!nav && getComputedStyle(nav).display !== 'none',
                            mobileMenuButtonVisible: !!menuButton && getComputedStyle(menuButton).display !== 'none',
                            menuButtonWidth: menuButton?.getBoundingClientRect().width || 0,
                            menuButtonHeight: menuButton?.getBoundingClientRect().height || 0
                          };
                        }""")
                        responsive_results.append({"route": route, **metrics})
                        if metrics["documentWidth"] > width + 1 or metrics["bodyWidth"] > width + 1:
                            fail(errors, f"responsive {width}px {route}: horizontal overflow (document {metrics['documentWidth']}px, body {metrics['bodyWidth']}px)")
                        if metrics["mainWidth"] < min(280, width - 24):
                            fail(errors, f"responsive {width}px {route}: main content collapsed to {metrics['mainWidth']:.1f}px")
                        if metrics["h1Right"] > width + 1:
                            fail(errors, f"responsive {width}px {route}: h1 extends outside viewport")
                        # The existing public header switches to its compact
                        # menu at 1600px; preserve that established breakpoint.
                        if width <= 1600:
                            if metrics["desktopNavVisible"]:
                                fail(errors, f"responsive {width}px {route}: desktop navigation remains visible in compact-header mode")
                            if not metrics["mobileMenuButtonVisible"]:
                                fail(errors, f"responsive {width}px {route}: compact menu control is hidden")
                        else:
                            if not metrics["desktopNavVisible"]:
                                fail(errors, f"responsive {width}px {route}: desktop navigation is unexpectedly hidden above 1600px")
                            if metrics["mobileMenuButtonVisible"]:
                                fail(errors, f"responsive {width}px {route}: compact menu control remains visible above 1600px")
                    except PlaywrightTimeoutError as exc:
                        fail(errors, f"responsive {width}px {route}: timed out ({exc})")
                    except Exception as exc:
                        fail(errors, f"responsive {width}px {route}: {type(exc).__name__}: {exc}")

                if width in (390, 1280):
                    route = "/"
                    page.goto(base_url + route, wait_until="domcontentloaded", timeout=12000)
                    page.wait_for_selector("main h1", state="visible", timeout=6000)
                    name = f"{'mobile' if width == 390 else 'desktop'}-home-viewport.png"
                    destination = ARTIFACTS / name
                    page.screenshot(path=str(destination), full_page=False, animations="disabled")
                    screenshots.append(str(destination.relative_to(ROOT)))

            # Focus and touch-target probes are non-blocking diagnostics; severe
            # navigation/overflow defects above remain hard failures.
            try:
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(base_url + "/", wait_until="domcontentloaded", timeout=12000)
                page.wait_for_selector("[data-menu-toggle]", state="visible", timeout=5000)
                page.locator("[data-menu-toggle]").focus()
                focus_visible = page.evaluate("""() => {
                  const el = document.activeElement;
                  const s = getComputedStyle(el);
                  return {tag: el?.tagName, outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth, boxShadow: s.boxShadow};
                }""")
                if focus_visible["outlineStyle"] == "none" and focus_visible["outlineWidth"] in ("0px", "0"):
                    warnings.append("Mobile menu button: focus indicator is not detectable from outline or box-shadow")
            except Exception as exc:
                warnings.append(f"Keyboard focus diagnostic could not complete: {type(exc).__name__}: {exc}")

            for error in browser_errors[:30]:
                fail(errors, "Uncaught browser exception: " + error)

            context.close()
            browser.close()

        report = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "base": "generated _site build",
            "routesRenderedDesktop": len(page_results),
            "responsiveRouteCount": len(responsive_routes),
            "responsiveViewportWidths": list(RESPONSIVE_WIDTHS),
            "responsivePageViewChecks": len(responsive_results),
            "screenshots": screenshots,
            "errors": errors,
            "warnings": warnings,
            "desktopPages": page_results,
            "responsiveChecks": responsive_results,
        }
        report_path = ARTIFACTS / "report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"UI quality report: {report_path}")
        print(f"Rendered {len(page_results)}/{len(urls)} desktop routes and {len(responsive_results)} responsive page/view combinations.")
        print(f"Saved {len(screenshots)} screenshots under {ARTIFACTS}.")
        print(f"Warnings: {len(warnings)}; failures: {len(errors)}.")
        if errors:
            return 1
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(run())
