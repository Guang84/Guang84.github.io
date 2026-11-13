export function initSupportCopy() {
  document.querySelectorAll("[data-copy-support-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.dataset.copySupportId || "";
      const status = document.querySelector("[data-support-copy-status]");
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(value);
        } else {
          const field = document.createElement("textarea");
          field.value = value;
          field.setAttribute("readonly", "");
          field.style.position = "fixed";
          field.style.opacity = "0";
          document.body.append(field);
          field.select();
          const copied = document.execCommand("copy");
          field.remove();
          if (!copied) throw new Error("Copy failed");
        }
        button.textContent = "Copied";
        if (status) status.textContent = "UPI ID copied to clipboard.";
      } catch {
        if (status) status.textContent = "Copy failed. Please copy the UPI ID manually.";
      }
      window.setTimeout(() => { button.textContent = "Copy UPI ID"; }, 1800);
    });
  });
}
