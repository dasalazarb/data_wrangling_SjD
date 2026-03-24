from __future__ import annotations

from pathlib import Path

import pandas as pd

from clinical_data_pipeline.io.writers import write_excel


def write_quality_report(rows: list[dict], output_path: str | Path) -> Path:
    return write_excel(pd.DataFrame(rows), output_path)
