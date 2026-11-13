#!/usr/bin/env node
/**
 * Check local HTML links and fragments in a staged static site.
 * Usage: node tools/check-links.mjs [site-root]
 * Set CHECK_EXTERNAL=1 to record external status and redirect chains.
 * Set CHECK_EXTERNAL_STRICT=1 to fail on external HTTP errors/network failures.
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.argv[2] || ".");
const ignoredDirectories = new Set([".git", "node_modules", "_site"]);
const htmlFiles = [];
const failures = [];
const externalUrls = new Set();
const externalFindings = [];

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
  const target = path.resolve(root, "." + decodedPath);
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

async function inspectExternal(startUrl) {
  let current = startUrl;
  const redirects = [];
  const maxRedirects = 6;

  for (let hop = 0; hop <= maxRedirects; hop += 1) {
    let response;
    try {
      response = await fetch(current, {
        method: "HEAD",
        redirect: "manual",
        signal: AbortSignal.timeout(12000),
        headers: { "user-agent": "GLabSiteLinkCheck/1.0" },
      });
      // Some hosts reject HEAD even when their page is reachable by GET.
      if (response.status === 405 || response.status === 501) {
        response = await fetch(current, {
          method: "GET",
          redirect: "manual",
          signal: AbortSignal.timeout(12000),
          headers: {
            "user-agent": "GLabSiteLinkCheck/1.0",
            range: "bytes=0-0",
          },
        });
      }
    } catch (error) {
      return {
        url: startUrl,
        status: "ERROR",
        finalUrl: current,
        redirects,
        detail: error.message,
        ok: false,
      };
    }

    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get("location");
      if (!location) {
        return {
          url: startUrl,
          status: response.status,
          finalUrl: current,
          redirects,
          detail: "redirect response has no Location header",
          ok: false,
        };
      }
      const nextUrl = new URL(location, current).href;
      redirects.push({ status: response.status, from: current, to: nextUrl });
      if (hop === maxRedirects) {
        return {
          url: startUrl,
          status: "TOO_MANY_REDIRECTS",
          finalUrl: nextUrl,
          redirects,
          detail: "redirect limit exceeded",
          ok: false,
        };
      }
      current = nextUrl;
      continue;
    }

    return {
      url: startUrl,
      status: response.status,
      finalUrl: current,
      redirects,
      detail: response.ok ? "reachable" : "HTTP response is not successful",
      ok: response.ok,
    };
  }

  return {
    url: startUrl,
    status: "TOO_MANY_REDIRECTS",
    finalUrl: current,
    redirects,
    detail: "redirect limit exceeded",
    ok: false,
  };
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
  console.log("External URL check: best-effort HEAD requests, GET fallback for 405/501; redirects are recorded.");
  for (const url of [...externalUrls].sort()) {
    const finding = await inspectExternal(url);
    externalFindings.push(finding);
    for (const redirect of finding.redirects) {
      console.warn("REDIRECT " + redirect.status + " " + redirect.from + " -> " + redirect.to);
    }
    const chain = finding.redirects.length ? " (redirects: " + finding.redirects.length + ")" : "";
    if (finding.ok) {
      console.log("EXTERNAL OK " + finding.status + " " + finding.url + chain);
    } else {
      console.warn("EXTERNAL REVIEW " + finding.status + " " + finding.url + " — " + finding.detail + chain);
    }
  }
  const redirected = externalFindings.filter(item => item.redirects.length);
  const notOk = externalFindings.filter(item => !item.ok);
  console.log("External summary: " + externalFindings.length + " checked, " + redirected.length + " redirected, " + notOk.length + " requiring review.");

  if (process.env.GITHUB_STEP_SUMMARY) {
    const lines = [
      "## External link check",
      "",
      externalFindings.length + " URLs checked; " + redirected.length + " redirected; " + notOk.length + " require review.",
      "",
      "| Result | URL | Final URL / detail |",
      "|---|---|---|",
      ...externalFindings.map(item => {
        const result = item.ok ? (item.redirects.length ? "Redirected (" + item.status + ")" : "OK (" + item.status + ")") : "Review (" + item.status + ")";
        const final = item.finalUrl === item.url ? item.detail : item.finalUrl;
        return "| " + result + " | " + item.url.replace(/\|/g, "%7C") + " | " + final.replace(/\|/g, "%7C") + " |";
      }),
    ];
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, lines.join("\n") + "\n");
  }
  if (process.env.CHECK_EXTERNAL_STRICT === "1" && externalFindings.some(item => !item.ok)) {
    console.error("External strict mode found URL(s) requiring review.");
    process.exitCode = 1;
  }
} else {
  console.log("External requests were not probed. Set CHECK_EXTERNAL=1 to record external statuses and redirects.");
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
