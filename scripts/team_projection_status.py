#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.checkpoints import render_status, team_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    parser.add_argument("--team", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    print(render_status(team_status(root, args.season, args.team)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
