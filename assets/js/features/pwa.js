let promptEvent = null;

function toast(message, action) {
  let node = document.querySelector('[data-app-toast]');
  if (!node) {
    node = document.createElement('div');
    node.className = 'app-toast';
    node.dataset.appToast = '';
    node.setAttribute('role', 'status');
    document.body.append(node);
  }
  node.replaceChildren();
  const text = document.createElement('span');
  text.textContent = message;
  node.append(text);
  if (action) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = action.label;
    button.addEventListener('click', action.run);
    node.append(button);
  }
  node.hidden = false;
  if (!action) setTimeout(() => { node.hidden = true; }, 2600);
}

export async function initPWA() {
  const install = document.querySelector('[data-install]');
  if (install) {
    addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      promptEvent = event;
      install.hidden = false;
    });
    install.addEventListener('click', async () => {
      if (!promptEvent) return;
      promptEvent.prompt();
      await promptEvent.userChoice;
      promptEvent = null;
      install.hidden = true;
    });
    addEventListener('appinstalled', () => {
      install.hidden = true;
      promptEvent = null;
      toast('GLab installed.');
    });
  }

  if (!('serviceWorker' in navigator)) return;
  try {
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/',
      updateViaCache: 'none'
    });
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      location.reload();
    });
    const offer = (worker) => toast('A newer GLab version is ready.', {
      label: 'Update',
      run: () => worker.postMessage({ type: 'SKIP_WAITING' })
    });
    if (registration.waiting && navigator.serviceWorker.controller) offer(registration.waiting);
    registration.addEventListener('updatefound', () => {
      const worker = registration.installing;
      if (!worker) return;
      worker.addEventListener('statechange', () => {
        if (worker.state === 'installed' && navigator.serviceWorker.controller) offer(worker);
      });
    });
  } catch {
    // The site remains fully usable when service workers are unavailable.
  }

  addEventListener('offline', () => toast('You are offline. Cached GLab pages remain available.'));
  addEventListener('online', () => toast('Connection restored.'));
}
