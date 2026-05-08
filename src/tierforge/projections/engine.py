from __future__ import annotations

from pathlib import Path

import pandas as pd

from .load_inputs import load_models, season_projection_dir
from .models import OffseasonChange, PlayerAssumption, ScoringFormat, TeamAssumption
from .offseason_changes import aggregate_unit_scores
from .player_projection import project_players
from .rankings import rank_players
from .validation import combine_results, validate_player_assumptions, validate_team_assumptions


def load_projection_inputs(root: Path, season: str):
    projection_dir = season_projection_dir(root, season)
    raw_dir = projection_dir / "raw"
    teams = load_models(raw_dir / "team_assumptions.csv", TeamAssumption)
    players = load_models(raw_dir / "player_assumptions.csv", PlayerAssumption)
    changes = load_models(raw_dir / "offseason_team_changes.csv", OffseasonChange)
    return teams, players, changes


def validate_inputs(root: Path, season: str):
    teams, players, _changes = load_projection_inputs(root, season)
    return combine_results(validate_team_assumptions(teams), validate_player_assumptions(players, teams))


def build_outputs(root: Path, season: str, scoring_format: ScoringFormat) -> tuple[Path, Path]:
    teams, players, changes = load_projection_inputs(root, season)
    result = combine_results(validate_team_assumptions(teams), validate_player_assumptions(players, teams))
    if not result.ok:
        raise ValueError("\n".join(result.errors))

    projections = project_players(players, teams, scoring_format)
    rankings = rank_players(projections)
    projection_dir = season_projection_dir(root, season)
    processed_dir = projection_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    projections_path = processed_dir / f"player_projections_{scoring_format}.csv"
    rankings_path = processed_dir / f"player_rankings_{scoring_format}.csv"
    projection_rows = [projection.model_dump() for projection in projections]
    ranking_rows = [projection.model_dump() for projection in rankings]
    pd.DataFrame(projection_rows).to_csv(projections_path, index=False)
    pd.DataFrame(ranking_rows).to_csv(rankings_path, index=False)

    score_rows = [
        {"team_id": team_id, "unit": unit, "unit_change_score": score}
        for (team_id, unit), score in aggregate_unit_scores(changes).items()
    ]
    pd.DataFrame(score_rows).to_csv(processed_dir / "offseason_unit_scores.csv", index=False)
    return projections_path, rankings_path
