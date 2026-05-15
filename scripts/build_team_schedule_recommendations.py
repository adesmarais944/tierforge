from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.team_schedule import build_team_schedule_recommendations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_path = build_team_schedule_recommendations(root, args.season)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
