# TierForge - Fantasy Draft Kit

Seasonal fantasy football draft-kit generator for snake drafts.

This repo is intentionally small and seasonal. The goal is not to build a year-round fantasy platform. The goal is to wake the repo up during the offseason, refresh rankings/ADP, generate a clean draft-room cheat sheet, use it for drafts, then archive it until next offseason.

## Default assumptions

- 1QB redraft
- Half-PPR
- No TE premium
- Snake drafts only
- No auction values
- No K/DST unless explicitly added later
- ADP shown as round.pick, not raw overall pick
- The sheet does **not** duplicate the league draft board
- One live interaction only: click a checkbox when a player is drafted

## Repo layout

```text
seasons/2026/
  data/
    players_master.csv      # source of truth for player rows
    manual_overrides.yaml   # optional player overrides
    settings.yaml           # league size, scoring, display behavior
    adp/                    # dated ADP snapshots
  logic/
    draft_tags.yaml         # green/yellow/red tag definitions
    tier_rules.yaml         # tier naming conventions
    risk_upside_rules.yaml  # risk/upside definitions
  output/
    2026_fantasy_draft_cheat_sheet.xlsx
scripts/
  generate_cheatsheet.py
  validate_players.py
docs/
  design_decisions.md
  codex_prompts.md
```

## Setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Validate and generate

With the virtualenv activated:

```bash
python scripts/validate_players.py --season 2026
python scripts/generate_cheatsheet.py --season 2026
```

Generated workbook:

```text
seasons/2026/output/2026_fantasy_draft_cheat_sheet.xlsx
```

## Typical offseason workflow

```text
1. Refresh ADP snapshot in seasons/2026/data/adp/.
2. Edit seasons/2026/data/players_master.csv.
3. Use draft_tag for personal stance:
   - MY_GUY = green/star target
   - VALUE_ONLY = yellow/value-only
   - DND = red/do-not-draft at cost
   - WATCH = blue/watchlist
   - NEUTRAL = no strong stance
4. Run validation.
5. Regenerate workbook.
6. Use the workbook during draft with the checkbox-only interaction.
```

## Draft-day behavior

The workbook is not a draft board. It does not track teams, picks, rosters, or queues.

It only lets you:

```text
[ ] Player still available
[x] Player drafted somewhere; grey/strike him out
```

Keep the real league draft board open separately.
