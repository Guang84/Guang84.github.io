import { safeUrl } from './content.js';

const el = (tag, options = {}, children = []) => {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value == null) continue;
    if (key === 'className') node.className = value;
    else if (key === 'text') node.textContent = value;
    else node.setAttribute(key, value);
  }
  node.append(...children.filter(Boolean));
  return node;
};

const isExternal = (url) => /^https?:\/\//.test(url);

function renderImportantLinks(links = []) {
  const root = document.querySelector('[data-site-important-links]');
  if (!root || !Array.isArray(links)) return;
  const cards = links.map((link) => {
    const href = safeUrl(link?.url);
    if (!href || !link?.label) return null;
    return el('a', {
      className: 'important-link-card',
      href,
      ...(isExternal(href) ? { target: '_blank', rel: 'noopener noreferrer' } : {})
    }, [
      el('span', { className: 'link-kind', text: link.kind || 'Link' }),
      el('strong', { text: link.label }),
      link.description ? el('p', { text: link.description }) : null,
      el('span', { className: 'link-arrow', 'aria-hidden': 'true', text: isExternal(href) ? ' ↗' : ' →' })
    ]);
  }).filter(Boolean);
  if (cards.length) root.replaceChildren(...cards);
}

function renderProfile(profile = {}) {
  const heading = document.querySelector('[data-site-greeting]');
  if (heading && profile.greeting) heading.textContent = profile.greeting;

  const roles = document.querySelector('[data-site-roles]');
  if (roles && Array.isArray(profile.roles)) {
    roles.replaceChildren(...profile.roles.flatMap((role, index) => [
      index ? el('i', { 'aria-hidden': 'true', text: '•' }) : null,
      el('span', { text: role })
    ]).filter(Boolean));
  }

  const intro = document.querySelector('[data-site-intro]');
  if (intro && Array.isArray(profile.intro)) {
    const paragraphs = profile.intro.filter(Boolean).map((text) => el('p', { text }));
    if (paragraphs.length) intro.replaceChildren(...paragraphs);
  }

  const workLine = document.querySelector('[data-site-work-line]');
  if (workLine && profile.workLine) workLine.textContent = profile.workLine;

  const interestLine = document.querySelector('[data-site-interest-line]');
  if (interestLine && profile.interestLine) interestLine.textContent = profile.interestLine;

  const interests = document.querySelector('[data-site-interests]');
  if (interests && Array.isArray(profile.interests)) {
    const cards = profile.interests.filter((item) => item?.title).map((item, index) => el('article', {
      className: 'interest-card'
    }, [
      el('span', { className: 'interest-index', text: String(index + 1).padStart(2, '0') }),
      el('h3', { text: item.title }),
      item.description ? el('p', { text: item.description }) : null
    ]));
    if (cards.length) interests.replaceChildren(...cards);
  }
}

export async function initSiteConfig() {
  const needsConfig = document.querySelector('[data-site-important-links], [data-site-greeting], [data-site-interests]');
  if (!needsConfig) return;
  const response = await fetch('/data/config/site.json', { cache: 'no-cache', credentials: 'same-origin', signal: AbortSignal.timeout(12000) });
  if (!response.ok) return;
  const site = await response.json();
  renderImportantLinks(site.importantLinks);
  renderProfile(site.profile);
}
