from __future__ import annotations

import pandas as pd


def derive_age_group(df: pd.DataFrame, age_col: str = "AGE_AT_VISIT") -> pd.DataFrame:
    out = df.copy()
    if age_col in out.columns:
        age = pd.to_numeric(out[age_col], errors="coerce")
        out["AGE_GROUP"] = pd.cut(age, bins=[0, 17, 39, 64, 200], labels=["child", "young_adult", "adult", "senior"])
    return out
