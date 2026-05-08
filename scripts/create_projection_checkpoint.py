#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tierforge.projections.checkpoints import write_checkpoint


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2026")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    path = write_checkpoint(root, args.season, args.note)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
