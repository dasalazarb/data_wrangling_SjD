from __future__ import annotations

import pandas as pd

from data_pipeline.utils.dataframe import standardize_columns


def standardize_names(df: pd.DataFrame) -> pd.DataFrame:
    return standardize_columns(df)


def cast_columns(df: pd.DataFrame, cast_map: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    for col, dtype in cast_map.items():
        if col in out.columns:
            if dtype == "datetime":
                out[col] = pd.to_datetime(out[col], errors="coerce")
            else:
                out[col] = out[col].astype(dtype, errors="ignore")
    return out
