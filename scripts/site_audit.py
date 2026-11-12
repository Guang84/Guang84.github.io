#!/usr/bin/env python3
"""Audit GLab's generated static site for broken local references and release hygiene."""
from __future__ import annotations
import json, re, sys, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[]; self.duplicate_ids=[]; self.refs=[]; self.images=[]; self.h1=0; self.main=0; self.footer=0; self.title=0; self.canonical=0; self.description=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids: self.duplicate_ids.append(a['id'])
            self.ids.append(a['id'])
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main += 1
        if tag == 'footer' and 'detail-section' not in (a.get('class') or '').split(): self.footer += 1
        if tag == 'title': self.title += 1
        rel=a.get('rel') or ''
        if isinstance(rel, list): rel=' '.join(rel)
        if tag == 'link' and 'canonical' in rel.split(): self.canonical += 1
        if tag == 'meta' and (a.get('name') or '').lower() == 'description' and a.get('content'): self.description += 1
        for key in ('href','src'):
            if a.get(key): self.refs.append((key,a[key]))
        if tag == 'img': self.images.append((a.get('src',''), 'alt' in a, a.get('alt','')))

def fail(msg):
    errors.append(msg)

def local_target(path: str, current: Path) -> Path:
    parsed=urlsplit(path)
    p=parsed.path
    if not p:
        return current
    if p.startswith('/'):
        target=SITE / p.lstrip('/')
    else:
        target=(current.parent / p).resolve()
    if target.is_dir(): target=target/'index.html'
    if not target.exists() and not target.suffix and (target/'index.html').exists(): target=target/'index.html'
    return target

errors=[]; warnings=[]
footer_template_path = ROOT / "data" / "templates" / "site-footer.html"
try:
    shared_footer_template = footer_template_path.read_text(encoding="utf-8").strip()
except OSError as ex:
    shared_footer_template = ""
    fail_template_error = f"Cannot read canonical footer template: {ex}"
else:
    fail_template_error = ""
if not SITE.exists():
    print('No _site directory. Run python scripts/stage_site.py first.', file=sys.stderr); raise SystemExit(2)
html_files=sorted(SITE.rglob('*.html'))
local_ref_count=0; image_count=0
first_party_titles=set(); first_party_descriptions=set()
protected_subsites={"RongmeiHymnal", "Noney-BSNL-Broadband-NMS", "Network-Analyzer"}
id_map={}
parsed_pages={}
for page in html_files:
    parser=PageParser()
    try: parser.feed(page.read_text(encoding='utf-8'))
    except Exception as ex:
        fail(f'{page.relative_to(SITE)}: cannot parse HTML: {ex}'); continue
    rel=page.relative_to(SITE).as_posix(); id_map[rel]=set(parser.ids); parsed_pages[rel]=(page,parser)
    if parser.title != 1: fail(f'{rel}: expected exactly one title, found {parser.title}')
    if parser.canonical != 1: fail(f'{rel}: expected exactly one canonical link, found {parser.canonical}')
    if parser.description != 1: fail(f'{rel}: expected a non-empty meta description, found {parser.description}')
    if parser.duplicate_ids: fail(f'{rel}: duplicate HTML id(s): {", ".join(parser.duplicate_ids)}')
    if parser.h1 != 1: fail(f'{rel}: expected exactly one h1, found {parser.h1}')
    if parser.main != 1: fail(f'{rel}: expected exactly one main, found {parser.main}')
    if parser.footer < 1 and rel != 'ai-updates.html': fail(f'{rel}: missing shared page footer')
    for src,has_alt,alt in parser.images:
        image_count += 1
        if not has_alt: fail(f'{rel}: image missing alt attribute: {src}')
    text=page.read_text(encoding='utf-8')
    # Enforce SEO metadata on the enterprise site, not the independently maintained sub-sites.
    if rel.split("/", 1)[0] not in protected_subsites:
        title_match = re.search(r"<title\b[^>]*>([\s\S]*?)</title>", text, re.I)
        title_value = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title_match.group(1))).strip() if title_match else ""
        description_tags = re.findall(r'<meta\b(?=[^>]*\bname=["\']description["\'])[^>]*>', text, re.I)
        canonical_tags = re.findall(r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>', text, re.I)
        description_value = ""
        if len(description_tags) == 1:
            value_match = re.search(r'\bcontent=["\']([^"\']*)["\']', description_tags[0], re.I)
            description_value = value_match.group(1).strip() if value_match else ""
        if not title_value:
            fail(f"{rel}: missing page title text")
        elif title_value in first_party_titles:
            fail(f"{rel}: page title is not unique: {title_value}")
        else:
            first_party_titles.add(title_value)
        if len(description_tags) != 1 or not description_value:
            fail(f"{rel}: expected exactly one non-empty meta description")
        elif not 120 <= len(description_value) <= 155:
            fail(f"{rel}: meta description must be 120–155 characters; found {len(description_value)}")
        elif description_value in first_party_descriptions:
            fail(f"{rel}: meta description is not unique")
        else:
            first_party_descriptions.add(description_value)
        if len(canonical_tags) != 1:
            fail(f"{rel}: expected exactly one canonical link")
    if rel == "about.html" and re.search(r"\b(?:Manipur|Northeast India|North-East India)\b", text, re.I):
        fail("about.html: regional location text must remain absent from the enterprise profile")
    footer_match = re.search(r'<footer\b(?=[^>]*\bclass=["\'][^"\']*\bsite-footer\b[^"\']*["\'])[^>]*>[\s\S]*?</footer>', text, re.I)
    if not footer_match:
        fail(f'{rel}: missing enterprise footer component')
    else:
        footer_html = footer_match.group(0)
        if fail_template_error:
            fail(fail_template_error)
        elif re.sub(r"\s+", " ", footer_html).strip() != re.sub(r"\s+", " ", shared_footer_template).strip():
            fail(f"{rel}: footer differs from canonical data/templates/site-footer.html; run python scripts/stage_site.py")
        if not re.search(r"""<div\b(?=[^>]*\bclass=["'][^"']*\bsite-footer-founder-card\b)""", footer_html, re.I):
            fail(f"{rel}: founder statement is missing its bordered card")
        if not re.search(r"""<mark\b(?=[^>]*\bclass=["'][^"']*\bsite-footer-founder-highlight\b)""", footer_html, re.I):
            fail(f"{rel}: founder statement is missing its green highlight")
        if not re.search(r"""<span\b(?=[^>]*\bclass=["'][^"']*\bsite-footer-founder-signature\b)[^>]*>\s*— Founder\s*</span>""", footer_html, re.I):
            fail(f"{rel}: founder signature must appear as — Founder")
        motto_match = re.search(r"""<p\b(?=[^>]*\bclass=["'][^"']*\bsite-footer-motto\b[^"']*["'])[^>]*>(.*?)</p>""", footer_html, re.I | re.S)
        motto_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", motto_match.group(1))).strip() if motto_match else ""
        expected_motto = "We build practical software for ISP operations and network teams. — Founder"
        if motto_text != expected_motto:
            fail(f'{rel}: footer motto must use the approved practical software tagline')
        if re.search(r"""class=["'][^"']*\bsite-footer-commitment\b""", footer_html, re.I):
            fail(f'{rel}: duplicate footer commitment must be removed')
        for required in (
            "We build practical software for ISP operations and network teams.",
            "/assets/brand/udyam-verification-qr.png",
            "https://udyamregistration.gov.in/verifyudyambarcode.aspx?verifyudrn=",
            "Official enterprise website",
        ):
            if required not in footer_html:
                fail(f'{rel}: footer missing required enterprise identity or Udyam verification element: {required}')
        outside_footer = text[:footer_match.start()] + text[footer_match.end():]
        if re.search(r"Udyam", outside_footer, re.I):
            fail(f'{rel}: Udyam registration disclosure must remain in the footer')
    if re.search(r'\{\{[A-Z][A-Z0-9_ -]*\}\}',text): fail(f'{rel}: published page contains an unreplaced template placeholder')
    map_match = re.search(
        r"""<nav\b[^>]*class=["'][^"']*\b(?:doc-toc|page-map)\b[^"']*["'][^>]*>(.*?)</nav>""",
        text, re.I | re.S
    )
    if map_match:
        nav_tag = re.search(r"<nav\b[^>]*>", map_match.group(0), re.I).group(0)
        class_match = re.search(r"""class=["'][^"']*\b(doc-toc|page-map)\b""", nav_tag, re.I)
        map_class = class_match.group(1) if class_match else ""
        map_html = map_match.group(1)
        title_class = "doc-toc-title" if map_class == "doc-toc" else "page-map-title"
        title_pattern = rf"""<h2\b(?=[^>]*\bclass=["'][^"']*\b{title_class}\b)[^>]*>\s*On This Page\s*</h2>"""
        if not map_class or not re.search(title_pattern, map_html, re.I):
            fail(f'{rel}: page contents map must have a visible On This Page heading')
        if "<details" in map_html or "<summary" in map_html:
            fail(f'{rel}: page contents map must be visible without an expandable control')
        map_links = re.findall(r'<a[^>]*href="#([^"]+)"', map_html, re.I)
        if len(map_links) < 2:
            fail(f'{rel}: page contents map needs at least two section links')
        missing_targets = [target for target in map_links if target not in parser.ids]
        if missing_targets:
            fail(f'{rel}: contents link target(s) not found: {", ".join(missing_targets)}')
    if 'assets/projects/noney-bsnl-broadband-nms/dashboard.png' in text or 'assets/projects/noney-bsnl-broadband-nms/admin-tools.png' in text:
        fail(f'{rel}: refers to removed operational screenshot')


# Canonical-host consistency: the JSON site configuration is the single source of truth.
config_path = SITE / "data/config/site.json"
site_origin = ""
try:
    site_config = json.loads(config_path.read_text(encoding="utf-8"))
    site_origin = str(site_config.get("url", "")).strip().rstrip("/")
    parsed_origin = urlsplit(site_origin)
    if parsed_origin.scheme != "https" or not parsed_origin.netloc or parsed_origin.path not in ("", "/") or parsed_origin.query or parsed_origin.fragment:
        fail("data/config/site.json: url must be an HTTPS origin")
    if site_origin != "https://guang84.github.io":
        fail(f"Unexpected canonical site origin {site_origin!r}; verify the intended GitHub Pages domain before release")
except Exception as ex:
    fail(f"Unable to validate canonical site configuration: {ex}")

for rel, (page, parser) in parsed_pages.items():
    raw_page = page.read_text(encoding="utf-8", errors="replace")
    canonical_tags = re.findall(r"<link\b(?=[^>]*\brel=[\"']canonical[\"'])[^>]*>", raw_page, re.I)
    if len(canonical_tags) != 1:
        fail(f"{rel}: could not parse exactly one canonical tag")
    for tag in canonical_tags:
        href = re.search(r"\bhref=[\"']([^\"']+)[\"']", tag, re.I)
        if not href:
            fail(f"{rel}: canonical link has no href")
            continue
        value = href.group(1)
        if site_origin and not value.startswith(site_origin + "/"):
            fail(f"{rel}: canonical URL {value!r} does not start with configured origin {site_origin!r}")
    for meta_attr, label in (("property", "og:url"), ("name", "twitter:url")):
        meta_pattern = re.compile(r'<meta\b(?=[^>]*\b' + meta_attr + r'="' + re.escape(label) + r'")[^>]*>', re.I)
        for tag in meta_pattern.findall(raw_page):
            href = re.search(r'\bcontent="([^"]+)"', tag, re.I)
            if href and site_origin and not href.group(1).startswith(site_origin + "/"):
                fail(f"{rel}: {label} URL does not match configured site origin")

# Guard against regressions in shared navigation and the GitHub footer.
for rel, (page, parser) in parsed_pages.items():
    raw_page = page.read_text(encoding="utf-8", errors="replace")
    if "&gt;<button" in raw_page:
        fail(f"{rel}: stray menu glyph before a button")
    if rel in ("index.html", "about.html") and "https://github.com/Guang84?tab=repositories" not in raw_page:
        fail(f"{rel}: missing all-public-repositories GitHub link")

    # Legacy URL redirects are intentionally minimal and have no site navigation.
    is_noindex_redirect = re.search(
        r"""<meta\b(?=[^>]*\bname=["']robots["'])(?=[^>]*\bcontent=["'][^"']*noindex)""",
        raw_page, re.I
    )
    if not is_noindex_redirect:
        primary_nav = re.search(
            r"""<nav\b(?=[^>]*\bclass=["'][^"']*\bnav\b[^"']*["'])[^>]*>([\s\S]*?)</nav>""",
            raw_page, re.I
        )
        if not primary_nav or not re.search(r"""href=["']/contact\.html["']""", primary_nav.group(1), re.I):
            fail(f'{rel}: missing Contact link in primary navigation')
        if primary_nav:
            if not re.search(r"""<a\b(?=[^>]*href=["']/services\.html["'])[^>]*>Services</a>""", primary_nav.group(1), re.I):
                fail(f'{rel}: primary navigation must label /services.html as Services')
            if "Engineering Services" in primary_nav.group(1):
                fail(f'{rel}: legacy Engineering Services navigation label remains')
        mobile_menu = re.search(
            r"""<div\b(?=[^>]*\bclass=["'][^"']*\bmobile-menu\b[^"']*["'])[^>]*>([\s\S]*?)</div>""",
            raw_page, re.I
        )
        if not mobile_menu or not re.search(r"""href=["']/contact\.html["']""", mobile_menu.group(1), re.I):
            fail(f'{rel}: missing Contact link in mobile navigation')
        if mobile_menu:
            if not re.search(r"""<a\b(?=[^>]*href=["']/services\.html["'])[^>]*>Services</a>""", mobile_menu.group(1), re.I):
                fail(f'{rel}: mobile navigation must label /services.html as Services')
            if "Engineering Services" in mobile_menu.group(1):
                fail(f'{rel}: legacy Engineering Services label remains in mobile navigation')

for rel,(page,parser) in parsed_pages.items():
    for attr,value in parser.refs:
        value=value.strip()
        if not value or value.startswith(('data:','mailto:','tel:','javascript:')) or value.startswith('//'):
            continue
        parsed=urlsplit(value)
        if parsed.scheme and parsed.scheme not in ('http','https','file'):
            continue
        if parsed.scheme in ('http','https') and parsed.netloc:
            continue
        # For fragments, check the target page's known IDs.
        target=local_target(value,page)
        local_ref_count += 1
        if not target.exists():
            fail(f'{rel}: broken local {attr}={value}')
            continue
        if parsed.fragment:
            target_rel=target.relative_to(SITE).as_posix() if target.is_file() and SITE in target.parents else rel
            if target_rel in id_map and parsed.fragment not in id_map[target_rel]:
                fail(f'{rel}: fragment #{parsed.fragment} does not exist in {target_rel}')

# Search results must resolve to the corresponding published page and any advertised fragment.
search_path = SITE / "search-index.json"
if search_path.exists():
    try:
        search_rows = json.loads(search_path.read_text(encoding="utf-8"))
        for row in search_rows:
            url = row.get("url", "")
            if not url.startswith("/"): continue
            target = local_target(url, SITE / "index.html")
            if not target.exists():
                fail(f"search-index.json: broken URL {url}")
                continue
            parsed_url = urlsplit(url)
            if parsed_url.fragment:
                target_rel = target.relative_to(SITE).as_posix() if target.is_file() and SITE in target.parents else ""
                if target_rel in id_map and parsed_url.fragment not in id_map[target_rel]:
                    fail(f"search-index.json: broken fragment {url}")
    except Exception as ex:
        fail(f"search-index.json: invalid data: {ex}")

# Every local URL precached by the service worker must resolve in the generated site.
worker_path = SITE / "service-worker.js"
if worker_path.exists():
    worker_text = worker_path.read_text(encoding="utf-8", errors="replace")
    if "const files = next.files || []" in worker_text or "item.id}.json" in worker_text:
        fail("service-worker.js: legacy per-article JSON-body loading is still present")
    if "function validateCatalogue" not in worker_text or "HTML-first publishing note" not in worker_text:
        fail("service-worker.js: missing HTML-first catalogue validation")
    match = re.search(r"const PRECACHE=(\[.*?\]);", worker_text, re.S)
    if not match:
        fail("service-worker.js: unable to parse PRECACHE list")
    else:
        try:
            precache = json.loads(match.group(1))
            for url in precache:
                target = SITE / "index.html" if url == "/" else SITE / url.lstrip("/")
                if url != "/" and (url.endswith("/") or target.is_dir()): target = target / "index.html"
                if not target.exists(): fail(f"service-worker.js: missing precache target {url}")
        except Exception as ex:
            fail(f"service-worker.js: invalid PRECACHE data: {ex}")

# Guard the two-column section layout against the narrow-content regression.
layout_css = SITE / "assets/css/95-site-polish.css"
if not layout_css.is_file():
    fail("Missing shared layout stylesheet: assets/css/95-site-polish.css")
else:
    css_text = layout_css.read_text(encoding="utf-8", errors="replace")
    for required_rule in (
        ".detail-section > .eyebrow",
        ".detail-section > h2",
        ".detail-section > .eyebrow ~ *",
        ".detail-section > .eyebrow ~ .timeline-list",
        "grid-column: 1 / -1;",
        ".detail-section > h2 ~ *",
        "@media (max-width: 860px)",
    ):
        if required_rule not in css_text:
            fail(f"detail-section content-column regression guard: missing CSS rule {required_rule}")

# Required generated formats.
for file in ('data/config/site.json','data/articles/index.json','data/projects/index.json','search-index.json','manifest.webmanifest'):
    p=SITE/file
    if not p.exists(): fail(f'Missing generated file: {file}')
    elif file.endswith('.json') or file.endswith('.webmanifest'):
        try: json.loads(p.read_text(encoding='utf-8'))
        except Exception as ex: fail(f'{file}: invalid JSON: {ex}')
for file in ('sitemap.xml','feed.xml'):
    p=SITE/file
    if not p.exists(): fail(f'Missing generated file: {file}')
    else:
        try: ET.parse(p)
        except Exception as ex: fail(f'{file}: invalid XML: {ex}')

# Catalogue and output consistency.
for kind in ('articles','projects'):
    p=SITE/f'data/{kind}/index.json'
    if p.exists():
        try:
            items=json.loads(p.read_text(encoding='utf-8')).get('items',[])
            for item in items:
                slug=item.get('id','')
                if item.get('publicationStatus') != 'published': fail(f'{kind}/{slug}: non-published item appears in public catalogue')
                if not (SITE/kind/slug/'index.html').exists(): fail(f'{kind}/{slug}: canonical HTML page missing')
        except Exception as ex: fail(f'{p.relative_to(SITE)}: {ex}')

# Repository maintenance documents and the repository licence belong in source, not the public website deployment.
for unwanted in ("README.md", "requirements.txt", "LICENSE.txt", "CHANGELOG-QUALITY-UPDATE.md", "CHANGELOG.md"):
    if (SITE/unwanted).exists(): fail(f"Source-only file should not be in public deployment: {unwanted}")

# Public package should not contain the removed private-looking screenshots.
for unwanted in ('assets/projects/noney-bsnl-broadband-nms/dashboard.png','assets/projects/noney-bsnl-broadband-nms/admin-tools.png'):
    if (SITE/unwanted).exists(): fail(f'Removed screenshot still in public deployment: {unwanted}')

print(f'GLab site audit: {len(html_files)} HTML pages, {local_ref_count} local references, {image_count} images checked.')
if warnings:
    for w in warnings: print('WARNING:',w)
if errors:
    print(f'FAILED with {len(errors)} issue(s):')
    for e in errors: print(' -',e)
    raise SystemExit(1)
print('PASS: local links/fragments, page metadata and structure, canonical-host consistency, image alt attributes, sitemap/RSS, search index, HTML-first service-worker catalogue refresh, catalogue status, navigation, GitHub footer link, and public screenshot boundary.')
