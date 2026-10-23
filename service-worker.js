const VERSION='glab-v15.5.2-content-refresh', CACHE_PREFIX='glab-', STATIC_CACHE=`${VERSION}-static`, CONTENT_CACHE=`${VERSION}-content`;
const PRECACHE=["/","/404.html","/about.html","/articles/better-light-better-night/index.html","/articles/building-with-nature-in-mind/index.html","/articles/buying-laptop-2026-specs-guide/index.html","/articles/index.html","/articles/learning-from-soil/index.html","/articles/passkeys-and-the-human-side-of-security/index.html","/articles/repair-before-replace/index.html","/articles/responsible-ai/index.html","/articles/right-sized-ai/index.html","/articles/security-is-care/index.html","/articles/soil-sensors-need-ground-truth/index.html","/assets/brand/glab-mark-16.png","/assets/brand/glab-mark-256.png","/assets/brand/glab-mark-32.png","/assets/brand/glab-mark-48.png","/assets/brand/glab-mark-64.png","/assets/brand/glab-mark.png","/assets/css/00-tokens.css","/assets/css/10-base.css","/assets/css/20-layout.css","/assets/css/30-navigation.css","/assets/css/40-components.css","/assets/css/45-profile.css","/assets/css/46-refresh.css","/assets/css/50-content.css","/assets/css/60-ads.css","/assets/css/70-responsive.css","/assets/css/75-editorial.css","/assets/css/80-accessibility.css","/assets/css/90-print.css","/assets/css/95-site-polish.css","/assets/css/main.css","/assets/icons/apple-touch-180.png","/assets/icons/glab-192.png","/assets/icons/glab-512.png","/assets/icons/glab-maskable-512.png","/assets/js/core/dom.js","/assets/js/core/storage.js","/assets/js/core/viewport.js","/assets/js/features/ads.js","/assets/js/features/code-copy.js","/assets/js/features/content.js","/assets/js/features/pwa.js","/assets/js/features/search.js","/assets/js/features/share.js","/assets/js/features/site-config.js","/assets/js/main.js","/assets/js/ui/header.js","/assets/js/ui/menu.js","/assets/js/ui/preferences.js","/assets/js/ui/reading.js","/assets/js/ui/reveal.js","/assets/projects/rongmei-hymnal/library-home.png","/assets/social/glab-social.png","/assets/social/profile.png","/contact.html","/data/articles/index.json","/data/config/site.json","/data/projects/index.json","/editorial-policy.html","/feed.xml","/index.html","/manifest.webmanifest","/offline.html","/privacy.html","/project-checklist.html","/projects/glabnetops/index.html","/projects/index.html","/projects/network-analyzer-v2024/index.html","/projects/network-analyzer-v2026/index.html","/projects/noney-bsnl-broadband-nms/index.html","/projects/noney-bsnl-nms/index.html","/projects/rongmei-hymnal/index.html","/projects/ssh-fleet-doctor/index.html","/search-index.json","/sitemap.xml","/start-here.html","/terms.html","/projects/","/articles/"];
const JSON_ENDPOINTS = [
  "/data/projects/index.json",
  "/data/articles/index.json",
  "/search-index.json",
];

self.addEventListener("install", (event) =>
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE)),
  ),
);

self.addEventListener("activate", (event) =>
  event.waitUntil(
    (async () => {
      await Promise.all(
        (await caches.keys())
          .filter(
            (key) =>
              key.startsWith(CACHE_PREFIX) &&
              ![STATIC_CACHE, CONTENT_CACHE].includes(key),
          )
          .map((key) => caches.delete(key)),
      );
      await self.registration.navigationPreload?.enable();
      await self.clients.claim();
    })(),
  ),
);

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
  if (event.data?.type === "CHECK_CONTENT") {
    event.waitUntil(
      refreshContent().then((result) =>
        event.ports?.[0]?.postMessage({ type: "CONTENT_CHECKED", result }),
      ),
    );
  }
});

async function cachedResponse(request) {
  const content = await caches.open(CONTENT_CACHE);
  const contentHit = await content.match(request);
  if (contentHit) return contentHit;
  return (await caches.open(STATIC_CACHE)).match(request);
}

async function downloadJSON(request) {
  const response = await fetch(request, {
    cache: "no-store",
    credentials: "same-origin",
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${request.url}`);
  const data = await response.clone().json();
  return { response, data };
}

function validateCatalogue(name, data) {
  if (
    !data ||
    typeof data !== "object" ||
    typeof data.contentVersion !== "string" ||
    !data.contentVersion ||
    !Array.isArray(data.items)
  ) {
    throw new Error(`Invalid ${name} metadata catalogue`);
  }
  const ids = new Set();
  for (const item of data.items) {
    if (
      !item ||
      typeof item.id !== "string" ||
      !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.id) ||
      item.publicationStatus !== "published" ||
      ids.has(item.id)
    ) {
      throw new Error(`Invalid or duplicate item in ${name} catalogue`);
    }
    ids.add(item.id);
  }
}

async function notifyContentUpdate(url) {
  for (const client of await self.clients.matchAll({ type: "window" })) {
    client.postMessage({ type: "CONTENT_UPDATED", url });
  }
}

let refreshInFlight;
function refreshContent() {
  if (!refreshInFlight) {
    refreshInFlight = updateContent().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

/*
 * HTML-first publishing note:
 * article/project bodies are complete, independently addressable HTML pages.
 * These JSON files contain only catalogue metadata and the search index; the
 * worker must never look for per-article or per-project JSON body files.
 */
async function updateContent() {
  try {
    // Download and validate everything before writing any new catalogue entries.
    const requests = JSON_ENDPOINTS.map(
      (path) => new Request(new URL(path, self.location.origin)),
    );
    const downloads = await Promise.all(requests.map(downloadJSON));
    const [projects, articles, search] = downloads.map((item) => item.data);

    validateCatalogue("projects", projects);
    validateCatalogue("articles", articles);
    if (!Array.isArray(search)) throw new Error("Invalid GLab search index");

    let changed = 0;
    let needsStore = false;
    for (let i = 0; i < downloads.length; i += 1) {
      const cached = await cachedResponse(requests[i]);
      if (!cached) {
        needsStore = true;
        continue;
      }
      const cachedText = await cached.clone().text();
      const nextText = await downloads[i].response.clone().text();
      if (cachedText !== nextText) {
        needsStore = true;
        changed += 1;
      }
    }

    if (needsStore) {
      const cache = await caches.open(CONTENT_CACHE);
      for (let i = 0; i < downloads.length; i += 1) {
        await cache.put(requests[i], downloads[i].response.clone());
      }
    }
    if (changed) await notifyContentUpdate("/data/");
    return {
      changed,
      records: projects.items.length + articles.items.length,
      stored: needsStore,
    };
  } catch (error) {
    // Leave the last good catalogue intact. The next check can retry the update.
    return { error: error?.message || "Unknown content refresh error" };
  }
}

async function networkFirst(event) {
  try {
    const response =
      (await event.preloadResponse) || (await fetch(event.request));
    if (response.ok) {
      await (
        await caches.open(STATIC_CACHE)
      ).put(event.request, response.clone());
    }
    return response;
  } catch {
    const url = new URL(event.request.url);
    return (
      (await cachedResponse(event.request)) ||
      (["/projects/", "/articles/"].includes(url.pathname)
        ? await cachedResponse(new URL(url.pathname, self.location.origin))
        : null) ||
      (await cachedResponse(new URL("/offline.html", self.location.origin)))
    );
  }
}

async function staleWhileRevalidate(event) {
  const cached = await cachedResponse(event.request);
  const update = fetch(event.request, { cache: "no-cache" })
    .then(async (response) => {
      if (response.ok) {
        await (
          await caches.open(STATIC_CACHE)
        ).put(event.request, response.clone());
      }
      return response;
    })
    .catch(() => cached || Response.error());
  event.waitUntil(update);
  return cached || (await update);
}

function belongsToGLab(path) {
  return (
    path === "/" ||
    path.startsWith("/projects/") ||
    path.startsWith("/articles/") ||
    path.startsWith("/assets/") ||
    path.startsWith("/data/") ||
    PRECACHE.includes(path) ||
    path === "/search-index.json"
  );
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || !belongsToGLab(url.pathname))
    return;

  if (event.request.mode === "navigate") {
    event.waitUntil(refreshContent());
    return event.respondWith(networkFirst(event));
  }

  // Catalogue indexes are committed from a fully validated refresh, not partly
  // overwritten by individual concurrent requests.
  if (JSON_ENDPOINTS.includes(url.pathname)) {
    return event.respondWith(
      (async () => {
        await refreshContent();
        return (await cachedResponse(event.request)) || Response.error();
      })(),
    );
  }

  event.respondWith(staleWhileRevalidate(event));
});

// Build fingerprint: f72e5e237cc296e5
