#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.apply_team_macro import (
    ACCEPT_MODES,
    apply_macro_recommendations,
    build_macro_diffs,
    render_macro_diffs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    parser.add_argument("--team", required=True)
    parser.add_argument("--accept", choices=sorted(ACCEPT_MODES))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--human-approved",
        action="store_true",
        help="Required with --accept. Use only after a human has reviewed the dry-run diff and approved the mode.",
    )
    args = parser.parse_args()

    if args.dry_run:
        mode = args.accept or "all"
        root = Path(__file__).resolve().parents[1]
        diffs = build_macro_diffs(root, args.season, args.team, mode)
        print(render_macro_diffs(args.team, mode, diffs))
        print("\nDry run only. No files changed.")
        return 0

    if not args.accept:
        parser.error("Either --dry-run or --accept is required.")
    if not args.human_approved:
        parser.error("--accept requires --human-approved after human review of the dry-run diff.")

    root = Path(__file__).resolve().parents[1]
    diffs = apply_macro_recommendations(root, args.season, args.team, args.accept)
    print(render_macro_diffs(args.team, args.accept, diffs))
    print("\nUpdated team_assumptions.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
