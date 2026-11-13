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

At main commit `6818c13`, the first-party static-site audit and Playwright smoke tests passed in GitHub Actions. The audit enforces one page title, one canonical link, one H1, and one non-empty 120–155 character meta description per first-party page. Titles and descriptions must be unique. It also checks local links, fragments, images and shared footer structure. The separately maintained Rongmei Hymnal, Noney historical site and Network Analyzer sub-sites are excluded from the enterprise-page metadata rule.

The enterprise site uses a generated static build. `scripts/build_content.py` sorts article records by publication date descending, generates the RSS feed and creates the deployed article archive from that sorted catalogue. The homepage article preview uses the first three records from the same date-sorted catalogue.

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

Existing skip links, main landmarks, focus-visible styles, text-size controls, dark/light themes and reduced-motion handling were retained. The Playwright smoke suite exercises key routes at 360, 768 and 1280 px. This is not a substitute for a manual keyboard/screen-reader review or measured contrast and touch-target checks.

## SEO, PWA and performance

Sitemap, robots, feed, 404 and offline pages already exist. The homepage has Organization JSON-LD with the enterprise name, brand logo and GitHub profile in `sameAs`. Article detail pages include Article JSON-LD.

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
- P1: owner confirmation of public email and AdSense/consent setup; project outcome evidence before any Results section; reconcile related-repository README/licence discrepancies listed below.
- P2: manual accessibility review, Lighthouse, social-image verification and performance profiling.

## Related repositories — report only

These checks were read-only. No related repository was changed.

### Network Analyzer — public

- The README identifies Network Analyzer v2026.08.21, describes authorised wireless assessment/passive monitoring and warns that active features can interrupt wireless service.
- The repository contains `LICENSE.txt` with the Apache License 2.0. The README does not identify a conflicting licence.
- Latest sampled commit: 16 September 2026. The project README is broadly aligned with the current site record; consider adding fuller command options and test instructions, but no urgent status mismatch was found.

### SSH Fleet Doctor — public

- The repository is named `SSH-Fleet-Doctor`, but its README title and description still call the project “SSH-Infiltrator”.
- Clone instructions point to `SSH-Infiltrator.git`, change into an old directory name and refer to old launcher files. They do not match the current repository name or the site’s SSH Fleet Doctor project record.
- The README describes password-based `sshpass` authentication and powerful shutdown, delete and stress-test actions. Review these instructions against the current source and the project’s authorisation/safety boundaries before promoting them.
- The README says the project is licensed under MIT, but the repository’s `LICENSE` file contains Apache License 2.0. This is a material README/licence mismatch.
- Latest sampled commit: 2 September 2026. The README should be reconciled with the current project identity, supported features and actual licence before public use.

### Noney-BSNL-Broadband-NMS — public

- The README describes the historical public gateway and states that the production environment is retired/offline.
- Its “Current Status” table also says development is upgrading to independent systems and a new version is in production testing, while listing the public gateway as online. Those rows conflict with the retired-project status on the enterprise website and should be reconciled.
- No `LICENSE` or `COPYING` file was found in the repository tree. A badge labelled “Portfolio” is not a standard licence grant. The owner should decide what rights, if any, apply to the public documentation and gateway files.
- Latest sampled commit: 23 September 2026. No repository files were changed.

### RongmeiHymnal — public

- The README explains how to run and validate the app and states that Apache License 2.0 applies to software, interface, tools and documentation only.
- It explicitly separates song lyrics, editions, arrangements, cover art and other content from the software licence, and points to a usage policy.
- Latest sampled commit: 30 October 2026. This is a useful rights distinction. Keep the existing public “content review and attribution ongoing” notice until collection-level review is complete. No hymn content, metadata or dataset was changed.

### Repositories not publicly reviewable in this audit

- GLabNetOps and Glab-assets are private repositories in the linked account. They were not counted as public repos. Their READMEs describe GLabNetOps as an in-development product with private source and a project-specific licence; Glab-assets describes proprietary brand assets that require written permission for reuse.
- The supplied `Guang84/Google-API-map` path returned 404 from the connected GitHub repository lookup and did not appear in the linked account’s accessible repository list. I could not verify its README, clone instructions, stray quote markers, API-key history/restrictions or contact address. This does not establish whether it was renamed, moved, deleted or made private. The owner must supply the current repository URL before those checks can be completed.

Public visibility alone does not grant permission to reuse third-party or cultural content.
