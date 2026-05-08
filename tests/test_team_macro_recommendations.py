from pathlib import Path

import pandas as pd

from tierforge.projections.load_inputs import load_models
from tierforge.projections.models import PriorYearTeamStats
from tierforge.projections.team_macro import RECOMMENDATION_COLUMNS, build_team_macro_recommendations


def test_bengals_baseline_uses_verified_pass_attempts():
    root = Path(__file__).resolve().parents[1]
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "prior_year_team_stats.csv"
    baselines = load_models(path, PriorYearTeamStats)
    bengals = next(baseline for baseline in baselines if baseline.team_id == "CIN")
    assert bengals.pass_attempts == 640


def test_recommended_attempts_reconcile_to_plays():
    root = Path(__file__).resolve().parents[1]
    output_path = build_team_macro_recommendations(root, "2026")
    row = pd.read_csv(output_path).iloc[0]
    assert row["recommended_pass_attempts"] + row["recommended_rush_attempts"] == row["recommended_offensive_plays"]


def test_defensive_improvement_can_reduce_pass_rate():
    root = Path(__file__).resolve().parents[1]
    output_path = build_team_macro_recommendations(root, "2026")
    row = pd.read_csv(output_path).iloc[0]
    assert row["recommended_pass_rate"] < row["baseline_pass_rate"]


def test_build_does_not_mutate_team_assumptions():
    root = Path(__file__).resolve().parents[1]
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    before = path.read_text()
    build_team_macro_recommendations(root, "2026")
    after = path.read_text()
    assert after == before


def test_recommendation_csv_column_order():
    root = Path(__file__).resolve().parents[1]
    output_path = build_team_macro_recommendations(root, "2026")
    columns = list(pd.read_csv(output_path).columns)
    assert columns == RECOMMENDATION_COLUMNS
