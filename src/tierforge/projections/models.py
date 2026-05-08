from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

Position = Literal["QB", "RB", "WR", "TE", "OTHER"]
ScoringFormat = Literal["half_ppr", "full_ppr"]


class TeamAssumption(BaseModel):
    team_id: str
    season: int
    team_name: str
    head_coach: str
    offensive_coordinator: str
    starting_qb: str
    prior_year_offensive_plays: float
    prior_year_pass_attempts: float
    prior_year_rush_attempts: float
    prior_year_pass_rate: float
    prior_year_rush_rate: float
    prior_year_points_scored: float
    prior_year_offensive_tds: float
    projected_offensive_plays: float
    projected_pass_rate: float
    projected_rush_rate: float
    projected_pass_attempts: float
    projected_rush_attempts: float
    projected_passing_yards: float
    projected_passing_tds: float
    projected_interceptions: float
    projected_rushing_yards: float
    projected_rushing_tds: float
    offense_change_score: float = 0
    defense_change_score: float = 0
    pace_change_score: float = 0
    pass_rate_change_score: float = 0
    rush_rate_change_score: float = 0
    pace_adjustment_note: str = ""
    pass_rush_ratio_note: str = ""
    coaching_note: str = ""
    defense_environment_note: str = ""
    general_projection_note: str = ""


class DefenseEnvironment(BaseModel):
    team_id: str
    season: int
    prior_year_points_allowed_rank: int
    prior_year_yards_allowed_rank: int
    prior_year_defensive_efficiency_rank: int
    projected_defense_quality: Literal["poor", "below_average", "average", "above_average", "elite"]
    projected_game_script_bias: Literal["negative", "neutral", "positive"]
    defense_change_score: float
    defense_pace_impact: float
    pass_volume_impact: float
    rush_volume_impact: float
    shootout_impact: float
    analyst_note: str = ""


class PriorYearTeamStats(BaseModel):
    team_id: str
    season: int
    team_name: str
    offensive_plays: float
    pass_attempts: float
    rush_attempts: float
    passing_yards: float
    passing_tds: float
    interceptions: float
    rushing_yards: float
    rushing_tds: float
    source_note: str = ""


class TeamMacroRecommendation(BaseModel):
    team_id: str
    baseline_season: int
    projection_season: int
    baseline_offensive_plays: float
    baseline_pass_attempts: float
    baseline_rush_attempts: float
    baseline_pass_rate: float
    baseline_rush_rate: float
    pace_adjustment: float
    pass_rate_adjustment: float
    efficiency_adjustment: float
    recommended_offensive_plays: float
    recommended_pass_rate: float
    recommended_rush_rate: float
    recommended_pass_attempts: float
    recommended_rush_attempts: float
    recommended_passing_yards: float
    recommended_passing_tds: float
    recommended_interceptions: float
    recommended_rushing_yards: float
    recommended_rushing_tds: float
    recommendation_note: str = ""


class OffseasonChange(BaseModel):
    team_id: str
    season: int
    unit: Literal["offense", "defense", "special_teams", "coaching"]
    change_type: str
    player_or_coach: str
    position: str = ""
    transaction_type: str
    prior_team: str = ""
    new_team: str = ""
    draft_round: Optional[float] = None
    draft_pick: Optional[float] = None
    expected_role: Literal["elite_starter", "starter", "rotational", "depth", "developmental", "unknown"]
    impact_timing: Literal["immediate", "partial_season", "developmental", "unknown"]
    certainty: Literal["low", "medium", "high"]
    unit_need_level: Literal["low", "medium", "high", "critical"]
    position_value: Literal["low", "medium", "high"]
    scheme_fit: Literal["poor", "neutral", "good", "excellent"]
    raw_impact_score: float
    weighted_impact_score: Optional[float] = None
    notes: str = ""


class PlayerAssumption(BaseModel):
    player_id: str
    player_name: str
    team_id: str
    position: Position
    include_in_rankings: bool = True
    games_projected: float = 17
    target_share: Optional[float] = None
    targets: Optional[float] = None
    catch_rate: Optional[float] = None
    receptions: Optional[float] = None
    yards_per_target: Optional[float] = None
    receiving_yards: Optional[float] = None
    receiving_td_share: Optional[float] = None
    receiving_tds: Optional[float] = None
    rush_share: Optional[float] = None
    carries: Optional[float] = None
    yards_per_carry: Optional[float] = None
    rushing_yards: Optional[float] = None
    rushing_td_share: Optional[float] = None
    rushing_tds: Optional[float] = None
    pass_attempt_share: Optional[float] = None
    pass_attempts: Optional[float] = None
    completion_rate: Optional[float] = None
    passing_yards_per_attempt: Optional[float] = None
    passing_yards: Optional[float] = None
    passing_td_share: Optional[float] = None
    passing_tds: Optional[float] = None
    interception_rate: Optional[float] = None
    interceptions: Optional[float] = None
    fumbles_lost: float = 0
    manual_fantasy_point_adjustment: float = 0
    manual_rank_adjustment: float = 0
    analyst_tag: str = ""
    analyst_note: str = ""


class PlayerProjection(BaseModel):
    player_id: str
    player_name: str
    team_id: str
    position: Position
    scoring_format: ScoringFormat
    include_in_rankings: bool
    games_projected: float
    targets: float = 0
    receptions: float = 0
    receiving_yards: float = 0
    receiving_tds: float = 0
    carries: float = 0
    rushing_yards: float = 0
    rushing_tds: float = 0
    pass_attempts: float = 0
    passing_yards: float = 0
    passing_tds: float = 0
    interceptions: float = 0
    fumbles_lost: float = 0
    raw_projected_fantasy_points: float
    manual_fantasy_point_adjustment: float
    final_projected_fantasy_points: float
    overall_rank: Optional[int] = None
    position_rank: Optional[int] = None
    analyst_tag: str = ""
    analyst_note: str = ""
