# Team Macro Recommendation CSV Plan

## Summary

Add a recommendation layer that calculates team macro projection suggestions from verified prior-year baseline stats plus offseason/defense/coaching adjustments.

Keep `team_assumptions.csv` as the editable analyst projection file. Write model output to a separate processed CSV only.

## Key Changes

- Add baseline source:
  - `seasons/2026/data/projections/raw/prior_year_team_stats.csv`
  - Use official Bengals 2025 values:
    - offensive plays: `1085`
    - pass attempts: `640`
    - rush attempts: `381`
    - passing yards: `4244`
    - passing TDs: `36`
    - interceptions: `17`
    - rushing yards: `1591`
    - rushing TDs: `11`

- Add macro recommendation output:
  - `seasons/2026/data/projections/processed/team_macro_recommendations.csv`
  - Include baseline fields, recommended fields, adjustment fields, and notes.
  - Do not mutate `team_assumptions.csv`.

- Add code path:
  - `src/tierforge/projections/team_macro.py`
  - `scripts/build_team_macro_recommendations.py --season 2026`

- Correct Bengals prior-year baseline fields in `team_assumptions.csv`:
  - pass attempts: `640`
  - rush attempts: `381`
  - offensive plays: `1085`
  - pass/rush rates recalculated from pass + rush attempts

## Calculation Behavior

- Start with prior-year baseline.
- Apply pace adjustment from `pace_change_score`.
- Apply pass-rate adjustment from `pass_rate_change_score`, `rush_rate_change_score`, and defense environment impacts.
- Apply conservative efficiency adjustments from `offense_change_score`.
- Clamp adjustments to avoid fake precision or runaway changes.
- Output recommendation only; analyst later chooses whether to copy into `projected_*`.

## Tests

Add tests for:

- Baseline loader uses `640`, not stale `652`.
- Recommended pass/rush attempts reconcile to recommended offensive plays.
- Positive defensive improvement can reduce recommended pass rate.
- Recommendation output does not mutate `team_assumptions.csv`.
- Recommendation CSV has stable column order.

Run:

```powershell
python -m pytest
python scripts/build_team_macro_recommendations.py --season 2026
python scripts/validate_projections.py --season 2026
python scripts/build_projections.py --season 2026 --scoring half_ppr
python scripts/build_projections.py --season 2026 --scoring full_ppr
python scripts/validate_players.py --season 2026
python scripts/generate_cheatsheet.py --season 2026
```

## Assumptions

- Recommendation output is advisory.
- `team_assumptions.csv` remains analyst-owned.
- No apply/accept command yet.
- No live scraping or API.
