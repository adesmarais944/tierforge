from tierforge.projections.models import OffseasonChange
from tierforge.projections.offseason_changes import aggregate_unit_scores, weighted_impact


def change(raw=4):
    return OffseasonChange(
        team_id="CIN",
        season=2026,
        unit="defense",
        change_type="addition",
        player_or_coach="Test Player",
        transaction_type="free_agency",
        expected_role="starter",
        impact_timing="immediate",
        certainty="high",
        unit_need_level="critical",
        position_value="high",
        scheme_fit="good",
        raw_impact_score=raw,
    )


def test_offseason_weighted_impact_scoring():
    assert weighted_impact(change()) == 5.78


def test_defense_change_score_aggregation_clamps():
    scores = aggregate_unit_scores([change(raw=8), change(raw=8)])
    assert scores[("CIN", "defense")] == 10
