from __future__ import annotations

from typing import Dict, Literal

from pydantic import BaseModel

ScoringFormatId = Literal["half_ppr", "full_ppr"]


class ScoringProfile(BaseModel):
    id: ScoringFormatId
    reception_points: float
    passing_yards_per_point: float = 25
    passing_touchdown_points: float = 4
    interception_points: float = -2
    rushing_yards_per_point: float = 10
    rushing_touchdown_points: float = 6
    receiving_yards_per_point: float = 10
    receiving_touchdown_points: float = 6
    fumble_lost_points: float = -2


SCORING_PROFILES: Dict[ScoringFormatId, ScoringProfile] = {
    "half_ppr": ScoringProfile(id="half_ppr", reception_points=0.5),
    "full_ppr": ScoringProfile(id="full_ppr", reception_points=1.0),
}


def fantasy_points(
    profile: ScoringProfile,
    passing_yards: float = 0,
    passing_tds: float = 0,
    interceptions: float = 0,
    rushing_yards: float = 0,
    rushing_tds: float = 0,
    receptions: float = 0,
    receiving_yards: float = 0,
    receiving_tds: float = 0,
    fumbles_lost: float = 0,
) -> float:
    points = 0.0
    points += passing_yards / profile.passing_yards_per_point
    points += passing_tds * profile.passing_touchdown_points
    points += interceptions * profile.interception_points
    points += rushing_yards / profile.rushing_yards_per_point
    points += rushing_tds * profile.rushing_touchdown_points
    points += receptions * profile.reception_points
    points += receiving_yards / profile.receiving_yards_per_point
    points += receiving_tds * profile.receiving_touchdown_points
    points += fumbles_lost * profile.fumble_lost_points
    return round(points, 2)
