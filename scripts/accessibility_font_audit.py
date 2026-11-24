#!/usr/bin/env python3
"""Production-font and accessibility audit for the generated GLab static site.

Run scripts/stage_site.py and install axe-core first. This suite checks the
actual browser font faces loaded from the production Google Fonts stylesheet,
runs axe-core against representative templates in light and dark modes, and
exercises keyboard-only navigation and focus restoration. It reports findings
without rewriting site content or styles.
"""
from __future__ import annotations

import json
import sys
import functools
import threading
from collections import Counter
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
AXE_SCRIPT = ROOT / "node_modules" / "axe-core" / "axe.min.js"
ARTIFACTS = ROOT / "artifacts" / "a11y-font"

ROUTES = (
    "/",
    "/about.html",
    "/articles/",
    "/articles/building-with-nature-in-mind/",
    "/projects/",
    "/projects/glabnetops/",
    "/services.html",
    "/contact.html",
    "/privacy.html",
    "/terms.html",
)
THEMES = ("light", "dark")
AXE_TAGS = (
    "wcag2a",
    "wcag2aa",
    "wcag21a",
    "wcag21aa",
    "wcag22aa",
    "best-practice",
)
FONT_REQUEST_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)
    print("FAIL:", message)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


def summarize_violation(violation: dict) -> dict:
    nodes = []
    for node in violation.get("nodes", [])[:30]:
        nodes.append({
            "target": node.get("target", []),
            "html": node.get("html", "")[:1200],
            "failureSummary": node.get("failureSummary", "")[:2400],
            "any": [
                {
                    "id": item.get("id"),
                    "message": item.get("message"),
                    "data": item.get("data"),
                }
                for item in node.get("any", [])
            ],
            "all": [
                {
                    "id": item.get("id"),
                    "message": item.get("message"),
                    "data": item.get("data"),
                }
                for item in node.get("all", [])
            ],
        })
    return {
        "id": violation.get("id"),
        "impact": violation.get("impact"),
        "help": violation.get("help"),
        "helpUrl": violation.get("helpUrl"),
        "tags": violation.get("tags", []),
        "description": violation.get("description"),
        "nodesAffected": violation.get("nodes", []).__len__(),
        "nodes": nodes,
    }


def run() -> int:
    if not SITE.is_dir():
        print("No _site directory. Run python scripts/stage_site.py first.", file=sys.stderr)
        return 2
    if not AXE_SCRIPT.is_file():
        print("axe-core is not installed. Run npm install --no-save --no-package-lock --ignore-scripts axe-core@4.10.3 first.", file=sys.stderr)
        return 2

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    warnings: list[str] = []
    axe_results: list[dict] = []
    keyboard_results: list[dict] = []
    font_result: dict = {}
    font_css_responses: list[dict] = []
    font_file_responses: list[dict] = []
    font_request_failures: list[dict] = []
    browser_errors: list[str] = []

    handler = functools.partial(QuietHandler, directory=str(SITE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                viewport={"width": 1440, "height": 1000},
                service_workers="block",
                reduced_motion="reduce",
                color_scheme="light",
                device_scale_factor=1,
            )
            # Inject axe into every navigation, not just the initial document.
            context.add_init_script(path=str(AXE_SCRIPT))
            page = context.new_page()
            page.on(
                "pageerror",
                lambda exc: browser_errors.append(f"{page.url}: {exc}"),
            )
            page.on("response", lambda response: (
                font_css_responses.append({"url": response.url, "status": response.status})
                if "fonts.googleapis.com" in response.url else None
            ))
            page.on("response", lambda response: (
                font_file_responses.append({"url": response.url, "status": response.status})
                if "fonts.gstatic.com" in response.url else None
            ))
            page.on("requestfailed", lambda request: (
                font_request_failures.append({"url": request.url, "failure": request.failure})
                if any(host in request.url for host in FONT_REQUEST_HOSTS) else None
            ))

            # Font verification uses the actual page stylesheet and browser
            # FontFaceSet. No request interception is applied to Google Fonts.
            response = page.goto(base_url + "/", wait_until="domcontentloaded", timeout=20000)
            if response is None or response.status >= 400:
                fail(errors, f"Font verification: homepage returned HTTP {getattr(response, 'status', None)}")
            page.wait_for_selector("main h1", state="visible", timeout=8000)
            try:
                font_result = page.evaluate("""async () => {
                  const specs = [
                    {family: 'Manrope', css: '400 16px "Manrope"', sample: 'GLab Enterprise practical software and systems'},
                    {family: 'DM Mono', css: '400 16px "DM Mono"', sample: 'NATURE TECHNOLOGY INNOVATION 012345'},
                    {family: 'Newsreader', css: '400 24px "Newsreader"', sample: 'Thoughtful engineering and innovation'}
                  ];
                  const loaded = [];
                  for (const spec of specs) {
                    const faces = await document.fonts.load(spec.css, spec.sample);
                    const declared = [...document.fonts].filter(face =>
                      face.family.replaceAll('"', '').replaceAll("'", '').trim() === spec.family
                    );
                    loaded.push({
                      family: spec.family,
                      loadedFaceCount: faces.length,
                      loadedFaceStatuses: faces.map(face => face.status),
                      declaredFaceCount: declared.length,
                      declaredStatuses: declared.map(face => face.status)
                    });
                  }
                  await document.fonts.ready;
                  const style = (selector) => {
                    const node = document.querySelector(selector);
                    return node ? getComputedStyle(node).fontFamily : null;
                  };
                  return {
                    fontSetStatus: document.fonts.status,
                    families: loaded,
                    computedFamilies: {
                      body: style('body'),
                      heading: style('main h1'),
                      eyebrow: style('main .eyebrow')
                    },
                    stylesheetLinks: [...document.querySelectorAll('link[rel="stylesheet"]')]
                      .map(link => link.href)
                      .filter(href => href.includes('fonts.googleapis.com'))
                  };
                }""")
            except Exception as exc:
                fail(errors, f"Font verification failed: {type(exc).__name__}: {exc}")

            required_families = ("Manrope", "DM Mono", "Newsreader")
            family_rows = {row.get("family"): row for row in font_result.get("families", [])}
            for family in required_families:
                row = family_rows.get(family)
                if not row or row.get("loadedFaceCount", 0) < 1:
                    fail(errors, f"Production font did not load a usable face: {family}")
                elif any(status != "loaded" for status in row.get("loadedFaceStatuses", [])):
                    fail(errors, f"Production font face is not fully loaded: {family} ({row.get('loadedFaceStatuses')})")
            if not font_result.get("stylesheetLinks"):
                fail(errors, "No Google Fonts stylesheet link was found on the rendered homepage")
            if not any(item.get("status") == 200 for item in font_css_responses):
                fail(errors, "Google Fonts CSS did not return HTTP 200")
            if not any(item.get("status") == 200 for item in font_file_responses):
                fail(errors, "Google Fonts did not deliver a font file with HTTP 200")
            if font_request_failures:
                fail(errors, f"Google Fonts request failure(s): {font_request_failures[:5]}")

            # Automated WCAG-oriented checks. Both colour schemes are tested
            # because the site changes surface and text tokens between themes.
            for theme in THEMES:
                for route in ROUTES:
                    try:
                        response = page.goto(base_url + route, wait_until="domcontentloaded", timeout=15000)
                        if response is None or response.status >= 400:
                            fail(errors, f"axe {theme} {route}: navigation returned HTTP {getattr(response, 'status', None)}")
                            continue
                        page.wait_for_selector("main h1", state="visible", timeout=7000)
                        page.emulate_media(color_scheme=theme)
                        page.evaluate("(theme) => { document.documentElement.dataset.theme = theme; }", theme)
                        page.wait_for_timeout(80)
                        result = page.evaluate("""async (tags) => {
                          const result = await axe.run(document, {
                            runOnly: {type: 'tag', values: tags},
                            resultTypes: ['violations']
                          });
                          return {
                            violations: result.violations.map(v => ({
                              id: v.id,
                              impact: v.impact,
                              help: v.help,
                              helpUrl: v.helpUrl,
                              tags: v.tags,
                              description: v.description,
                              nodes: v.nodes.map(node => ({
                                target: node.target,
                                html: node.html,
                                failureSummary: node.failureSummary,
                                any: node.any.map(item => ({id: item.id, message: item.message, data: item.data})),
                                all: node.all.map(item => ({id: item.id, message: item.message, data: item.data}))
                              }))
                            })),
                            passes: result.passes.length,
                            incomplete: result.incomplete.map(item => ({id: item.id, impact: item.impact, help: item.help, nodes: item.nodes.length}))
                          };
                        }""", list(AXE_TAGS))
                        violations = [summarize_violation(item) for item in result.get("violations", [])]
                        axe_results.append({
                            "route": route,
                            "theme": theme,
                            "passes": result.get("passes", 0),
                            "violations": violations,
                            "incomplete": result.get("incomplete", []),
                        })
                        for violation in violations:
                            impact = violation.get("impact") or "unknown"
                            label = f"{theme} {route}: axe {violation.get('id')} ({impact})"
                            if impact in ("critical", "serious"):
                                fail(errors, label + " — " + str(violation.get("help", "")))
                            else:
                                warnings.append(label + " — " + str(violation.get("help", "")))
                    except PlaywrightTimeoutError as exc:
                        fail(errors, f"axe {theme} {route}: browser timeout ({exc})")
                    except Exception as exc:
                        fail(errors, f"axe {theme} {route}: {type(exc).__name__}: {exc}")

            # Keyboard-only flow checks on the actual generated homepage.
            try:
                page.emulate_media(color_scheme="light")
                page.evaluate("document.documentElement.dataset.theme = 'light'")
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(base_url + "/", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_selector("main h1", state="visible", timeout=7000)
                page.keyboard.press("Tab")
                skip = page.evaluate("""() => {
                  const el = document.activeElement;
                  const rect = el?.getBoundingClientRect();
                  const style = el ? getComputedStyle(el) : null;
                  return {
                    className: el?.className || '',
                    text: (el?.textContent || '').trim(),
                    visible: !!rect && rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden',
                    outlineStyle: style?.outlineStyle || '',
                    outlineWidth: style?.outlineWidth || '',
                    transform: style?.transform || ''
                  };
                }""")
                if "skip-link" not in str(skip.get("className", "")):
                    fail(errors, f"Keyboard: first Tab did not focus the skip link ({skip})")
                if not skip.get("visible"):
                    fail(errors, f"Keyboard: skip link is not visible when focused ({skip})")
                if skip.get("outlineStyle") == "none" or skip.get("outlineWidth") in ("0px", "0"):
                    fail(errors, f"Keyboard: skip link has no visible focus indicator ({skip})")
                page.keyboard.press("Enter")
                if page.evaluate("location.hash") != "#main":
                    fail(errors, "Keyboard: activating the skip link did not navigate to #main")

                # Menu activation, initial focus, focus-ring and boundary wrapping.
                page.goto(base_url + "/", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_selector("[data-menu-toggle]", state="visible", timeout=5000)
                menu_button = page.locator("[data-menu-toggle]")
                menu_panel = page.locator("[data-mobile-menu]")
                menu_button.focus()
                page.keyboard.press("Enter")
                page.wait_for_function("""() => {
                  const menu = document.querySelector('[data-mobile-menu]');
                  const first = menu?.querySelector('a[href]');
                  return menu && !menu.hidden && first === document.activeElement;
                }""", timeout=3000)
                first_link = menu_panel.locator("a[href]").first
                last_link = menu_panel.locator("a[href]").last
                focus_metrics = first_link.evaluate("""el => {
                  const s = getComputedStyle(el);
                  return {outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth, boxShadow: s.boxShadow};
                }""")
                if focus_metrics["outlineStyle"] == "none" and focus_metrics["outlineWidth"] in ("0px", "0") and focus_metrics["boxShadow"] == "none":
                    fail(errors, f"Keyboard: focused menu link has no visible focus indicator ({focus_metrics})")

                page.keyboard.press("Shift+Tab")
                if not last_link.evaluate("el => el === document.activeElement"):
                    fail(errors, "Keyboard: Shift+Tab from the first menu item did not wrap to the last item")
                page.keyboard.press("Tab")
                if not first_link.evaluate("el => el === document.activeElement"):
                    fail(errors, "Keyboard: Tab from the last menu item did not wrap to the first item")
                page.keyboard.press("Escape")
                if menu_panel.is_visible() or menu_button.get_attribute("aria-expanded") != "false":
                    fail(errors, "Keyboard: Escape did not close the grouped menu")
                if not menu_button.evaluate("el => el === document.activeElement"):
                    fail(errors, "Keyboard: closing the grouped menu did not restore focus to its trigger")
                keyboard_results.append({"test": "grouped-menu", "passed": True, "focusIndicator": focus_metrics})

                # Search dialog keyboard activation and focus restoration.
                search_button = page.locator("[data-search-toggle]").first
                search_button.focus()
                page.keyboard.press("Enter")
                dialog = page.locator("[data-search-dialog]")
                page.wait_for_function("""() => {
                  const dialog = document.querySelector('[data-search-dialog]');
                  const input = document.querySelector('[data-global-search]');
                  return !!dialog?.open && document.activeElement === input;
                }""", timeout=3000)
                page.keyboard.press("Escape")
                if dialog.is_visible():
                    fail(errors, "Keyboard: Escape did not close the search dialog")
                if not search_button.evaluate("el => el === document.activeElement"):
                    fail(errors, "Keyboard: closing search did not restore focus to the search trigger")
                keyboard_results.append({"test": "search-dialog", "passed": True})

                # Appearance controls must be keyboard-operable.
                theme_button = page.locator("[data-theme-toggle]")
                theme_button.focus()
                before_theme = page.locator("html").get_attribute("data-theme")
                page.keyboard.press("Enter")
                after_theme = page.locator("html").get_attribute("data-theme")
                if before_theme == after_theme or after_theme not in ("light", "dark"):
                    fail(errors, "Keyboard: theme toggle did not respond to Enter")
                font_up = page.locator('[data-font-step="1"]')
                font_up.focus()
                before_size = page.locator("html").get_attribute("data-font-size")
                page.keyboard.press("Space")
                after_size = page.locator("html").get_attribute("data-font-size")
                if before_size == after_size:
                    fail(errors, "Keyboard: text-size control did not respond to Space")
                keyboard_results.append({"test": "appearance-controls", "passed": True})
            except Exception as exc:
                fail(errors, f"Keyboard interaction suite failed: {type(exc).__name__}: {exc}")

            for error in browser_errors[:30]:
                fail(errors, "Uncaught browser exception: " + error)

            context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    impact_counts = Counter(
        violation.get("impact") or "unknown"
        for result in axe_results
        for violation in result.get("violations", [])
    )
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "base": "generated _site build",
        "axeCore": "4.10.3",
        "axeTags": list(AXE_TAGS),
        "routesAudited": list(ROUTES),
        "themesAudited": list(THEMES),
        "axeRuns": len(axe_results),
        "axeViolationCountsByImpact": dict(impact_counts),
        "fontVerification": font_result,
        "fontCssResponses": font_css_responses,
        "fontFileResponses": font_file_responses,
        "fontRequestFailures": font_request_failures,
        "keyboardTests": keyboard_results,
        "axeResults": axe_results,
        "errors": errors,
        "warnings": warnings,
    }
    report_path = ARTIFACTS / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Accessibility/font report: {report_path}")
    print(f"axe-core: {len(axe_results)} route/theme scans; violations by impact: {dict(impact_counts)}")
    print(f"Production fonts: {sum(1 for row in font_result.get('families', []) if row.get('loadedFaceCount', 0) > 0)}/3 loaded")
    print(f"Keyboard flows completed: {len(keyboard_results)}")
    print(f"Warnings: {len(warnings)}; failures: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(run())
