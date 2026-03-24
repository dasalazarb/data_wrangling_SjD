from clinical_data_pipeline.integrate.joins import perform_merge
from clinical_data_pipeline.integrate.metrics import compute_merge_metrics


def test_perform_merge(sample_df):
    right = sample_df.copy()
    merged = perform_merge(sample_df, right, ["PATIENT_RECORD_NUMBER"])
    metrics = compute_merge_metrics(merged)
    assert metrics["matched_rows"] == 2
