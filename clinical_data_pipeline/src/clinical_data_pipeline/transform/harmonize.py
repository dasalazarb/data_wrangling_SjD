from __future__ import annotations

import pandas as pd


def harmonize_variables(df: pd.DataFrame, mappings: dict[str, str], study_id: str, needs_review: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.rename(columns=mappings).copy()
    trace = []
    needs_review = needs_review or []
    for original, harmonized in mappings.items():
        trace.append(
            {
                "variable_original": original,
                "variable_harmonized": harmonized,
                "study_origin": study_id,
                "rule_applied": "column_mapping",
                "observations": "needs_review" if original in needs_review else "ok",
            }
        )
    for col in needs_review:
        if col in out.columns:
            out[f"{col}_NEEDS_REVIEW"] = True
    return out, pd.DataFrame(trace)
