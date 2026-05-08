from tierforge.projections.models import PlayerAssumption
from tierforge.projections.player_projection import project_player
from tierforge.projections.rankings import rank_players
from tests.test_validation import team


def test_target_share_to_targets_conversion():
    projection = project_player(
        PlayerAssumption(
            player_id="wr",
            player_name="WR",
            team_id="CIN",
            position="WR",
            target_share=0.25,
            catch_rate=0.6,
            yards_per_target=8,
            receiving_td_share=0.2,
        ),
        team(),
        "half_ppr",
    )
    assert projection.targets == 150


def test_rush_share_to_carries_conversion():
    projection = project_player(
        PlayerAssumption(
            player_id="rb",
            player_name="RB",
            team_id="CIN",
            position="RB",
            rush_share=0.5,
            yards_per_carry=4,
            rushing_td_share=0.5,
        ),
        team(),
        "half_ppr",
    )
    assert projection.carries == 200


def test_manual_fantasy_point_adjustment():
    projection = project_player(
        PlayerAssumption(
            player_id="wr",
            player_name="WR",
            team_id="CIN",
            position="WR",
            receptions=10,
            receiving_yards=100,
            manual_fantasy_point_adjustment=3,
        ),
        team(),
        "half_ppr",
    )
    assert projection.raw_projected_fantasy_points == 15
    assert projection.final_projected_fantasy_points == 18


def test_ranking_sort_order():
    low = project_player(
        PlayerAssumption(player_id="low", player_name="Low", team_id="CIN", position="WR", receptions=1),
        team(),
        "half_ppr",
    )
    high = project_player(
        PlayerAssumption(player_id="high", player_name="High", team_id="CIN", position="WR", receptions=10),
        team(),
        "half_ppr",
    )
    ranked = rank_players([low, high])
    assert ranked[0].player_id == "high"
    assert ranked[0].overall_rank == 1
    assert ranked[0].position_rank == 1
