from __future__ import annotations

from pathlib import Path
from typing import Type, TypeVar

import pandas as pd
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def season_projection_dir(root: Path, season: str) -> Path:
    return root / "seasons" / season / "data" / "projections"


def clean_records(path: Path) -> list[dict]:
    frame = pd.read_csv(path, keep_default_na=False)
    records = []
    for row in frame.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if value == "":
                clean[key] = None
            else:
                clean[key] = value
        records.append(clean)
    return records


def load_models(path: Path, model: Type[T]) -> list[T]:
    return [model(**{k: v for k, v in record.items() if v is not None}) for record in clean_records(path)]
