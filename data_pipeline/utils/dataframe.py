from __future__ import annotations

import re

import pandas as pd


def normalize_column_name(col: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", col.strip())
    return re.sub(r"_+", "_", cleaned).strip("_").upper()


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [normalize_column_name(c) for c in out.columns]
    return out
