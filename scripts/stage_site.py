#!/usr/bin/env python3
"""Regenerate public artifacts and stage GLab for deployment."""

from build_content import build


def main() -> int:
    errors = build(write=True, stage=True)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("GLab staged in _site.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
