#!/usr/bin/env python3
"""Report stylesheet ownership and cascade overlaps without rewriting CSS."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CSS_DIR = ROOT / "assets" / "css"
ENTRY = CSS_DIR / "main.css"


def strip_comments(source: str) -> str:
    output: list[str] = []
    index = 0
    quote = ""
    while index < len(source):
        char = source[index]
        if quote:
            output.append(char)
            if char == "\\\\" and index + 1 < len(source):
                index += 1
                output.append(source[index])
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            output.append(char)
            index += 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("Unterminated CSS comment")
            output.append(" ")
            index = end + 2
            continue
        output.append(char)
        index += 1
    return "".join(output)


def find_block_end(source: str, opening: int) -> int:
    depth = 1
    index = opening + 1
    quote = ""
    while index < len(source):
        char = source[index]
        if quote:
            if char == "\\\\":
                index += 2
                continue
            if char == quote:
                quote = ""
        elif char in ("'", '"'):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise ValueError("Unclosed CSS block")


def iter_blocks(source: str):
    """Yield CSS blocks while ignoring braces inside strings and functions."""
    index = 0
    while index < len(source):
        while index < len(source) and (source[index].isspace() or source[index] == ";"):
            index += 1
        if index >= len(source):
            break

        start = index
        quote = ""
        parens = 0
        brackets = 0
        opening = -1
        while index < len(source):
            char = source[index]
            if quote:
                if char == "\\\\":
                    index += 2
                    continue
                if char == quote:
                    quote = ""
            elif char in ("'", '"'):
                quote = char
            elif char == "(":
                parens += 1
            elif char == ")":
                parens = max(0, parens - 1)
            elif char == "[":
                brackets += 1
            elif char == "]":
                brackets = max(0, brackets - 1)
            elif char == "{" and parens == 0 and brackets == 0:
                opening = index
                break
            elif char == ";" and parens == 0 and brackets == 0:
                index += 1
                break
            elif char == "}" and parens == 0 and brackets == 0:
                raise ValueError("Unexpected closing brace")
            index += 1

        if opening < 0:
            continue

        prelude = source[start:opening].strip()
        closing = find_block_end(source, opening)
        body = source[opening + 1:closing]
        yield prelude, body
        index = closing + 1


def split_declarations(body: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    index = 0
    quote = ""
    parens = 0
    while index < len(body):
        char = body[index]
        if quote:
            if char == "\\\\":
                index += 2
                continue
            if char == quote:
                quote = ""
        elif char in ("'", '"'):
            quote = char
        elif char == "(":
            parens += 1
        elif char == ")":
            parens = max(0, parens - 1)
        elif char == ";" and parens == 0:
            chunks.append(body[start:index])
            start = index + 1
        index += 1
    chunks.append(body[start:])
    return chunks


def declaration_names(body: str) -> set[str]:
    names: set[str] = set()
    for item in split_declarations(body):
        quote = ""
        parens = 0
        colon = -1
        for index, char in enumerate(item):
            if quote:
                if char == quote and (index == 0 or item[index - 1] != "\\\\"):
                    quote = ""
            elif char in ("'", '"'):
                quote = char
            elif char == "(":
                parens += 1
            elif char == ")":
                parens = max(0, parens - 1)
            elif char == ":" and parens == 0:
                colon = index
                break
        if colon > 0:
            name = item[:colon].strip().lower()
            if name:
                names.add(name)
    return names


def collect_rules(source: str, context: tuple[str, ...] = ()):
    rows = []
    for prelude, body in iter_blocks(source):
        if not prelude:
            continue
        if prelude.startswith("@"):
            name = prelude.split(None, 1)[0].lower()
            if name in {"@media", "@supports", "@container", "@layer", "@scope"}:
                rows.extend(collect_rules(body, context + (prelude,)))
            continue
        selector = re.sub(r"\s+", " ", prelude).strip()
        rows.append((selector, context, declaration_names(body)))
    return rows


def main() -> int:
    if not ENTRY.is_file():
        print("CSS audit: missing assets/css/main.css", file=sys.stderr)
        return 1

    css_files = sorted(CSS_DIR.glob("*.css"))
    if not css_files:
        print("CSS audit: no stylesheets found", file=sys.stderr)
        return 1

    errors: list[str] = []
    imported: list[Path] = []
    import_pattern = re.compile(r"""@import\s+(?:url\(\s*)?["']([^"']+)["']""", re.I)
    main_source = strip_comments(ENTRY.read_text(encoding="utf-8"))
    for value in import_pattern.findall(main_source):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or value.startswith("//"):
            print(f"External stylesheet import: {value}")
            continue
        target = (ENTRY.parent / parsed.path).resolve()
        if not target.is_file():
            errors.append(f"Missing stylesheet import: {value}")
        else:
            imported.append(target)

    if len(imported) != len(set(imported)):
        errors.append("main.css imports a stylesheet more than once")

    rules_by_selector: dict[str, list[tuple[str, tuple[str, ...], set[str]]]] = defaultdict(list)
    total_rules = 0
    important_count = 0
    parse_errors: list[str] = []
    for path in css_files:
        try:
            source = strip_comments(path.read_text(encoding="utf-8"))
            rows = collect_rules(source)
        except (OSError, ValueError) as error:
            parse_errors.append(f"{path.relative_to(ROOT)}: {error}")
            continue
        total_rules += len(rows)
        important_count += len(re.findall(r"!important\b", source, re.I))
        for selector, context, properties in rows:
            rules_by_selector[selector].append((path.name, context, properties))

    errors.extend(parse_errors)
    imported_set = set(imported)
    unimported = [path.name for path in css_files if path != ENTRY and path.resolve() not in imported_set]
    duplicates = {
        selector: rows
        for selector, rows in rules_by_selector.items()
        if len({row[0] for row in rows}) > 1
    }

    repeated_properties = []
    for selector, rows in duplicates.items():
        ownership: dict[str, set[str]] = defaultdict(set)
        for filename, _context, properties in rows:
            for property_name in properties:
                ownership[property_name].add(filename)
        for property_name, owners in ownership.items():
            if len(owners) > 1:
                repeated_properties.append((selector, property_name, sorted(owners)))

    print(
        f"CSS architecture audit: {len(css_files)} files, {len(imported)} imported modules, "
        f"{total_rules} rules, {important_count} !important declarations."
    )
    print(
        f"Cross-file repeated selectors: {len(duplicates)}; "
        f"repeated selector/property pairs: {len(repeated_properties)}."
    )
    if unimported:
        print("Stylesheets not imported by main.css: " + ", ".join(unimported))
    for selector, rows in list(duplicates.items())[:12]:
        owners = ", ".join(sorted({row[0] for row in rows}))
        print(f"  selector {selector!r}: {owners}")
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("CSS audit completed (overlaps are informational; no CSS was rewritten).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
