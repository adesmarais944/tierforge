from pathlib import Path

import pandas as pd

from tierforge.projections.engine import build_outputs


def test_csv_export_column_order():
    root = Path(__file__).resolve().parents[1]
    projections_path, _rankings_path = build_outputs(root, "2026", "half_ppr")
    columns = list(pd.read_csv(projections_path).columns)
    assert columns[:8] == [
        "player_id",
        "player_name",
        "team_id",
        "position",
        "scoring_format",
        "include_in_rankings",
        "games_projected",
        "targets",
    ]
