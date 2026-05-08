from __future__ import annotations

from collections import defaultdict

from .models import OffseasonChange

ROLE_MULTIPLIERS = {
    "elite_starter": 1.30,
    "starter": 1.00,
    "rotational": 0.60,
    "depth": 0.30,
    "developmental": 0.20,
    "unknown": 0.40,
}
CERTAINTY_MULTIPLIERS = {"high": 1.00, "medium": 0.75, "low": 0.50}
NEED_MULTIPLIERS = {"critical": 1.25, "high": 1.10, "medium": 1.00, "low": 0.85}
POSITION_VALUE_MULTIPLIERS = {"high": 1.10, "medium": 1.00, "low": 0.90}
SCHEME_FIT_MULTIPLIERS = {"excellent": 1.15, "good": 1.05, "neutral": 1.00, "poor": 0.75}


def weighted_impact(change: OffseasonChange) -> float:
    score = change.raw_impact_score
    score *= ROLE_MULTIPLIERS[change.expected_role]
    score *= CERTAINTY_MULTIPLIERS[change.certainty]
    score *= NEED_MULTIPLIERS[change.unit_need_level]
    score *= POSITION_VALUE_MULTIPLIERS[change.position_value]
    score *= SCHEME_FIT_MULTIPLIERS[change.scheme_fit]
    return round(score, 2)


def clamp_unit_score(score: float) -> float:
    return round(max(-10.0, min(10.0, score)), 2)


def aggregate_unit_scores(changes: list[OffseasonChange]) -> dict[tuple[str, str], float]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    for change in changes:
        score = change.weighted_impact_score
        if score is None:
            score = weighted_impact(change)
        totals[(change.team_id, change.unit)] += score
    return {key: clamp_unit_score(value) for key, value in totals.items()}
