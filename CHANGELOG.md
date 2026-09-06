# Changelog

## v12.1.0 — Technology and nature editorial collection

- published six original, evidence-based articles on passkeys, right-sized AI, soil-sensor calibration, electronics longevity, responsible outdoor lighting, and safe listening
- added practical checklists and direct links to W3C, FIDO Alliance, IEA, NIST, USDA NRCS, ITU, EPA, NPS, DOE, and WHO guidance
- expanded the homepage article selection from four to six so the complete new collection is visible at launch
- rebuilt article pages, global search, RSS, sitemap, and offline precache from the JSON sources
- verified the AdSense Auto Ads loader across every public HTML page and the inline ad placement on every article page
- advanced the PWA cache namespace to `glab-v12.1.0`

## v12.0.0 — Consolidated content architecture

- embedded each practical guide directly in its owning project JSON and project page
- removed the duplicate `content/guides/` source collection and generated `/guides/` section
- kept project guides discoverable through homepage cards and global-search anchor links
- moved reusable project, article, and page starters into a root `templates/` directory
- updated the draft generator to use the new templates and removed the obsolete standalone-guide option
- tightened validation around the new directory layout, embedded-guide schema, search index, sitemap, and service-worker routes
- advanced the PWA cache namespace to `glab-v12.0.0`

## v11.0.0 — Final hardened release

- verified all four linked project repositories are public and resolve on GitHub
- clarified editable `content/projects/` versus generated `/projects/` output
- restored theme/font preferences before first paint
- browser theme color now follows light/dark mode
- added mobile-menu keyboard focus trapping
- enriched Open Graph/Twitter metadata
- added sitemap `lastmod` and RFC-compliant RSS dates
- added service-worker navigation preload while retaining GLab-only route handling
- added `scripts/release_check.py` and stronger GitHub Actions validation
- retained PNG-only branding, no ICO/SVG assets, compact 22-page public architecture

## 11.0.0 — Reliability, icon cleanup and interface repair

- Removed all `.ico` files and legacy favicon references; PNG brand assets now provide browser/PWA icons.
- Fixed unrendered build-template expressions that appeared as literal `{e(...)}` text in the homepage.
- Removed the My public notebook/statistics panel copy, Independent work section and Keep exploring section.
- Reworked top-bar text controls into real decrease/increase stepping controls.
- Hardened theme, search and mobile-menu interaction and focus handling.
- Isolated feature startup so one JavaScript feature cannot disable every other control.
- Added code-block Copy controls for practical guides and technical pages.
- Restricted service-worker cache cleanup to GLab cache names only.
- Restricted root service-worker interception to GLab-owned routes to avoid interfering with other project sites on the same GitHub Pages origin.
- Added service-worker `updateViaCache: none` registration behavior.
- Added validation failures for raw template leakage, legacy ICO files and unsafe service-worker cache behavior.

## 8.0.0 — Brand, search and offline application upgrade

- Extracted the upper G/network/leaf mark from the supplied Guang artwork and adopted it as the GLab brand mark.
- Rebuilt favicon, Apple touch, 192px/512px PWA, maskable and social-card assets from the new mark.
- Updated every page header to use the actual logo instead of a CSS letter badge.
- Kept the repository SVG-free.
- Upgraded the service worker to `glab-v8.0.0`.
- Precached all 22 public HTML pages plus every local CSS/JS module and core app asset.
- Added network-first page navigation with offline fallback and stale-while-revalidate static assets.
- Added user-controlled service-worker update activation and update notification.
- Added install/offline/online status notifications.
- Added global Projects/Articles/Guides search with `/` and `Ctrl/⌘ K` shortcuts.
- Added active navigation state.
- Fixed reading progress so it actually initializes on generated content pages.
- Added Web Share / copy-link fallback to detail pages.
- Updated PWA manifest shortcuts and maskable branding.
- Retained the slim Projects / Articles / Guides information architecture.

## 7.0.0 — Slim single-page content architecture

- Reduced public site to Projects, Articles and Guides.
- Merged project architecture and validation data into project content records.
- Embedded project setup/use information directly in each complete project case study.
- Kept standalone Guides for procedural reading.
- Moved field notes into Articles and removed the separate Blogs hierarchy.
- Removed public Docs, Labs and duplicate generated `pages/` trees.
- Removed all SVG project covers and all remaining SVG assets.
- Replaced cover artwork with CSS-only project accents and metadata-first cards.
- Simplified primary/mobile navigation.
- Rebuilt sitemap, RSS feed and search index for the smaller information architecture.
- Simplified homepage around the three content pillars.
- Removed runtime project/content fetching from the homepage; project cards are static and filter progressively with JavaScript.
- Centralized AdSense loading.
- Strengthened responsive case-study and guide layouts.
- Added validation for page-count discipline and old-route/cover regression.

## 9.0.0 — Personal publishing hub
- Rebuilt the homepage around Guang’s profile, roles, values and six interests.
- Added data-driven Important links cards configurable in `content/site.json`.
- Added a clearer Projects / Articles / Guides publishing hierarchy.
- Added a documentation explainer, independent-work support note and closing call-to-action.
- Generated About from the same profile source.
- Added source-only templates and a draft generator for future content.
- Added homepage/profile-specific CSS as a separate module.
- Bumped the service worker cache namespace to v9.

## Final audit notes

- removed obsolete `my_github_image.png`
- added 48 px PNG favicon
- fixed archive card heading levels for semantic h1 → h2 structure
- added draft-deployment safety guard
- expanded validator to check heading structure, duplicate IDs, search-index integrity, RSS dates and sitemap metadata
