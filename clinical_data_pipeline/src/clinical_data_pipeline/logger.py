from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler


def init_logger(run_id: str, log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("clinical_data_pipeline")
    logger.handlers.clear()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    console_handler = RichHandler(rich_tracebacks=True)
    file_handler = logging.FileHandler(Path(log_dir) / f"pipeline_{run_id}.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
