#!/usr/bin/env python3
"""Check the GLab PWA shell's offline dependency closure and byte budgets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
MAX_PRECACHE_IMAGE_BYTES = 300 * 1024
IMPORT_RE = re.compile(
    r"""^\s*(?:import|export)\s+(?:[^'"]*?\s+from\s+)?["'](\.{1,2}/[^"']+)["']""",
    re.MULTILINE,
)
CSS_IMPORT_RE = re.compile(
    r"""@import\s+(?:url\(\s*)?["']([^"']+)["']""",
    re.IGNORECASE,
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def local_path(value: str, parent: Path | None = None) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith("//"):
        return None
    raw = parsed.path
    if not raw:
        return None
    if raw.startswith("/"):
        target = ROOT / raw.lstrip("/")
    elif parent is not None:
        target = parent.parent / raw
    else:
        return None
    target = target.resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return None
    if target.is_dir():
        target = target / "index.html"
    return target


def dependency_closure(entry: Path, pattern: re.Pattern[str], errors: list[str]) -> set[str]:
    found: set[str] = set()
    pending = [entry]
    while pending:
        current = pending.pop()
        relative = current.relative_to(ROOT).as_posix()
        if relative in found:
            continue
        if not current.is_file():
            fail(errors, f"Missing imported dependency: /{relative}")
            continue
        found.add(relative)
        source = current.read_text(encoding="utf-8")
        for match in pattern.finditer(source):
            target = local_path(match.group(1), current)
            if target is None:
                continue
            if not target.is_file():
                fail(errors, f"/{relative} imports missing file {match.group(1)}")
                continue
            pending.append(target)
    return found


def main() -> int:
    errors: list[str] = []
    worker_path = ROOT / "service-worker.js"
    worker = worker_path.read_text(encoding="utf-8")
    match = re.search(r"const PRECACHE\s*=\s*(\[.*?\]);", worker, re.DOTALL)
    if not match:
        print("FAIL: unable to read service-worker PRECACHE array")
        return 1
    try:
        precache = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid PRECACHE JSON: {exc}")
        return 1

    precache_set = set(precache)
    css_dependencies = dependency_closure(
        ROOT / "assets/css/main.css", CSS_IMPORT_RE, errors
    )
    js_dependencies = dependency_closure(
        ROOT / "assets/js/main.js", IMPORT_RE, errors
    )
    required = {f"/{path}" for path in css_dependencies | js_dependencies}
    missing = sorted(required - precache_set)
    for path in missing:
        fail(errors, f"Offline app-shell dependency is not precached: {path}")

    image_bytes = 0
    total_bytes = 0
    for url in precache:
        target = local_path(url)
        if target is None:
            continue
        if not target.is_file():
            fail(errors, f"Precache entry does not exist: {url}")
            continue
        size = target.stat().st_size
        total_bytes += size
        if target.suffix.lower() in IMAGE_SUFFIXES:
            image_bytes += size

    if image_bytes > MAX_PRECACHE_IMAGE_BYTES:
        fail(
            errors,
            f"PWA image precache is {image_bytes / 1024:.1f} KiB; "
            f"budget is {MAX_PRECACHE_IMAGE_BYTES / 1024:.0f} KiB",
        )

    pwa = (ROOT / "assets/js/features/pwa.js").read_text(encoding="utf-8")
    if "const UPDATE_CHECK_INTERVAL_MS = 30 * 60 * 1000;" not in pwa:
        fail(errors, "PWA worker update polling must use a 30-minute interval")
    if "const UPDATE_EVENT_COOLDOWN_MS = 5 * 60 * 1000;" not in pwa:
        fail(errors, "PWA event-triggered checks must use a five-minute cooldown")
    if "checkInFlight" not in pwa:
        fail(errors, "PWA update checks must deduplicate concurrent requests")

    if "const CONTENT_REFRESH_INTERVAL_MS = 5 * 60 * 1000;" not in worker:
        fail(errors, "Service-worker catalogue refresh must be throttled to five minutes")
    if "lastContentRefreshAt" not in worker or "if (refreshInFlight) return refreshInFlight;" not in worker:
        fail(errors, "Service-worker catalogue refresh must be throttled and deduplicated")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(
        "PWA/performance budget audit passed: "
        f"{len(precache)} precache entries, "
        f"{image_bytes / 1024:.1f} KiB of precached images "
        f"(budget {MAX_PRECACHE_IMAGE_BYTES / 1024:.0f} KiB), "
        f"{total_bytes / 1024:.1f} KiB total precache payload."
    )
    print(
        "Offline dependency closure passed: "
        f"{len(css_dependencies)} CSS files and "
        f"{len(js_dependencies)} JavaScript modules are precached."
    )
    print("PWA refresh policy: 30-minute worker checks, five-minute event cooldown and catalogue refresh throttle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
