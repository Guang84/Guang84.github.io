// Keep the small copyright year current without requiring server-side rendering.
document.querySelectorAll("[data-current-year]").forEach((node) => {
  node.textContent = String(new Date().getFullYear());
});

import { initViewport } from "./core/viewport.js";
import { initHeader } from "./ui/header.js";
import { initMenu } from "./ui/menu.js";
import { initPreferences } from "./ui/preferences.js";
import { initReading } from "./ui/reading.js";
import { initReveal } from "./ui/reveal.js";
import { initAds } from "./features/ads.js";
import { initSearch } from "./features/search.js";
import { initSiteConfig } from "./features/site-config.js";
import { initPWA } from "./features/pwa.js";
import { initShare } from "./features/share.js";
import { initCodeCopy } from "./features/code-copy.js";
import { initContent } from "./features/content.js";
import { initSupportCopy } from "./features/support-copy.js";
import { initPageMap } from "./ui/page-map.js";


// Pin both shared assets to the approved loader revision so the site never
// mixes files from different commits while the central package is updated.
const GLAB_LOADER_ASSET_BASE =
  "https://raw.githubusercontent.com/Guang84/Glab-assets/19c72468a6710e0a6d01ce3649eeb32f8979a493/shared/GLab-loader";
const GLAB_LOADER_MIN_VISIBLE_MS = 650;

let glabPageLoader = null;
let glabLoaderPendingMessage = null;
let glabLoaderAssetsPromise = null;
let glabLoaderAssetsFailed = false;
let glabLoaderShownAt = null;
let glabLoaderHideTimer = null;

function loadGlabLoaderStylesheet() {
  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${GLAB_LOADER_ASSET_BASE}/GLab-loader.css`;
    link.dataset.glabLoaderStylesheet = "";
    link.onload = resolve;
    link.onerror = () => {
      link.remove();
      reject(new Error("Could not load the shared GLab Loader stylesheet."));
    };
    document.head.append(link);
  });
}

function loadGlabLoaderScript() {
  if (typeof window.GLabLoader === "function") return Promise.resolve();

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `${GLAB_LOADER_ASSET_BASE}/GLab-loader.js`;
    script.async = true;
    script.dataset.glabLoaderScript = "";
    script.onload = () => {
      if (typeof window.GLabLoader === "function") resolve();
      else reject(new Error("The shared GLab Loader script did not expose GLabLoader."));
    };
    script.onerror = () => {
      script.remove();
      reject(new Error("Could not load the shared GLab Loader script."));
    };
    document.head.append(script);
  });
}

function loadGlabLoaderAssets() {
  if (!glabLoaderAssetsPromise) {
    glabLoaderAssetsPromise = Promise.all([
      loadGlabLoaderStylesheet(),
      loadGlabLoaderScript(),
    ]).then(() => {
      if (typeof window.GLabLoader !== "function") {
        throw new Error("The shared GLab Loader is unavailable.");
      }
    });
  }
  return glabLoaderAssetsPromise;
}

function getGlabLoaderTheme() {
  const theme = document.documentElement.dataset.theme;
  return theme === "light" || theme === "dark" ? theme : "auto";
}

function showGlabPageLoader(message = "Loading…") {
  if (glabLoaderAssetsFailed) return;
  glabLoaderPendingMessage = message;
  if (!glabPageLoader) return;

  if (glabLoaderHideTimer !== null) {
    window.clearTimeout(glabLoaderHideTimer);
    glabLoaderHideTimer = null;
  }

  const alreadyVisible = glabPageLoader.element.classList.contains("is-visible");
  if (!alreadyVisible) glabLoaderShownAt = performance.now();

  glabPageLoader.element.dataset.theme = getGlabLoaderTheme();
  glabPageLoader.show(message);
  glabLoaderPendingMessage = null;
}

function hideGlabPageLoader(force = false) {
  // Keep the initial show request until the shared script has finished loading.
  // Otherwise a fast page can clear it before the loader instance exists.
  if (!glabPageLoader) return;
  glabLoaderPendingMessage = null;

  if (glabLoaderHideTimer !== null) {
    window.clearTimeout(glabLoaderHideTimer);
    glabLoaderHideTimer = null;
  }

  if (!force && glabLoaderShownAt !== null) {
    const elapsed = performance.now() - glabLoaderShownAt;
    const remaining = GLAB_LOADER_MIN_VISIBLE_MS - elapsed;
    if (remaining > 0) {
      glabLoaderHideTimer = window.setTimeout(() => {
        glabLoaderHideTimer = null;
        hideGlabPageLoader(true);
      }, remaining);
      return;
    }
  }

  glabPageLoader.hide();
  glabLoaderShownAt = null;
}

function initGlabPageLoader() {
  let pageLoaded = document.readyState === "complete";
  let contentReady = false;
  const hideWhenReady = () => {
    if (pageLoaded && contentReady) hideGlabPageLoader();
  };

  // Load the shared component without blocking the site's other features.
  // If the asset host is unavailable, the website continues without an overlay.
  showGlabPageLoader("Loading…");
  loadGlabLoaderAssets()
    .then(() => {
      glabPageLoader = new window.GLabLoader({
        logoUrl: "/assets/brand/glab-mark-256.png",
        message: "Loading…",
        theme: getGlabLoaderTheme(),
        timeoutMs: 9000,
      });
      if (glabLoaderPendingMessage !== null) {
        showGlabPageLoader(glabLoaderPendingMessage);
      }
      hideWhenReady();
    })
    .catch((error) => {
      glabLoaderAssetsFailed = true;
      glabLoaderPendingMessage = null;
      document.querySelector("link[data-glab-loader-stylesheet]")?.remove();
      console.warn(
        "Shared GLab Loader unavailable; continuing without the loading overlay.",
        error,
      );
    });

  if (!pageLoaded) {
    window.addEventListener("load", () => {
      pageLoaded = true;
      hideWhenReady();
    }, { once: true });
  }

  window.addEventListener("pageshow", (event) => {
    if (event.persisted) hideGlabPageLoader(true);
  });

  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const target = event.target instanceof Element ? event.target.closest("a[href]") : null;
    if (!target || target.hasAttribute("download")) return;
    const browsingTarget = (target.getAttribute("target") || "").toLowerCase();
    if (browsingTarget && browsingTarget !== "_self") return;

    const href = target.getAttribute("href")?.trim();
    if (!href || href.startsWith("#")) return;

    let destination;
    try {
      destination = new URL(href, window.location.href);
    } catch {
      return;
    }
    if (destination.origin !== window.location.origin) return;
    if (destination.pathname === window.location.pathname && destination.search === window.location.search) return;
    if (/\.(?:pdf|zip|png|jpe?g|gif|svg|webp|mp[34]|xml|json|txt|ico)$/i.test(destination.pathname)) return;

    const linkLabel = (target.getAttribute("aria-label") || target.textContent || "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 54);
    showGlabPageLoader(linkLabel ? "Opening " + linkLabel + "…" : "Opening page…");
  }, true);

  return {
    contentReady() {
      contentReady = true;
      hideWhenReady();
    },
  };
}

const FEATURES = [
  ["viewport", initViewport],
  ["header", initHeader],
  ["menu", initMenu],
  ["preferences", initPreferences],
  ["reading", initReading],
  ["reveal", initReveal],
  ["search", initSearch],
  ["site-config", initSiteConfig],
  ["pwa", initPWA],
  ["share", initShare],
  ["code-copy", initCodeCopy],
  ["support-copy", initSupportCopy],
  ["page-map", initPageMap],
  ["ads", initAds],
];

async function boot() {
  document.documentElement.classList.add("js");
  const loaderState = initGlabPageLoader();
  const contentReady = initContent()
    .catch((error) => console.warn("GLab content feature failed", error))
    .finally(() => loaderState.contentReady());
  for (const [name, initializer] of FEATURES) {
    try {
      if (["reading", "reveal", "share", "code-copy", "ads"].includes(name)) {
        contentReady
          .then(initializer)
          .catch((error) => console.warn(`GLab ${name} feature failed`, error));
        continue;
      }
      const result = initializer();
      if (result instanceof Promise)
        result.catch((error) =>
          console.warn(`GLab ${name} feature failed`, error),
        );
    } catch (error) {
      console.warn(`GLab ${name} feature failed`, error);
    }
  }
}

document.readyState === "loading"
  ? document.addEventListener("DOMContentLoaded", boot, { once: true })
  : boot();
