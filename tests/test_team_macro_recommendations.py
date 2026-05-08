from pathlib import Path

import pandas as pd

from tierforge.projections.load_inputs import load_models
from tierforge.projections.models import OffseasonChange, PriorYearTeamStats
from tierforge.projections.team_macro import (
    LEAGUE_AVERAGE_RUSHING_TD_RATE,
    RECOMMENDATION_COLUMNS,
    build_team_macro_recommendations,
    recommend_team_macro,
)
from tests.test_validation import team


def baseline(rushing_yards: float = 1410) -> PriorYearTeamStats:
    return PriorYearTeamStats(
        team_id="CIN",
        season=2025,
        team_name="Cincinnati Bengals",
        offensive_plays=1000,
        pass_attempts=600,
        rush_attempts=381,
        passing_yards=4200,
        passing_tds=42,
        interceptions=18,
        rushing_yards=rushing_yards,
        rushing_tds=10,
    )


def offensive_line_change(raw_impact_score: float) -> OffseasonChange:
    return OffseasonChange(
        team_id="CIN",
        season=2026,
        unit="offense",
        change_type="addition",
        player_or_coach="Center",
        position="C",
        transaction_type="free_agency",
        expected_role="starter",
        impact_timing="immediate",
        certainty="high",
        unit_need_level="high",
        position_value="medium",
        scheme_fit="good",
        raw_impact_score=raw_impact_score,
    )


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


def test_passing_td_rate_regresses_toward_league_average():
    recommendation = recommend_team_macro(baseline(), team(), None, {})
    assert recommendation.regressed_passing_td_rate < recommendation.baseline_passing_td_rate


def test_interception_rate_regresses_toward_league_average():
    recommendation = recommend_team_macro(baseline(), team(), None, {})
    assert recommendation.regressed_interception_rate < recommendation.baseline_interception_rate


def test_rushing_td_rate_regresses_toward_league_average():
    recommendation = recommend_team_macro(baseline(), team(), None, {})
    assert recommendation.baseline_rushing_td_rate < recommendation.regressed_rushing_td_rate
    assert recommendation.regressed_rushing_td_rate < round(LEAGUE_AVERAGE_RUSHING_TD_RATE, 3)


def test_positive_offensive_line_impact_raises_rushing_ypc():
    neutral = recommend_team_macro(baseline(), team(), None, {})
    positive = recommend_team_macro(baseline(), team(), None, {}, [offensive_line_change(3)])
    assert positive.recommended_rushing_yards_per_attempt > neutral.recommended_rushing_yards_per_attempt


def test_negative_offensive_line_impact_lowers_rushing_ypc():
    neutral = recommend_team_macro(baseline(), team(), None, {})
    negative = recommend_team_macro(baseline(), team(), None, {}, [offensive_line_change(-3)])
    assert negative.recommended_rushing_yards_per_attempt < neutral.recommended_rushing_yards_per_attempt
