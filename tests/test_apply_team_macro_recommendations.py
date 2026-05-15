import shutil
import subprocess
import sys
import csv
from pathlib import Path

from tierforge.projections.apply_team_macro import (
    apply_macro_recommendations,
    build_macro_diffs,
    render_macro_diffs,
)


def copy_projection_fixture(tmp_path: Path) -> Path:
    source = Path(__file__).resolve().parents[1] / "seasons" / "2026" / "data" / "projections"
    target = tmp_path / "seasons" / "2026" / "data" / "projections"
    shutil.copytree(source, target)
    return tmp_path


def make_cin_volume_stale(root: Path) -> None:
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    text = path.read_text()
    text = text.replace("1085,0.606,0.394,658,427", "1000,0.600,0.400,600,400")
    path.write_text(text)


def test_dry_run_diff_does_not_mutate_team_assumptions(tmp_path):
    root = copy_projection_fixture(tmp_path)
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    before = path.read_text()
    diffs = build_macro_diffs(root, "2026", "CIN", "volume")
    after = path.read_text()
    assert diffs
    assert after == before


def test_apply_volume_updates_only_volume_fields(tmp_path):
    root = copy_projection_fixture(tmp_path)
    original_path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    with original_path.open(newline="", encoding="utf-8") as handle:
        original_cin = next(row for row in csv.DictReader(handle) if row["team_id"] == "CIN")
    make_cin_volume_stale(root)
    diffs = apply_macro_recommendations(root, "2026", "CIN", "volume")
    changed_fields = {diff.field for diff in diffs if diff.changed}
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        team_row = next(row for row in csv.DictReader(handle) if row["team_id"] == "CIN")
    assert changed_fields == {
        "projected_offensive_plays",
        "projected_pass_rate",
        "projected_rush_rate",
        "projected_pass_attempts",
        "projected_rush_attempts",
    }
    assert team_row["projected_passing_yards"] == original_cin["projected_passing_yards"]
    assert team_row["projected_rushing_yards"] == original_cin["projected_rushing_yards"]


def test_apply_all_updates_volume_and_efficiency_fields(tmp_path):
    root = copy_projection_fixture(tmp_path)
    apply_macro_recommendations(root, "2026", "CIN", "all")
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    macro_path = root / "seasons" / "2026" / "data" / "projections" / "processed" / "team_macro_recommendations.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        team_row = next(row for row in csv.DictReader(handle) if row["team_id"] == "CIN")
    with macro_path.open(newline="", encoding="utf-8") as handle:
        macro_row = next(row for row in csv.DictReader(handle) if row["team_id"] == "CIN")
    assert team_row["projected_passing_yards"] == str(int(round(float(macro_row["recommended_passing_yards"]))))
    assert team_row["projected_rushing_yards"] == str(int(round(float(macro_row["recommended_rushing_yards"]))))


def test_render_macro_diffs_marks_changed_fields():
    root = Path(__file__).resolve().parents[1]
    rendered = render_macro_diffs("GB", "volume", build_macro_diffs(root, "2026", "GB", "volume"))
    assert "Team macro recommendation diff: GB (volume)" in rendered
    assert "projected_offensive_plays" in rendered


def test_accept_cli_requires_human_approval():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "apply_team_macro_recommendations.py"),
            "--season",
            "2026",
            "--team",
            "CIN",
            "--accept",
            "volume",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--accept requires --human-approved" in result.stderr
