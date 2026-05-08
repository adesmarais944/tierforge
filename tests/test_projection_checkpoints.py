import csv
from pathlib import Path

from tierforge.projections.checkpoints import (
    diff_against_checkpoint,
    render_diffs,
    team_status,
    write_checkpoint,
)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def projection_root(tmp_path: Path) -> Path:
    root = tmp_path
    base = root / "seasons" / "2026" / "data" / "projections"
    write_csv(
        base / "raw" / "team_assumptions.csv",
        [{"team_id": "GB", "projected_pass_attempts": "580"}],
    )
    write_csv(base / "raw" / "defense_environment.csv", [{"team_id": "GB", "projected_defense_quality": "average"}])
    write_csv(
        base / "raw" / "player_assumptions.csv",
        [
            {
                "player_id": "wr",
                "team_id": "GB",
                "include_in_rankings": "true",
                "target_share": "0.25",
                "rush_share": "",
                "receiving_td_share": "0.30",
                "rushing_td_share": "",
            },
            {
                "player_id": "rb",
                "team_id": "GB",
                "include_in_rankings": "true",
                "target_share": "0.10",
                "rush_share": "0.55",
                "receiving_td_share": "0.05",
                "rushing_td_share": "0.60",
            },
        ],
    )
    write_csv(
        base / "raw" / "offseason_team_changes.csv",
        [{"team_id": "GB", "unit": "offense", "player_or_coach": "Starter", "transaction_type": "signing"}],
    )
    write_csv(base / "processed" / "team_macro_recommendations.csv", [{"team_id": "GB"}])
    write_csv(base / "processed" / "player_projections_half_ppr.csv", [{"player_id": "wr", "team_id": "GB"}])
    write_csv(base / "processed" / "player_rankings_half_ppr.csv", [{"player_id": "wr", "team_id": "GB"}])
    return root


def test_write_checkpoint_and_diff_rows(tmp_path):
    root = projection_root(tmp_path)
    path = write_checkpoint(root, "2026", "baseline")

    assert path.exists()

    write_csv(
        root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv",
        [{"team_id": "GB", "projected_pass_attempts": "590"}],
    )

    diffs = diff_against_checkpoint(root, "2026", "latest")
    assert [diff.path for diff in diffs] == ["raw/team_assumptions.csv"]
    assert diffs[0].changed_keys == ["GB"]
    assert "changed: raw/team_assumptions.csv" in render_diffs(diffs)


def test_team_status_reports_completion_and_share_totals(tmp_path):
    root = projection_root(tmp_path)
    write_checkpoint(root, "2026", "baseline")

    status = team_status(root, "2026", "GB")

    assert status["team_assumptions"] is True
    assert status["defense_environment"] is True
    assert status["macro_recommendations"] is True
    assert status["offseason_changes"] == 1
    assert status["player_rows"] == 2
    assert status["target_share_total"] == 0.35
    assert status["rush_share_total"] == 0.55
    assert status["receiving_td_share_total"] == 0.35
    assert status["rushing_td_share_total"] == 0.6
    assert status["latest_checkpoint"].endswith(".json")
