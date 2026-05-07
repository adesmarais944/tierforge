# Codex Instructions

## Project purpose

This is a seasonal fantasy football draft-kit generator. Keep it lightweight. Do not turn it into a web app, database, or year-round fantasy platform unless explicitly asked.

## Default fantasy assumptions

- 1QB redraft
- Half-PPR
- No TE premium
- Snake drafts only
- No auction values
- No K/DST by default
- ADP is market price, not the ranking
- Positional tiers matter more than a top-200 list
- Use Underdog ADP during early offseason when redraft ADP is thin

## UX principles

The generated workbook should behave like a draft-room cheat sheet, not a duplicate draft board.

Do:
- Show players by position and tier
- Show ADP as round.pick
- Include Risk/Upside as `R/U`
- Include green/yellow/red personal player tags
- Include a single Drafted? checkbox beside each player
- Grey/strike players out when checked
- Keep drafted players visible inside their tier

Do not add unless explicitly requested:
- Auction values
- Team/roster tracking
- Draft pick history
- Queue statuses
- Multi-status dropdowns
- Mobile-specific workflows
- Live scraping/automation

## Source of truth

Treat CSV/YAML files as source of truth. Treat Excel files in `output/` as generated artifacts.

Primary files:
- `seasons/<year>/data/players_master.csv`
- `seasons/<year>/data/settings.yaml`
- `seasons/<year>/data/manual_overrides.yaml`
- `seasons/<year>/logic/draft_tags.yaml`

## Required checks before finishing edits

Run:

```bash
python scripts/validate_players.py --season 2026
python scripts/generate_cheatsheet.py --season 2026
```

If changing the season, substitute the requested season.

## Style guidance

Favor readable, boring, maintainable scripts. Avoid clever abstractions. This repo may sit untouched for months and then be revived next offseason.
