#!/usr/bin/env python3
"""Run a human editorial review before publishing a GLab article."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    ("purpose", "Can you state the reader benefit in one sentence, and does the article add specific value?"),
    ("evidence", "Have you verified factual, technical, and time-sensitive claims against sources or tests?"),
    ("voice", "Are first-person claims true, and have generic filler, repetition, and invented anecdotes been removed?"),
    ("structure", "Does the structure fit this subject rather than a reusable article formula?"),
    ("limits", "Are trade-offs, uncertainty, failure cases, and untested steps clearly labelled?"),
    ("safety", "Are privacy, security, copyright, attribution, and accessibility concerns checked?"),
    ("metadata", "Do title, excerpt, dates, canonical URL, status, and structured metadata match?"),
]

def main() -> int:
    articles = sorted((ROOT / "articles").glob("*/index.html"))
    if len(sys.argv) > 1:
        slug = sys.argv[1].strip()
        page = ROOT / "articles" / slug / "index.html"
        if not page.is_file() or page.parent.parent != ROOT / "articles":
            print(f"Article not found: {slug}")
            return 2
    else:
        print("Choose an article to review:")
        for i, page in enumerate(articles, 1):
            print(f"  {i}. {page.parent.name}")
        raw = input("Article number: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(articles):
            print("Invalid article selection.")
            return 2
        page = articles[int(raw) - 1]
    print(f"\nEditorial review: {page.parent.name}")
    print("Answer y only if the statement is true for this article.")
    failures = []
    for key, question in QUESTIONS:
        answer = input(f"[y/N] {question} ").strip().lower()
        if answer not in {"y", "yes"}:
            failures.append(key)
    if failures:
        print("\nReview not passed. Rework these areas: " + ", ".join(failures))
        print("Keep the page as a draft until the issues are resolved.")
        return 1
    print("\nEditorial review passed. This run does not publish the article.")
    print("Now run the full site checks, inspect the staged page, and change status deliberately.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
