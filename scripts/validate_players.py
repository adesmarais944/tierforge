#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
import yaml

REQUIRED_COLUMNS = [
    'pos','tier','pos_rank','player','team','raw_adp','risk','upside',
    'draft_tag','tag_reason','threshold_note','player_note','source'
]
VALID_POSITIONS = {'QB','RB','WR','TE'}
VALID_TAGS = {'MY_GUY','VALUE_ONLY','DND','WATCH','NEUTRAL'}


def as_int(value, name, player, errors):
    try:
        return int(float(value))
    except Exception:
        errors.append(f'{player}: {name} must be numeric, got {value!r}')
        return None


def as_float(value, name, player, errors):
    if value in ('', None):
        return None
    try:
        return float(value)
    except Exception:
        errors.append(f'{player}: {name} must be numeric or blank, got {value!r}')
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2026')
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    season_dir = root / 'seasons' / args.season
    players_path = season_dir / 'data' / 'players_master.csv'
    settings_path = season_dir / 'data' / 'settings.yaml'

    errors = []
    if not players_path.exists():
        errors.append(f'Missing {players_path}')
    if not settings_path.exists():
        errors.append(f'Missing {settings_path}')
    if errors:
        print('\n'.join(errors))
        return 1

    settings = yaml.safe_load(settings_path.read_text(encoding='utf-8')) or {}
    league_size = int(settings.get('league_size', 12))
    if league_size < 8 or league_size > 20:
        errors.append(f'league_size should be between 8 and 20, got {league_size}')

    with players_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            errors.append(f'Missing columns: {missing}')
        rows = list(reader)

    seen = set()
    for row in rows:
        player = row.get('player','').strip()
        if not player:
            errors.append('Blank player name')
            continue
        if player in seen:
            errors.append(f'Duplicate player: {player}')
        seen.add(player)

        pos = row.get('pos','').strip()
        if pos not in VALID_POSITIONS:
            errors.append(f'{player}: invalid pos {pos!r}')

        tag = row.get('draft_tag','').strip()
        if tag not in VALID_TAGS:
            errors.append(f'{player}: invalid draft_tag {tag!r}')

        pos_rank = as_int(row.get('pos_rank'), 'pos_rank', player, errors)
        risk = as_int(row.get('risk'), 'risk', player, errors)
        upside = as_int(row.get('upside'), 'upside', player, errors)
        as_float(row.get('raw_adp'), 'raw_adp', player, errors)

        if risk is not None and not 1 <= risk <= 5:
            errors.append(f'{player}: risk must be 1-5, got {risk}')
        if upside is not None and not 1 <= upside <= 5:
            errors.append(f'{player}: upside must be 1-5, got {upside}')
        if pos_rank is not None and pos_rank < 1:
            errors.append(f'{player}: pos_rank must be positive, got {pos_rank}')

    if errors:
        print('Validation failed:')
        for e in errors:
            print(f'- {e}')
        return 1

    print(f'Validation passed: {len(rows)} players, league size {league_size}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
