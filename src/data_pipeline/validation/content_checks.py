from __future__ import annotations

import pandas as pd

from data_pipeline.exceptions import ValidationError


def validate_columns(df: pd.DataFrame, expected_columns: list[str], allowed_extra: list[str] | None = None) -> dict[str, list[str]]:
    allowed_extra = allowed_extra or []
    missing = sorted(set(expected_columns) - set(df.columns))
    unexpected = sorted(set(df.columns) - set(expected_columns) - set(allowed_extra))
    return {"missing": missing, "unexpected": unexpected}


def validate_required_fields(df: pd.DataFrame, required_fields: list[str]) -> dict[str, int]:
    return {col: int(df[col].isna().sum()) for col in required_fields if col in df.columns}


def validate_dtypes(df: pd.DataFrame, dtype_map: dict[str, str]) -> dict[str, str]:
    mismatches = {}
    for col, expected in dtype_map.items():
        if col in df.columns and expected not in str(df[col].dtype):
            mismatches[col] = str(df[col].dtype)
    return mismatches


def validate_domains(df: pd.DataFrame, domains: dict[str, list[str]]) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for col, allowed in domains.items():
        if col in df.columns and allowed:
            bad = sorted(set(df[col].dropna().astype(str)) - set(map(str, allowed)))
            if bad:
                errors[col] = bad
    return errors


def validate_ranges(df: pd.DataFrame, ranges: dict[str, tuple[float, float]]) -> dict[str, int]:
    issues = {}
    for col, (lower, upper) in ranges.items():
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            issues[col] = int(((s < lower) | (s > upper)).sum())
    return issues


def detect_duplicates(df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    return df[df.duplicated(subset=subset, keep=False)].copy()


def validate_primary_key(df: pd.DataFrame, key_columns: list[str]) -> None:
    duplicated = df.duplicated(subset=key_columns).any()
    if duplicated:
        raise ValidationError(f"Primary key duplicated for: {key_columns}")
