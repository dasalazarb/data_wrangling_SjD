from __future__ import annotations

import pandera.pandas as pa


def build_schema(required_columns: list[str]) -> pa.DataFrameSchema:
    cols = {c: pa.Column(object, nullable=True) for c in required_columns}
    return pa.DataFrameSchema(cols, strict=False, coerce=False)
