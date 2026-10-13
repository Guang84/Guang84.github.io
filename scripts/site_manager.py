#!/usr/bin/env python3
"""Interactive tools for creating, checking, and previewing the GLab website."""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_ -]*\}\}")
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}


class MetadataParser(HTMLParser):
    """Read the GLab page title and status from its metadata."""

    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "meta":
            values = dict(attrs)
            name = values.get("name")
            content = values.get("content")
            if name and content is not None:
                self.metadata[name.lower()] = content.strip()


def prompt_required(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Please enter a value.")


def prompt_default(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def prompt_slug() -> str:
    while True:
        slug = prompt_required("Folder name / URL slug (lowercase letters, numbers, hyphens): ")
        if SLUG_RE.fullmatch(slug):
            return slug
        print("Use a lowercase slug such as `my-new-project` (no spaces or underscores).")


def prompt_tags(default: str) -> list[str]:
    while True:
        raw = prompt_default("Comma-separated tags", default)
        tags = list(dict.fromkeys(tag.strip() for tag in raw.split(",") if tag.strip()))
        if tags:
            return tags
        print("Enter at least one non-empty tag.")


def prompt_repository_url() -> str:
    while True:
        value = input("Public source repository URL (optional; press Enter to skip): ").strip()
        if not value:
            return ""
        parsed = urlsplit(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
        print("Enter a complete http(s) URL, or leave it blank.")


def replace_meta_content(source: str, name: str, value: str) -> str:
    pattern = re.compile(
        r'(<meta\s+name="' + re.escape(name) + r'"\s+content=")[^"]*(">)',
        re.IGNORECASE,
    )
    return pattern.sub(lambda match: match.group(1) + html.escape(value, quote=True) + match.group(2), source)


def replace_json_ld_text(source: str, title: str, summary: str) -> str:
    def replace_values(match: re.Match[str]) -> str:
        script = match.group(2)
        for key, value in (("headline", title), ("description", summary)):
            pattern = re.compile(r'("' + key + r'"\s*:\s*")[^"]*(")')
            encoded = json.dumps(value, ensure_ascii=False)[1:-1]
            encoded = encoded.replace("<", r"\u003c").replace(">", r"\u003e").replace("&", r"\u0026")
            script = pattern.sub(lambda value_match: value_match.group(1) + encoded + value_match.group(2), script, count=1)
        return match.group(1) + script + match.group(3)

    return re.sub(
        r'(<script\s+type="application/ld\+json">\s*)(.*?)(\s*</script>)',
        replace_values,
        source,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )


def render_template(kind: str, slug: str, title: str, summary: str) -> str:
    template_name = "article-template.html" if kind == "articles" else "project-template.html"
    template_path = TEMPLATES / template_name
    if not template_path.is_file():
        raise FileNotFoundError(f"Missing page template: {template_path.relative_to(ROOT)}")

    content = template_path.read_text(encoding="utf-8")
    escaped = html.escape
    replacements = {
        "{{ARTICLE_SLUG}}": slug,
        "{{PROJECT_SLUG}}": slug,
        "{{ARTICLE_TITLE}}": escaped(title, quote=True),
        "{{PROJECT_TITLE}}": escaped(title, quote=True),
        "{{ARTICLE_EXCERPT}}": escaped(summary, quote=True),
        "{{PROJECT_SUMMARY}}": escaped(summary, quote=True),
    }

    if kind == "articles":
        tags = prompt_tags("Technology, Networking")
        read_time = prompt_default("Estimated reading time", "5 min read")
        replacements["{{READ_TIME}}"] = escaped(read_time, quote=True)
        replacements["{{SOURCE_URL}}"] = ""
        replacements["{{SOURCE_TITLE}}"] = "Add a source before publishing"
        replacements["{{WHAT_THIS_SOURCE_SUPPORTS}}"] = "Describe what the source supports."
        content = replace_meta_content(content, "glab:article-tags", ", ".join(tags))
        content = content.replace(
            '<ul class="tag-list"><li>Technology</li><li>Networking</li></ul>',
            '<ul class="tag-list">' + "".join(f"<li>{escaped(tag)}</li>" for tag in tags) + "</ul>",
        )
    else:
        category = prompt_default("Project category", "Technology")
        status = prompt_default("Project status", "In development")
        repository_url = prompt_repository_url()
        tags = prompt_tags("Technology, Documentation")
        replacements.update(
            {
                "{{PROJECT_CATEGORY}}": escaped(category, quote=True),
                "{{PROJECT_STATUS}}": escaped(status, quote=True),
                "{{PROJECT_YEAR}}": str(date.today().year),
                "{{REPOSITORY_URL}}": escaped(repository_url, quote=True),
                "{{TAG_ONE}}": escaped(tags[0]),
                "{{TAG_TWO}}": escaped(tags[1] if len(tags) > 1 else tags[0]),
            }
        )
        content = replace_meta_content(content, "glab:project-tags", ", ".join(tags))

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    content = content.replace("YYYY-MM-DD", date.today().isoformat())
    content = PLACEHOLDER_RE.sub("Draft this section before publishing.", content)
    return replace_json_ld_text(content, title, summary)


def create_page(kind: str) -> None:
    slug = prompt_slug()
    target = ROOT / kind / slug / "index.html"
    if target.exists():
        print(f"Page already exists: {target.relative_to(ROOT)}")
        return

    title = prompt_required("Page title: ")
    summary_label = "Short article excerpt" if kind == "articles" else "Short project summary"
    summary = prompt_required(f"{summary_label}: ")
    try:
        content = render_template(kind, slug, title, summary)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as error:
        print(f"Could not create the page: {error}")
        return

    print(f"Created draft page: {target.relative_to(ROOT)}")
    print("The page is marked as a draft. Complete the body and review it before publishing.")
    if input("Add public-safe files to this page now? [y/N]: ").strip().lower() in {"y", "yes"}:
        add_files(kind, slug)


def page_exists(kind: str, slug: str) -> bool:
    if kind not in {"articles", "projects"} or not SLUG_RE.fullmatch(slug):
        print("Choose a valid article or project slug.")
        return False
    page = ROOT / kind / slug / "index.html"
    if not page.is_file():
        print(f"No page found at {page.relative_to(ROOT)}.")
        return False
    return True


def add_files(kind: str, slug: str) -> None:
    if not page_exists(kind, slug):
        return

    destination = ROOT / "assets" / kind / slug
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"Could not prepare the asset folder: {error}")
        return
    print("Only add files you have permission to publish; review images for private information.")
    print("Enter one source file path at a time. Relative paths are based at the repository root.")
    added = 0
    while True:
        raw_path = input("Source file path (blank to finish): ").strip()
        if not raw_path:
            break
        source = Path(raw_path).expanduser()
        if not source.is_absolute():
            source = ROOT / source
        try:
            source = source.resolve(strict=True)
        except OSError as error:
            print(f"Cannot read {raw_path!r}: {error}")
            continue
        if not source.is_file():
            print(f"Not a regular file: {raw_path}")
            continue

        target = destination / source.name
        if target.exists():
            print(f"File already exists; not overwriting it: {target.relative_to(ROOT)}")
            continue
        try:
            shutil.copy2(source, target)
        except OSError as error:
            print(f"Could not copy {source}: {error}")
            continue

        asset_url = "/" + quote(target.relative_to(ROOT).as_posix(), safe="/-._~")
        if target.suffix.lower() in IMAGE_EXTENSIONS:
            alt = prompt_required("Describe this image for its alt text: ")
            width = prompt_default("Image width in pixels", "1200")
            height = prompt_default("Image height in pixels", "800")
            if not (width.isdigit() and height.isdigit()):
                print("Dimensions must be whole numbers. Use 1200 x 800 in the snippet and edit if needed.")
                width, height = "1200", "800"
            snippet = (
                f'<figure class="content-figure">\n'
                f'  <img src="{html.escape(asset_url, quote=True)}" '
                f'alt="{html.escape(alt, quote=True)}" width="{width}" height="{height}" '
                'loading="lazy" decoding="async">\n'
                f'  <figcaption>{html.escape(alt)}</figcaption>\n'
                "</figure>"
            )
        else:
            label = html.escape(source.stem)
            snippet = f'<a href="{html.escape(asset_url, quote=True)}">{label}</a>'
        print(f"Copied to {target.relative_to(ROOT)}")
        print("Paste this link into the page where it should appear:\n" + snippet)
        added += 1
    print(f"Added {added} file(s).")


def choose_kind() -> str:
    while True:
        choice = input("Content type: [1] Project  [2] Article: ").strip()
        if choice == "1":
            return "projects"
        if choice == "2":
            return "articles"
        print("Choose 1 for a project or 2 for an article.")


def list_content() -> None:
    for kind in ("projects", "articles"):
        print(f"\n{kind.title()}:")
        pages = sorted((ROOT / kind).glob("*/index.html"))
        if not pages:
            print("  (none)")
            continue
        for page in pages:
            parser = MetadataParser()
            parser.feed(page.read_text(encoding="utf-8"))
            prefix = "glab:project-" if kind == "projects" else "glab:article-"
            status_key = prefix + ("publication-status" if kind == "projects" else "status")
            status = parser.metadata.get(status_key, "draft")
            title = parser.metadata.get(prefix + "title", page.parent.name)
            print(f"  [{status}] {page.parent.name} — {title}")


def run_script(label: str, script_name: str) -> int:
    script = ROOT / "scripts" / script_name
    print(f"\n{label}…")
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, check=False)
    if result.returncode:
        print(f"{label} failed with exit code {result.returncode}.")
    else:
        print(f"{label} completed.")
    return result.returncode


def run_full_check() -> None:
    if run_script("Release metadata and source-link checks", "release_check.py") != 0:
        return
    if run_script("Build and stage the site", "stage_site.py") != 0:
        return
    run_script("Staged HTML, local-link, image, and generated-file audit", "site_audit.py")


def preview_site() -> None:
    if not (ROOT / "_site").is_dir():
        print("No staged site found. Run the full site check or build/stage the site first.")
        return
    print("Previewing http://localhost:8000/ — press Ctrl+C to return to the menu.")
    try:
        subprocess.run(
            [sys.executable, "-m", "http.server", "8000", "--directory", str(ROOT / "_site")],
            cwd=ROOT,
            check=False,
        )
    except KeyboardInterrupt:
        print("\nPreview stopped.")


def show_menu() -> None:
    print(
        "\nGLab site manager\n"
        "  1. Full site check (metadata, build, local links, fragments, images)\n"
        "  2. Check release metadata and source links\n"
        "  3. Build and stage the site\n"
        "  4. Run browser smoke tests\n"
        "  5. Create a project draft\n"
        "  6. Create an article draft\n"
        "  7. Add files to an existing page\n"
        "  8. List projects and articles\n"
        "  9. Preview the staged site\n"
        "  0. Exit"
    )


def main() -> int:
    actions = {
        "1": run_full_check,
        "2": lambda: run_script("Release metadata and source-link checks", "release_check.py"),
        "3": lambda: run_script("Build and stage the site", "stage_site.py"),
        "4": lambda: run_script("Browser smoke tests", "browser_smoke.py"),
        "5": lambda: create_page("projects"),
        "6": lambda: create_page("articles"),
        "8": list_content,
        "9": preview_site,
    }
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye.")
            return 0
        if choice == "7":
            kind = choose_kind()
            slug = prompt_slug()
            add_files(kind, slug)
        elif choice in actions:
            actions[choice]()
        else:
            print("Choose one of the listed menu options.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print("\nSite manager closed.")
        raise SystemExit(0)
