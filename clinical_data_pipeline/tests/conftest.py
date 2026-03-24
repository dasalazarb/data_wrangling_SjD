from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PATIENT_RECORD_NUMBER": [1, 2],
            "SEX": ["M", "F"],
            "AGE_AT_VISIT": [30, 42],
            "VISIT_DATE": ["2025-01-01", "2025-01-03"],
        }
    )


@pytest.fixture()
def tmp_csv(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    p = tmp_path / "sample.csv"
    sample_df.to_csv(p, index=False)
    return p
