from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.apply_team_schedule import (
    ACCEPT_MODES,
    apply_schedule_recommendations,
    build_schedule_diffs,
    render_schedule_diffs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    parser.add_argument("--team", required=True)
    parser.add_argument("--accept", choices=sorted(ACCEPT_MODES))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--human-approved", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    mode = args.accept or "all"
    if args.dry_run or not args.accept:
        diffs = build_schedule_diffs(root, args.season, args.team, mode)
        print(render_schedule_diffs(args.team, mode, diffs))
        print("\nDry run only. No files changed.")
        return 0

    if not args.human_approved:
        raise SystemExit("--human-approved is required when accepting schedule recommendations.")

    diffs = apply_schedule_recommendations(root, args.season, args.team, args.accept)
    print(render_schedule_diffs(args.team, args.accept, diffs))
    print("\nUpdated team_assumptions.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
