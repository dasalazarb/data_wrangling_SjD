from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from data_pipeline.models import RunContext
from data_pipeline.utils.paths import ensure_parent


def write_run_manifest(context: RunContext, output_path: str | Path, extra: dict[str, Any] | None = None) -> Path:
    payload = {
        "run_id": context.run_id,
        "start_time": context.start_time.isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "artifacts": context.artifacts,
        "warnings": context.warnings,
        "errors": context.errors,
        "counts": context.counts,
    }
    if extra:
        payload.update(extra)
    path = ensure_parent(output_path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
