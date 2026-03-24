import pytest

from data_pipeline.validation.file_checks import validate_file_exists


def test_validate_file_exists(tmp_csv):
    validate_file_exists(tmp_csv)


def test_validate_file_missing():
    with pytest.raises(Exception):
        validate_file_exists("missing.csv")
