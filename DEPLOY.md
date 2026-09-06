# Deploy GLab v7

## 1. Validate locally

```bash
python scripts/build.py
python scripts/validate.py
```

## 2. Preview

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/`.

Review at minimum:

- `/`
- `/projects/`
- one project case study
- `/articles/`
- one article
- `/guides/`
- one guide
- About, Privacy and Contact

Check both phone and desktop browser widths before publishing.

## 3. Commit

```bash
git add .
git commit -m "Release GLab v7 slim content architecture"
git push origin main
```

For the username repository `Guang84/Guang84.github.io`, GitHub Pages should serve the site from the repository root.

## 4. AdSense

The account identifier is already integrated. Actual advertising still depends on AdSense approval, policy eligibility, configured Auto Ads/consent requirements and available inventory.
