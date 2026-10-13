# GLab

**GLab — Learn. Build. Share. Grow.**

GLab is Guang’s personal site for documenting the projects he is working on and the technical problems he is learning to solve. It brings together the GLabNetOps network-operations workstream, software tools, practical guides, cybersecurity, ChatGPT workflows, community technology, and sustainability. Some pages are complete guides; others are notes on work still in progress.

## Canonical production URL

The configured GitHub Pages origin for this repository is `https://guang84.github.io/`. During verification on 12 October 2026, `https://guang.github.io/` returned 404. Do not change canonical URLs to another hostname unless GitHub Pages is explicitly configured for it and the address is verified. `data/config/site.json` is the single editable URL source for generated feed and sitemap URLs; HTML canonical tags should match it.

## Single source of truth

- **Article bodies:** complete HTML pages under `articles/<slug>/index.html`.
- **Project case studies:** complete HTML pages under `projects/<slug>/index.html`. The 2024 Network Analyzer page is deliberately retained as a historical archive.
- **JSON:** site configuration in `data/config/site.json`, the Rongmei Hymnal collection data under `data/RongmeiHymnal/`, and generated metadata-only catalogues at `data/articles/index.json` and `data/projects/index.json`. Catalogues are rebuilt from the HTML metadata and do not contain article or project body text.
- **Generated public artifacts:** `search-index.json`, `feed.xml`, `sitemap.xml`, service-worker precache data, and `_site/`. Do not hand-edit generated artifacts.
- **Templates and editorial instructions:** `docs/`. Project pages use a compact, captioned snapshot table followed by explanatory sections; the short/full formats and table conventions are documented in `docs/PROJECT-DOCUMENTATION.md`. Build scripts: `scripts/`.

## Add an article

1. Copy `docs/templates/article-template.html` to `articles/<slug>/index.html`.
2. Write the full article in HTML, replace all placeholders, add primary references, and complete the `glab:article-*` metadata.
3. Keep `glab:article-status` set to `draft` until every section is ready; set it to `published` only when the page is ready to be public.
4. Run the stage and release checks below.

## Add or update a project

Edit `projects/<slug>/index.html` as the authoritative case study, including `glab:project-*` metadata. Use `docs/templates/project-template.html` for a new page. Preserve a separate older slug when an earlier release has historical value.

## Interactive site manager

Run `python scripts/site_manager.py` for a menu to create draft article/project pages from the existing templates, attach public-safe files and get HTML snippets for linking them, list content status, run release and local-link checks, stage the site, run browser smoke tests, or preview `_site/`. New pages remain drafts; complete and review them before changing their publication status.

## Build and validate

```bash
python scripts/stage_site.py
python scripts/release_check.py
python scripts/site_audit.py
python scripts/browser_smoke.py
```

The release and site audits guard the project-section grid rules, canonical URLs, local references, generated feeds, and the HTML-first service-worker catalogue refresh. The browser suite exercises key routes at desktop/tablet/mobile widths plus search, filters, appearance controls, navigation, and service-worker behavior. In this sandbox, Chromium may block loopback HTTP navigation; the GitHub Actions workflow runs the browser suite in its normal CI environment.

The AdSense publisher ID and ad-slot placement are maintained centrally in `data/config/site.json`; `ads.txt` must contain the matching publisher record. Do not paste a second AdSense loader into individual pages. The configured slot is used once on the homepage and at the end of eligible article/project pages.

The generated deployment site is `_site/`. For local preview:

```bash
python -m http.server 8000 --directory _site
```

Then open `http://localhost:8000/`. A passing local build is not proof of live-host routing, search-engine indexing, security, or AdSense approval; verify the deployment separately.

## Content approach

ChatGPT use cases, benefits, limitations, and dated product notes belong in the Articles & Guides collection rather than a separate AI-updates navigation item. Feature claims are linked to official OpenAI documentation and should be rechecked when the article is substantially updated.

## Editorial change log

See [`docs/CHANGELOG.md`](docs/CHANGELOG.md) for the content, repository, and validation changes in this release.

## Public project boundaries

- `projects/glabnetops/` explains the network-operations workstream and its related but separate tools. It is a public portfolio overview, not a claim that every component is one live production product.
- The Noney Broadband NMS production environment is retired. Its public repository is a gateway/documentation surface; private production source, credentials, internal configuration, operational endpoints, and customer records are not included here.
- Optional image snippets are documented in `docs/templates/` and `docs/ADDING-CONTENT.md`. Review and redact screenshots before they enter the public repository.
- Browse Guang’s public repositories at https://github.com/Guang84?tab=repositories.
