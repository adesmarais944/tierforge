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


def player_ranges(players: List[Dict[str, Any]], position_order: List[str], field_offset: int) -> List[Dict[str, Any]]:
    ranges = []
    cols_per_pos = 8
    gap = 1

    for pos_idx, pos in enumerate(position_order):
        start_col = pos_idx * (cols_per_pos + gap) + field_offset
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


def tag_value_ranges(players: List[Dict[str, Any]], position_order: List[str], tags: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranges = []
    cols_per_pos = 8
    gap = 1

    for pos_idx, pos in enumerate(position_order):
        start_col = pos_idx * (cols_per_pos + gap) + 5
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

            tag_key = (player.get('draft_tag') or 'NEUTRAL').strip().upper()
            tag_label = '' if tag_key == 'NEUTRAL' else tags.get(tag_key, {}).get('label', tag_key)
            range_can_continue = (
                current_range
                and current_range['position'] == pos
                and current_range['tagLabel'] == tag_label
                and current_range['endRowIndex'] == current_row
            )
            if not range_can_continue:
                if current_range:
                    ranges.append(current_range)
                current_range = {
                    'position': pos,
                    'tagKey': tag_key,
                    'tagLabel': tag_label,
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


def tag_options(tags: Dict[str, Any]) -> List[str]:
    return [
        tags.get(key, {}).get('label', key)
        for key in ['MY_GUY', 'VALUE_ONLY', 'DND', 'WATCH', 'NEUTRAL']
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2026')
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    season_dir = root / 'seasons' / args.season
    settings = read_yaml(season_dir / 'data' / 'settings.yaml')
    tags = read_yaml(season_dir / 'logic' / 'draft_tags.yaml')
    players = read_csv(season_dir / 'data' / 'players_master.csv')
    position_order = settings.get('positions', {}).get('order', POSITION_ORDER_DEFAULT)
    players.sort(key=lambda row: sort_key(row, position_order))

    output = {
        'season': args.season,
        'workbook': str(season_dir / 'output' / f'{args.season}_fantasy_draft_cheat_sheet.xlsx'),
        'sheet': 'Draft Cheat Sheet',
        'checkboxRanges': player_ranges(players, position_order, field_offset=0),
        'tagRanges': player_ranges(players, position_order, field_offset=5),
        'tagValueRanges': tag_value_ranges(players, position_order, tags),
        'tagOptions': tag_options(tags),
        'tagTemplateSheet': 'Tag Dropdown Template',
        'tagTemplateCells': {
            'MY_GUY': "'Tag Dropdown Template'!A1",
            'VALUE_ONLY': "'Tag Dropdown Template'!A2",
            'DND': "'Tag Dropdown Template'!A3",
            'WATCH': "'Tag Dropdown Template'!A4",
            'NEUTRAL': "'Tag Dropdown Template'!A5",
        },
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
