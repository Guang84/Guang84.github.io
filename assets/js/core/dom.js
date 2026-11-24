export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null) continue;

    if (key === "class" || key === "className") {
      node.className = String(value);
    } else if (key === "text") {
      node.textContent = String(value);
    } else if (key === "dataset" && value && typeof value === "object") {
      Object.assign(node.dataset, value);
    } else if (key.startsWith("data-") || key.startsWith("aria-")) {
      node.setAttribute(key, String(value));
    } else if (/^aria[A-Z]/.test(key)) {
      const attribute = key.replace(
        /^aria([A-Z])/,
        (_, first) => "aria-" + first.toLowerCase(),
      );
      node.setAttribute(attribute, String(value));
    } else if (key in node) {
      node[key] = value;
    } else {
      node.setAttribute(key, String(value));
    }
  }

  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    if (typeof Node !== "undefined" && child instanceof Node) {
      node.append(child);
    } else {
      node.append(document.createTextNode(String(child)));
    }
  }

  return node;
}
