from pathlib import Path

import pandas as pd
import pytest

from tierforge.projections.apply_team_schedule import build_schedule_diffs
from tierforge.projections.load_inputs import load_models
from tierforge.projections.models import TeamScheduleEnvironment
from tierforge.projections.team_schedule import (
    SCHEDULE_RECOMMENDATION_COLUMNS,
    build_team_schedule_recommendations,
    recommend_team_schedule,
)
from tests.test_validation import team


def schedule(**updates) -> TeamScheduleEnvironment:
    data = {
        "team_id": "CIN",
        "season": 2026,
        "schedule_source": "test",
        "last_updated": "2026-05-15",
        "pass_defense_difficulty": "neutral",
        "rush_defense_difficulty": "neutral",
        "pace_environment": "neutral",
        "rest_travel_grade": "neutral",
        "fantasy_playoff_grade": "neutral",
        "playoff_pass_defense_difficulty": "neutral",
        "playoff_rush_defense_difficulty": "neutral",
    }
    data.update(updates)
    return TeamScheduleEnvironment(**data)


def test_easy_pass_schedule_raises_pass_efficiency():
    neutral = recommend_team_schedule(team(), schedule())
    easy = recommend_team_schedule(team(), schedule(pass_defense_difficulty="easy"))
    assert easy.recommended_passing_yards > neutral.recommended_passing_yards
    assert easy.recommended_interceptions <= neutral.recommended_interceptions


def test_easy_rush_schedule_raises_rushing_efficiency():
    neutral = recommend_team_schedule(team(), schedule())
    easy = recommend_team_schedule(team(), schedule(rush_defense_difficulty="easy"))
    assert easy.recommended_rushing_yards > neutral.recommended_rushing_yards


def test_schedule_adjustments_are_capped():
    recommendation = recommend_team_schedule(
        team(),
        schedule(
            pass_defense_difficulty="very_easy",
            rush_defense_difficulty="very_hard",
            pace_environment="faster",
            rest_travel_grade="positive",
        ),
    )
    assert recommendation.plays_adjustment <= 15
    assert recommendation.pass_rate_adjustment <= 0.015
    assert recommendation.passing_yards_adjustment_pct <= 0.035


def test_build_schedule_recommendations_writes_expected_columns():
    root = Path(__file__).resolve().parents[1]
    output_path = build_team_schedule_recommendations(root, "2026")
    columns = list(pd.read_csv(output_path).columns)
    assert columns == SCHEDULE_RECOMMENDATION_COLUMNS


def test_build_schedule_recommendations_does_not_mutate_team_assumptions():
    root = Path(__file__).resolve().parents[1]
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    before = path.read_text()
    build_team_schedule_recommendations(root, "2026")
    after = path.read_text()
    assert after == before


def test_schedule_environment_raw_file_loads():
    root = Path(__file__).resolve().parents[1]
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_schedule_environment.csv"
    rows = load_models(path, TeamScheduleEnvironment)
    assert all(row.season == 2026 for row in rows)


def test_missing_schedule_recommendation_has_clear_error():
    root = Path(__file__).resolve().parents[1]
    build_team_schedule_recommendations(root, "2026")
    with pytest.raises(ValueError, match="No team_schedule_recommendations row"):
        build_schedule_diffs(root, "2026", "GB")
