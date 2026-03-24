from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_hash(file_path: str | Path) -> str:
    hasher = hashlib.sha256()
    with Path(file_path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
