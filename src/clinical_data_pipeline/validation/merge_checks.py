from __future__ import annotations

import pandas as pd

from clinical_data_pipeline.exceptions import ValidationError


def validate_merge_keys(left: pd.DataFrame, right: pd.DataFrame, keys: list[str]) -> None:
    missing_left = [k for k in keys if k not in left.columns]
    missing_right = [k for k in keys if k not in right.columns]
    if missing_left or missing_right:
        raise ValidationError(f"Missing merge keys. left={missing_left}, right={missing_right}")
