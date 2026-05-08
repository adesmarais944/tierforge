from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import PlayerAssumption, TeamAssumption


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_team_assumptions(teams: list[TeamAssumption]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for team in teams:
        rate_total = team.projected_pass_rate + team.projected_rush_rate
        if abs(rate_total - 1.0) > 0.01:
            errors.append(f"{team.team_id}: projected pass/rush rates sum to {rate_total:.3f}")
        volume_total = team.projected_pass_attempts + team.projected_rush_attempts
        if abs(volume_total - team.projected_offensive_plays) > 2:
            errors.append(
                f"{team.team_id}: projected attempts {volume_total:.1f} do not reconcile to plays "
                f"{team.projected_offensive_plays:.1f}"
            )
        if team.projected_pass_attempts <= 0:
            errors.append(f"{team.team_id}: projected_pass_attempts must be positive")
        if team.projected_rush_attempts <= 0:
            errors.append(f"{team.team_id}: projected_rush_attempts must be positive")
    return ValidationResult(errors, warnings)


def validate_player_assumptions(players: list[PlayerAssumption], teams: list[TeamAssumption]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    team_ids = {team.team_id for team in teams}
    target_shares: dict[str, float] = defaultdict(float)
    rush_shares: dict[str, float] = defaultdict(float)
    receiving_td_shares: dict[str, float] = defaultdict(float)
    rushing_td_shares: dict[str, float] = defaultdict(float)

    for player in players:
        if player.team_id not in team_ids:
            errors.append(f"{player.player_id}: unknown team_id {player.team_id}")
        if player.target_share is not None:
            target_shares[player.team_id] += player.target_share
        if player.rush_share is not None:
            rush_shares[player.team_id] += player.rush_share
        if player.receiving_td_share is not None:
            receiving_td_shares[player.team_id] += player.receiving_td_share
        if player.rushing_td_share is not None:
            rushing_td_shares[player.team_id] += player.rushing_td_share
        if player.targets is not None and player.target_share is not None:
            warnings.append(f"{player.player_id}: both targets and target_share provided; explicit targets win")
        if player.carries is not None and player.rush_share is not None:
            warnings.append(f"{player.player_id}: both carries and rush_share provided; explicit carries win")

    for team_id, share in target_shares.items():
        if abs(share - 1.0) > 0.02:
            warnings.append(f"{team_id}: target shares sum to {share:.3f}")
    for team_id, share in rush_shares.items():
        if abs(share - 1.0) > 0.02:
            warnings.append(f"{team_id}: rush shares sum to {share:.3f}")
    for team_id, share in receiving_td_shares.items():
        if share > 1.02:
            errors.append(f"{team_id}: receiving TD shares sum to {share:.3f}")
    for team_id, share in rushing_td_shares.items():
        if share > 1.02:
            errors.append(f"{team_id}: rushing TD shares sum to {share:.3f}")
    return ValidationResult(errors, warnings)


def combine_results(*results: ValidationResult) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for result in results:
        errors.extend(result.errors)
        warnings.extend(result.warnings)
    return ValidationResult(errors, warnings)
