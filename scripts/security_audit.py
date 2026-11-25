#!/usr/bin/env python3
"""Check workflow pinning and prevent sensitive files entering the Pages output."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
WORKFLOWS = ROOT / ".github" / "workflows"

ACTION_RE = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_SITE_DIRS = {
    ".github", ".git", "docs", "scripts", "node_modules", "__pycache__",
    ".venv", "venv",
}
FORBIDDEN_DATA_DIRS = {
    ("data", "content"), ("data", "templates"), ("data", "schemas"),
    ("data", "drafts"),
}
SENSITIVE_NAMES = {
    ".env", ".npmrc", ".pypirc", ".netrc", "credentials", "credentials.json",
    "secrets.json", "id_rsa", "id_ed25519", "known_hosts",
}
SENSITIVE_SUFFIXES = {
    ".pem", ".p12", ".pfx", ".key", ".keytab", ".jks", ".kdbx",
    ".sqlite", ".sqlite3", ".db", ".log", ".bak", ".backup", ".swp",
}
TEXT_SUFFIXES = {
    ".html", ".js", ".mjs", ".cjs", ".json", ".css", ".xml", ".txt",
    ".md", ".yml", ".yaml", ".py", ".toml", ".webmanifest", ".svg",
}
SECRET_PATTERNS = [
    ("private-key material", re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("AWS access-key identifier", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("Stripe live secret", re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b")),
]
PUBLISHED_ONLY_FILES = {
    "SECURITY.md", ".gitleaksignore", ".gitleaks.toml", "package.json", "package-lock.json", "requirements-security.txt",
}


class PageMetadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        values = dict(attrs)
        name = values.get("name")
        if name:
            self.meta[name.lower()] = (values.get("content") or "").strip()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def audit_action_pins(errors: list[str]) -> int:
    count = 0
    files = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    if not files:
        fail(errors, "No GitHub Actions workflow files were found.")
        return count

    for workflow in files:
        source = workflow.read_text(encoding="utf-8")
        for match in ACTION_RE.finditer(source):
            reference = match.group(1)
            if reference.startswith("./"):
                continue
            if "@" not in reference:
                fail(errors, f"{workflow.relative_to(ROOT)}: action is not pinned: {reference}")
                continue
            action, ref = reference.rsplit("@", 1)
            if not SHA_RE.fullmatch(ref):
                fail(errors, f"{workflow.relative_to(ROOT)}: {action} must use a full 40-character commit SHA, got {ref!r}")
                continue
            count += 1
    return count


def audit_public_tree(errors: list[str]) -> tuple[int, int]:
    if not SITE.is_dir():
        fail(errors, "Missing _site directory. Run scripts/stage_site.py before this audit.")
        return 0, 0

    checked_files = 0
    checked_text = 0
    for path in sorted(SITE.rglob("*")):
        rel = path.relative_to(SITE)
        parts = tuple(part.lower() for part in rel.parts)
        name = path.name.lower()

        if path.is_dir():
            if name in FORBIDDEN_SITE_DIRS or parts[:2] in FORBIDDEN_DATA_DIRS:
                fail(errors, f"Development or private directory was copied to Pages output: {rel}")
            if name in {".ssh", "credentials", "secrets"}:
                fail(errors, f"Sensitive directory was copied to Pages output: {rel}")
            continue

        checked_files += 1
        if name in SENSITIVE_NAMES or name.startswith(".env."):
            fail(errors, f"Sensitive-looking filename was copied to Pages output: {rel}")
        if path.suffix.lower() in SENSITIVE_SUFFIXES:
            fail(errors, f"Sensitive or local-only file type was copied to Pages output: {rel}")
        if name in PUBLISHED_ONLY_FILES:
            fail(errors, f"Repository/tooling policy file should not be in the public site output: {rel}")
        if parts[:2] == ("data", "config") and name != "site.json":
            fail(errors, f"Unexpected public configuration file: {rel}")

        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 8 * 1024 * 1024:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        checked_text += 1
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(source):
                fail(errors, f"Possible {label} exposed in public output: {rel}")
    return checked_files, checked_text


def audit_draft_exclusions(errors: list[str]) -> int:
    checked = 0
    for kind in ("articles", "projects"):
        source_dir = ROOT / kind
        if not source_dir.is_dir():
            continue
        for source in sorted(source_dir.glob("*/index.html")):
            parser = PageMetadata()
            try:
                parser.feed(source.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError) as exc:
                fail(errors, f"Could not inspect publication status for {source.relative_to(ROOT)}: {exc}")
                continue
            key = "glab:article-status" if kind == "articles" else "glab:project-publication-status"
            default = "draft" if kind == "articles" else "published"
            status = parser.meta.get(key, default).lower()
            if status == "published":
                continue
            checked += 1
            output = SITE / kind / source.parent.name / "index.html"
            if output.exists():
                fail(errors, f"Unpublished {kind[:-1]} was included in Pages output: {source.parent.name}")
    return checked


def main() -> int:
    errors: list[str] = []
    action_count = audit_action_pins(errors)
    file_count, text_count = audit_public_tree(errors)
    draft_count = audit_draft_exclusions(errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"Security audit failed with {len(errors)} issue(s).")
        return 1

    print(f"PASS: {action_count} third-party action references use full commit SHAs.")
    print(f"PASS: {file_count} public files checked; {text_count} text files scanned for high-confidence secret patterns.")
    print(f"PASS: {draft_count} unpublished article/project page(s) are excluded from Pages output.")
    print("PASS: repository-only tooling and sensitive file types are excluded from Pages output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
