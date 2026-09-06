# Deploy GLab v9

GLab is a static GitHub Pages site. No application server or build service is required.

## Before publishing

```bash
python scripts/build.py
python scripts/validate.py
```

The validator should report `0 error(s)`.

## Publish

Commit and push the repository contents to the branch used by GitHub Pages.

```bash
git add .
git commit -m "Release GLab v9 personal publishing hub"
git push
```

## Content updates

Profile text, interests and Important links are stored in:

```text
content/site.json
```

Projects, articles and guides are stored in:

```text
content/projects/
content/articles/
content/guides/
```

After editing content, rebuild and validate.

## Create future content

```bash
python scripts/new_content.py article "article title"
python scripts/new_content.py project "project title"
python scripts/new_content.py guide "guide title"
python scripts/new_content.py page "page title"
```

These commands create unpublished drafts under `content/drafts/`. Finish the content and move public JSON into the appropriate collection before rebuilding.

## AdSense

The repository contains the publisher ID and centralized site-wide Auto Ads loader. Visible ad inventory remains controlled by Google AdSense approval, policy, consent, demand and Auto Ads configuration.

## Service worker

v9 uses the `glab-v9.0.0` cache namespace. When deploying a later version, rebuild the site with a new service-worker cache version so old static caches are retired cleanly.
