import pandas as pd

from data_pipeline.validation.content_checks import validate_columns, validate_required_fields


def test_validate_columns(sample_df):
    out = validate_columns(sample_df, ["PATIENT_RECORD_NUMBER", "SEX"])
    assert out["missing"] == []


def test_validate_required_fields(sample_df):
    sample_df.loc[0, "PATIENT_RECORD_NUMBER"] = None
    out = validate_required_fields(sample_df, ["PATIENT_RECORD_NUMBER"])
    assert out["PATIENT_RECORD_NUMBER"] == 1
