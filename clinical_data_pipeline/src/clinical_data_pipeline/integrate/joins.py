from __future__ import annotations

import pandas as pd


def perform_merge(left: pd.DataFrame, right: pd.DataFrame, keys: list[str], how: str = "outer") -> pd.DataFrame:
    return left.merge(right, on=keys, how=how, indicator=True, suffixes=("_15D", "_11D"))
