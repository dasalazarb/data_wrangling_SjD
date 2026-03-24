from __future__ import annotations

from pathlib import Path

from clinical_data_pipeline.exceptions import ValidationError


def validate_file_exists(file_path: str | Path) -> None:
    if not Path(file_path).exists():
        raise ValidationError(f"Input file does not exist: {file_path}")
