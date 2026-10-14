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


let glabLoaderFallbackTimer = null;
let glabLoaderFrame = null;

function ensureGlabPageLoader() {
  let loader = document.querySelector("[data-glab-page-loader]");
  if (loader) return loader;

  loader = document.createElement("div");
  loader.className = "glab-page-loader";
  loader.dataset.glabPageLoader = "";
  loader.setAttribute("role", "status");
  loader.setAttribute("aria-live", "polite");
  loader.setAttribute("aria-hidden", "true");

  const content = document.createElement("div");
  content.className = "glab-page-loader__content";

  const mark = document.createElement("img");
  mark.className = "glab-page-loader__mark";
  mark.src = "/assets/brand/glab-mark-256.png";
  mark.alt = "";
  mark.setAttribute("aria-hidden", "true");

  const label = document.createElement("span");
  label.className = "glab-page-loader__label";
  label.dataset.loaderMessage = "";
  label.textContent = "Loading GLab…";

  const track = document.createElement("span");
  track.className = "glab-page-loader__track";
  track.setAttribute("aria-hidden", "true");

  const fill = document.createElement("span");
  fill.className = "glab-page-loader__track-fill";
  track.append(fill);
  content.append(mark, label, track);
  loader.append(content);
  document.body.append(loader);
  return loader;
}

function showGlabPageLoader(message = "Loading GLab…") {
  const loader = ensureGlabPageLoader();
  const label = loader.querySelector("[data-loader-message]");
  if (label) label.textContent = message;
  loader.setAttribute("aria-hidden", "false");
  document.documentElement.classList.add("glab-loader-active");

  if (glabLoaderFrame !== null) cancelAnimationFrame(glabLoaderFrame);
  glabLoaderFrame = requestAnimationFrame(() => {
    loader.classList.add("is-visible");
    glabLoaderFrame = null;
  });

  window.clearTimeout(glabLoaderFallbackTimer);
  // Never leave a page covered if a navigation is cancelled or a resource hangs.
  glabLoaderFallbackTimer = window.setTimeout(hideGlabPageLoader, 9000);
}

function hideGlabPageLoader() {
  window.clearTimeout(glabLoaderFallbackTimer);
  glabLoaderFallbackTimer = null;
  if (glabLoaderFrame !== null) {
    cancelAnimationFrame(glabLoaderFrame);
    glabLoaderFrame = null;
  }
  const loader = document.querySelector("[data-glab-page-loader]");
  if (loader) {
    loader.classList.remove("is-visible");
    loader.setAttribute("aria-hidden", "true");
  }
  document.documentElement.classList.remove("glab-loader-active");
}

function initGlabPageLoader() {
  let pageLoaded = document.readyState === "complete";
  let contentReady = false;
  const hideWhenReady = () => {
    if (pageLoaded && contentReady) hideGlabPageLoader();
  };

  ensureGlabPageLoader();
  showGlabPageLoader("Loading GLab…");

  if (!pageLoaded) {
    window.addEventListener("load", () => {
      pageLoaded = true;
      hideWhenReady();
    }, { once: true });
  }

  window.addEventListener("pageshow", (event) => {
    if (event.persisted) hideGlabPageLoader();
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
