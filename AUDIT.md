# GLab Enterprise website audit

Audit scope: partial source and build-system review of the public enterprise website. The repository baseline had 106 tracked files. This is not a claim that every text and binary file or every historical git object received exhaustive manual review.

## Inventory

| Area | Purpose |
|---|---|
| Root HTML | Home, About, Services, Contact, legal/editorial pages, 404 and offline pages |
| `articles/` | Article archive and 11 article pages |
| `projects/` | GLabNetOps, Network Analyzer releases, SSH Fleet Doctor, Rongmei Hymnal and historical Noney NMS records |
| `data/` | Site profile, article/project catalogues and shared footer template |
| `assets/css/`, `assets/js/` | Theme, responsive layout, accessibility, navigation, search, PWA and advertising features |
| `RongmeiHymnal/`, `Noney-BSNL-Broadband-NMS/`, `Network-Analyzer/` | Existing published sub-sites; routes and song/project data are protected |
| `scripts/`, `.github/workflows/` | Static build, content validation, staging and browser smoke tests |

Potential historical duplicates include Network Analyzer version records and Noney route aliases. These remain in place because they represent historical releases or preserved routes.

## Page metadata

The first-party HTML pages are being validated for one unique title, one unique canonical URL and one unique 120–155 character description. `scripts/site_audit.py` now enforces these checks during the staged-site audit. The protected sub-sites are excluded from this enterprise-page metadata rule.

The enterprise site uses a generated static build. `scripts/build_content.py` sorts article records by publication date descending, generates the RSS feed and creates the deployed article archive from that sorted catalogue. The homepage article preview now uses the first three records from the same date-sorted catalogue.

## P0 findings

- The old About support block paired a sample QR with a payment identifier. The owner supplied a replacement QR. Its encoded UPI payload decoded and the handle matches the identifier already used on the site. The replacement is displayed with a reminder to verify payee and amount in the payment app. This does not independently prove bank-account ownership or a completed test transaction.
- The separate Udyam verification QR and official verification URL in the footer are unchanged.
- BSNL is named in the historical Noney case study. Confirm permission to use the name; do not imply affiliation or endorsement.
- Rongmei Hymnal needs a plain-language attribution/licensing note. Keep the existing “content review and attribution ongoing” notice. Do not edit song text, attribution data, book metadata or datasets as part of this website work.
- The sampled source scan did not identify a high-confidence API token or private key. It was not a complete historical git-object scan; a dedicated history scan remains an owner/security action.

## Third parties

- Google Fonts: typography.
- Google AdSense metadata and loader: retained pending owner confirmation of active ads and consent configuration.
- GitHub Pages: static hosting.
- WhatsApp: outbound contact option.
- Udyam portal: business-registration verification.

No additional tracker was introduced. No AdSense configuration was removed without approval.

## Accessibility and responsive design

Existing skip links, main landmarks, focus-visible styles, text-size controls, dark/light themes and reduced-motion handling were retained. The existing Playwright smoke suite exercises key routes and responsive viewports at 360, 768 and 1280 px. This is not a substitute for a manual keyboard/screen-reader review or measured contrast and touch-target checks.

## SEO, PWA and performance

Sitemap, robots, feed, 404 and offline pages already exist. The homepage already has Organization JSON-LD; the current update aligns its name/logo/description and keeps the GitHub profile in `sameAs`. Article detail pages already include Article JSON-LD.

The root site has a service worker and offline fallback. Rongmei Hymnal is a separate sub-site; no Hymnal song data or service-worker files were changed. Lighthouse scores, social-image byte/dimension verification, image compression, unused CSS/JS and render-blocking performance profiling still require dedicated measurement.

## Content and information architecture

- The homepage and About introduction were duplicates. The homepage now leads with ISP/network operations software; About carries the longer enterprise explanation.
- The homepage is organised as: hero, four build areas, GLabNetOps, other projects with lifecycle labels, four working steps, three newest articles and contact.
- The homepage no longer presents AI, cybersecurity or sustainable farming as broad enterprise service claims. Project and article evidence remains discoverable through the portfolio and publication archive.
- Music and Reading now appear as a short Interests line on About, not as homepage capabilities.
- About replaces generic quotations with a concrete repair/reuse/maintenance practice. The revised footer tagline describes the enterprise's software work.
- Project lifecycle wording remains grounded in existing project records. GLabNetOps remains in development with private source; Noney production remains retired; Rongmei Hymnal remains deployed with editorial review ongoing; SSH Fleet Doctor remains in development.
- Legal pages and article bodies were not rewritten.

## Priorities

- P0: replacement support QR is live; BSNL name permission, Hymnal rights note and exhaustive historical secret scan remain owner actions.
- P1: owner confirmation of public email and AdSense/consent setup; project outcome evidence before any Results section.
- P2: manual accessibility review, Lighthouse, social-image verification and performance profiling.

## Related repositories (report only)

The GitHub integration did not expose `Guang84/Google-API-map`; its README, clone instructions, stray quote markers, Google Maps key history/restrictions and public contact could not be verified. Owner review remains required.

Sampled related repositories: GLabNetOps (development, private source); Network Analyzer (Apache-2.0); SSH Fleet Doctor (Apache-2.0 metadata but README appears stale and refers to SSH-Infiltrator); Noney-BSNL-Broadband-NMS (retired production environment, no clear repo licence); Rongmei Hymnal (Apache-2.0 applies to software/docs, not song content); Glab-assets (custom brand-assets licence). Public visibility does not grant rights to third-party or cultural content.
