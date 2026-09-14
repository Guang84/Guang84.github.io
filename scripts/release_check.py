#!/usr/bin/env python3
"""Validate GLab before publishing."""

from build_content import build


def main() -> int:
    errors = build(write=False, stage=False)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("GLab release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
