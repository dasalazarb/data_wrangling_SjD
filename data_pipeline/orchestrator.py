from __future__ import annotations

import logging
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
from data_pipeline.reporting.export import write_dataframe_xlsx, write_dict_xlsx, write_json
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
from data_pipeline.logger import init_logger


def build_run_context(config_path: str) -> RunContext:
    return RunContext(run_id=datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8], start_time=datetime.utcnow(), config_path=Path(config_path))


def _load_codebook(path: str) -> pd.DataFrame:
    codebook = pd.read_excel(path, sheet_name="final_codebook")
    codebook.columns = [c.strip() for c in codebook.columns]
    return codebook


def run_pipeline(config_path: str, stage: str | None = None, verbose: bool = False) -> dict:
    app_cfg, env = load_settings(config_path)
    context = build_run_context(config_path)
    logger = init_logger(context.run_id, "DEBUG" if verbose else env.log_level)
    logger.info("Iniciando ejecución del pipeline.")
    logger.info("Run ID: %s | Configuración: %s | Stage: %s", context.run_id, config_path, stage or "all")

    pipeline = app_cfg.pipeline
    logger.info("Cargando codebook desde: %s", pipeline.codebook_path)
    codebook = _load_codebook(pipeline.codebook_path)
    expected_columns = sorted(set(codebook["QUESTION_NAME"].dropna().astype(str)))
    logger.info("Codebook cargado: %s columnas esperadas.", len(expected_columns))
    logger.debug("Columnas esperadas (primeras 25): %s", expected_columns[:25])

    quality_rows = []
    harmonized_frames = {}
    execution_rows = []

    for study in pipeline.studies:
        logger.info("---- Procesando estudio: %s (id=%s) ----", study.alias, study.study_id)
        input_path = Path("data/raw") / study.file_name
        validate_file_exists(input_path)
        logger.info("Archivo fuente detectado: %s", input_path)
        raw_df = read_dataset(input_path)
        metadata = collect_file_metadata(input_path, raw_df)
        logger.info("Lectura completada para %s: filas=%s, columnas=%s", study.alias, metadata.row_count, metadata.column_count)
        logger.debug("Columnas originales de %s: %s", study.alias, list(raw_df.columns))

        staging_path = Path("data/staging") / f"{study.alias}_{context.run_id}.parquet"
        write_parquet(raw_df, staging_path)
        context.artifacts.append(str(staging_path))
        logger.info("Staging guardado: %s", staging_path)

        col_checks = validate_columns(raw_df, expected_columns, allowed_extra=[
            "PATIENT_RECORD_NUMBER","SUBJECT_NUMBER","SUBJECT_EXTERNAL_ID","SUBJECT_ROLE","SUBJECT_GROUP",
            "SUBJECT_COHORT","SITE_NAME","LAST_NAME","FIRST_NAME","DOB","RACE","ETHNICITY","SEX",
            "AGE_AT_VISIT","INTERVAL_NAME","VISIT_DATE","TIME_24_HOUR"
        ])
        logger.info(
            "Validación de columnas %s -> faltantes=%s, inesperadas=%s",
            study.alias,
            len(col_checks["missing"]),
            len(col_checks["unexpected"]),
        )
        if col_checks["missing"]:
            logger.warning("%s columnas faltantes: %s", study.alias, col_checks["missing"])
        if col_checks["unexpected"]:
            logger.warning("%s columnas inesperadas: %s", study.alias, col_checks["unexpected"])

        req = validate_required_fields(raw_df, ["PATIENT_RECORD_NUMBER"])
        if req.get("PATIENT_RECORD_NUMBER", 0):
            logger.warning(
                "%s registros sin PATIENT_RECORD_NUMBER: %s",
                study.alias,
                req["PATIENT_RECORD_NUMBER"],
            )
        dtype_map = {r["QUESTION_NAME"]: str(r.get("final_answer_format", "")) for _, r in codebook.iterrows() if pd.notna(r.get("QUESTION_NAME"))}
        dtype_mismatches = validate_dtypes(raw_df, dtype_map)
        logger.info("Validación de dtypes %s -> mismatches=%s", study.alias, len(dtype_mismatches))
        range_issues = validate_ranges(raw_df, {"AGE_AT_VISIT": (0, 120)})
        if range_issues.get("AGE_AT_VISIT", 0):
            logger.warning("%s valores fuera de rango AGE_AT_VISIT: %s", study.alias, range_issues.get("AGE_AT_VISIT", 0))

        standardized = standardize_names(raw_df)
        standardized = parse_dates_safely(standardized, ["DOB", "VISIT_DATE"])
        standardized = cast_columns(standardized, {"AGE_AT_VISIT": "float"})
        standardized = normalize_categories(standardized, {"SEX": {"M": "MALE", "F": "FEMALE"}})
        standardized = derive_age_group(standardized)
        logger.info("Estandarización completa para %s.", study.alias)
        logger.debug("Columnas estandarizadas %s: %s", study.alias, list(standardized.columns))

        duplicate_count = 0
        if "PATIENT_RECORD_NUMBER" in standardized.columns:
            dupes = detect_duplicates(standardized, ["PATIENT_RECORD_NUMBER"])
            duplicate_count = len(dupes)
            if not dupes.empty:
                context.warnings.append(f"{study.alias} duplicates: {len(dupes)}")
                logger.warning("%s detectó duplicados por PATIENT_RECORD_NUMBER: %s", study.alias, len(dupes))
            validate_primary_key(standardized.drop_duplicates(subset=["PATIENT_RECORD_NUMBER"]), ["PATIENT_RECORD_NUMBER"])
            logger.info("Validación de clave primaria completada para %s.", study.alias)

        mapping = {c: c for c in standardized.columns}
        harm_df, trace = harmonize_variables(standardized, mapping, study.study_id, needs_review=[])
        logger.info("Armonización completada para %s: filas=%s, columnas=%s", study.alias, len(harm_df), len(harm_df.columns))
        curated_path = Path("data/curated") / f"{study.alias}_{context.run_id}.parquet"
        write_parquet(harm_df, curated_path)
        context.artifacts.extend([str(curated_path)])
        logger.info("Curated parquet guardado: %s", curated_path)

        curated_xlsx_path = Path("data/curated") / f"{study.alias}_{context.run_id}.xlsx"
        write_dataframe_xlsx(harm_df, curated_xlsx_path, sheet_name="curated")
        context.artifacts.append(str(curated_xlsx_path))
        logger.info("Curated xlsx guardado: %s", curated_xlsx_path)

        trace_path = Path("reports/summaries") / f"trace_{study.alias}_{context.run_id}.parquet"
        write_parquet(trace, trace_path)
        context.artifacts.append(str(trace_path))
        logger.info("Trace parquet guardado: %s", trace_path)
        trace_xlsx_path = Path("reports/summaries") / f"trace_{study.alias}_{context.run_id}.xlsx"
        write_dataframe_xlsx(trace, trace_xlsx_path, sheet_name="trace")
        context.artifacts.append(str(trace_xlsx_path))
        logger.info("Trace xlsx guardado: %s", trace_xlsx_path)

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
        execution_rows.append(
            {
                "run_id": context.run_id,
                "study": study.alias,
                "source_file": metadata.name,
                "input_rows": metadata.row_count,
                "input_columns": metadata.column_count,
                "missing_columns_count": len(col_checks["missing"]),
                "unexpected_columns_count": len(col_checks["unexpected"]),
                "missing_required_patient_id": req.get("PATIENT_RECORD_NUMBER", 0),
                "dtype_mismatch_count": len(dtype_mismatches),
                "age_range_issues": range_issues.get("AGE_AT_VISIT", 0),
                "duplicate_patient_ids": duplicate_count,
                "harmonized_rows": len(harm_df),
                "trace_rows": len(trace),
            }
        )
        harmonized_frames[study.alias] = harm_df

    left = harmonized_frames[pipeline.studies[0].alias]
    right = harmonized_frames[pipeline.studies[1].alias]
    keys = ["PATIENT_RECORD_NUMBER"]
    logger.info("Validando llaves de merge para datasets: %s vs %s", pipeline.studies[0].alias, pipeline.studies[1].alias)
    validate_merge_keys(left, right, keys)
    merged = perform_merge(left, right, keys=keys, how="outer")
    metrics = compute_merge_metrics(merged)
    logger.info("Merge completado: filas=%s, columnas=%s", len(merged), len(merged.columns))
    logger.info("Métricas de merge: %s", metrics)

    analytic_path = Path("data/analytic") / f"final_analytic_{context.run_id}.parquet"
    write_parquet(merged, analytic_path)
    context.artifacts.append(str(analytic_path))
    logger.info("Dataset analítico parquet guardado: %s", analytic_path)
    analytic_xlsx_path = Path("data/analytic") / f"final_analytic_{context.run_id}.xlsx"
    write_dataframe_xlsx(merged, analytic_xlsx_path, sheet_name="analytic")
    context.artifacts.append(str(analytic_xlsx_path))
    logger.info("Dataset analítico xlsx guardado: %s", analytic_xlsx_path)

    excluded = merged[merged["_merge"] != "both"].copy() if "_merge" in merged.columns else pd.DataFrame()
    if not excluded.empty:
        excluded_path = Path("data/excluded") / f"excluded_{context.run_id}.parquet"
        write_parquet(excluded, excluded_path)
        context.artifacts.append(str(excluded_path))
        excluded_xlsx_path = Path("data/excluded") / f"excluded_{context.run_id}.xlsx"
        write_dataframe_xlsx(excluded, excluded_xlsx_path, sheet_name="excluded")
        context.artifacts.append(str(excluded_xlsx_path))
        context.counts["excluded_rows"] = len(excluded)
        logger.warning("Registros excluidos detectados: %s", len(excluded))
        logger.info("Excluidos guardados en: %s y %s", excluded_path, excluded_xlsx_path)
    else:
        logger.info("No se detectaron registros excluidos.")

    q_path = write_quality_report(quality_rows, Path("reports/file_quality") / f"{pipeline.output_naming.get('quality_report_prefix','00_file_quality')}_{context.run_id}.xlsx")
    m_path = write_merge_report(metrics, Path("reports/merge_quality") / f"{pipeline.output_naming.get('merge_report_prefix','01_merge_quality')}_{context.run_id}.xlsx")
    context.artifacts.extend([str(q_path), str(m_path)])
    logger.info("Reporte de calidad: %s", q_path)
    logger.info("Reporte de merge: %s", m_path)

    execution_detail_path = Path("reports/summaries") / f"execution_details_{context.run_id}.xlsx"
    write_dataframe_xlsx(pd.DataFrame(execution_rows), execution_detail_path, sheet_name="execution")
    context.artifacts.append(str(execution_detail_path))
    logger.info("Reporte de ejecución detallado (xlsx): %s", execution_detail_path)
    context.counts.update(metrics)

    summary = build_final_summary(context)
    s_path = write_json(summary, Path("reports/summaries") / f"{pipeline.output_naming.get('summary_prefix','02_final_summary')}_{context.run_id}.json")
    context.artifacts.append(str(s_path))
    s_xlsx_path = write_dict_xlsx(summary, Path("reports/summaries") / f"{pipeline.output_naming.get('summary_prefix','02_final_summary')}_{context.run_id}.xlsx", sheet_name="summary")
    context.artifacts.append(str(s_xlsx_path))
    logger.info("Resumen final guardado (json/xlsx): %s | %s", s_path, s_xlsx_path)

    manifest = write_run_manifest(context, Path("reports/manifests") / f"manifest_{context.run_id}.json", extra={"config": app_cfg.model_dump()})
    context.artifacts.append(str(manifest))
    manifest_xlsx = write_dict_xlsx(
        {
            "run_id": context.run_id,
            "start_time_utc": context.start_time.isoformat(),
            "config_path": str(context.config_path),
            "warnings": context.warnings,
            "counts": context.counts,
            "artifacts": context.artifacts,
        },
        Path("reports/manifests") / f"manifest_{context.run_id}.xlsx",
        sheet_name="manifest",
    )
    context.artifacts.append(str(manifest_xlsx))
    logger.info("Manifest guardado (json/xlsx): %s | %s", manifest, manifest_xlsx)
    logger.info("Pipeline finalizado correctamente. Artefactos totales: %s", len(context.artifacts))

    return summary
