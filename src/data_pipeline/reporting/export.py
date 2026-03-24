from __future__ import annotations

import json
from pathlib import Path

from data_pipeline.utils.paths import ensure_parent


def write_json(payload: dict, output_path: str | Path) -> Path:
    path = ensure_parent(output_path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
