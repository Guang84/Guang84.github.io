import { getPref, setPref } from '../core/storage.js';

const SIZES = ['small', 'medium', 'large'];

function applySize(root, size) {
  const safe = SIZES.includes(size) ? size : 'medium';
  root.dataset.fontSize = safe;
  setPref('glab-font-size', safe);
  document.querySelectorAll('[data-font-step]').forEach((button) => {
    const step = Number(button.dataset.fontStep || 0);
    const index = SIZES.indexOf(safe);
    const disabled = (step < 0 && index === 0) || (step > 0 && index === SIZES.length - 1);
    button.disabled = disabled;
    button.setAttribute('aria-disabled', String(disabled));
  });
}

function effectiveTheme(root) {
  if (root.dataset.theme === 'dark' || root.dataset.theme === 'light') return root.dataset.theme;
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function updateThemeColor(theme) {
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'dark' ? '#0d1c15' : '#f6f3ec';
}

function updateThemeButton(button, theme) {
  const next = theme === 'dark' ? 'light' : 'dark';
  button.setAttribute('aria-label', `Use ${next} theme`);
  button.setAttribute('title', `Use ${next} theme`);
  button.setAttribute('aria-pressed', String(theme === 'dark'));
  const icon = button.querySelector('[data-theme-icon]');
  if (icon) icon.textContent = theme === 'dark' ? '☀' : '☾';
  updateThemeColor(theme);
}

export function initPreferences() {
  const root = document.documentElement;
  const storedSize = getPref('glab-font-size', 'medium');
  applySize(root, storedSize);

  document.querySelectorAll('[data-font-step]').forEach((button) => {
    button.addEventListener('click', () => {
      const step = Number(button.dataset.fontStep || 0);
      const current = SIZES.includes(root.dataset.fontSize) ? root.dataset.fontSize : 'medium';
      const index = SIZES.indexOf(current);
      const next = SIZES[Math.min(SIZES.length - 1, Math.max(0, index + step))];
      applySize(root, next);
    });
  });

  const themeButton = document.querySelector('[data-theme-toggle]');
  if (!themeButton) return;

  const storedTheme = getPref('glab-theme', '');
  if (storedTheme === 'dark' || storedTheme === 'light') root.dataset.theme = storedTheme;
  updateThemeButton(themeButton, effectiveTheme(root));

  themeButton.addEventListener('click', () => {
    const current = effectiveTheme(root);
    const next = current === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    setPref('glab-theme', next);
    updateThemeButton(themeButton, next);
  });

  const media = matchMedia('(prefers-color-scheme: dark)');
  media.addEventListener?.('change', () => {
    if (!root.dataset.theme) updateThemeButton(themeButton, effectiveTheme(root));
  });
}
