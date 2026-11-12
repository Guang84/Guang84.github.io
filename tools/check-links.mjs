#!/usr/bin/env node
/**
 * Check local HTML links and fragments in a staged static site.
 * Usage: node tools/check-links.mjs [site-root]
 * Set CHECK_EXTERNAL=1 for best-effort external HEAD requests.
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.argv[2] || ".");
const ignoredDirectories = new Set([".git", "node_modules", "_site"]);
const htmlFiles = [];
const failures = [];
const externalUrls = new Set();

function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath);
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) {
      htmlFiles.push(fullPath);
    }
  }
}

function findTarget(urlPath) {
  let decodedPath;
  try {
    decodedPath = decodeURIComponent(urlPath);
  } catch {
    return null;
  }
  let target = path.resolve(root, "." + decodedPath);
  if (target !== root && !target.startsWith(root + path.sep)) return null;
  const candidates = [target, path.join(target, "index.html"), path.join(target, "index.htm")];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      for (const indexFile of ["index.html", "index.htm"]) {
        const indexPath = path.join(candidate, indexFile);
        if (fs.existsSync(indexPath) && fs.statSync(indexPath).isFile()) return indexPath;
      }
    } else if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      return candidate;
    }
  }
  return null;
}

function hasFragment(htmlPath, fragment) {
  if (!fragment) return true;
  const html = fs.readFileSync(htmlPath, "utf8");
  for (const match of html.matchAll(/\b(?:id|name)\s*=\s*(["'])(.*?)\1/gi)) {
    if (match[2] === fragment) return true;
  }
  return false;
}

walk(root);
for (const file of htmlFiles) {
  const html = fs.readFileSync(file, "utf8");
  const relativeFile = path.relative(root, file).split(path.sep).join("/");
  const baseUrl = new URL("/" + relativeFile, "https://glab-local.invalid/");
  const references = [...html.matchAll(/\b(?:href|src|poster)\s*=\s*(["'])(.*?)\1/gi)].map(match => match[2].trim());

  for (const reference of references) {
    if (!reference || reference.startsWith("#")) {
      if (reference === "#") continue;
    }
    let url;
    try {
      url = new URL(reference, baseUrl);
    } catch {
      failures.push({ file, reference, reason: "invalid URL" });
      continue;
    }
    if (url.protocol !== "http:" && url.protocol !== "https:") continue;
    if (url.origin !== baseUrl.origin) {
      externalUrls.add(url.href.split("#")[0]);
      continue;
    }

    const target = findTarget(url.pathname);
    if (!target) {
      failures.push({ file, reference, reason: "missing local target" });
      continue;
    }
    let fragment = "";
    try {
      fragment = decodeURIComponent(url.hash.slice(1));
    } catch {
      failures.push({ file, reference, reason: "invalid fragment encoding" });
      continue;
    }
    if (fragment && target.toLowerCase().endsWith(".html") && !hasFragment(target, fragment)) {
      failures.push({ file, reference, reason: "missing fragment #" + fragment });
    }
  }
}

console.log("Scanned " + htmlFiles.length + " HTML files and found " + externalUrls.size + " unique external URLs.");
if (process.env.CHECK_EXTERNAL === "1") {
  for (const url of externalUrls) {
    try {
      const response = await fetch(url, {
        method: "HEAD",
        redirect: "follow",
        signal: AbortSignal.timeout(10000),
      });
      if (!response.ok) console.error("EXTERNAL " + response.status + " " + url);
    } catch (error) {
      console.error("EXTERNAL ERROR " + url + ": " + error.message);
    }
  }
} else {
  console.log("External requests were not probed. Set CHECK_EXTERNAL=1 to run best-effort HEAD checks.");
}

for (const failure of failures) {
  console.error(
    "BROKEN " + path.relative(root, failure.file) + " -> " + failure.reference + " (" + failure.reason + ")",
  );
}
if (failures.length) {
  console.error("Found " + failures.length + " broken local link(s).");
  process.exitCode = 1;
} else {
  console.log("No broken local HTML links or fragments found.");
}
