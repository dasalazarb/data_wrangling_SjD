from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StudyConfig(BaseModel):
    study_id: str
    file_name: str
    alias: str


class PipelineConfig(BaseModel):
    name: str
    fail_fast: bool = True
    codebook_path: str
    studies: list[StudyConfig]
    stages: list[str] = Field(default_factory=list)
    output_naming: dict[str, str] = Field(default_factory=dict)


class AppConfig(BaseModel):
    pipeline: PipelineConfig


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PIPELINE_", env_file=".env", extra="ignore")
    root: str = "."
    config: str = "configs/pipeline.yaml"
    fail_fast: bool = True
    log_level: str = "INFO"


def load_settings(config_path: str | None = None) -> tuple[AppConfig, EnvSettings]:
    env = EnvSettings()
    path = Path(config_path or env.config)
    with path.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    cfg = AppConfig.model_validate(data)
    return cfg, env
