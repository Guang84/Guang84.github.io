import { initViewport } from './core/viewport.js';
import { initHeader } from './ui/header.js';
import { initMenu } from './ui/menu.js';
import { initPreferences } from './ui/preferences.js';
import { initReading } from './ui/reading.js';
import { initAds } from './features/ads.js';
import { initProjects } from './features/projects.js';
import { initSearch } from './features/search.js';
import { initPWA } from './features/pwa.js';
import { initShare } from './features/share.js';
import { initCodeCopy } from './features/code-copy.js';

const FEATURES = [
  ['viewport', initViewport],
  ['header', initHeader],
  ['menu', initMenu],
  ['preferences', initPreferences],
  ['reading', initReading],
  ['search', initSearch],
  ['pwa', initPWA],
  ['share', initShare],
  ['code-copy', initCodeCopy],
  ['ads', initAds],
  ['projects', initProjects]
];

function boot() {
  document.documentElement.classList.add('js');
  for (const [name, initializer] of FEATURES) {
    try {
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
