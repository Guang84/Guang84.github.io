import{initViewport}from'./core/viewport.js';
import{initHeader}from'./ui/header.js';
import{initMenu}from'./ui/menu.js';
import{initPreferences}from'./ui/preferences.js';
import{initReading}from'./ui/reading.js';
import{initAds}from'./features/ads.js';
import{initProjects}from'./features/projects.js';
import{initSearchShortcut}from'./features/search.js';
import{initPWA}from'./features/pwa.js';
function boot(){initViewport();initHeader();initMenu();initPreferences();initReading();initSearchShortcut();initPWA();initAds();initProjects()}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',boot,{once:true}):boot();
