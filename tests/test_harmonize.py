from data_pipeline.transform.harmonize import harmonize_variables


def test_harmonize_variables(sample_df):
    out, trace = harmonize_variables(sample_df, {"SEX": "SEX_AT_BIRTH"}, "15D")
    assert "SEX_AT_BIRTH" in out.columns
    assert len(trace) == 1
