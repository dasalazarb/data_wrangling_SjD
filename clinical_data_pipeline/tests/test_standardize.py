from clinical_data_pipeline.transform.standardize import standardize_names


def test_standardize_names(sample_df):
    df = sample_df.rename(columns={"VISIT_DATE": "Visit Date"})
    out = standardize_names(df)
    assert "VISIT_DATE" in out.columns
