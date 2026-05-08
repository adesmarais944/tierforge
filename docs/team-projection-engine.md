# Team Projection Engine - Implementation Brief

## Branch Goal

This branch adds a team-level projection engine to TierForge. The engine produces a projected fantasy point baseline for players on one real NFL team. Later phases will apply weights, adjustments, rankings, and tier integration so these projections can drive the draft cheat sheet.

This is an addition to the existing model:

```text
season CSV/YAML inputs
  -> Python projection engine
  -> projected player baselines
  -> rankings/tier logic
  -> generated workbook / Google Sheets preview
```

CSV/YAML remains source of truth. Excel/Google Sheets remain generated or preview surfaces.

## Product Boundary

Do not build a web app, React app, Next.js app, database, live scraper, or year-round platform.

MVP must be deterministic, local, explainable, and inspectable. Python owns projection math. Google Sheets owns review, formatting, filtering, and draft-room interaction.

## MVP Scope

Start with the Cincinnati Bengals only. Cincinnati is the first validation case, not a hard-coded team.

MVP outputs:

- team macro projection inputs
- defensive environment inputs
- offseason-change inputs
- player assumption inputs
- half-PPR player projections
- full-PPR player projections
- rankings-ready CSVs
- tests for scoring, validation, offseason scoring, rankings, and export shape

MVP non-goals:

- live API integrations
- Google OAuth
- Monte Carlo simulation
- weekly projections
- dynasty rankings
- auction values
- direct draft cheat sheet integration

## Season-Scoped Layout

Use season-scoped files to match the existing repo:

```text
seasons/2026/data/projections/
  raw/
    team_assumptions.csv
    defense_environment.csv
    offseason_team_changes.csv
    player_assumptions.csv
  processed/
    player_projections_half_ppr.csv
    player_projections_full_ppr.csv
    player_rankings_half_ppr.csv
    player_rankings_full_ppr.csv
```

Use Python code under:

```text
src/tierforge/projections/
```

Use script entrypoints:

```text
scripts/validate_projections.py
scripts/build_projections.py
```

## Projection Flow

Projection is top-down:

```text
team play volume
  -> pass/rush split
  -> QB passing baseline
  -> target/carry shares
  -> player stat projections
  -> fantasy points by scoring profile
  -> rankings-ready outputs
```

Player projections must reconcile to team assumptions. Do not create isolated player projections that ignore team volume.

## Scoring

Required scoring formats:

- `half_ppr`
- `full_ppr`

Both use 4-point passing TDs for MVP. Every fantasy-point calculation must receive a scoring profile. Reception scoring must not be hard-coded.

Future extension may add 6-point passing TDs and custom scoring.

## Defense And Offseason Changes

Defense is first-class because it affects play volume, pass volume, rush volume, game script, and shootout pressure.

Offseason changes use structured analyst inputs:

- offense change score
- defense change score
- pace change score
- pass-rate change score
- rush-rate change score

Individual changes receive raw impact scores and weighted impact scores. Clamp aggregate unit scores between `-10` and `+10`.

Example names or transactions in planning docs are hypothetical unless backed by real input data.

## Player Assumptions

Player input supports explicit stat overrides or share-based calculations.

Rules:

- if `targets` exists, use it; otherwise calculate from team pass attempts and `target_share`
- if `carries` exists, use it; otherwise calculate from team rush attempts and `rush_share`
- if explicit volume and share both exist, explicit volume wins and validation warns
- keep `raw_projected_fantasy_points`, `manual_fantasy_point_adjustment`, and `final_projected_fantasy_points` separate
- include "other" bucket rows for team reconciliation
- exclude bucket rows from final rankings unless explicitly configured

## Validation

Hard failures:

- missing required projection input files
- missing required columns
- invalid scoring format
- invalid enum value
- unknown team IDs
- negative or zero team pass/rush attempts
- projected pass rate plus rush rate not near `1.0`
- projected pass attempts plus rush attempts not near projected offensive plays
- receiving or rushing TD shares above available team TD pool

Warnings:

- target shares not near `100%`
- rush shares not near `100%`
- explicit volume and share both provided

## Acceptance Criteria

First implementation is complete when repo can:

1. Store Bengals macro assumptions.
2. Store Bengals defensive environment assumptions.
3. Store Bengals offseason-change inputs.
4. Aggregate offseason changes into unit scores.
5. Store Bengals player assumptions.
6. Validate team pass/rush volume.
7. Validate target/rush share reconciliation.
8. Calculate player stat projections.
9. Calculate half-PPR and full-PPR fantasy points.
10. Keep manual adjustments separate from raw projections.
11. Generate overall and positional ranks.
12. Export Google Sheets-ready CSV files.
13. Include tests for scoring, validation, offseason scoring, ranking order, and export column order.

## Required Commands

```powershell
python -m pytest
python scripts/validate_projections.py --season 2026
python scripts/build_projections.py --season 2026 --scoring half_ppr
python scripts/build_projections.py --season 2026 --scoring full_ppr
python scripts/validate_players.py --season 2026
python scripts/generate_cheatsheet.py --season 2026
```
