"""Dataset profiling: the "inspect before you decide" step.

`profile_dataframe` computes everything the workspace's Profile step
shows: shape, duplicate rows, and a `types.ColumnProfile` per column
(dtype, detected semantic type, missing/unique counts, summary statistics,
and a simple IQR-based outlier count for numeric columns). It never
mutates the input DataFrame.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .types import ColumnProfile, ColumnType, detect_column_type, to_object_str


def _iqr_outlier_count(values: pd.Series) -> int | None:
    finite = pd.to_numeric(values, errors="coerce").dropna()
    if finite.size < 4:
        return None
    q1, q3 = np.percentile(finite, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((finite < lo) | (finite > hi)).sum())


def profile_column(series: pd.Series) -> ColumnProfile:
    name = str(series.name)
    n = len(series)
    missing = int(series.isna().sum())
    non_null = series.dropna()
    unique = int(non_null.nunique())
    detected = detect_column_type(series, name)

    sample = non_null.head(5).tolist()
    sample = [None if (isinstance(v, float) and np.isnan(v)) else v for v in sample]

    profile = ColumnProfile(
        name=name,
        dtype=str(series.dtype),
        detected_type=detected,
        count=n,
        missing=missing,
        missing_pct=(missing / n * 100.0) if n else 0.0,
        unique=unique,
        cardinality_ratio=(unique / len(non_null)) if len(non_null) else 0.0,
        sample_values=sample,
    )

    if detected in (ColumnType.NUMERIC, ColumnType.CURRENCY, ColumnType.PERCENTAGE) or pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(numeric):
            profile.numeric_min = float(numeric.min())
            profile.numeric_max = float(numeric.max())
            profile.numeric_mean = float(numeric.mean())
            profile.numeric_median = float(numeric.median())
            profile.numeric_std = float(numeric.std()) if len(numeric) > 1 else 0.0
            profile.outlier_count = _iqr_outlier_count(numeric)
    elif detected in (ColumnType.TEXT, ColumnType.CATEGORICAL, ColumnType.IDENTIFIER):
        lengths = to_object_str(non_null).str.len()
        if len(lengths):
            profile.min_length = int(lengths.min())
            profile.max_length = int(lengths.max())

    return profile


@dataclass
class DatasetProfile:
    row_count: int
    column_count: int
    duplicate_rows: int
    memory_bytes: int
    columns: list[ColumnProfile] = field(default_factory=list)

    def type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self.columns:
            counts[c.detected_type.value] = counts.get(c.detected_type.value, 0) + 1
        return counts

    def columns_of_type(self, *types: ColumnType) -> list[str]:
        return [c.name for c in self.columns if c.detected_type in types]

    def total_missing(self) -> int:
        return sum(c.missing for c in self.columns)


def profile_dataframe(df: pd.DataFrame) -> DatasetProfile:
    return DatasetProfile(
        row_count=len(df),
        column_count=df.shape[1],
        duplicate_rows=int(df.duplicated().sum()),
        memory_bytes=int(df.memory_usage(deep=True).sum()),
        columns=[profile_column(df[col]) for col in df.columns],
    )
