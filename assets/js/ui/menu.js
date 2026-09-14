export function initMenu() {
  const button = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('[data-mobile-menu]');
  const backdrop = document.querySelector('[data-menu-backdrop]');
  if (!button || !menu || !backdrop) return;

  let previousFocus = null;
  const focusables = () => [...menu.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])')];
  const setOpen = (open) => {
    menu.hidden = !open;
    backdrop.hidden = !open;
    button.setAttribute('aria-expanded', String(open));
    document.documentElement.classList.toggle('menu-open', open);
    if (open) {
      previousFocus = document.activeElement;
      requestAnimationFrame(() => focusables()[0]?.focus());
    } else if (previousFocus instanceof HTMLElement && document.contains(previousFocus)) {
      previousFocus.focus({ preventScroll: true });
    }
  };

  button.addEventListener('click', () => setOpen(menu.hidden));
  backdrop.addEventListener('click', () => setOpen(false));
  menu.addEventListener('click', (event) => { if (event.target.closest('a')) setOpen(false); });
  addEventListener('keydown', (event) => {
    if (menu.hidden) return;
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); return; }
    if (event.key !== 'Tab') return;
    const items = focusables();
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  addEventListener('resize', () => { if (innerWidth > 860 && !menu.hidden) setOpen(false); }, { passive: true });
}
