# GLab website maintenance

## Content model

GLab has three editorial pillars: **Nature**, **Technology**, and **Innovation**. Articles and projects are separate content collections. Each published article or project has one primary pillar and may have additional related pillars. The build process uses this metadata to populate each pillar landing page and the global search index.

Use the primary pillar that best describes the content's main purpose. Use related pillars only when the content genuinely serves another pillar. Tags describe narrower subjects; they do not replace the pillar.

## Nature statements and initiative records

Nature is both an editorial area and a principle guiding GLab's development. Write about current practices, intentions, support and completed contributions distinctly. Do not claim a conservation programme, partnership, restoration result, donation or measurable environmental benefit unless it has actually occurred and can be documented.

When a Nature initiative is added, record the activity, date, GLab's role, partner (if applicable), geographic scope at an appropriate privacy level, evidence and outcome. Do not publish personal details or sensitive ecological location data.

## Create an article or project draft

Run the local manager from the repository root:

```bash
python scripts/site_manager.py
```

Choose **Create a project draft** or **Create an article draft**. The manager writes a canonical HTML page with draft metadata. Complete its body, sources, image rights, alt text, technical limits and related content before publication. Draft pages are excluded from the public deployment.

For each content page, keep the title, description, canonical URL, dates, tags, primary pillar and publication status consistent. A project status (for example, In development or Released) is different from its publication status (draft or published).

## Review and publish

Before changing publication status to `published`:

1. Read `docs/editorial-review-checklist.md`.
2. Verify every important factual or technical claim against a reliable source, repository, test or recorded observation.
3. Check spelling, grammar, British English consistency, headings, links, image attribution and accessible alt text.
4. State what is implemented, tested, planned and not yet verified.
5. Exclude credentials, customer information, private network details and unredacted screenshots.

Run the full local release sequence:

```bash
python scripts/stage_site.py
python scripts/release_check.py
python scripts/site_audit.py
python scripts/browser_smoke.py
```

Review the staged site in a browser before committing. Keep generated catalogues and feed/search/sitemap artifacts in sync with their canonical source pages.

## Browser CMS status

There is currently no authenticated browser CMS configured for this GitHub Pages site. The site manager is a local authoring utility. GitHub Pages serves static files; a browser CMS that writes to GitHub needs a secure authentication and repository-access service. Configure and test that service separately before enabling a web editor. Never embed a personal access token or client secret in public JavaScript.

## Release discipline

Use a working branch based on the latest verified `main`. Run the repository's pull-request workflow and review its results before merging. A successful static build does not by itself prove the technical claims in an article or product page; editorial and engineering review remain necessary.
