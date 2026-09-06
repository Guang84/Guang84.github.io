# GLab v12.1.0 build report

Release target: **https://guang84.github.io/**

## Architecture result

- `content/projects/` is the only project source collection.
- Every project JSON contains its practical instructions in a nested `guide` object.
- `content/articles/` is the only article source collection.
- `templates/` contains the reusable project, article, and custom-page starters.
- `projects/` and `articles/` contain generated public HTML for GitHub Pages.
- The old `content/guides/`, `content/templates/`, and public `guides/` directories have been removed.

Project guides remain visible on the homepage and in global search. Both now link to the owning project page’s `#guide` section, so there is one source record and one canonical public page per project.

## Build outputs

- projects: **4**
- articles: **10**
- embedded project guides: **4**
- search records: **18** (projects, articles, and project-guide anchors)
- public HTML pages: **23**
- sitemap URLs: **21**
- service-worker precache resources: **58**
- PWA cache namespace: **`glab-v12.1.0`**

## Verification

- `python scripts/release_check.py`: **PASS**
- content/build validation: **0 errors, 0 warnings**
- Python compilation: **PASS**
- JavaScript and service-worker syntax: **PASS**
- HTTP smoke test for every sitemap URL: **PASS**
- AdSense account loader: **23/23 public HTML pages**
- inline article ad placement: **10/10 article pages**
- internal links, assets, IDs, heading hierarchy, RSS, sitemap, manifest, and precache targets: **PASS**
- embedded-guide schema and search-anchor validation: **PASS**
- project/article/custom-page template generation: **PASS**
- template JSON parsing and custom-page title escaping: **PASS**
- repeat-build checksum comparison: **PASS**
- external content links: **46 reviewed**; 42 returned HTTP 2xx/3xx to the automated checker, while two IEA pages rejected the checker and two NRCS pages reset its HTTP/2 connection but remained valid authoritative source URLs
- search result to embedded `#guide` section: **PASS**
- project guide jump link and share control: **PASS**
- offline cached project navigation: **PASS**
- horizontal-overflow checks at 280, 320, 390, 600, 768, 1024, 1440, and 1920 px: **PASS**

## Additional fixes found during the v12 check

- removed the fixed 280px body width that overflowed narrow usable viewports
- prevented command blocks from expanding project-detail grids on phones
- removed the obsolete Guides shortcut and route from the manifest, navigation, sitemap, search URLs, and service worker
- preserved guide structured data by emitting a `HowTo` object on the canonical project page
