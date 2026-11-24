import { getPref } from "../core/storage.js";

const AD_SCRIPT_URL =
  "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";
let adScriptPromise = null;

function loadAdScript(publisherId) {
  if (adScriptPromise) return adScriptPromise;

  const existing = document.querySelector(
    'script[src*="pagead/js/adsbygoogle.js"]',
  );
  if (existing) {
    adScriptPromise = new Promise((resolve, reject) => {
      if (existing.dataset.loaded === "true") return resolve();
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
    });
    return adScriptPromise;
  }

  adScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.async = true;
    script.crossOrigin = "anonymous";
    script.src = `${AD_SCRIPT_URL}?client=${publisherId}`;
    script.addEventListener(
      "load",
      () => {
        script.dataset.loaded = "true";
        resolve();
      },
      { once: true },
    );
    script.addEventListener(
      "error",
      () => {
        script.remove();
        adScriptPromise = null;
        reject(new Error("GLab could not load the Google AdSense script."));
      },
      { once: true },
    );
    document.head.append(script);
  });
  return adScriptPromise;
}

function scheduleAutoAds(publisherId) {
  const load = () => {
    loadAdScript(publisherId).catch((error) => {
      console.warn(error.message);
    });
  };
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(load, { timeout: 2500 });
  } else {
    window.setTimeout(load, 1500);
  }
}

function prepareManualZone(zone, slot, publisherId) {
  const label = document.createElement("span");
  label.className = "ad-label";
  label.textContent = "Advertisement";

  const unit = document.createElement("ins");
  unit.className = "adsbygoogle";
  unit.style.display = "block";
  Object.assign(unit.dataset, {
    adClient: publisherId,
    adSlot: slot,
    adFormat: "auto",
    fullWidthResponsive: "true",
  });

  // Activate the reserved area before inserting its contents. The zone is
  // outside <main>, so advertising cannot resize the measured content region.
  zone.dataset.active = "true";
  zone.replaceChildren(label, unit);

  let requested = false;
  const requestAd = async () => {
    if (requested) return;
    requested = true;
    try {
      await loadAdScript(publisherId);
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (error) {
      requested = false;
      console.warn(error.message);
    }
  };

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        observer.disconnect();
        void requestAd();
      },
      { rootMargin: "400px 0px", threshold: 0 },
    );
    observer.observe(zone);
  } else {
    void requestAd();
  }
}

export async function initAds() {
  const response = await fetch("/data/config/site.json", { cache: "no-cache" });
  if (!response.ok)
    throw new Error(`Could not load AdSense settings: HTTP ${response.status}`);
  const { ads, appearance } = await response.json();
  if (
    [
      "cobalt",
      "forest",
      "terracotta",
      "sage",
      "ocean",
      "orchid",
      "ember",
    ].includes(appearance?.palette) &&
    !getPref("glab-palette", "")
  ) {
    document.documentElement.dataset.palette = appearance.palette;
    document.dispatchEvent(new CustomEvent("glab:appearance-updated"));
  }
  if (
    !ads?.enabled ||
    !/^ca-pub-\d{16}$/.test(ads.publisherId) ||
    !["auto", "manual"].includes(ads.mode)
  )
    return;

  const meta = document.querySelector('meta[name="google-adsense-account"]');
  if (meta) meta.content = ads.publisherId;

  // Keep ads on publishing pages, not utility, policy, error, or catalogue screens.
  const path = location.pathname;
  const home = path === "/" || path === "/index.html";
  const archive = /^\/(?:articles|projects)\/$/.test(path);
  const staticContent =
    /^\/(?:articles|projects)\/[a-z0-9-]+\/$/.test(path) ||
    (/^\/(?:content|data\/content)\/(?:articles|projects)\/[a-z0-9-]+\.html$/.test(
      path,
    ) &&
      !path.endsWith("/index.html"));
  if (!home && !archive && !staticContent) return;

  if (ads.mode === "auto") {
    scheduleAutoAds(ads.publisherId);
    return;
  }

  const main = document.querySelector("main");
  let zones = [...document.querySelectorAll("[data-ad-position]")];
  if (!zones.length && main) {
    const zone = document.createElement("aside");
    zone.className = "ad-zone";
    zone.dataset.adPosition = "content-end";
    zone.setAttribute("aria-label", "Advertisement");
    main.insertAdjacentElement("afterend", zone);
    zones = [zone];
  }

  let validZoneCount = 0;
  for (const zone of zones) {
    const slot = ads.slots?.[zone.dataset.adPosition];
    if (!/^\d{10}$/.test(slot || "") || zone.querySelector(".adsbygoogle"))
      continue;
    validZoneCount += 1;
    prepareManualZone(zone, slot, ads.publisherId);
  }

  if (!validZoneCount) return;
}
