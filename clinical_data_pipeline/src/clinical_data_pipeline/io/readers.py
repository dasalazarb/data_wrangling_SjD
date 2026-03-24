from __future__ import annotations

from pathlib import Path

import pandas as pd

from clinical_data_pipeline.models import FileMetadata
from clinical_data_pipeline.utils.hashes import compute_file_hash


def read_dataset(file_path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet_name)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def collect_file_metadata(file_path: str | Path, df: pd.DataFrame) -> FileMetadata:
    path = Path(file_path)
    return FileMetadata(
        name=path.name,
        path=str(path.resolve()),
        size_bytes=path.stat().st_size,
        sha256=compute_file_hash(path),
        extension=path.suffix.lower(),
        read_timestamp=pd.Timestamp.utcnow().isoformat(),
        row_count=len(df),
        column_count=len(df.columns),
    )
