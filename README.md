# GLab Enterprise — **Nature · Technology · Innovation**

The official website of **GLab Enterprise (GLab Ent.)**, an independent technology and engineering enterprise developing practical software, digital products, and technical solutions. Driven by creativity, technological exploration, and a spirit of innovation, GLab develops useful technologies that address practical needs and encourage new possibilities.

Alongside technological development, GLab values the natural environment and aspires to contribute to a future where **technology and nature co-exist in harmony**. Its approach reflects a commitment to responsible innovation and environmental awareness, encouraging a more balanced and sustainable future.

## Shared Page Footer

The canonical site footer is maintained in `data/templates/site-footer.html`. Edit that file when changing footer wording, links, or structure; do not make page-by-page footer edits.

Run the staging command to synchronize the shared footer across public HTML pages and rebuild the deployment output:

```bash
python scripts/stage_site.py
python scripts/site_audit.py
```

The site audit checks that each staged page uses the canonical footer template.

## Website content and maintenance

The site is a static GitHub Pages publication. Canonical article and project pages are stored as HTML; the build scripts generate the searchable catalogues, archives, RSS feed, sitemap and deployment copy.

For local content authoring and release checks, see [Website maintenance](docs/website-maintenance.md). The local site manager creates unpublished drafts; it is not a browser-based CMS. Do not place GitHub tokens or other credentials in browser-side code. A web CMS requires a separately configured authentication provider before it can write to the repository.

## Website

- [Official Website](https://guang84.github.io/)
- [About GLab Enterprise](https://guang84.github.io/about.html)
- [GitHub Profile](https://github.com/Guang84)

## Copyright & Use of Content

© 2026 GLab Enterprise. All rights reserved.

The work presented through this website and its projects reflects the development, ideas, designs, and efforts of GLab Enterprise.

Please respect that work. Content, documents, designs, graphics, and other original materials published here are not to be copied, republished, redistributed, modified, or presented as another person's or organisation's work without prior permission.

Making this website or repository accessible to the public does not mean its original materials are free to reuse.

Any third-party materials remain subject to their respective ownership and usage terms.
