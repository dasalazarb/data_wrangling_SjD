import pandas as pd

from data_pipeline.transform.standardize import standardize_names


def test_standardize_names(sample_df):
    df = sample_df.rename(columns={"VISIT_DATE": "Visit Date"})
    out = standardize_names(df)
    assert "VISIT_DATE" in out.columns


def test_standardize_names_deduplicates_collisions():
    df = pd.DataFrame({"A-B": [1], "A B": [2], "a_b": [3]})

    out = standardize_names(df)

    assert list(out.columns) == ["A_B", "A_B__2", "A_B__3"]
