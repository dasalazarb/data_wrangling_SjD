from pathlib import Path

import pandas as pd

from data_pipeline.orchestrator import run_pipeline


def test_pipeline_e2e(tmp_path, monkeypatch):
    monkeypatch.chdir(Path.cwd())
    raw = Path("data/raw")
    raw.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "PATIENT_RECORD_NUMBER": [1, 2],
        "SEX": ["M", "F"],
        "AGE_AT_VISIT": [20, 35],
        "VISIT_DATE": ["2025-01-01", "2025-01-02"],
    })
    df.to_excel(raw / "CTDB Data Download 15D.xlsx", index=False)
    df.to_excel(raw / "CTDB Data Download 11D.xlsx", index=False)

    codebook = pd.DataFrame({
        "QUESTION_NAME": ["PATIENT_RECORD_NUMBER", "SEX", "AGE_AT_VISIT", "VISIT_DATE"],
        "final_answer_format": ["int", "object", "float", "datetime"],
        "final_display_options": [None, "M|F", None, None],
        "needs_review": [False, False, False, False],
    })
    sample_raw = Path("sample_data/raw")
    sample_raw.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(sample_raw / "codebook_final_harmonized_once_quince.xlsx") as w:
        codebook.to_excel(w, sheet_name="final_codebook", index=False)

    summary = run_pipeline("configs/pipeline.yaml")
    assert summary["artifacts_generated"] >= 1
