# GLab — Guang's technical portfolio and publication

GLab is a static GitHub Pages site organized around three clear public sections:

1. **Projects** — complete project case studies.
2. **Articles** — technical articles and field notes.
3. **Guides** — complete procedural guides.

Live site: `https://guang84.github.io/`

## Why v7 is smaller

Earlier versions split a project across project, documentation, guide, lab, and validation pages. That created too many thin or overlapping URLs. v7 consolidates the information.

A project page now contains its context, purpose, features, architecture, implementation notes, setup/use workflow, validation checklist, safety boundaries, status, license and repository links on one page.

There are no public `/docs/`, `/labs/`, `/pages/`, or separate blog sections.

## No SVG project covers

Project cards and case-study headers use typography, metadata and lightweight CSS accent bars instead of generated SVG cover images. The repository contains PNG/ICO application and social icons only.

## Front-end structure

```text
assets/
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

The generated HTML is committed so GitHub Pages can serve it without a server-side framework.

## Advertising

The site contains the Google AdSense account identifier `ca-pub-6371342728710125` and a single centralized loader in `assets/js/features/ads.js`. Auto Ads only render when the site/account is eligible and configured in Google AdSense. No fake manual slot IDs are included.

## Deployment

Push the repository to the `main` branch of `Guang84/Guang84.github.io`. GitHub Pages should serve from the repository root.
