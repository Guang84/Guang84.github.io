function announce(text) {
  const live = document.querySelector('[data-live-region]');
  if (live) live.textContent = text;
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.opacity = '0';
  document.body.append(area);
  area.select();
  const ok = document.execCommand('copy');
  area.remove();
  if (!ok) throw new Error('Copy unavailable');
}

export function initCodeCopy() {
  document.querySelectorAll('pre > code').forEach((code) => {
    const pre = code.parentElement;
    if (!pre || pre.querySelector('[data-copy-code]')) return;
    pre.classList.add('copyable-code');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy-code-button';
    button.dataset.copyCode = '';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', 'Copy code to clipboard');
    button.addEventListener('click', async () => {
      try {
        await copyText(code.textContent || '');
        button.textContent = 'Copied';
        announce('Code copied to clipboard.');
      } catch {
        button.textContent = 'Copy failed';
      }
      setTimeout(() => { button.textContent = 'Copy'; }, 1600);
    });
    pre.append(button);
  });
}
