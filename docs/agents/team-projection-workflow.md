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

Calibration guardrails:

- Treat `games_projected` as context only. The engine does not automatically scale stat shares by games played, so season-long shares must already account for missed time.
- Do not make first-pass baselines ceiling outcomes. Prefer a strong median/mean case, then use analyst notes for upside.
- Be conservative with extreme target concentration. A player above roughly 28% target share, 30% receiving TD share, 90 receptions, or 1,200 receiving yards needs a clear reason.
- Be conservative with RB workhorse profiles. A player above roughly 275 carries or 90 targets should be an obvious offensive centerpiece.
- Be conservative with QB rushing TD share above roughly 35% unless the offense has a proven goal-line QB identity.
- If several players on one team all look like ceiling outcomes, redistribute some share to bucket rows instead of ranking every starter at their upside case.

5. Generate macro recommendations.

```powershell
python scripts/build_team_macro_recommendations.py --season 2026
```

6. Review team recommendation diff before accepting any macro values.

```powershell
python scripts/apply_team_macro_recommendations.py --season 2026 --team GB --dry-run
```

Stop here and show the dry-run output to the human user. Also provide a recommendation for `volume`, `efficiency`, `all`, or leaving the manual baseline unchanged.

The recommendation must explain:

- why the volume changes do or do not match the researched team context
- why the efficiency changes do or do not match the researched team context
- whether `all` would over-amplify or appropriately combine the two
- which mode the agent would choose, while still requiring human sign-off

Default recommendation posture:

- `volume` is usually the most useful macro mode.
- `efficiency` should be accepted only with strong continuity at QB, play caller, offensive line, and skill roles.
- `all` should be rare because it can compound volume and efficiency optimism.
- `no accept` is correct when a team is a deliberate outlier or the macro recommendation conflicts with researched context.

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

Always create this after-checkpoint once the team baseline is complete, even when no macro recommendation is accepted. In that case, note that the macro was intentionally not accepted.

```powershell
python scripts/create_projection_checkpoint.py --season 2026 --note "GB baseline complete; sources checked through YYYY-MM-DD"
python scripts/create_projection_checkpoint.py --season 2026 --note "BAL baseline complete; macro intentionally not accepted; sources checked through YYYY-MM-DD"
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

Do not silently accept macro recommendations. Show the diff, explain the likely fantasy impact, and recommend one of `volume`, `efficiency`, `all`, or no accept. The recommendation is advisory only.

6. If the user approves a mode, accept it with `--human-approved`, validate, rebuild, and checkpoint.

If the user chooses no accept or agrees with an agent recommendation to leave the manual baseline unchanged, still validate, rebuild, and create an after-checkpoint noting that the macro was intentionally not accepted.

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
- Include an agent recommendation and short analysis for `volume`, `efficiency`, `all`, or no accept after every macro dry-run.
- Never accept macro recommendations unless the human user explicitly approves the exact mode: `volume`, `efficiency`, or `all`.
- Use `--human-approved` only after that explicit human approval.
- Run validation and generation before calling work complete.
- Create checkpoints before and after meaningful projection changes.
- For team stat-out work, always create a completion checkpoint, even when no macro recommendation is accepted.
