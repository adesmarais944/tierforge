#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml
from xlsxwriter.utility import xl_col_to_name

POSITION_ORDER_DEFAULT = ['WR', 'RB', 'QB', 'TE']


def read_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in ('', None):
            return default
        return int(float(value))
    except Exception:
        return default


def sort_key(row: Dict[str, Any], position_order: List[str]) -> tuple:
    try:
        pos_idx = position_order.index(row.get('pos'))
    except ValueError:
        pos_idx = 99
    return (pos_idx, as_int(row.get('pos_rank'), 999))


def checkbox_ranges(players: List[Dict[str, Any]], position_order: List[str]) -> List[Dict[str, Any]]:
    ranges = []
    cols_per_pos = 8
    gap = 1

    for pos_idx, pos in enumerate(position_order):
        start_col = pos_idx * (cols_per_pos + gap)
        col_name = xl_col_to_name(start_col)
        current_row = 4
        last_tier = None
        current_range = None

        for player in [p for p in players if p.get('pos') == pos]:
            tier = player.get('tier', '')
            if tier != last_tier:
                if current_range:
                    ranges.append(current_range)
                    current_range = None
                current_row += 1
                last_tier = tier

            # Google Sheets API indexes are zero-based and end-exclusive.
            if not current_range:
                current_range = {
                'position': pos,
                'tier': tier,
                'startRowIndex': current_row,
                'startColumnIndex': start_col,
                'endColumnIndex': start_col + 1,
            }
            current_range['endRowIndex'] = current_row + 1
            current_range['a1'] = (
                f"'Draft Cheat Sheet'!{col_name}{current_range['startRowIndex'] + 1}:"
                f"{col_name}{current_range['endRowIndex']}"
            )
            current_row += 1

        if current_range:
            ranges.append(current_range)

    return ranges


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2026')
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    season_dir = root / 'seasons' / args.season
    settings = read_yaml(season_dir / 'data' / 'settings.yaml')
    players = read_csv(season_dir / 'data' / 'players_master.csv')
    position_order = settings.get('positions', {}).get('order', POSITION_ORDER_DEFAULT)
    players.sort(key=lambda row: sort_key(row, position_order))

    output = {
        'season': args.season,
        'workbook': str(season_dir / 'output' / f'{args.season}_fantasy_draft_cheat_sheet.xlsx'),
        'sheet': 'Draft Cheat Sheet',
        'checkboxRanges': checkbox_ranges(players, position_order),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
