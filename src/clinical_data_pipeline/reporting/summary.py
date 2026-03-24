from __future__ import annotations

from datetime import datetime

from clinical_data_pipeline.models import RunContext


def build_final_summary(context: RunContext) -> dict:
    return {
        "run_id": context.run_id,
        "finished_at": datetime.utcnow().isoformat(),
        "artifacts_generated": len(context.artifacts),
        "warnings": len(context.warnings),
        "errors": len(context.errors),
        "counts": context.counts,
    }
