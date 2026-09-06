let indexPromise = null;

function loadIndex() {
  return indexPromise || (indexPromise = fetch('/search-index.json', {
    credentials: 'same-origin',
    cache: 'no-cache'
  }).then((response) => {
    if (!response.ok) throw new Error('Search index unavailable');
    return response.json();
  }));
}

function score(item, query) {
  const value = query.toLowerCase().trim();
  if (!value) return 1;
  const words = value.split(/\s+/).filter(Boolean);
  const title = (item.title || '').toLowerCase();
  const summary = (item.summary || '').toLowerCase();
  const tags = (item.tags || []).join(' ').toLowerCase();
  const type = (item.type || '').toLowerCase();
  let result = 0;
  for (const word of words) {
    if (title.includes(word)) result += 8;
    if (tags.includes(word)) result += 4;
    if (type.includes(word)) result += 2;
    if (summary.includes(word)) result += 1;
  }
  return result;
}

function makeResult(item) {
  const link = document.createElement('a');
  link.className = 'search-result';
  link.href = item.url;
  const type = document.createElement('span');
  type.className = 'eyebrow';
  type.textContent = item.type || 'Result';
  const title = document.createElement('strong');
  title.textContent = item.title;
  const summary = document.createElement('span');
  summary.className = 'search-result-summary';
  summary.textContent = item.summary || '';
  link.append(type, title, summary);
  return link;
}

export function initSearch() {
  const dialog = document.querySelector('[data-search-dialog]');
  const input = document.querySelector('[data-global-search]');
  const results = document.querySelector('[data-search-results]');
  const openers = [...document.querySelectorAll('[data-search-toggle]')];
  const closeButton = document.querySelector('[data-search-close]');
  if (!dialog || !input || !results || !openers.length) return;

  let previousFocus = null;

  const render = async () => {
    results.setAttribute('aria-busy', 'true');
    try {
      const data = await loadIndex();
      const query = input.value.trim();
      const matches = data
        .map((item) => [score(item, query), item])
        .filter(([value]) => value > 0)
        .sort((a, b) => b[0] - a[0] || a[1].title.localeCompare(b[1].title))
        .slice(0, 10)
        .map(([, item]) => item);
      if (matches.length) {
        results.replaceChildren(...matches.map(makeResult));
      } else {
        const empty = document.createElement('p');
        empty.className = 'empty-state';
        empty.textContent = 'No matching projects, articles or project guides.';
        results.replaceChildren(empty);
      }
    } catch {
      const empty = document.createElement('p');
      empty.className = 'empty-state';
      empty.textContent = 'Search is temporarily unavailable.';
      results.replaceChildren(empty);
    } finally {
      results.removeAttribute('aria-busy');
    }
  };

  const open = () => {
    previousFocus = document.activeElement;
    if (!dialog.open) {
      if (typeof dialog.showModal === 'function') dialog.showModal();
      else dialog.setAttribute('open', '');
    }
    requestAnimationFrame(() => {
      input.focus();
      input.select();
      render();
    });
  };

  const close = () => {
    if (dialog.open && typeof dialog.close === 'function') dialog.close();
    else dialog.removeAttribute('open');
    if (previousFocus instanceof HTMLElement && document.contains(previousFocus)) {
      previousFocus.focus({ preventScroll: true });
    }
  };

  openers.forEach((button) => button.addEventListener('click', open));
  closeButton?.addEventListener('click', close);
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) close();
  });
  input.addEventListener('input', render);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      const first = results.querySelector('a');
      if (first) {
        event.preventDefault();
        location.href = first.href;
      }
    }
  });
  addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && dialog.open) {
      close();
      return;
    }
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(event.target?.tagName || '');
    const shortcut = (event.key === '/' && !typing && !event.ctrlKey && !event.metaKey && !event.altKey)
      || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k');
    if (shortcut) {
      event.preventDefault();
      open();
    }
  });
}
