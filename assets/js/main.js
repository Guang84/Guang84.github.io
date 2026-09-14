import { initViewport } from './core/viewport.js';
import { initHeader } from './ui/header.js';
import { initMenu } from './ui/menu.js';
import { initPreferences } from './ui/preferences.js';
import { initReading } from './ui/reading.js';
import { initReveal } from './ui/reveal.js';
import { initAds } from './features/ads.js';
import { initSearch } from './features/search.js';
import { initSiteConfig } from './features/site-config.js';
import { initPWA } from './features/pwa.js';
import { initShare } from './features/share.js';
import { initCodeCopy } from './features/code-copy.js';
import { initContent } from './features/content.js';

const FEATURES = [
  ['viewport', initViewport],
  ['header', initHeader],
  ['menu', initMenu],
  ['preferences', initPreferences],
  ['reading', initReading],
  ['reveal', initReveal],
  ['search', initSearch],
  ['site-config', initSiteConfig],
  ['pwa', initPWA],
  ['share', initShare],
  ['code-copy', initCodeCopy],
  ['ads', initAds]
];

async function boot() {
  document.documentElement.classList.add('js');
  const contentReady = initContent().catch((error) => console.warn('GLab content feature failed', error));
  for (const [name, initializer] of FEATURES) {
    try {
      if (['reading', 'reveal', 'share', 'code-copy', 'ads'].includes(name)) {
        contentReady.then(initializer).catch((error) => console.warn(`GLab ${name} feature failed`, error));
        continue;
      }
      const result = initializer();
      if (result instanceof Promise) result.catch((error) => console.warn(`GLab ${name} feature failed`, error));
    } catch (error) {
      console.warn(`GLab ${name} feature failed`, error);
    }
  }
}

document.readyState === 'loading'
  ? document.addEventListener('DOMContentLoaded', boot, { once: true })
  : boot();
