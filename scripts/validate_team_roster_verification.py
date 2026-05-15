#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.load_inputs import load_models, season_projection_dir
from tierforge.projections.models import TeamRosterVerification
from tierforge.projections.validation import validate_team_roster_verification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    parser.add_argument("--team", required=True)
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--max-age-days", type=int, default=14)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    path = season_projection_dir(root, args.season) / "raw" / "team_roster_verification.csv"
    verifications = load_models(path, TeamRosterVerification)
    result = validate_team_roster_verification(
        verifications,
        args.team,
        as_of=date.fromisoformat(args.as_of),
        max_age_days=args.max_age_days,
    )
    for warning in result.warnings:
        print(f"Warning: {warning}")
    if result.errors:
        print(f"Roster verification failed for {args.team}:")
        for error in result.errors:
            print(f"- {error}")
        return 1
    print(f"Roster verification passed for {args.team}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
