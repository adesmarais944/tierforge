from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .apply_team_macro import format_recommended_value, read_csv_rows, write_csv_rows
from .load_inputs import season_projection_dir


VOLUME_FIELD_MAP = {
    "projected_offensive_plays": "recommended_offensive_plays",
    "projected_pass_rate": "recommended_pass_rate",
    "projected_rush_rate": "recommended_rush_rate",
    "projected_pass_attempts": "recommended_pass_attempts",
    "projected_rush_attempts": "recommended_rush_attempts",
}

EFFICIENCY_FIELD_MAP = {
    "projected_passing_yards": "recommended_passing_yards",
    "projected_passing_tds": "recommended_passing_tds",
    "projected_interceptions": "recommended_interceptions",
    "projected_rushing_yards": "recommended_rushing_yards",
    "projected_rushing_tds": "recommended_rushing_tds",
}

ACCEPT_MODES = {
    "volume": VOLUME_FIELD_MAP,
    "efficiency": EFFICIENCY_FIELD_MAP,
    "all": {**VOLUME_FIELD_MAP, **EFFICIENCY_FIELD_MAP},
}


@dataclass(frozen=True)
class ScheduleDiff:
    field: str
    current_value: str
    recommended_value: str

    @property
    def changed(self) -> bool:
        return self.current_value != self.recommended_value


def schedule_paths(root: Path, season: str) -> tuple[Path, Path]:
    projection_dir = season_projection_dir(root, season)
    return (
        projection_dir / "raw" / "team_assumptions.csv",
        projection_dir / "processed" / "team_schedule_recommendations.csv",
    )


def load_team_and_schedule_recommendation(
    root: Path, season: str, team_id: str
) -> tuple[list[str], list[dict[str, str]], dict[str, str], dict[str, str]]:
    team_path, recommendation_path = schedule_paths(root, season)
    fieldnames, team_rows = read_csv_rows(team_path)
    _recommendation_fieldnames, recommendation_rows = read_csv_rows(recommendation_path)

    try:
        team_row = next(row for row in team_rows if row["team_id"] == team_id)
    except StopIteration as exc:
        raise ValueError(f"No team_assumptions row found for team {team_id}") from exc

    try:
        recommendation_row = next(row for row in recommendation_rows if row["team_id"] == team_id)
    except StopIteration as exc:
        raise ValueError(f"No team_schedule_recommendations row found for team {team_id}") from exc

    return fieldnames, team_rows, team_row, recommendation_row


def build_schedule_diffs(root: Path, season: str, team_id: str, mode: str = "all") -> list[ScheduleDiff]:
    if mode not in ACCEPT_MODES:
        raise ValueError(f"Unknown accept mode {mode}")
    _fieldnames, _team_rows, team_row, recommendation_row = load_team_and_schedule_recommendation(root, season, team_id)
    diffs = []
    for current_field, recommendation_field in ACCEPT_MODES[mode].items():
        recommended_value = format_recommended_value(current_field, recommendation_row[recommendation_field])
        diffs.append(
            ScheduleDiff(
                field=current_field,
                current_value=team_row[current_field],
                recommended_value=recommended_value,
            )
        )
    return diffs


def apply_schedule_recommendations(root: Path, season: str, team_id: str, mode: str) -> list[ScheduleDiff]:
    if mode not in ACCEPT_MODES:
        raise ValueError(f"Unknown accept mode {mode}")
    team_path, _recommendation_path = schedule_paths(root, season)
    fieldnames, team_rows, team_row, recommendation_row = load_team_and_schedule_recommendation(root, season, team_id)
    diffs = build_schedule_diffs(root, season, team_id, mode)

    for current_field, recommendation_field in ACCEPT_MODES[mode].items():
        team_row[current_field] = format_recommended_value(current_field, recommendation_row[recommendation_field])

    write_csv_rows(team_path, fieldnames, team_rows)
    return diffs


def render_schedule_diffs(team_id: str, mode: str, diffs: list[ScheduleDiff]) -> str:
    lines = [f"Team schedule recommendation diff: {team_id} ({mode})", ""]
    width = max(len(diff.field) for diff in diffs)
    for diff in diffs:
        marker = "*" if diff.changed else " "
        lines.append(f"{marker} {diff.field.ljust(width)}  {diff.current_value} -> {diff.recommended_value}")
    return "\n".join(lines)
