from __future__ import annotations

from pathlib import Path

import pandas as pd

from clinical_data_pipeline.utils.paths import ensure_parent


def write_parquet(df: pd.DataFrame, output_path: str | Path) -> Path:
    path = ensure_parent(output_path)
    df.to_parquet(path, index=False)
    return path


def write_excel(df: pd.DataFrame, output_path: str | Path) -> Path:
    path = ensure_parent(output_path)
    df.to_excel(path, index=False)
    return path
