#!/usr/bin/env node
/**
 * Validate mobile Lighthouse reports.
 * Accessibility, Best Practices and SEO must each score at least 90.
 * Performance is reported but not gated.
 */
import fs from "node:fs";
import path from "node:path";

const reportDir = path.resolve(process.argv[2] || "/tmp/glab-lighthouse");
const pages = ["home", "about", "services"];
const gated = ["accessibility", "best-practices", "seo"];
const failures = [];

const percent = (value) =>
  Number.isFinite(value) ? Math.round(value * 100) : null;

for (const page of pages) {
  const reportPath = path.join(reportDir, page + ".json");
  if (!fs.existsSync(reportPath)) {
    failures.push("Missing Lighthouse report: " + reportPath);
    continue;
  }

  let report;
  try {
    report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
  } catch (error) {
    failures.push("Invalid Lighthouse JSON for " + page + ": " + error.message);
    continue;
  }

  const categories = report.categories || {};
  const performance = percent(categories.performance?.score);
  console.log(
    page + " mobile performance: " +
    (performance === null ? "unavailable" : performance + "/100")
  );

  for (const category of gated) {
    const score = percent(categories[category]?.score);
    const label = page + " mobile " + category.replace("-", " ");
    if (score === null) {
      failures.push(label + " score is missing");
    } else {
      console.log(label + ": " + score + "/100");
      if (score < 90) failures.push(label + " is below 90 (" + score + ")");
    }
  }
}

if (failures.length) {
  for (const failure of failures) console.error("FAIL: " + failure);
  process.exitCode = 1;
} else {
  console.log("All three pages meet the 90/100 Accessibility, Best Practices and SEO gates.");
}
