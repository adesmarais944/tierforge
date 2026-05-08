from __future__ import annotations

from collections import defaultdict

from .models import PlayerProjection


def rank_players(projections: list[PlayerProjection]) -> list[PlayerProjection]:
    ranked = sorted(
        [p for p in projections if p.include_in_rankings],
        key=lambda p: (-p.final_projected_fantasy_points, p.player_name),
    )
    position_counts: dict[str, int] = defaultdict(int)
    out: list[PlayerProjection] = []
    for overall_index, projection in enumerate(ranked, start=1):
        position_counts[projection.position] += 1
        updated = projection.model_copy(
            update={
                "overall_rank": overall_index,
                "position_rank": position_counts[projection.position],
            }
        )
        out.append(updated)
    return out
