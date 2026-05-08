from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .load_inputs import season_projection_dir


SNAPSHOT_RELATIVE_PATHS = [
    "raw/team_assumptions.csv",
    "raw/defense_environment.csv",
    "raw/offseason_team_changes.csv",
    "raw/player_assumptions.csv",
    "raw/news_events.csv",
    "processed/team_macro_recommendations.csv",
    "processed/offseason_unit_scores.csv",
    "processed/player_projections_half_ppr.csv",
    "processed/player_projections_full_ppr.csv",
    "processed/player_rankings_half_ppr.csv",
    "processed/player_rankings_full_ppr.csv",
]

TEAM_STATUS_RELATIVE_PATHS = [
    "raw/team_assumptions.csv",
    "raw/defense_environment.csv",
    "raw/player_assumptions.csv",
    "raw/offseason_team_changes.csv",
    "processed/team_macro_recommendations.csv",
    "processed/player_projections_half_ppr.csv",
    "processed/player_rankings_half_ppr.csv",
]


@dataclass(frozen=True)
class FileDiff:
    path: str
    status: str
    old_hash: str | None = None
    new_hash: str | None = None
    added_keys: list[str] | None = None
    removed_keys: list[str] | None = None
    changed_keys: list[str] | None = None


def checkpoints_dir(root: Path, season: str) -> Path:
    return season_projection_dir(root, season) / "checkpoints"


def checkpoint_path(root: Path, season: str, checkpoint_id: str) -> Path:
    return checkpoints_dir(root, season) / f"{checkpoint_id}.json"


def latest_checkpoint_path(root: Path, season: str) -> Path | None:
    directory = checkpoints_dir(root, season)
    if not directory.exists():
        return None
    checkpoints = sorted(directory.glob("*.json"))
    return checkpoints[-1] if checkpoints else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_row(row: dict[str, str]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def row_key(row: dict[str, str], fallback_index: int) -> str:
    for fields in (
        ("team_id", "unit", "player_id", "scoring_format"),
        ("team_id", "unit", "player_or_coach", "transaction_type", "position"),
        ("player_id", "scoring_format"),
        ("player_id",),
        ("team_id",),
    ):
        if all(field in row and row[field] != "" for field in fields):
            return "|".join(row[field] for field in fields)
    return f"row:{fallback_index}"


def csv_row_hashes(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        hashes = {}
        for index, row in enumerate(reader, start=1):
            hashes[row_key(row, index)] = hashlib.sha256(normalize_row(row).encode("utf-8")).hexdigest()
        return hashes


def file_snapshot(base_dir: Path, relative_path: str) -> dict[str, Any]:
    path = base_dir / relative_path
    if not path.exists():
        return {"path": relative_path, "exists": False}

    snapshot: dict[str, Any] = {
        "path": relative_path,
        "exists": True,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    if path.suffix.lower() == ".csv":
        row_hashes = csv_row_hashes(path)
        snapshot["row_count"] = len(row_hashes)
        snapshot["row_hashes"] = row_hashes
    return snapshot


def build_snapshot(root: Path, season: str, note: str = "") -> dict[str, Any]:
    base_dir = season_projection_dir(root, season)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    checkpoint_id = created_at.replace(":", "").replace("-", "")
    return {
        "checkpoint_id": checkpoint_id,
        "season": season,
        "created_at": created_at,
        "note": note,
        "files": {relative_path: file_snapshot(base_dir, relative_path) for relative_path in SNAPSHOT_RELATIVE_PATHS},
    }


def write_checkpoint(root: Path, season: str, note: str = "") -> Path:
    snapshot = build_snapshot(root, season, note)
    directory = checkpoints_dir(root, season)
    directory.mkdir(parents=True, exist_ok=True)
    path = checkpoint_path(root, season, snapshot["checkpoint_id"])
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_checkpoint(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_checkpoint(root: Path, season: str, checkpoint: str) -> Path:
    if checkpoint == "latest":
        path = latest_checkpoint_path(root, season)
        if path is None:
            raise ValueError(f"No checkpoints found for season {season}")
        return path

    path = Path(checkpoint)
    if path.exists():
        return path

    candidate = checkpoint_path(root, season, checkpoint.removesuffix(".json"))
    if candidate.exists():
        return candidate

    raise ValueError(f"Checkpoint not found: {checkpoint}")


def diff_against_checkpoint(root: Path, season: str, checkpoint: str = "latest") -> list[FileDiff]:
    path = resolve_checkpoint(root, season, checkpoint)
    old_snapshot = read_checkpoint(path)
    current_snapshot = build_snapshot(root, season, note="")
    diffs: list[FileDiff] = []

    all_paths = sorted(set(old_snapshot["files"]) | set(current_snapshot["files"]))
    for relative_path in all_paths:
        old_file = old_snapshot["files"].get(relative_path, {"exists": False})
        new_file = current_snapshot["files"].get(relative_path, {"exists": False})
        if not old_file.get("exists") and not new_file.get("exists"):
            continue
        if not old_file.get("exists"):
            diffs.append(FileDiff(path=relative_path, status="added", new_hash=new_file.get("sha256")))
            continue
        if not new_file.get("exists"):
            diffs.append(FileDiff(path=relative_path, status="removed", old_hash=old_file.get("sha256")))
            continue
        if old_file.get("sha256") == new_file.get("sha256"):
            continue

        old_rows = old_file.get("row_hashes", {})
        new_rows = new_file.get("row_hashes", {})
        added = sorted(set(new_rows) - set(old_rows))
        removed = sorted(set(old_rows) - set(new_rows))
        changed = sorted(key for key in set(old_rows) & set(new_rows) if old_rows[key] != new_rows[key])
        diffs.append(
            FileDiff(
                path=relative_path,
                status="changed",
                old_hash=old_file.get("sha256"),
                new_hash=new_file.get("sha256"),
                added_keys=added,
                removed_keys=removed,
                changed_keys=changed,
            )
        )
    return diffs


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def find_team_row(rows: list[dict[str, str]], team_id: str) -> dict[str, str] | None:
    return next((row for row in rows if row.get("team_id") == team_id), None)


def numeric(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def team_status(root: Path, season: str, team_id: str) -> dict[str, Any]:
    base_dir = season_projection_dir(root, season)
    rows = {relative_path: read_csv_dicts(base_dir / relative_path) for relative_path in TEAM_STATUS_RELATIVE_PATHS}
    players = [row for row in rows["raw/player_assumptions.csv"] if row.get("team_id") == team_id]
    target_share = sum(numeric(row.get("target_share")) for row in players)
    rush_share = sum(numeric(row.get("rush_share")) for row in players)
    receiving_td_share = sum(numeric(row.get("receiving_td_share")) for row in players)
    rushing_td_share = sum(numeric(row.get("rushing_td_share")) for row in players)
    latest = latest_checkpoint_path(root, season)

    return {
        "season": season,
        "team_id": team_id,
        "team_assumptions": find_team_row(rows["raw/team_assumptions.csv"], team_id) is not None,
        "defense_environment": find_team_row(rows["raw/defense_environment.csv"], team_id) is not None,
        "macro_recommendations": find_team_row(rows["processed/team_macro_recommendations.csv"], team_id) is not None,
        "offseason_changes": sum(1 for row in rows["raw/offseason_team_changes.csv"] if row.get("team_id") == team_id),
        "player_rows": len(players),
        "included_player_rows": sum(1 for row in players if row.get("include_in_rankings", "true").lower() == "true"),
        "target_share_total": round(target_share, 3),
        "rush_share_total": round(rush_share, 3),
        "receiving_td_share_total": round(receiving_td_share, 3),
        "rushing_td_share_total": round(rushing_td_share, 3),
        "half_ppr_projection_rows": sum(1 for row in rows["processed/player_projections_half_ppr.csv"] if row.get("team_id") == team_id),
        "half_ppr_ranking_rows": sum(1 for row in rows["processed/player_rankings_half_ppr.csv"] if row.get("team_id") == team_id),
        "latest_checkpoint": latest.name if latest else "",
    }


def render_status(status: dict[str, Any]) -> str:
    lines = [f"Team projection status: {status['team_id']} ({status['season']})", ""]
    for key in (
        "team_assumptions",
        "defense_environment",
        "macro_recommendations",
        "offseason_changes",
        "player_rows",
        "included_player_rows",
        "target_share_total",
        "rush_share_total",
        "receiving_td_share_total",
        "rushing_td_share_total",
        "half_ppr_projection_rows",
        "half_ppr_ranking_rows",
        "latest_checkpoint",
    ):
        lines.append(f"{key}: {status[key]}")
    return "\n".join(lines)


def render_diffs(diffs: list[FileDiff]) -> str:
    if not diffs:
        return "No projection checkpoint differences."

    lines = ["Projection checkpoint differences:", ""]
    for diff in diffs:
        lines.append(f"{diff.status}: {diff.path}")
        for label, values in (
            ("added", diff.added_keys),
            ("removed", diff.removed_keys),
            ("changed", diff.changed_keys),
        ):
            if values:
                preview = ", ".join(values[:12])
                suffix = "" if len(values) <= 12 else f", ... (+{len(values) - 12} more)"
                lines.append(f"  {label} rows: {preview}{suffix}")
    return "\n".join(lines)
