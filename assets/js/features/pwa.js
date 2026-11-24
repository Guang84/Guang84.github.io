import { initContent } from "./content.js";

const UPDATE_CHECK_INTERVAL_MS = 30 * 60 * 1000;
const UPDATE_EVENT_COOLDOWN_MS = 5 * 60 * 1000;

let promptEvent = null;
let toastTimer;

function toast(message, action) {
  clearTimeout(toastTimer);
  let node = document.querySelector("[data-app-toast]");
  if (!node) {
    node = document.createElement("div");
    node.className = "app-toast";
    node.dataset.appToast = "";
    node.setAttribute("role", "status");
    document.body.append(node);
  }
  node.replaceChildren();
  const text = document.createElement("span");
  text.textContent = message;
  node.append(text);
  if (action) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = action.label;
    button.addEventListener("click", action.run);
    node.append(button);
  }
  node.hidden = false;
  if (!action)
    toastTimer = setTimeout(() => {
      node.hidden = true;
    }, 2600);
}

export async function initPWA() {
  const install = document.querySelector("[data-install]");
  if (install) {
    addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      promptEvent = event;
      install.hidden = false;
    });
    install.addEventListener("click", async () => {
      if (!promptEvent) return;
      promptEvent.prompt();
      await promptEvent.userChoice;
      promptEvent = null;
      install.hidden = true;
    });
    addEventListener("appinstalled", () => {
      install.hidden = true;
      promptEvent = null;
      toast("GLab installed.");
    });
  }

  if (!("serviceWorker" in navigator)) return;
  let registration;
  let updateReloadTimer;
  const offer = (worker) =>
    toast("A newer GLab version is ready.", {
      label: "Update",
      run: () => {
        clearTimeout(updateReloadTimer);
        const target = registration?.waiting || worker;
        if (!target) {
          location.reload();
          return;
        }
        target.addEventListener?.("statechange", () => {
          if (target.state === "activated") location.reload();
        });
        target.postMessage({ type: "SKIP_WAITING" });
        updateReloadTimer = setTimeout(() => location.reload(), 1800);
      },
    });
  let contentTimer;
  navigator.serviceWorker.addEventListener("message", (event) => {
    if (event.data?.type !== "CONTENT_UPDATED") return;
    document.dispatchEvent(new CustomEvent("glab:catalog-updated"));
    if (new URLSearchParams(location.search).has("id")) {
      if (registration?.waiting) {
        offer(registration?.waiting);
        return;
      }
      toast("New content is available. Refresh when you finish reading.", {
        label: "Refresh",
        run: () => location.reload(),
      });
    } else {
      clearTimeout(contentTimer);
      contentTimer = setTimeout(async () => {
        await initContent();
        if (registration?.waiting) offer(registration?.waiting);
        else toast("Projects and articles updated.");
      }, 300);
    }
  });
  try {
    registration = await navigator.serviceWorker.register(
      "/service-worker.js",
      {
        scope: "/",
        updateViaCache: "none",
      },
    );
    let refreshing = false;
    const wasControlled = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (refreshing || !wasControlled) return;
      refreshing = true;
      location.reload();
    });
    if (registration.waiting && navigator.serviceWorker.controller)
      offer(registration.waiting);
    registration.addEventListener("updatefound", () => {
      const worker = registration.installing;
      if (!worker) return;
      worker.addEventListener("statechange", () => {
        if (worker.state === "installed" && navigator.serviceWorker.controller)
          offer(worker);
      });
    });
    let lastCheckAt = 0;
    let checkInFlight = null;
    const check = ({ force = false } = {}) => {
      if (checkInFlight) return checkInFlight;

      const now = Date.now();
      if (!force && now - lastCheckAt < UPDATE_EVENT_COOLDOWN_MS)
        return Promise.resolve();

      lastCheckAt = now;
      checkInFlight = (async () => {
        await registration.update().catch(() => {});
        const controller =
          navigator.serviceWorker.controller || registration.active;
        if (controller) controller.postMessage({ type: "CHECK_CONTENT" });
      })().finally(() => {
        checkInFlight = null;
      });
      return checkInFlight;
    };
    const checkOnActivity = () => {
      void check();
    };
    navigator.serviceWorker.ready
      .then(() => check({ force: true }))
      .catch(() => {});
    setInterval(() => {
      if (document.visibilityState === "visible") void check({ force: true });
    }, UPDATE_CHECK_INTERVAL_MS);
    addEventListener("focus", checkOnActivity, { passive: true });
    addEventListener("online", checkOnActivity, { passive: true });
    addEventListener("pageshow", checkOnActivity, { passive: true });
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") checkOnActivity();
    });
  } catch {
    // The site remains fully usable when service workers are unavailable.
  }

  addEventListener("offline", () =>
    toast("You are offline. Cached GLab pages remain available."),
  );
  addEventListener("online", () => toast("Connection restored."));
}
