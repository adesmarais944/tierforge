from tierforge.projections.models import PlayerAssumption, TeamAssumption
from tierforge.projections.validation import validate_player_assumptions, validate_team_assumptions


def team():
    return TeamAssumption(
        team_id="CIN",
        season=2026,
        team_name="Cincinnati Bengals",
        head_coach="Zac Taylor",
        offensive_coordinator="Dan Pitcher",
        starting_qb="Joe Burrow",
        prior_year_offensive_plays=1000,
        prior_year_pass_attempts=600,
        prior_year_rush_attempts=400,
        prior_year_pass_rate=0.6,
        prior_year_rush_rate=0.4,
        prior_year_points_scored=400,
        prior_year_offensive_tds=45,
        projected_offensive_plays=1000,
        projected_pass_rate=0.6,
        projected_rush_rate=0.4,
        projected_pass_attempts=600,
        projected_rush_attempts=400,
        projected_passing_yards=4200,
        projected_passing_tds=30,
        projected_interceptions=10,
        projected_rushing_yards=1600,
        projected_rushing_tds=12,
    )


def test_pass_rate_and_rush_rate_validation():
    bad = team().model_copy(update={"projected_pass_rate": 0.7, "projected_rush_rate": 0.4})
    result = validate_team_assumptions([bad])
    assert result.errors


def test_team_pass_rush_attempts_reconciliation():
    bad = team().model_copy(update={"projected_pass_attempts": 500})
    result = validate_team_assumptions([bad])
    assert result.errors


def test_receiving_td_share_validation():
    players = [
        PlayerAssumption(player_id="a", player_name="A", team_id="CIN", position="WR", receiving_td_share=0.7),
        PlayerAssumption(player_id="b", player_name="B", team_id="CIN", position="WR", receiving_td_share=0.5),
    ]
    result = validate_player_assumptions(players, [team()])
    assert result.errors


def test_rushing_td_share_validation():
    players = [
        PlayerAssumption(player_id="a", player_name="A", team_id="CIN", position="RB", rushing_td_share=0.8),
        PlayerAssumption(player_id="b", player_name="B", team_id="CIN", position="RB", rushing_td_share=0.3),
    ]
    result = validate_player_assumptions(players, [team()])
    assert result.errors
