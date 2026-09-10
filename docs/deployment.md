# Deploy GLab

The site targets the domain root (`https://guang84.github.io/`), not a repository subpath.

1. Install build dependencies with `python3 -m pip install -r requirements.txt`.
2. Run `python3 scripts/release_check.py` locally.
3. In GitHub **Settings → Pages → Build and deployment**, select **GitHub Actions** once.
4. Push source changes to `main`. The workflow rebuilds folder indexes, validates records and routes, stages public assets, and deploys the generated artifact. Pull requests only run checks.

Adding a published JSON record needs no new HTML or manual service-worker version bump. The build regenerates folder indexes, search, RSS, and detail sitemap URLs. Application, schema, and published content changes update a generated worker fingerprint. The service worker checks folder index hashes on focus, reconnection, startup, and every 15 minutes. Homepage and archive lists refresh automatically when new content is downloaded, preserving active filters. Open detail pages offer Refresh; navigation also fetches current JSON records. Offline detail routes reuse the cached collection shell.

`python3 scripts/stage_site.py` creates `_site/`. It excludes source files, draft items, tests, and tooling. Deploy that directory when using another static host. For local previews use `python3 -m http.server 8000 --directory _site` after building and staging.

All pages initialize the shared AdSense Auto ads integration after their content renders. Configure `ads.enabled`, `ads.publisherId`, and `ads.mode: "auto"` in `data/config/site.json`. Keep `ads.txt` consistent with your publisher account. Auto ads must also be enabled for the site in AdSense; actual ad placement and delivery are controlled by Google and the account's approval/settings. Empty placeholder areas remain collapsed. No invented ad-slot IDs are used.

Set `appearance.palette` to `sage` (default), `ocean`, `orchid`, or `ember` for the default accent palette. Readers can cycle palettes with the ◈ button and toggle light/dark mode; their preferences persist locally.

References: [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [AdSense Auto ads setup](https://support.google.com/adsense/answer/9261307?hl=en).

Optional explicit ad units: add real AdSense display-unit IDs to `ads.slots`, keyed by `home-top`, `home-middle`, `home-bottom`, or `content-end`. All non-home views get a content-end placement automatically, including JSON detail views. Empty configuration stays collapsed. `mode: "manual"` loads only configured units; `mode: "auto"` keeps Auto ads and can also render configured units. Use your account settings to control Auto ads placement.
