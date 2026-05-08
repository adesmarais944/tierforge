from __future__ import annotations

from pathlib import Path

import pandas as pd

from .load_inputs import load_models, season_projection_dir
from .models import DefenseEnvironment, OffseasonChange, PriorYearTeamStats, TeamAssumption, TeamMacroRecommendation
from .offseason_changes import aggregate_unit_scores


RECOMMENDATION_COLUMNS = [
    "team_id",
    "baseline_season",
    "projection_season",
    "baseline_offensive_plays",
    "baseline_pass_attempts",
    "baseline_rush_attempts",
    "baseline_pass_rate",
    "baseline_rush_rate",
    "pace_adjustment",
    "pass_rate_adjustment",
    "efficiency_adjustment",
    "recommended_offensive_plays",
    "recommended_pass_rate",
    "recommended_rush_rate",
    "recommended_pass_attempts",
    "recommended_rush_attempts",
    "recommended_passing_yards",
    "recommended_passing_tds",
    "recommended_interceptions",
    "recommended_rushing_yards",
    "recommended_rushing_tds",
    "recommendation_note",
]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_team_macro_inputs(
    root: Path, season: str
) -> tuple[list[PriorYearTeamStats], list[TeamAssumption], list[DefenseEnvironment], list[OffseasonChange]]:
    raw_dir = season_projection_dir(root, season) / "raw"
    baselines = load_models(raw_dir / "prior_year_team_stats.csv", PriorYearTeamStats)
    teams = load_models(raw_dir / "team_assumptions.csv", TeamAssumption)
    defenses = load_models(raw_dir / "defense_environment.csv", DefenseEnvironment)
    changes = load_models(raw_dir / "offseason_team_changes.csv", OffseasonChange)
    return baselines, teams, defenses, changes


def recommend_team_macro(
    baseline: PriorYearTeamStats,
    team: TeamAssumption,
    defense: DefenseEnvironment | None,
    unit_scores: dict[tuple[str, str], float],
) -> TeamMacroRecommendation:
    baseline_attempts = baseline.pass_attempts + baseline.rush_attempts
    baseline_pass_rate = baseline.pass_attempts / baseline_attempts
    baseline_rush_rate = baseline.rush_attempts / baseline_attempts

    offense_score = unit_scores.get((team.team_id, "offense"), team.offense_change_score)
    defense_score = unit_scores.get((team.team_id, "defense"), team.defense_change_score)
    coaching_score = unit_scores.get((team.team_id, "coaching"), 0)

    defense_pace_impact = defense.defense_pace_impact if defense else 0
    pass_volume_impact = defense.pass_volume_impact if defense else 0
    rush_volume_impact = defense.rush_volume_impact if defense else 0
    shootout_impact = defense.shootout_impact if defense else 0

    pace_adjustment = clamp(
        (team.pace_change_score * 4.0) + (coaching_score * 2.0) + (defense_pace_impact * 12.0),
        -35.0,
        35.0,
    )
    recommended_offensive_plays = round(baseline.offensive_plays + pace_adjustment)

    pass_rate_adjustment = clamp(
        (team.pass_rate_change_score * 0.005)
        - (team.rush_rate_change_score * 0.005)
        + ((pass_volume_impact - rush_volume_impact) * 0.010)
        - (max(defense_score, 0) * 0.002),
        -0.045,
        0.045,
    )
    recommended_pass_rate = round(clamp(baseline_pass_rate + pass_rate_adjustment, 0.50, 0.70), 3)
    recommended_rush_rate = round(1.0 - recommended_pass_rate, 3)
    recommended_pass_attempts = round(recommended_offensive_plays * recommended_pass_rate)
    recommended_rush_attempts = recommended_offensive_plays - recommended_pass_attempts

    efficiency_adjustment = clamp((offense_score * 0.005) + (team.offense_change_score * 0.005), -0.08, 0.08)
    pass_yards_per_attempt = baseline.passing_yards / baseline.pass_attempts
    pass_td_rate = baseline.passing_tds / baseline.pass_attempts
    interception_rate = baseline.interceptions / baseline.pass_attempts
    rush_yards_per_attempt = baseline.rushing_yards / baseline.rush_attempts
    rush_td_rate = baseline.rushing_tds / baseline.rush_attempts

    passing_context = 1 + efficiency_adjustment + (shootout_impact * 0.010)
    rushing_context = 1 + (efficiency_adjustment * 0.5)
    recommended_passing_yards = round(recommended_pass_attempts * pass_yards_per_attempt * passing_context)
    recommended_passing_tds = round(recommended_pass_attempts * pass_td_rate * passing_context)
    recommended_interceptions = round(recommended_pass_attempts * interception_rate * (1 - (efficiency_adjustment * 0.5)))
    recommended_rushing_yards = round(recommended_rush_attempts * rush_yards_per_attempt * rushing_context)
    recommended_rushing_tds = round(recommended_rush_attempts * rush_td_rate * rushing_context)

    note = (
        f"Baseline from {baseline.season}; pace {pace_adjustment:+.1f} plays; "
        f"pass rate {pass_rate_adjustment:+.3f}; efficiency {efficiency_adjustment:+.3f}."
    )

    return TeamMacroRecommendation(
        team_id=team.team_id,
        baseline_season=baseline.season,
        projection_season=team.season,
        baseline_offensive_plays=baseline.offensive_plays,
        baseline_pass_attempts=baseline.pass_attempts,
        baseline_rush_attempts=baseline.rush_attempts,
        baseline_pass_rate=round(baseline_pass_rate, 3),
        baseline_rush_rate=round(baseline_rush_rate, 3),
        pace_adjustment=round(pace_adjustment, 1),
        pass_rate_adjustment=round(pass_rate_adjustment, 3),
        efficiency_adjustment=round(efficiency_adjustment, 3),
        recommended_offensive_plays=recommended_offensive_plays,
        recommended_pass_rate=recommended_pass_rate,
        recommended_rush_rate=recommended_rush_rate,
        recommended_pass_attempts=recommended_pass_attempts,
        recommended_rush_attempts=recommended_rush_attempts,
        recommended_passing_yards=recommended_passing_yards,
        recommended_passing_tds=recommended_passing_tds,
        recommended_interceptions=recommended_interceptions,
        recommended_rushing_yards=recommended_rushing_yards,
        recommended_rushing_tds=recommended_rushing_tds,
        recommendation_note=note,
    )


def build_team_macro_recommendations(root: Path, season: str) -> Path:
    baselines, teams, defenses, changes = load_team_macro_inputs(root, season)
    baseline_by_team = {baseline.team_id: baseline for baseline in baselines}
    defense_by_team = {defense.team_id: defense for defense in defenses}
    unit_scores = aggregate_unit_scores(changes)

    recommendations = [
        recommend_team_macro(baseline_by_team[team.team_id], team, defense_by_team.get(team.team_id), unit_scores)
        for team in teams
        if team.team_id in baseline_by_team
    ]

    processed_dir = season_projection_dir(root, season) / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "team_macro_recommendations.csv"
    rows = [{column: recommendation.model_dump()[column] for column in RECOMMENDATION_COLUMNS} for recommendation in recommendations]
    pd.DataFrame(rows, columns=RECOMMENDATION_COLUMNS).to_csv(output_path, index=False)
    return output_path
