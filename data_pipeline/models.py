from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FileMetadata:
    name: str
    path: str
    size_bytes: int
    sha256: str
    extension: str
    read_timestamp: str
    row_count: int
    column_count: int


@dataclass
class RunContext:
    run_id: str
    start_time: datetime
    config_path: Path
    artifacts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    counts: dict[str, Any] = field(default_factory=dict)
