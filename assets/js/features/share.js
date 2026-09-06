function announce(text) {
  const node = document.querySelector('[data-live-region]');
  if (node) node.textContent = text;
}

export function initShare() {
  const hero = document.querySelector('.content-hero, .case-hero > div:first-child');
  if (!hero) return;

  const tools = document.createElement('div');
  tools.className = 'content-tools';
  const share = document.createElement('button');
  share.type = 'button';
  share.className = 'button-secondary compact-action';
  share.textContent = 'Share';
  share.setAttribute('aria-label', 'Share this page');
  share.addEventListener('click', async () => {
    const data = {
      title: document.title,
      text: document.querySelector('meta[name="description"]')?.content || '',
      url: location.href
    };
    try {
      if (navigator.share) {
        await navigator.share(data);
        announce('Share sheet opened.');
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(location.href);
        share.textContent = 'Link copied';
        announce('Page link copied to clipboard.');
        setTimeout(() => { share.textContent = 'Share'; }, 1600);
      } else {
        throw new Error('Share unavailable');
      }
    } catch (error) {
      if (error?.name !== 'AbortError') {
        share.textContent = 'Copy unavailable';
        setTimeout(() => { share.textContent = 'Share'; }, 1600);
      }
    }
  });
  tools.append(share);
  hero.append(tools);
}
