from __future__ import annotations

import pandas as pd


def parse_dates_safely(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in date_columns:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out
