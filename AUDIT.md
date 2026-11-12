# GLab Enterprise website audit

Audit baseline: `main` and `upgrade/site-2026` both pointed to `1c959f5` before work. The repository contained 106 tracked files. This is a partial source audit, not a line-by-line review of every tracked text file or binary asset. No browser/Lighthouse run is claimed here.

## Inventory

| Area | Purpose |
|---|---|
| Root HTML | Home, About, Services, Contact, legal/editorial pages, 404 and offline pages |
| `articles/` | Archive and 12 article pages |
| `projects/` | GLabNetOps, Network Analyzer versions, SSH Fleet Doctor, Rongmei Hymnal and historical Noney NMS records |
| `data/` | Site profile, article/project catalogues, shared footer |
| `assets/css`, `assets/js` | Themes, responsive layout, accessibility, navigation, search, PWA and ads |
| `RongmeiHymnal/`, `Noney-BSNL-Broadband-NMS/`, `Network-Analyzer/` | Existing published sub-sites; preserve URLs and data |
| `scripts/`, `.github/workflows/` | Static build, content validation, staging and browser smoke tests |

Potential historical duplicates include Network Analyzer version records and Noney route aliases. Preserve them unless owner confirms removal.

## Page metadata baseline

| Page | Description length | Canonical |
|---|---:|---|
| Home | 228 | Missing |
| About | 228 | Missing |
| Services | 225 | Missing |
| GLabNetOps | 414 | Missing |
| Articles archive | 179 | Missing |
| GLabNetOps project story | 263 | Missing |
| Network Analyzer v2024 | 185 | Missing |
| Network Analyzer v2026 | 211 | Missing |
| SSH Fleet Doctor | 346 | Missing |
| Terms | 103 | Present |
| Privacy | 128 | Present |

Sampled pages had one H1, `lang` and alt attributes. Validate all pages after metadata remediation. The repository already generates sitemap, RSS and service-worker cache versions through `scripts/build_content.py`.

## P0 findings

- About previously showed a sample support QR beside a public payment identifier. That sample has been replaced by the owner-supplied UPI QR. Its payload decoded and its UPI handle matches the existing site identifier; the payment block now displays the new image with a payee/amount confirmation reminder. This verifies the encoded payload, not bank-account ownership or a completed test transaction. The separate Udyam verification QR remains unchanged.
- BSNL is named in the historical Noney case study. Keep the name but ask owner to confirm permission; no affiliation is asserted.
- Rongmei Hymnal still needs a plain-language attribution/licensing note. Keep the existing “content review and attribution ongoing” notice. Do not modify hymn/song content, attribution data or datasets.
- Sampled source did not reveal a high-confidence API token or private key. This is not a complete historical git-object secret scan; run a dedicated history scan and rotate any exposed credential.

## Third parties

Google Fonts (typography); Google AdSense metadata/loader (owner must confirm active ads and consent setup); GitHub Pages (hosting); WhatsApp (outbound contact); Udyam portal (registration verification). No new tracker was added. AdSense configuration is retained pending owner approval.

## Accessibility

Existing skip links, main landmarks, focus-visible styles, font-size preferences, dark/light themes and reduced-motion handling were found in source. Keyboard-only, screen-reader, contrast, touch-target and 360/768/1280px checks require a real browser. No score is claimed.

## SEO, PWA and performance

Sitemap, robots, feed, 404 and offline pages already exist. Validate canonical URLs, 120–155 character unique descriptions, JSON-LD, OG image alt and 1200×630 dimensions, and feed order. Root PWA has a service worker/offline fallback. Rongmei Hymnal is a separate sub-site; no Hymnal service-worker/data changes were made. Image byte sizes, unused CSS/JS and render-blocking resources need browser profiling.

## Content

Home and About lead copy were identical. The article archive is grouped by category rather than globally newest-first, although source catalogue/feed are date-ordered. Verify article dates against publication history before changing them. Retain BSNL pending permission and the Hymnal review notice. Legal pages were not rewritten.

## Priorities

- P0: owner-supplied payment QR is now live in the About support block; confirm BSNL name permission and Hymnal content rights, and complete the historical secret scan.
- P1: metadata remediation, split home/about copy, homepage information architecture, globally newest-first article archive, confirm contact email and AdSense consent status.
- P2: visual accessibility checks, OG image validation, Lighthouse and performance profiling.

## Related repositories (report only)

The GitHub integration did not expose `Guang84/Google-API-map`; its README, clone commands, stray quote markers, key history/restrictions and contact could not be verified. Review required. Sampled related repositories: GLabNetOps (development, private source); Network Analyzer (Apache-2.0); SSH Fleet Doctor (Apache-2.0 metadata but README appears stale and refers to SSH-Infiltrator); Noney-BSNL-Broadband-NMS (retired environment, no clear repo licence); Rongmei Hymnal (Apache-2.0 applies to software/docs, not song content); Glab-assets (custom brand-assets licence). Public visibility does not grant rights to third-party or cultural content.
