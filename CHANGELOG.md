# Changelog

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
