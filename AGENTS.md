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

## Projection macro recommendations

For every new team stat-out, run the full projection preflight. Do not skip layers:

1. Verify roster/depth chart and run `validate_team_roster_verification.py`.
2. Add/update team assumptions, defense environment, offseason changes, player assumptions, and schedule environment.
3. Build macro recommendations and show the macro dry-run.
4. Build schedule recommendations and show the schedule dry-run.
5. Provide agent recommendations for macro and schedule modes, but wait for explicit human approval before accepting either.
6. Validate, build projections, regenerate the workbook, and checkpoint.

Macro recommendations are advisory. Always run and show the dry-run diff before accepting:

```bash
python scripts/apply_team_macro_recommendations.py --season 2026 --team <TEAM> --dry-run
```

Do not accept macro recommendations on behalf of the user. Only run `--accept` after the human user explicitly approves the exact mode (`volume`, `efficiency`, or `all`). The command requires `--human-approved` to make that handoff explicit.

After showing a macro dry-run, provide an agent recommendation (`volume`, `efficiency`, `all`, or no accept) with short reasoning about why the volume and efficiency changes do or do not fit the researched team context. This recommendation is advisory only; human sign-off is still required.

For team stat-out work, create a completion checkpoint after validation/build even when no macro recommendation is accepted. The note should say the macro was intentionally not accepted.

Projection calibration should prefer strong median/mean baselines over ceiling cases. Be cautious with extreme target concentration, RB workloads above roughly 275 carries or 90 targets, and QB rushing TD shares above roughly 35% unless team context strongly supports it. Remember `games_projected` is context only; player shares must already represent season-long shares.

## Projection schedule recommendations

After the NFL schedule release, every new team stat-out must include schedule context.

Add/update a row in:

```bash
seasons/2026/data/projections/raw/team_schedule_environment.csv
```

Then build and show the schedule dry-run diff:

```bash
python scripts/build_team_schedule_recommendations.py --season 2026
python scripts/apply_team_schedule_recommendations.py --season 2026 --team <TEAM> --dry-run
```

Schedule recommendations are advisory and conservative. They should be smaller than roster/coaching/macro effects. Use them mostly for small volume/efficiency nudges plus fantasy-playoff notes or close ranking tiebreaks.

Do not accept schedule recommendations on behalf of the user. Only run `--accept` after the human user explicitly approves the exact mode (`volume`, `efficiency`, or `all`). The command requires `--human-approved`.

After showing a schedule dry-run, provide an agent recommendation (`volume`, `efficiency`, `all`, or no accept) with short reasoning. Explain why schedule volume and efficiency changes do or do not fit the researched schedule context. Human sign-off is still required.

## Projection roster verification

Before statting out or materially updating any team, verify the current roster and depth chart from at least two independent sources. Prefer the official team roster plus NFL/team transaction reporting, then cross-check with a stable depth-chart/news source when roles are unclear.

Record the check in:

```bash
seasons/2026/data/projections/raw/team_roster_verification.csv
```

Then run:

```bash
python scripts/validate_team_roster_verification.py --season 2026 --team <TEAM>
```

Do this before editing `player_assumptions.csv`. The verification row should include the checked date, source names/URLs, QB/RB/WR/TE room, removed players, unresolved items, and notes. If sources conflict, stop and tell the human user what is unresolved before projecting the affected players.

## Required checks before finishing edits

Run:

```bash
python scripts/validate_players.py --season 2026
python scripts/generate_cheatsheet.py --season 2026
```

If changing the season, substitute the requested season.

## Style guidance

Favor readable, boring, maintainable scripts. Avoid clever abstractions. This repo may sit untouched for months and then be revived next offseason.
