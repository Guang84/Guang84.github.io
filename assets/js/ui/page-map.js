export function initPageMap() {
  const maps = [...document.querySelectorAll("nav.doc-toc, nav.page-map")];
  if (!maps.length || !("IntersectionObserver" in window)) return;

  const targets = [];
  for (const map of maps) {
    for (const link of map.querySelectorAll('a[href^="#"]')) {
      let id = "";
      try {
        id = decodeURIComponent(link.getAttribute("href").slice(1));
      } catch {
        continue;
      }
      const target = document.getElementById(id);
      if (target) targets.push({ target, link, map });
    }
  }
  if (!targets.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (!visible.length) return;
      const current = targets.find((item) => item.target === visible[0].target);
      if (!current) return;
      for (const item of targets) {
        if (item.map !== current.map) continue;
        if (item === current) item.link.setAttribute("aria-current", "location");
        else item.link.removeAttribute("aria-current");
      }
    },
    { rootMargin: "-18% 0px -68% 0px", threshold: 0 },
  );
  targets.forEach(({ target }) => observer.observe(target));
}
