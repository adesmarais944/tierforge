#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.engine import validate_inputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    result = validate_inputs(root, args.season)
    for warning in result.warnings:
        print(f"Warning: {warning}")
    if result.errors:
        print("Projection validation failed:")
        for error in result.errors:
            print(f"- {error}")
        return 1
    print(f"Projection validation passed for season {args.season}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
