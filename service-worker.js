const VERSION='glab-v14.2.0-2c3e0ecedc419011', CACHE_PREFIX='glab-', STATIC_CACHE=`${VERSION}-static`, CONTENT_CACHE=`${VERSION}-content`;
const PRECACHE=["/","/404.html","/about.html","/articles/index.html","/assets/brand/glab-mark-16.png","/assets/brand/glab-mark-256.png","/assets/brand/glab-mark-32.png","/assets/brand/glab-mark-48.png","/assets/brand/glab-mark-64.png","/assets/brand/glab-mark.png","/assets/css/00-tokens.css","/assets/css/10-base.css","/assets/css/20-layout.css","/assets/css/30-navigation.css","/assets/css/40-components.css","/assets/css/45-profile.css","/assets/css/46-refresh.css","/assets/css/50-content.css","/assets/css/60-ads.css","/assets/css/70-responsive.css","/assets/css/80-accessibility.css","/assets/css/90-print.css","/assets/css/main.css","/assets/icons/apple-touch-180.png","/assets/icons/glab-192.png","/assets/icons/glab-512.png","/assets/icons/glab-maskable-512.png","/assets/js/core/dom.js","/assets/js/core/storage.js","/assets/js/core/viewport.js","/assets/js/features/ads.js","/assets/js/features/code-copy.js","/assets/js/features/content.js","/assets/js/features/pwa.js","/assets/js/features/search.js","/assets/js/features/share.js","/assets/js/features/site-config.js","/assets/js/main.js","/assets/js/ui/header.js","/assets/js/ui/menu.js","/assets/js/ui/preferences.js","/assets/js/ui/reading.js","/assets/js/ui/reveal.js","/assets/social/glab-social.png","/assets/social/profile.png","/contact.html","/data/articles/better-light-better-night.json","/data/articles/buying-laptop-2026-specs-guide.json","/data/articles/index.json","/data/articles/learning-from-soil.json","/data/articles/passkeys-and-the-human-side-of-security.json","/data/articles/repair-before-replace.json","/data/articles/responsible-ai.json","/data/articles/right-sized-ai.json","/data/articles/security-is-care.json","/data/articles/soil-sensors-need-ground-truth.json","/data/config/site.json","/data/projects/index.json","/data/projects/network-analyzer-v2024.json","/data/projects/network-analyzer-v2026.json","/data/projects/noney-bsnl-broadband-nms.json","/data/projects/rongmei-hymnal.json","/data/projects/ssh-fleet-doctor.json","/data/schemas/article.schema.json","/data/schemas/articles.schema.json","/data/schemas/project.schema.json","/data/schemas/projects.schema.json","/feed.xml","/index.html","/manifest.webmanifest","/offline.html","/privacy.html","/projects/index.html","/search-index.json","/sitemap.xml","/terms.html","/projects/","/articles/"];

self.addEventListener('install', event => event.waitUntil(caches.open(STATIC_CACHE).then(cache => cache.addAll(PRECACHE))));
self.addEventListener('activate', event => event.waitUntil((async () => {
  await Promise.all((await caches.keys()).filter(key => key.startsWith(CACHE_PREFIX) && ![STATIC_CACHE, CONTENT_CACHE].includes(key)).map(key => caches.delete(key)));
  await self.registration.navigationPreload?.enable();
  await self.clients.claim();
})()));
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'CHECK_CONTENT') event.waitUntil(refreshContent().then(result => event.ports?.[0]?.postMessage({type: 'CONTENT_CHECKED', result})));
});
async function cachedResponse(request) {
  return await (await caches.open(CONTENT_CACHE)).match(request) || await (await caches.open(STATIC_CACHE)).match(request);
}
async function notifyContentUpdate(url) {
  for (const client of await self.clients.matchAll({type: 'window'})) client.postMessage({type: 'CONTENT_UPDATED', url});
}
async function download(request) {
  const response = await fetch(request, {cache: 'no-store', signal: AbortSignal.timeout(8000)});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  // A hosting fallback returning HTML must never replace a JSON catalog.
  await response.clone().json();
  return response;
}
async function freshContent(request) {
  const cached = await cachedResponse(request);
  try {
    const response = await download(request);
    await (await caches.open(CONTENT_CACHE)).put(request, response.clone());
    if (cached && await cached.clone().text() !== await response.clone().text()) await notifyContentUpdate(new URL(request.url).pathname);
    return response;
  } catch { return cached || Response.error(); }
}
let refreshInFlight;
function refreshContent() {
  return refreshInFlight || (refreshInFlight = updateContent().finally(() => { refreshInFlight = null; }));
}
async function updateContent() {
  try {
    const downloads = [];
    let changed = 0;
    let records = 0;
    for (const name of ['projects', 'articles']) {
      const request = new Request(new URL(`/data/${name}/index.json`, self.location.origin));
      const cached = await cachedResponse(request);
      const response = await download(request), next = await response.clone().json();
      const previous = cached ? await cached.json() : null;
      if (previous?.contentVersion === next.contentVersion) continue;
      const files = next.files || [];
      if (!Array.isArray(files)) throw new Error(`Invalid ${name} index`);
      const recordDownloads = await Promise.all(files.map(async file => {
        if (typeof file !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*\.json$/.test(file) || file === 'index.json') throw new Error('Invalid content path');
        const req = new Request(new URL(`/data/${name}/${file}`, self.location.origin));
        const data = await download(req);
        const item = await data.clone().json();
        if (`${item.id}.json` !== file) throw new Error('Content id mismatch');
        return [req, data];
      }));
      downloads.push(...recordDownloads, [request, response]);
      records += files.length;
      changed += 1;
    }
    if (changed) {
      const search = new Request(new URL('/search-index.json', self.location.origin));
      downloads.push([search, await download(search)]);
    }
    const cache = await caches.open(CONTENT_CACHE);
    for (const [req, data] of downloads) await cache.put(req, data);
    if (changed) await notifyContentUpdate('/data/');
    return {changed, records};
  } catch (error) {
    // Keep the previous indexes so the next check retries failed updates.
    return {error: error.message};
  }
}
async function networkFirst(event) {
  try {
    const response = (await event.preloadResponse) || await fetch(event.request);
    if (response.ok) await (await caches.open(STATIC_CACHE)).put(event.request, response.clone());
    return response;
  } catch {
    const url = new URL(event.request.url);
    return await cachedResponse(event.request)
      || (['/projects/', '/articles/'].includes(url.pathname) ? await cachedResponse(url.pathname) : null)
      || await cachedResponse('/offline.html');
  }
}
async function staleWhileRevalidate(event) {
  const cached = await cachedResponse(event.request);
  const update = fetch(event.request).then(async response => {
    if (response.ok) await (await caches.open(STATIC_CACHE)).put(event.request, response.clone());
    return response;
  }).catch(() => cached || Response.error());
  event.waitUntil(update);
  return cached || await update;
}
function belongsToGLab(path) {
  return path === '/' || path.startsWith('/projects/') || path.startsWith('/articles/') || path.startsWith('/assets/') || path.startsWith('/data/') || PRECACHE.includes(path);
}
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || !belongsToGLab(url.pathname)) return;
  if (event.request.mode === 'navigate') {
    event.waitUntil(refreshContent());
    return event.respondWith(networkFirst(event));
  }
  // Folder indexes are committed exclusively by the update transaction.
  if (url.pathname === '/data/projects/index.json' || url.pathname === '/data/articles/index.json') return event.respondWith((async () => {
    await refreshContent(); return await cachedResponse(event.request) || Response.error();
  })());
  if (url.pathname.startsWith('/data/') || url.pathname === '/search-index.json') return event.respondWith(freshContent(event.request));
  event.respondWith(staleWhileRevalidate(event));
});
// Build fingerprint: 2c3e0ecedc419011
