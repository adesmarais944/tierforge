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
    team_roster_verification.csv
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

## Plain-English Projection Map

The projection system has one main rule:

```text
team assumptions are the source of truth for team volume
player assumptions divide that volume among players
scoring rules turn player stats into fantasy points
```

In normal projection builds, this is the path:

```text
raw/team_assumptions.csv
  + raw/player_assumptions.csv
  -> player stat projections
  -> fantasy points
  -> overall and position rankings
```

Think of `team_assumptions.csv` as the team bucket. It answers questions like:

- How many passes will this team throw?
- How many rushes will this team run?
- How many passing TDs, rushing TDs, interceptions, passing yards, and rushing yards should the team have?

Think of `player_assumptions.csv` as the player share sheet. It answers questions like:

- What share of team targets does this player get?
- What share of team rush attempts does this player get?
- What share of team TDs does this player get?
- Does this player have an exact override instead of a share?

Example:

```text
team projected_pass_attempts = 600
player target_share = 0.25

player targets = 600 * 0.25 = 150
```

Then rates finish the stat line:

```text
targets = 150
catch_rate = 0.70
yards_per_target = 9.0

receptions = 150 * 0.70 = 105
receiving_yards = 150 * 9.0 = 1350
```

Touchdowns work the same way:

```text
team projected_passing_tds = 30
player receiving_td_share = 0.30

player receiving_tds = 30 * 0.30 = 9
```

Explicit player stats win over calculated stats. If `targets` is filled in, the engine uses that value. If `targets` is blank and `target_share` is filled in, the engine calculates targets from team pass attempts. If both are blank, targets become `0`.

Before the player share sheet is edited, the team should have a roster verification row:

```text
raw/team_roster_verification.csv
```

This file does not change fantasy points by itself. It is an audit/preflight layer that records when the roster was checked, which sources were cross-referenced, the current QB/RB/WR/TE rooms, removed players, and any unresolved items. It exists because bad roster assumptions can make every downstream projection look mathematically clean but football-wrong.

For one team, validate it with:

```powershell
python scripts/validate_team_roster_verification.py --season 2026 --team HOU
```

If that check fails, the team should not be considered ready for projection work.

After the stat line exists, scoring turns stats into points:

```text
passing yards / 25
passing TDs * 4
interceptions * -2
rushing yards / 10
rushing TDs * 6
receptions * 0.5 for half-PPR, or * 1.0 for full-PPR
receiving yards / 10
receiving TDs * 6
fumbles lost * -2
```

Final projected points are:

```text
raw fantasy points + manual_fantasy_point_adjustment
```

Rankings sort players by final projected fantasy points, with separate overall and position ranks.

## Macro Recommendation Files

There are two processed files that can look like part of the projection math:

```text
processed/offseason_unit_scores.csv
processed/team_macro_recommendations.csv
processed/team_schedule_recommendations.csv
```

They are decision-support files. They do not directly change player projections unless their recommendations are accepted back into `raw/team_assumptions.csv`.

`offseason_unit_scores.csv` summarizes `raw/offseason_team_changes.csv`. Each team change starts with a `raw_impact_score`, then gets weighted by role, certainty, team need, position value, and scheme fit. The output is a clamped team/unit score from `-10` to `+10`.

Example idea:

```text
offseason_team_changes.csv
  -> offense score, defense score, coaching score
  -> offseason_unit_scores.csv
```

This file is mostly for audit and review. It helps explain why a team is treated as improved, worse, or mostly unchanged.

`team_macro_recommendations.csv` uses prior-year stats, team assumptions, defensive environment, and offseason changes to suggest new team-level volume and efficiency numbers.

Example idea:

```text
prior_year_team_stats.csv
  + team_assumptions.csv
  + defense_environment.csv
  + offseason_team_changes.csv
  -> team_macro_recommendations.csv
```

The recommendations include values like:

- recommended offensive plays
- recommended pass rate
- recommended rush rate
- recommended pass attempts
- recommended rush attempts
- recommended passing yards
- recommended passing TDs
- recommended interceptions
- recommended rushing yards
- recommended rushing TDs

Those recommendations stay in the processed file until accepted.

To preview a recommendation for one team:

```powershell
python scripts/apply_team_macro_recommendations.py --season 2026 --team CIN --dry-run
```

To accept it into `raw/team_assumptions.csv`:

```powershell
python scripts/apply_team_macro_recommendations.py --season 2026 --team CIN --accept all
```

Accept modes:

- `volume`: copies recommended plays, pass rate, rush rate, pass attempts, and rush attempts
- `efficiency`: copies recommended passing/rushing yards, TDs, and interceptions
- `all`: copies both volume and efficiency fields

After accepting macro recommendations, rebuild projections. At that point, the player projection engine reads the updated `team_assumptions.csv`, and player projections change.

### Schedule recommendations

The released NFL schedule should be modeled as a small advisory layer, not as a full projection rewrite.

Schedule source files:

```text
raw/team_schedule_environment.csv
processed/team_schedule_recommendations.csv
```

`team_schedule_environment.csv` stores team-level schedule context such as opponent difficulty, pace environment, rest/travel, bye week, short weeks, international games, and fantasy playoff grade.

After the NFL schedule release, every new team projection should include a schedule environment row before final review. The schedule layer is now part of the normal projection workflow, even when the final recommendation is no accept.

`team_schedule_recommendations.csv` turns that context into small team-level recommendations:

- projected offensive plays
- pass/rush split
- passing/rushing yards
- passing/rushing TDs
- interceptions

Schedule recommendations are advisory only. They do not affect player projections until accepted into `raw/team_assumptions.csv`.

Build and dry-run:

```powershell
python scripts/build_team_schedule_recommendations.py --season 2026
python scripts/apply_team_schedule_recommendations.py --season 2026 --team CIN --dry-run
```

Accept only after human approval:

```powershell
python scripts/apply_team_schedule_recommendations.py --season 2026 --team CIN --accept volume --human-approved
python scripts/apply_team_schedule_recommendations.py --season 2026 --team CIN --accept efficiency --human-approved
python scripts/apply_team_schedule_recommendations.py --season 2026 --team CIN --accept all --human-approved
```

Schedule effects should stay conservative. Use them mostly for small macro nudges and fantasy-playoff notes or tiebreaks.

Full mental model:

```text
roster verification
  -> player universe and role sanity check
offseason changes
  -> unit scores
  -> macro recommendations
  -> optional update to team_assumptions.csv
  -> player shares calculate stats
  -> scoring calculates fantasy points
  -> rankings
```

If a user is unsure which file to edit, default to this:

```text
Edit raw/team_assumptions.csv for team volume.
Edit raw/player_assumptions.csv for player roles.
Use processed macro files as guidance, not source of truth.
```

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
