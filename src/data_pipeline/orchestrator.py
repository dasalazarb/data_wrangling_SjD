from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from data_pipeline.integrate.joins import perform_merge
from data_pipeline.integrate.metrics import compute_merge_metrics
from data_pipeline.io.manifest import write_run_manifest
from data_pipeline.io.readers import collect_file_metadata, read_dataset
from data_pipeline.io.writers import write_parquet
from data_pipeline.models import RunContext
from data_pipeline.reporting.merge_reports import write_merge_report
from data_pipeline.reporting.quality_reports import write_quality_report
from data_pipeline.reporting.summary import build_final_summary
from data_pipeline.reporting.export import write_json
from data_pipeline.settings import load_settings
from data_pipeline.transform.harmonize import harmonize_variables
from data_pipeline.transform.standardize import cast_columns, standardize_names
from data_pipeline.transform.normalize import normalize_categories
from data_pipeline.transform.derive import derive_age_group
from data_pipeline.utils.dates import parse_dates_safely
from data_pipeline.validation.content_checks import (
    detect_duplicates,
    validate_columns,
    validate_dtypes,
    validate_primary_key,
    validate_ranges,
    validate_required_fields,
)
from data_pipeline.validation.file_checks import validate_file_exists
from data_pipeline.validation.merge_checks import validate_merge_keys


def build_run_context(config_path: str) -> RunContext:
    return RunContext(run_id=datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8], start_time=datetime.utcnow(), config_path=Path(config_path))


def _load_codebook(path: str) -> pd.DataFrame:
    codebook = pd.read_excel(path, sheet_name="final_codebook")
    codebook.columns = [c.strip() for c in codebook.columns]
    return codebook


def run_pipeline(config_path: str, stage: str | None = None, verbose: bool = False) -> dict:
    app_cfg, env = load_settings(config_path)
    context = build_run_context(config_path)

    pipeline = app_cfg.pipeline
    codebook = _load_codebook(pipeline.codebook_path)
    expected_columns = sorted(set(codebook["QUESTION_NAME"].dropna().astype(str)))

    quality_rows = []
    harmonized_frames = {}

    for study in pipeline.studies:
        input_path = Path("data/raw") / study.file_name
        validate_file_exists(input_path)
        raw_df = read_dataset(input_path)
        metadata = collect_file_metadata(input_path, raw_df)

        staging_path = Path("data/staging") / f"{study.alias}_{context.run_id}.parquet"
        write_parquet(raw_df, staging_path)
        context.artifacts.append(str(staging_path))

        col_checks = validate_columns(raw_df, expected_columns, allowed_extra=[
            "PATIENT_RECORD_NUMBER","SUBJECT_NUMBER","SUBJECT_EXTERNAL_ID","SUBJECT_ROLE","SUBJECT_GROUP",
            "SUBJECT_COHORT","SITE_NAME","LAST_NAME","FIRST_NAME","DOB","RACE","ETHNICITY","SEX",
            "AGE_AT_VISIT","INTERVAL_NAME","VISIT_DATE","TIME_24_HOUR"
        ])
        req = validate_required_fields(raw_df, ["PATIENT_RECORD_NUMBER"])
        dtype_map = {r["QUESTION_NAME"]: str(r.get("final_answer_format", "")) for _, r in codebook.iterrows() if pd.notna(r.get("QUESTION_NAME"))}
        dtype_mismatches = validate_dtypes(raw_df, dtype_map)
        range_issues = validate_ranges(raw_df, {"AGE_AT_VISIT": (0, 120)})

        standardized = standardize_names(raw_df)
        standardized = parse_dates_safely(standardized, ["DOB", "VISIT_DATE"])
        standardized = cast_columns(standardized, {"AGE_AT_VISIT": "float"})
        standardized = normalize_categories(standardized, {"SEX": {"M": "MALE", "F": "FEMALE"}})
        standardized = derive_age_group(standardized)

        if "PATIENT_RECORD_NUMBER" in standardized.columns:
            dupes = detect_duplicates(standardized, ["PATIENT_RECORD_NUMBER"])
            if not dupes.empty:
                context.warnings.append(f"{study.alias} duplicates: {len(dupes)}")
            validate_primary_key(standardized.drop_duplicates(subset=["PATIENT_RECORD_NUMBER"]), ["PATIENT_RECORD_NUMBER"])

        mapping = {c: c for c in standardized.columns}
        harm_df, trace = harmonize_variables(standardized, mapping, study.study_id, needs_review=[])
        curated_path = Path("data/curated") / f"{study.alias}_{context.run_id}.parquet"
        write_parquet(harm_df, curated_path)
        context.artifacts.extend([str(curated_path)])
        trace_path = Path("reports/summaries") / f"trace_{study.alias}_{context.run_id}.parquet"
        write_parquet(trace, trace_path)
        context.artifacts.append(str(trace_path))

        quality_rows.append({
            "study": study.alias,
            "file": metadata.name,
            "rows": metadata.row_count,
            "columns": metadata.column_count,
            "missing_columns": ",".join(col_checks["missing"]),
            "unexpected_columns": ",".join(col_checks["unexpected"]),
            "required_missing_PATIENT_RECORD_NUMBER": req.get("PATIENT_RECORD_NUMBER", 0),
            "dtype_mismatches": len(dtype_mismatches),
            "range_issues": range_issues.get("AGE_AT_VISIT", 0),
        })
        harmonized_frames[study.alias] = harm_df

    left = harmonized_frames[pipeline.studies[0].alias]
    right = harmonized_frames[pipeline.studies[1].alias]
    keys = ["PATIENT_RECORD_NUMBER"]
    validate_merge_keys(left, right, keys)
    merged = perform_merge(left, right, keys=keys, how="outer")
    metrics = compute_merge_metrics(merged)

    analytic_path = Path("data/analytic") / f"final_analytic_{context.run_id}.parquet"
    write_parquet(merged, analytic_path)
    context.artifacts.append(str(analytic_path))

    excluded = merged[merged["_merge"] != "both"].copy() if "_merge" in merged.columns else pd.DataFrame()
    if not excluded.empty:
        excluded_path = Path("data/excluded") / f"excluded_{context.run_id}.parquet"
        write_parquet(excluded, excluded_path)
        context.artifacts.append(str(excluded_path))
        context.counts["excluded_rows"] = len(excluded)

    q_path = write_quality_report(quality_rows, Path("reports/file_quality") / f"{pipeline.output_naming.get('quality_report_prefix','00_file_quality')}_{context.run_id}.xlsx")
    m_path = write_merge_report(metrics, Path("reports/merge_quality") / f"{pipeline.output_naming.get('merge_report_prefix','01_merge_quality')}_{context.run_id}.xlsx")
    context.artifacts.extend([str(q_path), str(m_path)])
    context.counts.update(metrics)

    summary = build_final_summary(context)
    s_path = write_json(summary, Path("reports/summaries") / f"{pipeline.output_naming.get('summary_prefix','02_final_summary')}_{context.run_id}.json")
    context.artifacts.append(str(s_path))

    manifest = write_run_manifest(context, Path("reports/manifests") / f"manifest_{context.run_id}.json", extra={"config": app_cfg.model_dump()})
    context.artifacts.append(str(manifest))

    return summary
