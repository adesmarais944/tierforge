from __future__ import annotations

from pathlib import Path

import pandas as pd

from .load_inputs import load_models, season_projection_dir
from .models import TeamAssumption, TeamScheduleEnvironment, TeamScheduleRecommendation


SCHEDULE_RECOMMENDATION_COLUMNS = [
    "team_id",
    "season",
    "plays_adjustment",
    "pass_rate_adjustment",
    "passing_yards_adjustment_pct",
    "rushing_yards_adjustment_pct",
    "passing_td_adjustment",
    "interception_adjustment",
    "rushing_td_adjustment",
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
    "fantasy_playoff_note",
    "recommendation_note",
]

DIFFICULTY_SCORE = {
    "very_easy": 2,
    "easy": 1,
    "neutral": 0,
    "hard": -1,
    "very_hard": -2,
}
PACE_SCORE = {"slower": -1, "neutral": 0, "faster": 1}
REST_TRAVEL_SCORE = {"negative": -1, "neutral": 0, "positive": 1}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_team_schedule_inputs(root: Path, season: str) -> tuple[list[TeamAssumption], list[TeamScheduleEnvironment]]:
    raw_dir = season_projection_dir(root, season) / "raw"
    teams = load_models(raw_dir / "team_assumptions.csv", TeamAssumption)
    schedules = load_models(raw_dir / "team_schedule_environment.csv", TeamScheduleEnvironment)
    return teams, schedules


def recommend_team_schedule(team: TeamAssumption, schedule: TeamScheduleEnvironment) -> TeamScheduleRecommendation:
    pass_score = DIFFICULTY_SCORE[schedule.pass_defense_difficulty]
    rush_score = DIFFICULTY_SCORE[schedule.rush_defense_difficulty]
    pace_score = PACE_SCORE[schedule.pace_environment]
    rest_score = REST_TRAVEL_SCORE[schedule.rest_travel_grade]

    plays_adjustment = clamp((pace_score * 6.0) + (rest_score * 4.0) - (schedule.short_week_count * 1.5), -15.0, 15.0)
    pass_rate_adjustment = clamp((pass_score * 0.004) - (rush_score * 0.004), -0.015, 0.015)
    passing_yards_adjustment_pct = clamp((pass_score * 0.012) + (rest_score * 0.004), -0.035, 0.035)
    rushing_yards_adjustment_pct = clamp((rush_score * 0.012) + (rest_score * 0.004), -0.035, 0.035)
    passing_td_adjustment = clamp(round(pass_score * 0.5), -1, 1)
    interception_adjustment = clamp(round(-pass_score * 0.5), -1, 1)
    rushing_td_adjustment = clamp(round(rush_score * 0.5), -1, 1)

    recommended_offensive_plays = round(team.projected_offensive_plays + plays_adjustment)
    recommended_pass_rate = round(clamp(team.projected_pass_rate + pass_rate_adjustment, 0.50, 0.70), 3)
    recommended_rush_rate = round(1.0 - recommended_pass_rate, 3)
    recommended_pass_attempts = round(recommended_offensive_plays * recommended_pass_rate)
    recommended_rush_attempts = recommended_offensive_plays - recommended_pass_attempts

    recommended_passing_yards = round(team.projected_passing_yards * (1 + passing_yards_adjustment_pct))
    recommended_rushing_yards = round(team.projected_rushing_yards * (1 + rushing_yards_adjustment_pct))
    recommended_passing_tds = round(team.projected_passing_tds + passing_td_adjustment)
    recommended_interceptions = round(max(0, team.projected_interceptions + interception_adjustment))
    recommended_rushing_tds = round(team.projected_rushing_tds + rushing_td_adjustment)

    fantasy_note = (
        f"Fantasy playoff schedule {schedule.fantasy_playoff_grade}; "
        f"pass {schedule.playoff_pass_defense_difficulty}; rush {schedule.playoff_rush_defense_difficulty}."
    )
    note = (
        f"Schedule source {schedule.schedule_source or 'manual'}; plays {plays_adjustment:+.1f}; "
        f"pass rate {pass_rate_adjustment:+.3f}; pass yards {passing_yards_adjustment_pct:+.3f}; "
        f"rush yards {rushing_yards_adjustment_pct:+.3f}. Use as advisory only."
    )

    return TeamScheduleRecommendation(
        team_id=team.team_id,
        season=team.season,
        plays_adjustment=round(plays_adjustment, 1),
        pass_rate_adjustment=round(pass_rate_adjustment, 3),
        passing_yards_adjustment_pct=round(passing_yards_adjustment_pct, 3),
        rushing_yards_adjustment_pct=round(rushing_yards_adjustment_pct, 3),
        passing_td_adjustment=passing_td_adjustment,
        interception_adjustment=interception_adjustment,
        rushing_td_adjustment=rushing_td_adjustment,
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
        fantasy_playoff_note=fantasy_note,
        recommendation_note=note,
    )


def build_team_schedule_recommendations(root: Path, season: str) -> Path:
    teams, schedules = load_team_schedule_inputs(root, season)
    teams_by_id = {team.team_id: team for team in teams}
    recommendations = [
        recommend_team_schedule(teams_by_id[schedule.team_id], schedule)
        for schedule in schedules
        if schedule.team_id in teams_by_id
    ]

    processed_dir = season_projection_dir(root, season) / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "team_schedule_recommendations.csv"
    rows = [
        {column: recommendation.model_dump()[column] for column in SCHEDULE_RECOMMENDATION_COLUMNS}
        for recommendation in recommendations
    ]
    pd.DataFrame(rows, columns=SCHEDULE_RECOMMENDATION_COLUMNS).to_csv(output_path, index=False)
    return output_path
