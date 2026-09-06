# GLab — Guang's technical portfolio and publication

GLab is a static GitHub Pages site organized around three public sections:

1. **Projects** — complete project case studies.
2. **Articles** — technical articles and field notes.
3. **Guides** — complete procedural guides.

Live site: `https://guang84.github.io/`

## v8 branding and PWA upgrade

GLab v8 keeps the compact v7 information architecture and adds a complete branded application layer. The upper G/network/leaf mark from the supplied Guang artwork is now used as the header logo, favicon, Apple touch icon, PWA icon, maskable icon and social-card branding. The repository still contains no SVG assets.

The service worker was upgraded to v8 and now precaches all 22 public pages, every CSS/JS module, the search index, manifest and core brand assets. Navigation uses network-first behavior with offline fallback; static application assets use stale-while-revalidate caching. A waiting service worker now presents an Update action instead of silently replacing the active version.

## Compact content architecture

Earlier versions split a project across project, documentation, guide, lab and validation pages. The current site consolidates project details into one complete case-study URL while keeping genuinely procedural material under Guides.

There are no public `/docs/`, `/labs/`, `/pages/` or separate blog sections.

## Front-end features

- responsive layouts from narrow phone to ultrawide screens
- light/dark preference and adjustable reading size
- global search across Projects, Articles and Guides (`/` or `Ctrl/⌘ K`)
- active navigation state
- reading progress on project/article/guide pages
- share/copy-link action on detail pages
- back-to-top control
- installable PWA with update notification
- offline fallback and full public-page precache
- centralized AdSense Auto Ads loader
- accessibility, reduced-motion, high-contrast and print support

## Front-end structure

```text
assets/
├── brand/
│   └── glab-mark*.png
├── css/
│   ├── 00-tokens.css
│   ├── 10-base.css
│   ├── 20-layout.css
│   ├── 30-navigation.css
│   ├── 40-components.css
│   ├── 50-content.css
│   ├── 60-ads.css
│   ├── 70-responsive.css
│   ├── 80-accessibility.css
│   ├── 90-print.css
│   └── main.css
└── js/
    ├── core/
    ├── features/
    ├── ui/
    └── main.js
```

## Content structure

```text
content/
├── site.json
├── projects/
├── articles/
└── guides/
```

See `content/SCHEMA.md` for the editable content format.

## Build and validate

```bash
python scripts/build.py
python scripts/validate.py
```

Generated HTML is committed so GitHub Pages can serve the site directly.

## Advertising

The site contains the Google AdSense publisher identifier `ca-pub-6371342728710125` and a centralized loader in `assets/js/features/ads.js`. Auto Ads only render when the site/account is eligible and configured in Google AdSense. No fabricated manual ad-slot IDs are included.

## Deployment

Push the repository to the `main` branch of `Guang84/Guang84.github.io`. GitHub Pages should serve from the repository root.

## GLab v9 profile publishing model

The home page is a personal profile plus a publishing hub for Projects, Articles and Guides. Profile copy, interests and the **Important links** cards are configured in `content/site.json`.

To pin or remove a link, edit `importantLinks` in `content/site.json` and run:

```bash
python scripts/build.py
python scripts/validate.py
```

Source-only starter templates live in `content/templates/`; they are not linked, indexed or included in the sitemap. Create an unpublished draft with:

```bash
python scripts/new_content.py article "new article title"
python scripts/new_content.py project "new project"
python scripts/new_content.py guide "new guide"
python scripts/new_content.py page "custom page"
```

Completed JSON content is published only after it is moved into `content/projects/`, `content/articles/`, or `content/guides/` and the build script is run.
