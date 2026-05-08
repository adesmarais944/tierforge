import shutil
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
    diffs = apply_macro_recommendations(root, "2026", "CIN", "volume")
    changed_fields = {diff.field for diff in diffs if diff.changed}
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    text = path.read_text()
    assert changed_fields == {
        "projected_offensive_plays",
        "projected_pass_rate",
        "projected_rush_rate",
        "projected_pass_attempts",
        "projected_rush_attempts",
    }
    assert "1085,0.606,0.394,658,427,4500,34,10,1650,14" in text


def test_apply_all_updates_volume_and_efficiency_fields(tmp_path):
    root = copy_projection_fixture(tmp_path)
    apply_macro_recommendations(root, "2026", "CIN", "all")
    path = root / "seasons" / "2026" / "data" / "projections" / "raw" / "team_assumptions.csv"
    text = path.read_text()
    assert "1085,0.606,0.394,658,427,4442,35,16,1824,14" in text


def test_render_macro_diffs_marks_changed_fields():
    rendered = render_macro_diffs("CIN", "volume", build_macro_diffs(Path(__file__).resolve().parents[1], "2026", "CIN", "volume"))
    assert "Team macro recommendation diff: CIN (volume)" in rendered
    assert "* projected_offensive_plays" in rendered
