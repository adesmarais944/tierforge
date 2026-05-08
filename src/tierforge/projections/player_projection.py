from __future__ import annotations

from .models import PlayerAssumption, PlayerProjection, ScoringFormat, TeamAssumption
from .scoring import SCORING_PROFILES, fantasy_points


def value_or_zero(value: float | None) -> float:
    return 0.0 if value is None else float(value)


def project_player(player: PlayerAssumption, team: TeamAssumption, scoring_format: ScoringFormat) -> PlayerProjection:
    targets = value_or_zero(player.targets)
    if player.targets is None and player.target_share is not None:
        targets = team.projected_pass_attempts * player.target_share
    receptions = value_or_zero(player.receptions)
    if player.receptions is None and targets and player.catch_rate is not None:
        receptions = targets * player.catch_rate
    receiving_yards = value_or_zero(player.receiving_yards)
    if player.receiving_yards is None and targets and player.yards_per_target is not None:
        receiving_yards = targets * player.yards_per_target
    receiving_tds = value_or_zero(player.receiving_tds)
    if player.receiving_tds is None and player.receiving_td_share is not None:
        receiving_tds = team.projected_passing_tds * player.receiving_td_share

    carries = value_or_zero(player.carries)
    if player.carries is None and player.rush_share is not None:
        carries = team.projected_rush_attempts * player.rush_share
    rushing_yards = value_or_zero(player.rushing_yards)
    if player.rushing_yards is None and carries and player.yards_per_carry is not None:
        rushing_yards = carries * player.yards_per_carry
    rushing_tds = value_or_zero(player.rushing_tds)
    if player.rushing_tds is None and player.rushing_td_share is not None:
        rushing_tds = team.projected_rushing_tds * player.rushing_td_share

    pass_attempts = value_or_zero(player.pass_attempts)
    if player.pass_attempts is None and player.pass_attempt_share is not None:
        pass_attempts = team.projected_pass_attempts * player.pass_attempt_share
    passing_yards = value_or_zero(player.passing_yards)
    if player.passing_yards is None:
        if player.pass_attempt_share is not None:
            passing_yards = team.projected_passing_yards * player.pass_attempt_share
        elif pass_attempts and player.passing_yards_per_attempt is not None:
            passing_yards = pass_attempts * player.passing_yards_per_attempt
    passing_tds = value_or_zero(player.passing_tds)
    if player.passing_tds is None and player.passing_td_share is not None:
        passing_tds = team.projected_passing_tds * player.passing_td_share
    interceptions = value_or_zero(player.interceptions)
    if player.interceptions is None:
        if player.pass_attempt_share is not None:
            interceptions = team.projected_interceptions * player.pass_attempt_share
        elif pass_attempts and player.interception_rate is not None:
            interceptions = pass_attempts * player.interception_rate

    raw_points = fantasy_points(
        SCORING_PROFILES[scoring_format],
        passing_yards=passing_yards,
        passing_tds=passing_tds,
        interceptions=interceptions,
        rushing_yards=rushing_yards,
        rushing_tds=rushing_tds,
        receptions=receptions,
        receiving_yards=receiving_yards,
        receiving_tds=receiving_tds,
        fumbles_lost=player.fumbles_lost,
    )
    final_points = round(raw_points + player.manual_fantasy_point_adjustment, 2)
    return PlayerProjection(
        player_id=player.player_id,
        player_name=player.player_name,
        team_id=player.team_id,
        position=player.position,
        scoring_format=scoring_format,
        include_in_rankings=player.include_in_rankings,
        games_projected=player.games_projected,
        targets=round(targets, 1),
        receptions=round(receptions, 1),
        receiving_yards=round(receiving_yards, 1),
        receiving_tds=round(receiving_tds, 1),
        carries=round(carries, 1),
        rushing_yards=round(rushing_yards, 1),
        rushing_tds=round(rushing_tds, 1),
        pass_attempts=round(pass_attempts, 1),
        passing_yards=round(passing_yards, 1),
        passing_tds=round(passing_tds, 1),
        interceptions=round(interceptions, 1),
        fumbles_lost=player.fumbles_lost,
        raw_projected_fantasy_points=raw_points,
        manual_fantasy_point_adjustment=player.manual_fantasy_point_adjustment,
        final_projected_fantasy_points=final_points,
        analyst_tag=player.analyst_tag,
        analyst_note=player.analyst_note,
    )


def project_players(
    players: list[PlayerAssumption],
    teams: list[TeamAssumption],
    scoring_format: ScoringFormat,
) -> list[PlayerProjection]:
    teams_by_id = {team.team_id: team for team in teams}
    return [project_player(player, teams_by_id[player.team_id], scoring_format) for player in players]
