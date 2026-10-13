#!/usr/bin/env python3
"""Build GLab archives and deployment artifacts from canonical full-page HTML."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def configured_site_url() -> str:
    """Read the canonical host from the single editable site configuration."""
    fallback = "https://guang84.github.io"
    try:
        config = json.loads((ROOT / "data/config/site.json").read_text(encoding="utf-8"))
        value = str(config.get("url", "")).strip().rstrip("/")
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.netloc and parsed.path == "" and not parsed.query and not parsed.fragment:
            return value
    except (OSError, ValueError, TypeError):
        pass
    return fallback


SITE_URL = configured_site_url()
STATIC_PAGES = [
    ("", "index.html"), ("projects/", "projects/index.html"), ("articles/", "articles/index.html"),
    ("about.html", "about.html"), ("contact.html", "contact.html"), ("privacy.html", "privacy.html"),
    ("terms.html", "terms.html"), ("start-here.html", "start-here.html"),
    ("project-checklist.html", "project-checklist.html"), ("editorial-policy.html", "editorial-policy.html"),
]
PUBLIC_SKIP_DIRS = {".git", ".github", ".agents", ".codex", "docs", "scripts", "_site", "__pycache__", "content"}
PUBLIC_SKIP_FILES = {".gitignore", "pending.txt", "README.md", "requirements.txt", "LICENSE.txt", "CHANGELOG-QUALITY-UPDATE.md"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.canonical = ""
        self.h1 = 0
        self.main = 0
        self.body = 0
        self.title_text = False
        self.title = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name"):
            self.meta[attrs["name"].lower()] = attrs.get("content", "").strip()
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "").strip()
        if tag == "h1": self.h1 += 1
        if tag == "main": self.main += 1
        if tag == "body": self.body += 1
        if tag == "title": self.title_text = True
    def handle_endtag(self, tag):
        if tag == "title": self.title_text = False
    def handle_data(self, data):
        if self.title_text: self.title.append(data)

def page_info(path: Path) -> MetaParser:
    parser = MetaParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser

def meta_item(path: Path, kind: str) -> dict | None:
    info = page_info(path)
    prefix = "glab:article-" if kind == "articles" else "glab:project-"
    m = info.meta
    # Legacy URL redirects may live under articles/ or projects/ so they can be
    # deployed, but noindex pages must never become content catalogue records.
    if "noindex" in m.get("robots", "").lower():
        return None
    status = m.get(prefix + ("status" if kind == "articles" else "publication-status"), "draft" if kind == "articles" else "published").lower()
    if status != "published":
        return None
    slug = path.parent.name
    if not SLUG_RE.fullmatch(slug): raise ValueError(f"Invalid {kind[:-1]} slug: {slug}")
    title = m.get(prefix + "title", "")
    summary = m.get(prefix + ("excerpt" if kind == "articles" else "summary"), "")
    if not title or not summary: raise ValueError(f"{path.relative_to(ROOT)} needs {prefix}title and {prefix}{'excerpt' if kind == 'articles' else 'summary'} metadata")
    expected = f"{SITE_URL}/{kind}/{slug}/"
    if info.canonical != expected: raise ValueError(f"{path.relative_to(ROOT)} canonical must be {expected}")
    if info.h1 != 1 or info.main != 1 or info.body != 1: raise ValueError(f"{path.relative_to(ROOT)} must have one h1, one main, and one body")
    text = path.read_text(encoding="utf-8")
    if re.search(r"\{\{[A-Z][A-Z0-9_ -]*\}\}", text): raise ValueError(f"Published page {path.relative_to(ROOT)} contains template placeholders")
    tags = [x.strip() for x in m.get(prefix + "tags", "General").split(",") if x.strip()]
    featured = m.get(prefix + "featured", "false").lower() == "true"
    updated = m.get(prefix + "updated" if kind == "articles" else prefix + "updated", m.get(prefix+"date", ""))
    if kind == "articles":
        date = m.get(prefix + "date", "")
        if not DATE_RE.fullmatch(date): raise ValueError(f"{path.relative_to(ROOT)} has invalid glab:article-date")
        if not DATE_RE.fullmatch(updated): raise ValueError(f"{path.relative_to(ROOT)} has invalid glab:article-updated")
        return {"id":slug,"title":title,"date":date,"updated":updated,"excerpt":summary,"kind":m.get(prefix+"kind","Article"),"readTime":m.get(prefix+"read-time",""),"tags":tags,"publicationStatus":"published","featured":featured}
    year = m.get(prefix + "year", "")
    if not year.isdigit(): raise ValueError(f"{path.relative_to(ROOT)} needs numeric glab:project-year")
    if not m.get(prefix+"category") or not m.get(prefix+"status"):
        raise ValueError(f"{path.relative_to(ROOT)} needs project category and status metadata")
    return {"id":slug,"title":title,"category":m[prefix+"category"],"year":int(year),"status":m[prefix+"status"],"summary":summary,"updated":updated or f"{year}-01-01","tags":tags,"repository":{"url":m.get(prefix+"repository","")},"demoUrl":m.get(prefix+"demo",""),"featured":featured,"publicationStatus":"published","guide":{"title":m.get(prefix+"guide-title",""),"summary":m.get(prefix+"guide-summary","")}}

def load_records(kind: str) -> list[dict]:
    base = ROOT / kind
    rows=[]
    for path in sorted(base.glob("*/index.html")):
        item = meta_item(path, kind)
        if item is not None: rows.append(item)
    if kind == "articles": rows.sort(key=lambda x:(x.get("date",""),x.get("title","")), reverse=True)
    else: rows.sort(key=lambda x:(not x.get("featured",False),x.get("year",0),x.get("title","")))
    return rows

def file_hash(items: list[dict]) -> str:
    return hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]

def write_catalog(kind: str, items: list[dict]) -> None:
    target = ROOT / "data" / kind / "index.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    payload={"schemaVersion":2,"contentVersion":file_hash(items),"updated":datetime.now(timezone.utc).date().isoformat(),"items":items}
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def detail_url(kind: str, item_id: str, fragment: str = "") -> str:
    return f"/{kind}/{item_id}/{fragment}"

def build_search_index(projects: list[dict], articles: list[dict]) -> None:
    rows=[]
    for item in projects:
        base={"id":item["id"],"summary":item.get("summary",""),"tags":item.get("tags",[])}
        rows.append({**base,"type":"Project","title":item["title"],"url":detail_url("projects",item["id"])})
        if item.get("guide",{}).get("title"):
            rows.append({**base,"type":"Project guide","title":item["guide"]["title"],"summary":item["guide"].get("summary",base["summary"]),"url":detail_url("projects",item["id"],"#guide")})
    for item in articles:
        rows.append({"type":item.get("kind","Article"),"id":item["id"],"title":item["title"],"summary":item.get("excerpt",""),"tags":item.get("tags",[]),"url":detail_url("articles",item["id"])})
    rows.extend([
      {"type":"Guide","id":"start-here","title":"Start here","summary":"Choose a practical reading path through GLab articles and project case studies.","tags":[],"url":"/start-here.html"},
      {"type":"Guide","id":"project-checklist","title":"Before you run a project","summary":"Evaluate prerequisites, permissions, risks, verification, and rollback before trying a project.","tags":[],"url":"/project-checklist.html"},
      {"type":"Guide","id":"editorial-policy","title":"Editorial policy and corrections","summary":"How GLab handles sources, AI-assisted editing, project status, limitations, and corrections.","tags":[],"url":"/editorial-policy.html"},
    ])
    (ROOT/"search-index.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def build_feed(articles: list[dict], config: dict) -> None:
    items=[]
    for article in articles:
        date=datetime.fromisoformat(article.get("date",datetime.now(timezone.utc).date().isoformat())).replace(tzinfo=timezone.utc)
        url=f"{SITE_URL}{detail_url('articles',article['id'])}"
        items.append("<item>"+f"<title>{escape(article['title'])}</title><link>{escape(url)}</link><guid>{escape(url)}</guid><description>{escape(article.get('excerpt',''))}</description><pubDate>{format_datetime(date)}</pubDate></item>")
    feed='<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>GLab articles</title>'+f"<link>{SITE_URL}/articles/</link><description>{escape(config.get('description',''))}</description>"+"".join(items)+"</channel></rss>\n"
    (ROOT/"feed.xml").write_text(feed,encoding="utf-8")

def build_sitemap(projects: list[dict], articles: list[dict]) -> None:
    entries=[];today=datetime.now(timezone.utc).date().isoformat()
    for loc,_ in STATIC_PAGES: entries.append((f"{SITE_URL}/{loc}",today))
    for item in projects: entries.append((f"{SITE_URL}{detail_url('projects',item['id'])}",item.get("updated",today)))
    for item in articles: entries.append((f"{SITE_URL}{detail_url('articles',item['id'])}",item.get("updated",item.get("date",today))))
    body="\n".join(f"  <url><loc>{escape(url)}</loc><lastmod>{escape(date)}</lastmod></url>" for url,date in entries)
    (ROOT/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+body+'\n</urlset>\n',encoding="utf-8")

def public_files() -> list[str]:
    files=[]
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file(): continue
        rel=path.relative_to(ROOT)
        if not rel.parts: continue
        if rel.parts[0] in PUBLIC_SKIP_DIRS or rel.name in PUBLIC_SKIP_FILES: continue
        if rel.parts[0] == "data" and len(rel.parts)>1 and rel.parts[1] in {"content","templates","schemas"}: continue
        if rel.parts[0] in {"articles", "projects"} and len(rel.parts)>2 and rel.parts[-1] == "index.html":
            info=page_info(path)
            if rel.parts[0] == "articles":
                publication_status = info.meta.get("glab:article-status", "draft").lower()
            else:
                publication_status = info.meta.get("glab:project-publication-status", "published").lower()
            if publication_status != "published": continue
        if rel.parts[0] == "content": continue
        files.append("/"+rel.as_posix())
    return files

def update_service_worker(config: dict) -> None:
    path=ROOT/"service-worker.js";text=path.read_text(encoding="utf-8")
    precache=["/"]
    for rel in public_files():
        if rel == "/service-worker.js": continue
        # The hymnal's large collections are downloaded explicitly in the app; do not cache all song text on first visit.
        if rel.startswith("/data/RongmeiHymnal/"): continue
        if rel == "/index.html": precache.append(rel);continue
        if rel.endswith((".html",".css",".js",".json",".webmanifest",".png",".xml",".svg",".ico")): precache.append(rel)
    for folder in ["/projects/","/articles/"]:
        if folder not in precache:precache.append(folder)
    unique=list(dict.fromkeys(precache))
    h=hashlib.sha256()
    for rel in unique:
        target=ROOT/rel.lstrip("/")
        if target.is_file():h.update(rel.encode());h.update(target.read_bytes())
    fingerprint=h.hexdigest()[:16]
    version=f"glab-v{config.get('version','0.0.0')}-{fingerprint}"
    replacement=f"const VERSION='{version}', CACHE_PREFIX='glab-', STATIC_CACHE=`${{VERSION}}-static`, CONTENT_CACHE=`${{VERSION}}-content`;\nconst PRECACHE={json.dumps(unique,separators=(',',':'))};"
    text=re.sub(r"^const VERSION\b.*?const PRECACHE\s*=\s*\[.*?\];",replacement,text,count=1,flags=re.S)
    text=re.sub(r"// Build fingerprint: .*",f"// Build fingerprint: {fingerprint}",text)
    path.write_text(text,encoding="utf-8")

def update_archive(root_path: Path, kind: str, items: list[dict]) -> None:
    if not root_path.exists(): raise ValueError(f"Missing archive page: {root_path}")
    # HTMLParser-based boundary replacement avoids a nested-div regex truncating the card list.
    text=root_path.read_text(encoding="utf-8")
    tag='div'
    marker='data-content-root'
    start_re=re.compile(r'<div\b(?=[^>]*\b'+marker+r'\b)[^>]*>',re.I)
    match=start_re.search(text)
    if not match: raise ValueError(f"{root_path.relative_to(ROOT)} does not contain data-content-root")
    start=match.start(); open_end=match.end(); depth=1
    token_re=re.compile(r'<div\b[^>]*>|</div\s*>',re.I)
    for tok in token_re.finditer(text,open_end):
        if tok.group(0).lower().startswith('<div'): depth+=1
        else: depth-=1
        if depth==0:
            end=tok.end();break
    else: raise ValueError(f"Unclosed archive root in {root_path.relative_to(ROOT)}")
    cards=[]
    if kind=='articles':
        for item in items:
            query=' '.join([item['id'],item['title'],item.get('excerpt',''),*item.get('tags',[])]).lower()
            tags=escape(query,quote=True)
            card=f'<a class="writing-item" data-project-card data-category="{escape(item.get("kind","Article"),quote=True)}" data-search="{tags}" href="{detail_url("articles",item["id"])}"><time class="writing-date" datetime="{escape(item.get("date",""))}">{escape(item.get("date",""))}</time><div><p class="eyebrow">{escape(item.get("kind","Article"))} · {escape(item.get("readTime",""))}</p><h2>{escape(item["title"])}</h2></div><p class="writing-excerpt">{escape(item.get("excerpt",""))}</p><span aria-hidden="true">↗</span></a>'
            cards.append(card)
    else:
        for index,item in enumerate(items):
            query=' '.join([item['id'],item['title'],item.get('summary',''),item.get('category',''),*item.get('tags',[])]).lower()
            tags_html = ''.join(f"<li>{escape(t)}</li>" for t in item.get("tags", []))
            card = f"""<article class="project-card" data-project-card data-category="{escape(item.get('category','Other'), quote=True)}" data-search="{escape(query, quote=True)}"><div class="project-card-head"><span class="project-number">{index+1:02}</span><span class="project-status">{escape(item.get('status',''))}</span></div><div class="project-copy"><p class="eyebrow">{escape(item.get('category','Project'))} · {escape(str(item.get('year','')))}</p><h2>{escape(item['title'])}</h2><p>{escape(item.get('summary',''))}</p><ul>{tags_html}</ul><a href="{detail_url('projects', item['id'])}">Read complete case study →</a></div></article>"""
            cards.append(card)
    replacement=text[start:open_end]+"\n"+"\n".join(cards)+"\n      </div>"
    root_path.write_text(text[:start]+replacement+text[end:],encoding="utf-8")

def validate_links() -> list[str]:
    errors=[]
    local_re=re.compile(r"\b(?:href|src)\s*=\s*([\"\'])(.*?)\1",re.I|re.S)
    for page in sorted(ROOT.rglob("*.html")):
        rel=page.relative_to(ROOT)
        if rel.parts[0] in {"docs","scripts","_site","content","data"}: continue
        if page.name=='index.html' and page.parent.name in {'articles','projects'}: pass
        source=page.read_text(encoding="utf-8")
        for _,raw in local_re.findall(source):
            value=raw.strip()
            if not value.startswith('/') or value.startswith('//'):continue
            path=urlsplit(value).path
            if not path:continue
            if path.endswith('/'): target=ROOT/path.lstrip('/')/'index.html'
            else:
                target=ROOT/path.lstrip('/')
                if not target.exists() and (ROOT/path.lstrip('/')/'index.html').exists():target=ROOT/path.lstrip('/')/'index.html'
            if not target.exists(): errors.append(f"{rel}: broken local link {value}")
    return errors

def validate_catalog(items_by_kind: dict[str,list[dict]]) -> list[str]:
    errors=[]
    for kind,items in items_by_kind.items():
        seen=set()
        for item in items:
            if item['id'] in seen:errors.append(f"Duplicate {kind} slug: {item['id']}")
            seen.add(item['id'])
            target=ROOT/kind/item['id']/'index.html'
            if not target.is_file():errors.append(f"Missing canonical page {target.relative_to(ROOT)}")
    # The generated browser catalogue should contain metadata only, not long-form bodies.
    for kind,items in items_by_kind.items():
        path=ROOT/'data'/kind/'index.json'
        if path.exists():
            try: saved=json.loads(path.read_text(encoding='utf-8'))
            except Exception as ex:errors.append(f"Invalid {path.relative_to(ROOT)}: {ex}");continue
            if saved.get('items') != items:errors.append(f"{path.relative_to(ROOT)} is out of date; run scripts/stage_site.py")
            for item in saved.get('items',[]):
                if 'sections' in item or 'body' in item:errors.append(f"{path.relative_to(ROOT)} must contain metadata only")
    return errors

def validate_layout_css() -> list[str]:
    """Catch the .detail-section two-column content placement regression."""
    css_path = ROOT / "assets/css/95-site-polish.css"
    if not css_path.is_file():
        return ["Missing shared layout stylesheet: assets/css/95-site-polish.css"]
    css = css_path.read_text(encoding="utf-8")
    required = (
        ".detail-section > .eyebrow",
        ".detail-section > h2",
        ".detail-section > .eyebrow ~ *",
        ".detail-section > .eyebrow ~ .timeline-list",
        "grid-column: 1 / -1;",
        ".detail-section > h2 ~ *",
        "@media (max-width: 860px)",
        "grid-column: 1;",
        "grid-column: 2;",
    )
    missing = [token for token in required if token not in css]
    return ["Shared layout CSS is missing required content-column rule(s): " + ", ".join(missing)] if missing else []



def validate_site_config() -> list[str]:
    errors = []
    path = ROOT / "data/config/site.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:
        return [f"Invalid site configuration {path.relative_to(ROOT)}: {ex}"]
    url = str(config.get("url", "")).strip()
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        errors.append("data/config/site.json url must be an HTTPS origin with no path, query, or fragment")
    elif url.rstrip("/") != SITE_URL:
        errors.append(f"Canonical URL mismatch: configured={url!r}, build={SITE_URL!r}")
    if not config.get("version"):
        errors.append("data/config/site.json must specify a site version")
    return errors

def build(write: bool, stage: bool) -> list[str]:
    errors=[]
    errors.extend(validate_site_config())
    try:
        articles=load_records('articles')
        projects=load_records('projects')
    except Exception as ex:
        return [f"Content metadata validation failed: {ex}"]
    if write:
        write_catalog('articles',articles);write_catalog('projects',projects)
        config=json.loads((ROOT/'data/config/site.json').read_text(encoding='utf-8'))
        update_archive(ROOT/'articles/index.html','articles',articles)
        update_archive(ROOT/'projects/index.html','projects',projects)
        build_search_index(projects,articles)
        build_feed(articles,config)
        build_sitemap(projects,articles)
        update_service_worker(config)
    errors.extend(validate_catalog({'articles':articles,'projects':projects}))
    errors.extend(validate_layout_css())
    for loc,rel in STATIC_PAGES:
        if not (ROOT/rel).exists():errors.append(f"Missing required static page: {rel}")
    if not (ROOT/'ads.txt').exists():errors.append('Missing ads.txt')
    errors.extend(validate_links())
    if stage:
        dest=ROOT/'_site'
        if dest.exists():shutil.rmtree(dest)
        for rel in public_files():
            src=ROOT/rel.lstrip('/')
            target=dest/rel.lstrip('/')
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,target)
        # Every sitemap URL for an article/project should resolve to staged HTML.
        for kind,items in [('articles',articles),('projects',projects)]:
            for item in items:
                if not (dest/kind/item['id']/'index.html').is_file():errors.append(f"Staged page missing: {kind}/{item['id']}/index.html")
    return errors

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--stage',action='store_true')
    args=parser.parse_args()
    errors=build(write=args.write,stage=args.stage)
    if errors:
        for error in errors:print(error)
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
