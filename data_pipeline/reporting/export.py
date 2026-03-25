from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from data_pipeline.utils.paths import ensure_parent


def write_json(payload: dict, output_path: str | Path) -> Path:
    path = ensure_parent(output_path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_dict_xlsx(payload: dict, output_path: str | Path, sheet_name: str = "summary") -> Path:
    rows = []
    for key, value in payload.items():
        serialized = value
        if isinstance(value, (dict, list, tuple, set)):
            serialized = json.dumps(value, ensure_ascii=False)
        rows.append({"key": key, "value": serialized})
    df = pd.DataFrame(rows)
    return write_dataframe_xlsx(df, output_path, sheet_name=sheet_name)


def write_dataframe_xlsx(df: pd.DataFrame, output_path: str | Path, sheet_name: str = "data") -> Path:
    path = ensure_parent(output_path)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return path
