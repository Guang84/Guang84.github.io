# Deploy GLab v12.1

GLab is a static GitHub Pages site. No application server is required.

## 1. Rebuild

```bash
python scripts/build.py
python scripts/validate.py
```

Expected result:

```text
GLab v12.1.0 validation: 0 error(s), 0 warning(s)
```

## 2. Review

```bash
git status
git diff
```

Confirm that no draft or private information is being published.

## 3. Commit and push

```bash
git add .
git commit -m "Release GLab v12.1"
git push
```

GitHub Pages should serve the repository root from `main`.

## Updating profile and pinned links

Edit:

```text
content/site.json
```

Then rebuild and validate.

## Adding content

Public JSON records live in:

```text
content/projects/
content/articles/
```

Each project JSON contains its own `guide` object. Create an unpublished project, article, or custom-page draft with `scripts/new_content.py`, finish it, move project/article JSON into the appropriate public collection, then rebuild.

## Service worker

v12.1 uses the `glab-v12.1.0` cache namespace. Cache cleanup is limited to cache names beginning with `glab-`, and fetch interception is limited to GLab routes (`/`, `/projects/`, `/articles/` and `/assets/`). This avoids deleting or intercepting unrelated project-PWA caches hosted under the same `guang84.github.io` origin.

After deployment, an older installed GLab PWA may show an **Update** prompt when v12.1 is detected.

## AdSense

The site-wide Auto Ads loader remains enabled. Visible ads are controlled by Google AdSense and are not guaranteed on every request or page.

## Draft safety

`content/drafts/` is ignored by Git. `python scripts/release_check.py` fails if unpublished draft files exist, so clear or publish them before a final deployment.
