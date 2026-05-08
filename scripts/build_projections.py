#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.engine import build_outputs
from tierforge.projections.scoring import SCORING_PROFILES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    parser.add_argument("--scoring", choices=sorted(SCORING_PROFILES), required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    projections_path, rankings_path = build_outputs(root, args.season, args.scoring)
    print(f"Wrote {projections_path}")
    print(f"Wrote {rankings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
