from clinical_data_pipeline.io.readers import collect_file_metadata, read_dataset


def test_read_dataset_csv(tmp_csv):
    df = read_dataset(tmp_csv)
    assert len(df) == 2


def test_collect_file_metadata(tmp_csv):
    df = read_dataset(tmp_csv)
    meta = collect_file_metadata(tmp_csv, df)
    assert meta.row_count == 2
    assert len(meta.sha256) == 64
