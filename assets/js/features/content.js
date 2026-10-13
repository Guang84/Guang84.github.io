const CATALOGS = {
  projects: "/data/projects/index.json",
  articles: "/data/articles/index.json",
};

export const safeUrl = (value) => {
  if (typeof value !== "string" || /[\\\s\u0000-\u001f]/.test(value)) return "";
  if (/^\/(?!\/)/.test(value) || /^#\S+/.test(value)) return value;
  try {
    const url = new URL(value);
    return /^https?:$/.test(url.protocol) && url.hostname ? value : "";
  } catch {
    return "";
  }
};

export const detailUrl = (type, id, fragment = "") =>
  `/${type}/${id}/${fragment}`;
const el = (tag, attrs = {}, children = []) => {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null) continue;
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else node.setAttribute(key, value);
  }
  node.append(...children.filter(Boolean));
  return node;
};
const tags = (items = []) =>
  items.length
    ? el(
        "ul",
        { className: "tag-list" },
        items.map((tag) => el("li", { text: tag })),
      )
    : null;
const eyebrow = (text) => el("p", { className: "eyebrow", text });
const paragraph = (text) => el("p", { text });

export async function loadCatalog(type) {
  const endpoint = CATALOGS[type];
  if (!endpoint) throw new Error(`Unknown GLab catalogue: ${type}`);
  const response = await fetch(endpoint, {
    cache: "no-cache",
    credentials: "same-origin",
    signal: AbortSignal.timeout(12000),
  });
  if (!response.ok)
    throw new Error(
      `Unable to load ${type} catalogue: HTTP ${response.status}`,
    );
  const catalog = await response.json();
  if (!Array.isArray(catalog.items))
    throw new Error(`Invalid metadata catalogue: ${type}`);
  return catalog.items.filter(
    (item) => item && item.publicationStatus === "published",
  );
}

function articleCard(article) {
  const query = [
    article.id,
    article.title,
    article.excerpt,
    ...(article.tags || []),
  ]
    .join(" ")
    .toLowerCase();
  return el(
    "a",
    {
      className: "writing-item",
      dataset: {
        projectCard: "",
        category: article.kind || "Article",
        search: query,
      },
      href: detailUrl("articles", article.id),
    },
    [
      el("time", {
        className: "writing-date",
        dateTime: article.date,
        text: article.date,
      }),
      el("div", {}, [
        eyebrow(`${article.kind || "Article"} · ${article.readTime || ""}`),
        el("h2", { text: article.title }),
      ]),
      paragraph(article.excerpt || ""),
      el("span", { ariaHidden: "true", text: "↗" }),
    ],
  );
}
function projectCard(project, index) {
  const query = [
    project.id,
    project.title,
    project.summary,
    project.category,
    ...(project.tags || []),
  ]
    .join(" ")
    .toLowerCase();
  return el(
    "article",
    {
      className: "project-card",
      dataset: {
        projectCard: "",
        category: project.category || "Other",
        search: query,
      },
    },
    [
      el("div", { className: "project-card-head" }, [
        el("span", {
          className: "project-number",
          text: String(index + 1).padStart(2, "0"),
        }),
        el("span", { className: "project-status", text: project.status || "" }),
      ]),
      el("div", { className: "project-copy" }, [
        eyebrow(`${project.category || "Project"} · ${project.year || ""}`),
        el("h2", { text: project.title }),
        paragraph(project.summary || ""),
        tags(project.tags || []),
        el("a", {
          href: detailUrl("projects", project.id),
          text: "Read complete case study →",
        }),
      ]),
    ],
  );
}
function guideCard(project) {
  return el(
    "a",
    {
      className: "archive-card guide-card",
      href: detailUrl("projects", project.id, "#guide"),
    },
    [
      eyebrow(`${project.title} · Project guide`),
      el("h3", { text: project.guide.title }),
      paragraph(project.guide.summary || project.summary || ""),
    ],
  );
}
function initFilters(root) {
  const search = document.querySelector("[data-collection-search]");
  const filters = document.querySelector("[data-project-filters]");
  if (!filters && !search) return;
  const cards = [...root.querySelectorAll("[data-project-card]")];
  const categories = [
    "All",
    ...new Set(cards.map((card) => card.dataset.category).filter(Boolean)),
  ];
  let category = "All";
  if (filters)
    filters.replaceChildren(
      ...categories.map((name) => {
        const button = el("button", {
          type: "button",
          className: `filter-button${name === "All" ? " active" : ""}`,
          text: name,
          "aria-pressed": String(name === "All"),
        });
        button.addEventListener("click", () => {
          category = name;
          [...filters.children].forEach((btn) => {
            const active = btn === button;
            btn.classList.toggle("active", active);
            btn.setAttribute("aria-pressed", String(active));
          });
          update();
        });
        return button;
      }),
    );
  const status = el("p", { className: "search-hint", role: "status" });
  root.after(status);
  function update() {
    const q = search?.value.trim().toLowerCase() || "";
    cards.forEach((card) => {
      card.hidden =
        (category !== "All" && card.dataset.category !== category) ||
        (q && !card.dataset.search.includes(q));
    });
    const count = cards.filter((c) => !c.hidden).length;
    status.textContent = count
      ? `${count} of ${cards.length} results`
      : "No matches. Try another search or category.";
  }
  if (search) search.addEventListener("input", update);
  update();
}

export async function initContent() {
  // Canonical article/project pages are complete HTML; never fetch JSON to render their body.
  const root = document.querySelector("[data-content-root]");
  const type = root?.dataset.collection;
  if (root && CATALOGS[type]) {
    const legacyId = new URLSearchParams(location.search).get("id");
    if (legacyId && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(legacyId)) {
      location.replace(detailUrl(type, legacyId) + location.hash);
      return;
    }
    if (
      root.querySelector("[data-project-card]") &&
      root.dataset.filtersInitialized !== "true"
    ) {
      initFilters(root);
      root.dataset.filtersInitialized = "true";
    }
  }
  const previews = [...document.querySelectorAll("[data-preview]")];
  if (!previews.length) return;
  await Promise.allSettled(
    ["projects", "articles"].map(async (type) => {
      const targets = previews.filter(
        (node) =>
          node.dataset.preview === type ||
          (type === "projects" && node.dataset.preview === "guides"),
      );
      if (!targets.length) return;
      const items = await loadCatalog(type);
      const selected = [
        ...items.filter((x) => x.featured),
        ...items.filter((x) => !x.featured),
      ].slice(0, type === "projects" ? 4 : 6);
      targets.forEach((node) =>
        node.replaceChildren(
          ...(node.dataset.preview === "guides"
            ? items
                .filter((x) => x.guide?.title)
                .slice(0, 4)
                .map(guideCard)
            : selected.map((item, index) =>
                type === "projects"
                  ? projectCard(item, index)
                  : articleCard(item),
              )),
        ),
      );
    }),
  );
}
