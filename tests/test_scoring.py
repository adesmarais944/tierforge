from tierforge.projections.scoring import SCORING_PROFILES, fantasy_points


def test_half_ppr_receiving_points():
    points = fantasy_points(SCORING_PROFILES["half_ppr"], receptions=100, receiving_yards=1000, receiving_tds=8)
    assert points == 198


def test_full_ppr_receiving_points():
    points = fantasy_points(SCORING_PROFILES["full_ppr"], receptions=100, receiving_yards=1000, receiving_tds=8)
    assert points == 248


def test_qb_passing_points():
    points = fantasy_points(SCORING_PROFILES["half_ppr"], passing_yards=4000, passing_tds=30, interceptions=10)
    assert points == 260


def test_rushing_points():
    points = fantasy_points(SCORING_PROFILES["half_ppr"], rushing_yards=1000, rushing_tds=10)
    assert points == 160
