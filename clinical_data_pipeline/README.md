# Clinical Data Pipeline

Pipeline modular para data wrangling, validación, harmonización, integración y auditoría de datos clínicos multi-estudio.

## Arquitectura
- **Configuración**: YAML + `pydantic-settings`.
- **IO**: lectura/escritura CSV/XLSX/Parquet + metadata auditables.
- **Validación**: contratos `pandera`, dominios, tipos, duplicados, reglas de negocio.
- **Transformación**: estandarización, casteo, normalización y derivaciones.
- **Harmonización**: mappings guiados por config y codebook.
- **Integración**: merges auditables con métricas.
- **Reporting**: reportes de calidad, merge, resumen y manifiesto.
- **Observabilidad**: run_id, logging en consola/archivo, artefactos versionados.

## Estructura
Ver árbol en la especificación del proyecto (`clinical_data_pipeline/`).

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Configuración
1. Copiar `.env.example` a `.env` si se desea.
2. Ajustar `configs/pipeline.yaml` y archivos bajo `configs/files`, `configs/merges`, `configs/rules`.
3. Colocar archivos fuente en `data/raw/`.

## Ejecución
```bash
python -m clinical_data_pipeline.main run --config configs/pipeline.yaml
# o
clinical-pipeline run --config configs/pipeline.yaml --verbose
# ejecutar etapa puntual
clinical-pipeline run --config configs/pipeline.yaml --stage validate_content
```

## Flujo
1. Carga configuración
2. Crea `run_id`
3. Inicializa logger
4. Descubre inputs
5. Valida estructura + metadata
6. Persiste staging
7. Valida contenido
8. Transforma + harmoniza
9. Persiste curated
10. Integra y calcula métricas
11. Genera analítico + excluidos
12. Reportes + manifiesto + resumen

## Outputs
- `data/staging/*.parquet`
- `data/curated/*.parquet`
- `data/analytic/final_analytic_<run_id>.parquet`
- `data/excluded/excluded_<run_id>.parquet`
- `reports/file_quality/00_file_quality_<run_id>.xlsx`
- `reports/merge_quality/01_merge_quality_<run_id>.xlsx`
- `reports/summaries/02_final_summary_<run_id>.json`
- `reports/manifests/manifest_<run_id>.json`
- `logs/pipeline_<run_id>.log`

## Testing
```bash
pytest
```
Incluye pruebas unitarias de config/IO/validación/transformación/merge y e2e mínima.

## Extensión enterprise opcional
El core está desacoplado de capacidades enterprise (Great Expectations, dashboards, CI/CD, contratos avanzados).
