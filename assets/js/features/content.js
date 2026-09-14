const COLLECTIONS = {
  projects: '/data/projects/',
  articles: '/data/articles/'
};

const el = (tag, options = {}, children = []) => {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value == null) continue;
    if (key === 'className') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key === 'dataset') Object.assign(node.dataset, value);
    else node.setAttribute(key, value);
  }
  node.append(...children.filter(Boolean));
  return node;
};

const paragraph = (text) => el('p', { text });
const list = (items, ordered = false) => items?.length
  ? el(ordered ? 'ol' : 'ul', {}, items.map((item) => el('li', { text: item })))
  : null;
const eyebrow = (text) => el('p', { className: 'eyebrow', text });
export const safeUrl = (value) => {
  if (typeof value !== 'string' || /[\\\s\u0000-\u001f]/.test(value)) return '';
  if (/^\/(?!\/)/.test(value) || /^#\S+/.test(value)) return value;
  try { const url = new URL(value); return /^https?:$/.test(url.protocol) && url.hostname ? value : ''; }
  catch { return ''; }
};
const action = (label, href) => safeUrl(href) ? el('a', {
  href, text: `${label}${/^https?:/.test(href) ? ' ↗' : ' →'}`,
  ...( /^https?:/.test(href) ? { target: '_blank', rel: 'noopener noreferrer' } : {})
}) : null;
export const detailUrl = (type, id, fragment = '') => `/${type}/?id=${encodeURIComponent(id)}${fragment}`;
export const publishedItems = (items = []) => items.filter((item) => (item.publicationStatus || 'published') === 'published');
export const normalizeSection = (section = {}) => ({
  paragraphs: [...(section.content ? [section.content] : []), ...(section.paragraphs || []), ...(!section.content && !section.paragraphs?.length && section.summary ? [section.summary] : [])],
  points: [...(section.points || []), ...(section.items || [])]
});

function setMetadata(item, type) {
  const description = item.summary || item.excerpt || '';
  document.title = `${item.title} — GLab`;
  document.querySelector('meta[name="description"]')?.setAttribute('content', description);
  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) canonical.href = `${location.origin}${detailUrl(type, item.id)}`;
  document.querySelector('meta[property="og:url"]')?.setAttribute('content', canonical?.href || location.href);
  for (const [selector, value] of [['meta[property=\"og:title\"]', document.title], ['meta[name=\"twitter:title\"]', document.title], ['meta[property=\"og:description\"]', description], ['meta[name=\"twitter:description\"]', description]]) document.querySelector(selector)?.setAttribute('content', value);
  history.replaceState(null, '', `${detailUrl(type, item.id)}${location.hash}`);
}

function links(items) {
  if (!items?.length) return null;
  return el('div', { className: 'section-links' }, items
    .filter((item) => typeof item === 'string' || item?.url)
    .map((item) => typeof item === 'string' ? action('Open link', item) : action(item.label || 'Open link', item.url)));
}

function narrativeSection(section) {
  const body = el('div');
  body.append(el('h2', { text: section.title || section.label }));
  const normalized = normalizeSection(section);
  normalized.paragraphs.forEach((text) => body.append(paragraph(text)));
  body.append(...[list(normalized.points), section.callout ? el('p', { className: 'detail-callout', text: section.callout }) : null, links(section.links)].filter(Boolean));
  return el('section', { className: 'detail-section' }, [eyebrow(section.label || 'Details'), body]);
}

function tags(items) {
  return items?.length ? el('ul', { className: 'tag-list' }, items.map((tag) => el('li', { text: tag }))) : null;
}

function facts(items) {
  return el('div', { className: 'case-facts' }, items.filter(([, value]) => value).map(([label, value]) =>
    el('div', {}, [el('span', { text: label }), el('strong', { text: String(value) })])));
}

export function accentStyle(item) {
  const palettes = [['#5465db','#30b8aa'],['#ad4c73','#efbd64'],['#087b91','#80bd73'],['#825ac2','#76b7e5']];
  const seed = [...(item.category || item.kind || item.id || '')].reduce((sum, c) => sum + c.charCodeAt(0), 0);
  const colors = item.colors?.length === 2 && item.colors.every(c => /^#[0-9a-f]{6}$/i.test(c)) ? item.colors : palettes[seed % palettes.length];
  return `--project-a:${colors[0]};--project-b:${colors[1]}`;
}

function projectCard(project, index) {
  const card = el('article', {
    className: 'project-card',
    dataset: {
      projectCard: '', category: project.category || 'Other',
      search: [project.id, project.title, project.summary, project.category, ...(project.tags || [])].join(' ').toLowerCase()
    },
    style: accentStyle(project)
  });
  card.append(
    el('div', { className: 'project-card-glow', 'aria-hidden': 'true' }),
    el('div', { className: 'project-card-head' }, [
      el('span', { className: 'project-number', text: String(index + 1).padStart(2, '0') }),
      el('span', { className: 'project-status', text: project.status })
    ]),
    el('div', { className: 'project-copy' }, [
      eyebrow(`${project.category} · ${project.year}`), el('h2', { text: project.title }),
      paragraph(project.summary), tags(project.tags),
      action('Read complete case study', detailUrl('projects', project.id))
    ])
  );
  return card;
}

function articleCard(article) {
  return el('a', { className: 'writing-item', style: accentStyle(article), dataset: {projectCard: '', category: article.kind || 'Article', search: [article.id, article.title, article.excerpt, ...(article.tags || [])].join(' ').toLowerCase()}, href: detailUrl('articles', article.id) }, [
    el('time', { className: 'writing-date', datetime: article.date, text: article.date }),
    el('div', {}, [eyebrow(`${article.kind || 'Article'} · ${article.readTime || ''}`), el('h2', { text: article.title })]),
    el('p', { className: 'writing-excerpt', text: article.excerpt }), el('span', { 'aria-hidden': 'true', text: '↗' })
  ]);
}

function renderProject(project, root) {
  setMetadata(project, 'projects');
  root.className = 'content-page case-page';
  const hero = el('header', { className: 'case-hero', style: accentStyle(project) }, [
    el('div', {}, [eyebrow(`${project.category} · ${project.year}`), el('h1', { text: project.title }), el('p', { className: 'lead', text: project.summary }), tags(project.tags)]),
    facts([['Status', project.status], ['Year', project.year], ['Category', project.category], ['License', project.repository?.license]])
  ]);
  root.replaceChildren(hero);
  (project.sections || []).forEach((section) => root.append(narrativeSection(section)));
  if (project.architecture) root.append(narrativeSection({ label: 'Architecture', title: project.architecture.title, paragraphs: [project.architecture.summary], points: project.architecture.steps, links: project.architecture.url ? [{ label: 'View architecture source', url: project.architecture.url }] : [] }));
  if (project.guide) {
    const guide = project.guide;
    const body = el('div');
    body.append(el('h2', {text: guide.title}), paragraph(guide.summary));
    if (guide.audience) body.append(el('p', {className: 'detail-callout', text: `For: ${guide.audience}`}));
    for (const [label, values, ordered] of [['Prerequisites', guide.prerequisites], ['Steps', guide.steps, true]]) {
      if (values?.length) body.append(el('h3', {text: label}), list(values, ordered));
    }
    if (guide.command) body.append(el('h3', {text: 'Commands'}), el('pre', {className: 'copyable-code'}, [el('code', {text: guide.command})]));
    for (const [label, values] of [['Verification', guide.verification], ['Troubleshooting', guide.troubleshooting]]) {
      if (values?.length) body.append(el('h3', {text: label}), list(values));
    }
    if (guide.url) body.append(links([{label: 'Open source guide', url: guide.url}]));
    root.append(el('section', { className: 'detail-section', id: 'guide' }, [eyebrow('Project guide'), body]));
  }
  if (project.validation) root.append(narrativeSection({ label: 'Testing', title: project.validation.title, paragraphs: [project.validation.summary], points: project.validation.checks, links: project.validation.url ? [{ label: 'View validation source', url: project.validation.url }] : [] }));
  const sources = [project.repository?.url && { label: 'Source repository', url: project.repository.url }, project.demoUrl && { label: 'Live demo', url: project.demoUrl }, project.url && { label: 'Project link', url: project.url }].filter(Boolean);
  root.append(el('section', { className: 'detail-section' }, [eyebrow('Project status and links'), el('div', {}, [el('h2', { text: project.status || 'Project links' }), project.pageNote ? paragraph(project.pageNote) : null, links(sources)])]));
}

function renderArticle(article, root) {
  setMetadata(article, 'articles');
  root.className = 'content-page';
  root.replaceChildren(el('header', { className: 'content-hero', style: accentStyle(article) }, [eyebrow(`${article.kind || 'Article'} · ${article.readTime || ''}`), el('h1', { text: article.title }), el('p', { className: 'lead', text: article.excerpt }), tags(article.tags), el('p', { className: 'content-meta', text: `Published ${article.date}${article.updated ? ` · Updated ${article.updated}` : ''}` })]));
  const body = el('article', { className: 'article-body' });
  (article.sections || []).forEach((section) => {
    const sectionNode = narrativeSection(section);
    sectionNode.className = '';
    sectionNode.firstElementChild?.remove();
    body.append(sectionNode);
  });
  if (article.url) body.append(links([{label: 'Source / further reading', url: article.url}]));
  root.append(body);
}

function addContents(root, type) {
  const sections = [...root.querySelectorAll('section')].filter(section => section.querySelector('h2'));
  const nav = el('nav', {className: 'content-navigation', 'aria-label': 'On this page'}, [action(`All ${type}`, `/${type}/`)]);
  if (sections.length > 1) {
    const contents = el('details', {className: 'contents-list'}, [el('summary', {text: 'On this page'})]);
    contents.append(el('ol', {}, sections.map((section, index) => {
      if (!section.id) section.id = `section-${index + 1}`;
      return el('li', {}, [action(section.querySelector('h2').textContent, `#${section.id}`)]);
    })));
    nav.append(contents);
  }
  root.prepend(nav);
}

function renderNotFound(type, root) {
  root.className = 'archive';
  root.replaceChildren(el('div', { className: 'empty-state' }, [el('h1', { text: 'Content not found' }), paragraph(`This ${type.slice(0, -1)} may have moved or is not published.`), action(`Browse all ${type}`, `/${type}/`)]));
}

function initFilters(root) {
  const cards = [...root.querySelectorAll('[data-project-card]')];
  const filters = document.querySelector('[data-project-filters]');
  const search = document.querySelector('[data-collection-search]');
  if (!filters) return;
  let category = filters.querySelector('[aria-pressed="true"]')?.textContent || 'All';
  const categories = ['All', ...new Set(cards.map((card) => card.dataset.category))];
  if (!categories.includes(category)) category = 'All';
  root.parentElement.querySelector('.collection-status')?.remove();
  const status = el('p', {className: 'collection-status', role: 'status'});
  root.after(status);
  const update = () => {
    const query = search?.value.trim().toLowerCase() || '';
    cards.forEach((card) => { card.hidden = (category !== 'All' && card.dataset.category !== category) || (query && !card.dataset.search.includes(query)); });
    const count = cards.filter(card => !card.hidden).length;
    status.textContent = count ? `${count} of ${cards.length} results` : 'No matches. Try another search or category.';
  };
  filters.replaceChildren(...categories.map((name) => {
    const button = el('button', { type: 'button', className: `filter-button${name === category ? ' active' : ''}`, text: name, 'aria-pressed': String(name === category) });
    button.addEventListener('click', () => { category = name; [...filters.children].forEach((item) => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', String(item === button)); }); update(); });
    return button;
  }));
  if (search) search.oninput = update;
  update();
}

export async function loadCatalog(type) {
  const base = COLLECTIONS[type];
  const response = await fetch(`${base}index.json`, {cache: 'no-cache', credentials: 'same-origin', signal: AbortSignal.timeout(12000)});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const index = await response.json();
  if (Array.isArray(index?.items)) return publishedItems(index.items);
  const files = Array.isArray(index) ? index : index.files;
  if (!Array.isArray(files)) throw new Error(`Invalid ${type} index`);
  const results = await Promise.allSettled(files.map(async (file) => {
    if (typeof file !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*\.json$/.test(file) || file === 'index.json') throw new Error(`Invalid ${type} record path`);
    const itemResponse = await fetch(`${base}${file}`, {cache: 'no-cache', credentials: 'same-origin', signal: AbortSignal.timeout(12000)});
    if (!itemResponse.ok) throw new Error(`HTTP ${itemResponse.status}`);
    const item = await itemResponse.json();
    if (`${item.id}.json` !== file) throw new Error(`Record filename/id mismatch: ${file}`);
    return item;
  }));
  const records = results.filter((result) => result.status === 'fulfilled').map((result) => result.value);
  const failures = results.filter((result) => result.status === 'rejected');
  if (failures.length) console.warn(`GLab skipped ${failures.length} invalid ${type} record(s)`, failures.map((result) => result.reason));
  if (!records.length && failures.length) throw failures[0].reason;
  return publishedItems(records);
}

async function loadRecord(type, id) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id || '')) return null;
  const response = await fetch(`${COLLECTIONS[type]}${id}.json`, {cache: 'no-cache', credentials: 'same-origin', signal: AbortSignal.timeout(12000)});
  if (!response.ok) return null;
  const item = await response.json();
  return item.id === id && (item.publicationStatus || 'published') === 'published' ? item : null;
}

export async function initContent() {
  const previews = [...document.querySelectorAll('[data-preview]')];
  await Promise.allSettled(['projects', 'articles'].map(async type => {
    const targets = previews.filter(node => node.dataset.preview === type || (type === 'projects' && node.dataset.preview === 'guides'));
    if (!targets.length) return;
    const items = await loadCatalog(type);
    const selected = [...items.filter(item => item.featured), ...items.filter(item => !item.featured)].slice(0, type === 'projects' ? 4 : 6);
    targets.forEach(node => {
      node.replaceChildren(...(node.dataset.preview === 'guides'
        ? items.filter(item => item.guide?.title).slice(0,4).map(item => el('a', {className:'archive-card guide-card', href:detailUrl('projects', item.id, '#guide')}, [eyebrow(`${item.title} · Project guide`),el('h3',{text:item.guide.title}),paragraph(item.guide.summary)]))
        : selected.map(type === 'projects' ? projectCard : articleCard)));
    });
  }));
  let root = document.querySelector('[data-content-root]');
  const type = root?.dataset.collection;
  if (!root || !COLLECTIONS[type]) return;
  root.setAttribute('aria-busy', 'true');
  try {
    const items = await loadCatalog(type);
    const id = new URLSearchParams(location.search).get('id');
    if (id) {
      const page = root.closest('main');
      if (page) { page.replaceChildren(root); root = page; }
    }
    if (id) {
      const item = items.find((entry) => entry.id === id) || await loadRecord(type, id);
      if (!item) renderNotFound(type, root);
      else if (type === 'projects') renderProject(item, root);
      else renderArticle(item, root);
      if (item) addContents(root, type);
    } else if (type === 'projects') {
      root.replaceChildren(...items.map(projectCard));
      initFilters(root);
    } else {
      root.replaceChildren(...items.map(articleCard));
      initFilters(root);
    }
    if (!items.length && !id) root.append(paragraph('New content is on the way. Check back soon.'));
    if (location.hash) requestAnimationFrame(() => {
      try { document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView(); }
      catch { /* Ignore malformed fragment encoding without replacing the article. */ }
    });
    document.dispatchEvent(new CustomEvent('glab:content-rendered'));
  } catch (error) {
    root.replaceChildren(el('div', { className: 'empty-state' }, [el('h2', { text: 'Content is temporarily unavailable' }), paragraph('Check your connection and try again.'), el('button', { type: 'button', className: 'button-secondary', text: 'Try again' })]));
    root.querySelector('button')?.addEventListener('click', () => location.reload());
    console.warn('GLab content load failed', error);
  } finally { root.removeAttribute('aria-busy'); }
}
