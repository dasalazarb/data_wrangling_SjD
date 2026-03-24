from __future__ import annotations

import pandas as pd


def normalize_categories(df: pd.DataFrame, category_maps: dict[str, dict[str, str]]) -> pd.DataFrame:
    out = df.copy()
    for col, mapping in category_maps.items():
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip().replace(mapping)
    return out
