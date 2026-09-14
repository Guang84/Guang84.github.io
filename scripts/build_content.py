#!/usr/bin/env python3
"""Build and validate GLab's dynamic content artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://guang84.github.io"
STATIC_PAGES = [
    ("", "index.html"),
    ("projects/", "projects/index.html"),
    ("articles/", "articles/index.html"),
    ("about.html", "about.html"),
    ("contact.html", "contact.html"),
    ("privacy.html", "privacy.html"),
    ("terms.html", "terms.html"),
]
PUBLIC_SKIP_DIRS = {".git", ".github", ".agents", ".codex", "docs", "scripts", "_site"}
PUBLIC_SKIP_FILES = {".gitignore", "pending.txt", "README.md", "requirements.txt"}
RECORD_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.json$")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def site_config() -> dict:
    return read_json(ROOT / "data/config/site.json")


def record_sort_key(item: dict):
    return (
        item.get("featured") is not True,
        item.get("date", item.get("updated", "")),
        item.get("year", 0),
        item.get("title", ""),
    )


def load_records(kind: str) -> list[tuple[str, dict]]:
    base = ROOT / "data" / kind
    records = []
    for path in sorted(base.glob("*.json")):
        if path.name == "index.json":
            continue
        if not RECORD_NAME_RE.fullmatch(path.name):
            raise ValueError(f"Invalid {kind} filename: {path}")
        item = read_json(path)
        if item.get("id") != path.stem:
            raise ValueError(f"{path}: id must match filename")
        if item.get("publicationStatus", "published") == "published":
            records.append((path.name, item))
    if kind == "articles":
        records.sort(key=lambda row: (row[1].get("date", ""), row[1].get("title", "")), reverse=True)
    else:
        records.sort(key=lambda row: record_sort_key(row[1]))
    return records


def content_hash(records: list[tuple[str, dict]]) -> str:
    h = hashlib.sha256()
    for name, item in records:
        h.update(name.encode())
        h.update(json.dumps(item, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def update_catalog(kind: str) -> dict:
    records = load_records(kind)
    catalog = {
        "schemaVersion": 1,
        "contentVersion": content_hash(records),
        "updated": datetime.now(timezone.utc).date().isoformat(),
        "files": [name for name, _ in records],
    }
    write_json(ROOT / "data" / kind / "index.json", catalog)
    return catalog


def detail_url(kind: str, item_id: str, fragment: str = "") -> str:
    return f"/{kind}/?id={item_id}{fragment}"


def build_search_index(projects: list[tuple[str, dict]], articles: list[tuple[str, dict]]) -> list[dict]:
    rows = []
    for _, item in projects:
        base = {
            "id": item["id"],
            "summary": item.get("summary", ""),
            "tags": item.get("tags", []),
        }
        rows.append({**base, "type": "Project", "title": item["title"], "url": detail_url("projects", item["id"])})
        if item.get("guide", {}).get("title"):
            rows.append({
                **base,
                "type": "Project guide",
                "title": item["guide"]["title"],
                "summary": item["guide"].get("summary", base["summary"]),
                "url": detail_url("projects", item["id"], "#guide"),
            })
    for _, item in articles:
        rows.append({
            "type": item.get("kind", "Article"),
            "id": item["id"],
            "title": item["title"],
            "summary": item.get("excerpt", ""),
            "tags": item.get("tags", []),
            "url": detail_url("articles", item["id"]),
        })
    write_json(ROOT / "search-index.json", rows)
    return rows


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def build_feed(articles: list[tuple[str, dict]], config: dict) -> None:
    items = []
    for _, article in articles:
        date = parse_date(article.get("date", datetime.now(timezone.utc).date().isoformat()))
        url = f"{SITE_URL}{detail_url('articles', article['id'])}"
        items.append(
            "<item>"
            f"<title>{escape(article['title'])}</title>"
            f"<link>{escape(url)}</link>"
            f"<guid>{escape(url)}</guid>"
            f"<description>{escape(article.get('excerpt', ''))}</description>"
            f"<pubDate>{format_datetime(date)}</pubDate>"
            "</item>"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        "<title>GLab articles</title>"
        f"<link>{SITE_URL}/articles/</link>"
        f"<description>{escape(config.get('description', ''))}</description>"
        f"{''.join(items)}"
        "</channel></rss>\n"
    )
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")


def build_sitemap(projects: list[tuple[str, dict]], articles: list[tuple[str, dict]]) -> None:
    entries = []
    today = datetime.now(timezone.utc).date().isoformat()
    for loc, path in STATIC_PAGES:
        entries.append((f"{SITE_URL}/{loc}", today))
    for _, item in projects:
        entries.append((f"{SITE_URL}{detail_url('projects', item['id'])}", item.get("updated", today)))
    for _, item in articles:
        entries.append((f"{SITE_URL}{detail_url('articles', item['id'])}", item.get("updated", item.get("date", today))))
    body = "\n".join(f"  <url><loc>{escape(url)}</loc><lastmod>{escape(date)}</lastmod></url>" for url, date in entries)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n",
        encoding="utf-8",
    )


def public_files() -> list[str]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts[0] in PUBLIC_SKIP_DIRS or rel.name in PUBLIC_SKIP_FILES:
            continue
        if rel.parts[:2] == ("data", "templates"):
            continue
        files.append("/" + rel.as_posix())
    return files


def update_service_worker(config: dict) -> None:
    path = ROOT / "service-worker.js"
    text = path.read_text(encoding="utf-8")
    precache = ["/"]
    for rel in public_files():
        if rel in {"/service-worker.js"}:
            continue
        if rel == "/index.html":
            precache.append(rel)
            continue
        if rel.endswith((".html", ".css", ".js", ".json", ".webmanifest", ".png", ".xml")):
            precache.append(rel)
    for folder in ["/projects/", "/articles/"]:
        if folder not in precache:
            precache.append(folder)
    unique = []
    for item in precache:
        if item not in unique:
            unique.append(item)
    h = hashlib.sha256()
    for rel in unique:
        target = ROOT / rel.lstrip("/")
        if target.is_file():
            h.update(rel.encode())
            h.update(target.read_bytes())
    fingerprint = h.hexdigest()[:16]
    version = f"glab-v{config.get('version', '0.0.0')}-{fingerprint}"
    replacement = (
        f"const VERSION='{version}', CACHE_PREFIX='glab-', STATIC_CACHE=`${{VERSION}}-static`, "
        f"CONTENT_CACHE=`${{VERSION}}-content`;\n"
        f"const PRECACHE={json.dumps(unique, separators=(',', ':'))};"
    )
    text = re.sub(r"^const VERSION=.*?;\nconst PRECACHE=.*?;", replacement, text, count=1, flags=re.S)
    text = re.sub(r"// Build fingerprint: .*", f"// Build fingerprint: {fingerprint}", text)
    path.write_text(text, encoding="utf-8")


def validate_links(projects: list[tuple[str, dict]], articles: list[tuple[str, dict]]) -> list[str]:
    project_ids = {item["id"] for _, item in projects}
    article_ids = {item["id"] for _, item in articles}
    errors = []
    pattern = re.compile(r"/(projects|articles)/\?id=([a-z0-9-]+)")
    for path in sorted(ROOT.glob("*.html")) + sorted((ROOT / "projects").glob("*.html")) + sorted((ROOT / "articles").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        for kind, item_id in pattern.findall(text):
            if kind == "projects" and item_id not in project_ids:
                errors.append(f"{path.relative_to(ROOT)} links missing project id {item_id}")
            if kind == "articles" and item_id not in article_ids:
                errors.append(f"{path.relative_to(ROOT)} links missing article id {item_id}")
    return errors


def validate_records(projects: list[tuple[str, dict]], articles: list[tuple[str, dict]]) -> list[str]:
    errors = []
    for kind, rows in [("projects", projects), ("articles", articles)]:
        seen = set()
        for name, item in rows:
            if item["id"] in seen:
                errors.append(f"Duplicate {kind} id: {item['id']}")
            seen.add(item["id"])
            for field in ["title", "sections"]:
                if not item.get(field):
                    errors.append(f"data/{kind}/{name} missing {field}")
            if kind == "projects":
                for field in ["category", "year", "status", "summary"]:
                    if not item.get(field):
                        errors.append(f"data/{kind}/{name} missing {field}")
            if kind == "articles":
                for field in ["date", "excerpt"]:
                    if not item.get(field):
                        errors.append(f"data/{kind}/{name} missing {field}")
    return errors


def stage_site() -> None:
    dest = ROOT / "_site"
    if dest.exists():
        shutil.rmtree(dest)
    for rel in public_files():
        src = ROOT / rel.lstrip("/")
        target = dest / rel.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)


def build(write: bool, stage: bool) -> list[str]:
    config = site_config()
    if write:
        update_catalog("projects")
        update_catalog("articles")
    projects = load_records("projects")
    articles = load_records("articles")
    if write:
        build_search_index(projects, articles)
        build_feed(articles, config)
        build_sitemap(projects, articles)
        update_service_worker(config)
    errors = validate_records(projects, articles)
    errors.extend(validate_links(projects, articles))
    if stage:
        stage_site()
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Regenerate dynamic artifacts.")
    parser.add_argument("--stage", action="store_true", help="Create _site after checks.")
    args = parser.parse_args()
    errors = build(write=args.write, stage=args.stage)
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
