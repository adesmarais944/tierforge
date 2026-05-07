#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any, Dict, List

import yaml
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name

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


def as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in ('', None):
            return default
        return float(value)
    except Exception:
        return default


def round_pick(raw_adp: float | None, league_size: int) -> str:
    if raw_adp is None or raw_adp <= 0:
        return ''
    overall = max(1, int(round(raw_adp)))
    rnd = ((overall - 1) // league_size) + 1
    pick = ((overall - 1) % league_size) + 1
    return f'{rnd}.{pick:02d}'


def normalize(players: List[Dict[str, Any]], league_size: int) -> List[Dict[str, Any]]:
    out = []
    for row in players:
        row = {str(k).strip(): v for k, v in row.items()}
        row['pos_rank'] = as_int(row.get('pos_rank'))
        row['raw_adp'] = as_float(row.get('raw_adp'))
        row['adp_display'] = round_pick(row['raw_adp'], league_size)
        row['risk'] = as_int(row.get('risk'), 3)
        row['upside'] = as_int(row.get('upside'), 3)
        row['draft_tag'] = (row.get('draft_tag') or 'NEUTRAL').strip().upper()
        out.append(row)
    return out


def apply_overrides(players: List[Dict[str, Any]], overrides: Dict[str, Any]) -> None:
    for row in players:
        name = row.get('player')
        if name in overrides and isinstance(overrides[name], dict):
            row.update(overrides[name])


def sort_key(row: Dict[str, Any], position_order: List[str]) -> tuple:
    try:
        pos_idx = position_order.index(row.get('pos'))
    except ValueError:
        pos_idx = 99
    return (pos_idx, as_int(row.get('pos_rank'), 999))


def make_formats(workbook, tags: Dict[str, Any]):
    formats = {}
    formats['title'] = workbook.add_format({
        'bold': True, 'font_size': 16, 'font_color': 'white', 'bg_color': '#111827',
        'align': 'center', 'valign': 'vcenter'
    })
    formats['subtitle'] = workbook.add_format({
        'italic': True, 'font_color': '#374151', 'align': 'center', 'valign': 'vcenter'
    })
    formats['pos_header'] = workbook.add_format({
        'bold': True, 'font_color': 'white', 'bg_color': '#1F2937', 'align': 'center',
        'valign': 'vcenter', 'border': 1, 'border_color': '#111827'
    })
    formats['col_header'] = workbook.add_format({
        'bold': True, 'font_color': '#111827', 'bg_color': '#D9EAF7', 'align': 'center',
        'valign': 'vcenter', 'border': 1, 'border_color': '#9CA3AF'
    })
    formats['tier_header'] = workbook.add_format({
        'bold': True, 'font_color': '#111827', 'bg_color': '#E5E7EB', 'align': 'left',
        'valign': 'vcenter', 'border': 1, 'border_color': '#9CA3AF'
    })
    formats['player'] = workbook.add_format({'valign': 'vcenter', 'text_wrap': False, 'border': 1, 'border_color': '#E5E7EB'})
    formats['center'] = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#E5E7EB'})
    formats['small'] = workbook.add_format({'font_size': 9, 'valign': 'vcenter', 'border': 1, 'border_color': '#E5E7EB'})
    formats['note'] = workbook.add_format({'font_size': 9, 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'border_color': '#E5E7EB'})
    formats['checkbox'] = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#E5E7EB'})
    formats['drafted'] = workbook.add_format({'bg_color': '#E5E7EB', 'font_color': '#9CA3AF', 'font_strikeout': True})
    formats['drafted_checkbox'] = workbook.add_format({'bg_color': '#E5E7EB', 'font_color': '#9CA3AF', 'align': 'center', 'valign': 'vcenter'})
    formats['muted'] = workbook.add_format({'font_color': '#6B7280'})
    formats['detail_header'] = workbook.add_format({'bold': True, 'bg_color': '#D9EAF7', 'border': 1, 'align': 'center'})
    formats['legend_header'] = workbook.add_format({'bold': True, 'bg_color': '#111827', 'font_color': 'white', 'border': 1})
    formats['source'] = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'border_color': '#E5E7EB'})

    formats['tag'] = {}
    for key, cfg in tags.items():
        formats['tag'][key] = workbook.add_format({
            'bold': True,
            'font_color': cfg.get('font', '#111827'),
            'bg_color': cfg.get('fill', '#FFFFFF'),
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#E5E7EB'
        })
    return formats


def tag_label(row: Dict[str, Any], tags: Dict[str, Any]) -> str:
    tag = row.get('draft_tag', 'NEUTRAL')
    cfg = tags.get(tag, tags.get('NEUTRAL', {}))
    if tag == 'NEUTRAL':
        return ''
    return cfg.get('label', tag)


def write_printable(workbook, players: List[Dict[str, Any]], settings: Dict[str, Any], tags: Dict[str, Any], formats: Dict[str, Any]) -> None:
    ws = workbook.add_worksheet('Draft Cheat Sheet')
    ws.hide_gridlines(2)
    ws.freeze_panes(4, 0)
    ws.set_landscape()
    ws.fit_to_pages(1, 0)
    ws.set_zoom(85)

    position_order = settings.get('positions', {}).get('order', POSITION_ORDER_DEFAULT)
    cols_per_pos = 8
    gap = 1
    total_cols = len(position_order) * cols_per_pos + (len(position_order) - 1) * gap
    last_col = total_cols - 1

    ws.merge_range(0, 0, 0, last_col, '2026 Fantasy Football Snake Draft Cheat Sheet', formats['title'])
    ws.merge_range(1, 0, 1, last_col, '1QB | Half-PPR | No TE Premium | ADP shown as round.pick | Check drafted players off only', formats['subtitle'])

    headers = ['Drafted?', 'Player', 'Tm', 'ADP', 'R/U', 'Tag', 'Threshold', 'Note']
    pos_groups = {pos: [p for p in players if p.get('pos') == pos] for pos in position_order}

    for pos_idx, pos in enumerate(position_order):
        start_col = pos_idx * (cols_per_pos + gap)
        end_col = start_col + cols_per_pos - 1
        ws.merge_range(2, start_col, 2, end_col, pos, formats['pos_header'])
        for offset, h in enumerate(headers):
            ws.write(3, start_col + offset, h, formats['col_header'])

        current_row = 4
        last_tier = None
        for p in pos_groups.get(pos, []):
            tier = p.get('tier', '')
            if tier != last_tier:
                ws.merge_range(current_row, start_col, current_row, end_col, tier, formats['tier_header'])
                current_row += 1
                last_tier = tier

            # Drafted checkbox is a true cell checkbox/boolean. Conditional formatting keys off this cell.
            ws.insert_checkbox(current_row, start_col, False, formats['checkbox'])
            ws.write(current_row, start_col + 1, p.get('player', ''), formats['player'])
            ws.write(current_row, start_col + 2, p.get('team', ''), formats['center'])
            ws.write(current_row, start_col + 3, p.get('adp_display', ''), formats['center'])
            ws.write(current_row, start_col + 4, f"{p.get('risk','')}/{p.get('upside','')}", formats['center'])
            tag = p.get('draft_tag', 'NEUTRAL')
            ws.write(current_row, start_col + 5, tag_label(p, tags), formats['tag'].get(tag, formats['tag'].get('NEUTRAL')))
            ws.write(current_row, start_col + 6, p.get('threshold_note', ''), formats['small'])
            ws.write(current_row, start_col + 7, p.get('player_note', ''), formats['note'])

            checkbox_cell = xl_rowcol_to_cell(current_row, start_col, row_abs=False, col_abs=True)
            ws.conditional_format(current_row, start_col, current_row, end_col, {
                'type': 'formula',
                'criteria': f'={checkbox_cell}=TRUE',
                'format': formats['drafted'],
            })
            current_row += 1

        # column widths per position block
        widths = [4, 20, 6, 7, 6, 13, 12, 28]
        for offset, width in enumerate(widths):
            ws.set_column(start_col + offset, start_col + offset, width)
        if pos_idx < len(position_order) - 1:
            ws.set_column(end_col + 1, end_col + 1, 2)


def write_detail(workbook, players: List[Dict[str, Any]], formats: Dict[str, Any], tags: Dict[str, Any]) -> None:
    ws = workbook.add_worksheet('Player Detail')
    ws.hide_gridlines(2)
    ws.freeze_panes(1, 0)
    headers = ['Pos','Tier','Pos Rank','Player','Team','Raw ADP','ADP','Risk','Upside','Draft Tag','Tag Reason','Threshold','Note','Source']
    for c, h in enumerate(headers):
        ws.write(0, c, h, formats['detail_header'])
    for r, p in enumerate(players, start=1):
        values = [
            p.get('pos'), p.get('tier'), p.get('pos_rank'), p.get('player'), p.get('team'),
            p.get('raw_adp'), p.get('adp_display'), p.get('risk'), p.get('upside'),
            p.get('draft_tag'), p.get('tag_reason'), p.get('threshold_note'),
            p.get('player_note'), p.get('source')
        ]
        for c, v in enumerate(values):
            fmt = formats['source'] if c in (12,13) else formats['player']
            ws.write(r, c, v, fmt)
    widths = [7,24,9,22,18,9,8,7,8,13,16,14,52,44]
    for c, w in enumerate(widths):
        ws.set_column(c, c, w)
    ws.autofilter(0, 0, len(players), len(headers)-1)


def write_settings(workbook, settings: Dict[str, Any], formats: Dict[str, Any]) -> None:
    ws = workbook.add_worksheet('Settings')
    ws.hide_gridlines(2)
    ws.write(0, 0, 'Setting', formats['legend_header'])
    ws.write(0, 1, 'Value', formats['legend_header'])
    rows = [
        ('Season', settings.get('season')),
        ('League Size', settings.get('league_size')),
        ('Scoring', settings.get('scoring', {}).get('format')),
        ('QB Passing TD', settings.get('scoring', {}).get('qb_passing_td')),
        ('TE Premium', settings.get('scoring', {}).get('te_premium')),
        ('ADP Format', settings.get('display', {}).get('adp_format')),
        ('Draft board duplicate?', settings.get('display', {}).get('duplicate_draft_board')),
        ('Checkbox-only interaction?', settings.get('display', {}).get('use_drafted_checkboxes')),
    ]
    for r, (k, v) in enumerate(rows, start=1):
        ws.write(r, 0, k, formats['player'])
        ws.write(r, 1, str(v), formats['player'])
    ws.set_column(0, 0, 28)
    ws.set_column(1, 1, 28)


def write_legend(workbook, tags: Dict[str, Any], formats: Dict[str, Any]) -> None:
    ws = workbook.add_worksheet('Legend')
    ws.hide_gridlines(2)
    headers = ['Draft Tag', 'Display', 'Meaning']
    for c, h in enumerate(headers):
        ws.write(0, c, h, formats['legend_header'])
    r = 1
    for key in ['MY_GUY','VALUE_ONLY','DND','WATCH','NEUTRAL']:
        cfg = tags.get(key, {})
        ws.write(r, 0, key, formats['player'])
        ws.write(r, 1, cfg.get('label', key), formats['tag'].get(key, formats['player']))
        ws.write(r, 2, cfg.get('meaning', ''), formats['source'])
        r += 1
    ws.write(r + 1, 0, 'Risk / Upside', formats['legend_header'])
    ws.write(r + 1, 1, 'Scale', formats['legend_header'])
    ws.write(r + 2, 0, 'Risk', formats['player'])
    ws.write(r + 2, 1, '1 = stable, 5 = fragile', formats['player'])
    ws.write(r + 3, 0, 'Upside', formats['player'])
    ws.write(r + 3, 1, '1 = capped, 5 = league-winning', formats['player'])
    ws.set_column(0, 0, 18)
    ws.set_column(1, 1, 20)
    ws.set_column(2, 2, 80)


def write_sources(workbook, formats: Dict[str, Any]) -> None:
    ws = workbook.add_worksheet('Sources')
    ws.hide_gridlines(2)
    headers = ['Source', 'Purpose', 'URL / File', 'Notes']
    for c, h in enumerate(headers):
        ws.write(0, c, h, formats['legend_header'])
    rows = [
        ['Underdog ADP via Sharp Football', 'Primary early-offseason market cost', 'https://www.sharpfootballanalysis.com/fantasy/fantasy-football-adp-half-ppr-underdog-best-ball/', 'Stored as a dated CSV snapshot in data/adp/.'],
        ['FantasyPros', 'Consensus/ranking structure reference', 'https://www.fantasypros.com/nfl/cheatsheets/half-ppr.php', 'Use as one input; do not blindly copy ECR.'],
        ['Fantasy Footballers UDK', 'Workflow/layout inspiration', 'https://www.thefantasyfootballers.com/ultimate-draft-kit/', 'Replicate personal tag/cheat-sheet workflow concept, not proprietary content.'],
        ['Local players_master.csv', 'Source of truth for player rows', 'seasons/2026/data/players_master.csv', 'Edit this file or manual_overrides.yaml, then regenerate.'],
    ]
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            ws.write(r, c, value, formats['source'])
    for c, w in enumerate([30, 34, 82, 54]):
        ws.set_column(c, c, w)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2026')
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    season_dir = root / 'seasons' / args.season
    settings = read_yaml(season_dir / 'data' / 'settings.yaml')
    league_size = int(settings.get('league_size', 12))
    tags = read_yaml(season_dir / 'logic' / 'draft_tags.yaml')
    overrides = read_yaml(season_dir / 'data' / 'manual_overrides.yaml')

    players = read_csv(season_dir / 'data' / 'players_master.csv')
    apply_overrides(players, overrides)
    players = normalize(players, league_size)
    position_order = settings.get('positions', {}).get('order', POSITION_ORDER_DEFAULT)
    players.sort(key=lambda r: sort_key(r, position_order))

    out_path = season_dir / 'output' / f'{args.season}_fantasy_draft_cheat_sheet.xlsx'
    out_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = xlsxwriter.Workbook(out_path)
    workbook.set_properties({
        'title': f'{args.season} Fantasy Football Draft Cheat Sheet',
        'subject': 'Snake draft tier-based cheat sheet',
        'author': 'Generated from fantasy-draft-kit repo',
        'comments': 'Generated artifact. Edit CSV/YAML source files, not this workbook.'
    })
    formats = make_formats(workbook, tags)
    write_printable(workbook, players, settings, tags, formats)
    write_detail(workbook, players, formats, tags)
    write_settings(workbook, settings, formats)
    write_legend(workbook, tags, formats)
    write_sources(workbook, formats)
    workbook.close()

    print(f'Wrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
