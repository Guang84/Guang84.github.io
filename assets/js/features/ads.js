import { getPref } from "../core/storage.js";
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

  if (ads.mode === "manual") {
    const main = document.querySelector("main");
    if (main && !main.querySelector("[data-ad-position]")) {
      const zone = document.createElement("aside");
      zone.className = "ad-zone";
      zone.dataset.adPosition = "content-end";
      zone.setAttribute("aria-label", "Advertisement");
      main.append(zone);
    }
    for (const zone of document.querySelectorAll("[data-ad-position]")) {
      const slot = ads.slots?.[zone.dataset.adPosition];
      if (!/^\d{10}$/.test(slot || "") || zone.querySelector(".adsbygoogle"))
        continue;
      const label = document.createElement("span");
      label.className = "ad-label";
      label.textContent = "Advertisement";
      const unit = document.createElement("ins");
      unit.className = "adsbygoogle";
      unit.style.display = "block";
      Object.assign(unit.dataset, {
        adClient: ads.publisherId,
        adSlot: slot,
        adFormat: "auto",
        fullWidthResponsive: "true",
      });
      zone.replaceChildren(label, unit);
      zone.dataset.active = "true";
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    }
    if (!document.querySelector(".adsbygoogle")) return;
  }

  if (document.querySelector('script[src*="pagead/js/adsbygoogle.js"]')) return;
  const script = document.createElement("script");
  script.async = true;
  script.crossOrigin = "anonymous";
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ads.publisherId}`;
  script.addEventListener("error", () => {
    console.warn("GLab could not load the Google AdSense script.");
    script.remove();
  });
  document.head.append(script);
}
