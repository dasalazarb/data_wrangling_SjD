from __future__ import annotations

import pandas as pd


def compute_merge_metrics(merged: pd.DataFrame) -> dict[str, float | int]:
    before = len(merged)
    both = int((merged["_merge"] == "both").sum()) if "_merge" in merged.columns else 0
    left_only = int((merged["_merge"] == "left_only").sum()) if "_merge" in merged.columns else 0
    right_only = int((merged["_merge"] == "right_only").sum()) if "_merge" in merged.columns else 0
    match_rate = both / before if before else 0
    return {
        "rows_after_merge": before,
        "matched_rows": both,
        "unmatched_left": left_only,
        "unmatched_right": right_only,
        "match_rate": round(match_rate, 4),
    }
