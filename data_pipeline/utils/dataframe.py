from __future__ import annotations

import re

import pandas as pd


def normalize_column_name(col: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", col.strip())
    return re.sub(r"_+", "_", cleaned).strip("_").upper()


def _deduplicate_column_names(columns: list[str]) -> list[str]:
    """Return unique column names while preserving order.

    The first occurrence keeps its name. Subsequent duplicates receive
    a numeric suffix (e.g. ``COL__2``, ``COL__3``).
    """
    seen: dict[str, int] = {}
    unique: list[str] = []

    for col in columns:
        seen[col] = seen.get(col, 0) + 1
        if seen[col] == 1:
            unique.append(col)
        else:
            unique.append(f"{col}__{seen[col]}")

    return unique


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    normalized = [normalize_column_name(c) for c in out.columns]
    out.columns = _deduplicate_column_names(normalized)
    return out
