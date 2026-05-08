# Team Projection Agent Workflow

Use this when asked to stat out a team or update a team after new information.

## Goals

Make the workflow repeatable:

```text
research real information
  -> edit source CSVs
  -> generate macro recommendations
  -> validate and build projections
  -> checkpoint the whole projection system
```

CSV files in `raw/` are source of truth. Files in `processed/` are generated outputs or recommendation surfaces.

## Source Standard

Use real information and cross-check important facts before editing assumptions.

Prefer primary or stable sources for:

- team stats
- coaching changes
- roster moves
- depth chart context
- injury status
- contract or transaction facts

Useful source categories:

- team official site for roster/coaching/news
- NFL transaction/news pages
- Pro Football Reference or Stathead-style historical stat pages
- ESPN/CBS/Sleeper/FantasyPros depth chart or player pages
- multiple beat/news sources when interpreting role changes

Do not treat one rumor or one analyst take as enough to move source-of-truth assumptions. Record uncertainty in `analyst_note` or `notes`.

## Stat Out A Team

Example request:

```text
Okay let's stat out the Green Bay Packers.
```

Steps:

1. Check current state.

```powershell
python scripts/team_projection_status.py --season 2026 --team GB
```

2. Create checkpoint before edits if meaningful data already exists.

```powershell
python scripts/create_projection_checkpoint.py --season 2026 --note "Before GB baseline"
```

3. Research and cross-check current team context.

Collect:

- prior-year offensive plays, pass attempts, rush attempts, passing/rushing yards, TDs, interceptions
- head coach, offensive coordinator, starting QB
- major offensive additions/losses
- major defensive additions/losses
- offensive line changes
- expected skill-player roles
- projected game-script or pace context

4. Edit source CSVs.

Primary files:

```text
seasons/2026/data/projections/raw/team_assumptions.csv
seasons/2026/data/projections/raw/defense_environment.csv
seasons/2026/data/projections/raw/offseason_team_changes.csv
seasons/2026/data/projections/raw/player_assumptions.csv
```

Use "other" bucket player rows for target/rush/TD reconciliation when needed. Keep bucket rows out of rankings with `include_in_rankings=false`.

5. Generate macro recommendations.

```powershell
python scripts/build_team_macro_recommendations.py --season 2026
```

6. Review team recommendation diff before accepting any macro values.

```powershell
python scripts/apply_team_macro_recommendations.py --season 2026 --team GB --dry-run
```

Stop here and show the dry-run output to the human user. Do not choose an accept mode yourself, even if the diff looks reasonable.

Accept only after the human user explicitly approves `volume`, `efficiency`, or `all`:

```powershell
python scripts/apply_team_macro_recommendations.py --season 2026 --team GB --accept volume --human-approved
python scripts/apply_team_macro_recommendations.py --season 2026 --team GB --accept efficiency --human-approved
python scripts/apply_team_macro_recommendations.py --season 2026 --team GB --accept all --human-approved
```

7. Validate and build outputs.

```powershell
python scripts/validate_projections.py --season 2026
python scripts/build_projections.py --season 2026 --scoring half_ppr
python scripts/build_projections.py --season 2026 --scoring full_ppr
python scripts/validate_players.py --season 2026
python scripts/generate_cheatsheet.py --season 2026
```

8. Check status again.

```powershell
python scripts/team_projection_status.py --season 2026 --team GB
```

9. Create after checkpoint.

```powershell
python scripts/create_projection_checkpoint.py --season 2026 --note "GB baseline complete; sources checked through YYYY-MM-DD"
```

## News Since Checkpoint

Example request:

```text
Based on all news since last checkpoint, does this affect the macro environment for the Packers?
```

Steps:

1. Find latest checkpoint and current status.

```powershell
python scripts/team_projection_status.py --season 2026 --team GB
python scripts/diff_projection_checkpoint.py --season 2026 --since latest
```

2. Research news since the checkpoint date.

Cross-check meaningful events before editing:

- injuries
- starting lineup changes
- coach/scheme comments
- free agent signings
- trades
- retirements
- depth chart movement
- major ADP/role changes

3. Translate confirmed news into structured changes.

Likely files:

```text
raw/offseason_team_changes.csv
raw/team_assumptions.csv
raw/player_assumptions.csv
raw/defense_environment.csv
```

Use notes to explain why a change was made and what sources support it.

4. Rebuild macro recommendations.

```powershell
python scripts/build_team_macro_recommendations.py --season 2026
```

5. Show macro diff before applying.

```powershell
python scripts/apply_team_macro_recommendations.py --season 2026 --team GB --dry-run
```

Do not silently accept macro recommendations. Show the diff and explain the likely fantasy impact.

6. After explicit user approval, accept the chosen recommendation mode with `--human-approved`, validate, rebuild, and checkpoint.

## Checkpoint And Diff Commands

Create whole-system checkpoint:

```powershell
python scripts/create_projection_checkpoint.py --season 2026 --note "Short note"
```

Diff current files against latest checkpoint:

```powershell
python scripts/diff_projection_checkpoint.py --season 2026 --since latest
```

Diff against a specific checkpoint:

```powershell
python scripts/diff_projection_checkpoint.py --season 2026 --since 20260508T150000Z
```

Team status:

```powershell
python scripts/team_projection_status.py --season 2026 --team GB
```

## Agent Safety Rules

- Research before editing assumptions.
- Cross-check real-world facts.
- Keep source links or source names in notes when practical.
- Keep `raw/` as source of truth.
- Treat `processed/` as generated output or recommendation output.
- Show macro recommendation diffs before accepting them.
- Never accept macro recommendations unless the human user explicitly approves the exact mode: `volume`, `efficiency`, or `all`.
- Use `--human-approved` only after that explicit human approval.
- Run validation and generation before calling work complete.
- Create checkpoints before and after meaningful projection changes.
