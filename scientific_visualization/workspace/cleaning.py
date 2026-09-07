"""Reproducible cleaning (and transform, see transforms.py) operations.

Every operation here is a plain function ``(df, **params) -> df`` that
returns a *new* DataFrame -- the original is never mutated in place. A
:class:`PipelineStep` just records which operation ran with which
parameters, so a whole pipeline is a small, inspectable, serializable
list that :func:`apply_pipeline` replays from the original data. This is
what makes undo/reorder/toggle possible (see ``session.WorkspaceSession``):
"undo" is just "drop the last step and replay", not a snapshot stack.

Operations are looked up in ``OPERATIONS`` by name (also used by
``transforms.py``, which registers into the same dict) so the GUI layer
only needs to know operation names and parameter dicts, never import
individual functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

from .types import to_object_str

OPERATIONS: dict[str, Callable[..., pd.DataFrame]] = {}


def operation(name: str):
    """Register a cleaning/transform function under `name` for use in a
    pipeline step. Kept as a decorator so every operation's implementation
    sits right next to its registration -- one place to look, not two."""
    def wrap(func):
        OPERATIONS[name] = func
        return func
    return wrap


@dataclass
class PipelineStep:
    op: str
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    note: str = ""  # human-readable summary, e.g. "Fill missing (age): mean"

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        func = OPERATIONS.get(self.op)
        if func is None:
            raise ValueError(f"Unknown operation: {self.op!r}")
        return func(df, **self.params)


def apply_pipeline(df: pd.DataFrame, steps: list[PipelineStep]) -> tuple[pd.DataFrame, list[str]]:
    """Replay `steps` on `df` in order. Returns (result, errors) -- a step
    that raises is skipped (not fatal to the rest of the pipeline) and its
    message is collected, so one bad step doesn't block every step after it
    or destroy the ability to see/fix it.
    """
    result = df
    errors = []
    for i, step in enumerate(steps):
        if not step.enabled:
            continue
        try:
            result = step.run(result)
        except Exception as exc:
            errors.append(f"Step {i + 1} ({step.op}): {exc}")
    return result, errors


# --------------------------------------------------------------------------
# Cleaning operations
# --------------------------------------------------------------------------

@operation("remove_duplicates")
def remove_duplicates(df: pd.DataFrame, subset: list[str] | None = None, keep: str = "first") -> pd.DataFrame:
    return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)


@operation("drop_rows_with_missing")
def drop_rows_with_missing(df: pd.DataFrame, columns: list[str] | None = None, how: str = "any") -> pd.DataFrame:
    subset = columns or None
    return df.dropna(subset=subset, how=how).reset_index(drop=True)


@operation("fill_missing")
def fill_missing(df: pd.DataFrame, columns: list[str], method: str = "mean", value=None) -> pd.DataFrame:
    """method: 'mean' | 'median' | 'mode' | 'constant' | 'ffill' | 'bfill'"""
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            continue
        series = df[col]
        if method == "mean":
            df[col] = series.fillna(pd.to_numeric(series, errors="coerce").mean())
        elif method == "median":
            df[col] = series.fillna(pd.to_numeric(series, errors="coerce").median())
        elif method == "mode":
            mode = series.mode(dropna=True)
            if len(mode):
                df[col] = series.fillna(mode.iloc[0])
        elif method == "constant":
            df[col] = series.fillna(value)
        elif method == "ffill":
            df[col] = series.ffill()
        elif method == "bfill":
            df[col] = series.bfill()
        else:
            raise ValueError(f"Unknown fill method: {method!r}")
    return df


@operation("replace_values")
def replace_values(df: pd.DataFrame, column: str, mapping: dict) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].replace(mapping)
    return df


@operation("rename_column")
def rename_column(df: pd.DataFrame, column: str, new_name: str) -> pd.DataFrame:
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("New column name cannot be empty")
    if new_name in df.columns and new_name != column:
        raise ValueError(f"Column '{new_name}' already exists")
    return df.rename(columns={column: new_name})


@operation("change_dtype")
def change_dtype(df: pd.DataFrame, column: str, dtype: str) -> pd.DataFrame:
    """dtype: 'numeric' | 'string' | 'datetime' | 'category' | 'boolean'"""
    df = df.copy()
    series = df[column]
    if dtype == "numeric":
        # Strip common currency/percentage/thousands decoration before
        # coercing, so "$1,234.50" and "12.5%" convert instead of becoming
        # all-NaN.
        cleaned = to_object_str(series).str.replace(r"[,$\u20ac\u00a3\u00a5%\s]", "", regex=True)
        df[column] = pd.to_numeric(cleaned, errors="coerce")
    elif dtype == "string":
        df[column] = to_object_str(series).where(series.notna(), other=pd.NA)
    elif dtype == "datetime":
        df[column] = pd.to_datetime(series, errors="coerce", format="mixed")
    elif dtype == "category":
        df[column] = series.astype("category")
    elif dtype == "boolean":
        tokens = {"true": True, "yes": True, "y": True, "t": True, "1": True,
                  "false": False, "no": False, "n": False, "f": False, "0": False}
        df[column] = to_object_str(series).str.strip().str.lower().map(tokens).astype("boolean")
    else:
        raise ValueError(f"Unknown target dtype: {dtype!r}")
    return df


@operation("trim_whitespace")
def trim_whitespace(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    df = df.copy()
    cols = columns or [c for c in df.columns if df[c].dtype == object or pd.api.types.is_string_dtype(df[c])]
    for col in cols:
        df[col] = df[col].astype(object).where(df[col].isna(), to_object_str(df[col]).str.strip())
    return df


@operation("standardize_text")
def standardize_text(df: pd.DataFrame, columns: list[str], case: str = "lower") -> pd.DataFrame:
    """case: 'lower' | 'upper' | 'title'"""
    df = df.copy()
    for col in columns:
        text = to_object_str(df[col])
        if case == "lower":
            text = text.str.lower()
        elif case == "upper":
            text = text.str.upper()
        elif case == "title":
            text = text.str.title()
        else:
            raise ValueError(f"Unknown case: {case!r}")
        df[col] = df[col].astype(object).where(df[col].isna(), text)
    return df


@operation("remove_empty_columns")
def remove_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, df.notna().any(axis=0)]


@operation("remove_constant_columns")
def remove_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in df.columns if df[c].nunique(dropna=True) > 1]
    return df.loc[:, keep]


@operation("handle_outliers")
def handle_outliers(df: pd.DataFrame, column: str, method: str = "clip", factor: float = 1.5) -> pd.DataFrame:
    """method: 'clip' (winsorize to the IQR fence) | 'remove' (drop those rows)"""
    df = df.copy()
    numeric = pd.to_numeric(df[column], errors="coerce")
    q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - factor * iqr, q3 + factor * iqr
    if method == "clip":
        df[column] = numeric.clip(lower=lo, upper=hi)
    elif method == "remove":
        mask = numeric.isna() | ((numeric >= lo) & (numeric <= hi))
        df = df.loc[mask].reset_index(drop=True)
    else:
        raise ValueError(f"Unknown outlier method: {method!r}")
    return df


@operation("parse_dates")
def parse_dates(df: pd.DataFrame, column: str, date_format: str | None = None) -> pd.DataFrame:
    df = df.copy()
    if date_format:
        df[column] = pd.to_datetime(df[column], format=date_format, errors="coerce")
    else:
        df[column] = pd.to_datetime(df[column], errors="coerce", format="mixed")
    return df


@operation("extract_date_component")
def extract_date_component(df: pd.DataFrame, column: str, component: str, new_name: str | None = None) -> pd.DataFrame:
    """component: 'year' | 'month' | 'day' | 'weekday' | 'hour' | 'quarter'"""
    df = df.copy()
    dt = pd.to_datetime(df[column], errors="coerce", format="mixed")
    accessors = {
        "year": dt.dt.year, "month": dt.dt.month, "day": dt.dt.day,
        "weekday": dt.dt.day_name(), "hour": dt.dt.hour, "quarter": dt.dt.quarter,
    }
    if component not in accessors:
        raise ValueError(f"Unknown date component: {component!r}")
    df[new_name or f"{column}_{component}"] = accessors[component]
    return df


@operation("split_column")
def split_column(df: pd.DataFrame, column: str, delimiter: str, new_names: list[str] | None = None,
                 max_splits: int = -1) -> pd.DataFrame:
    df = df.copy()
    parts = to_object_str(df[column]).str.split(delimiter, n=max_splits if max_splits >= 0 else -1, expand=True)
    for i in range(parts.shape[1]):
        name = new_names[i] if new_names and i < len(new_names) else f"{column}_{i + 1}"
        df[name] = parts[i]
    return df


@operation("combine_columns")
def combine_columns(df: pd.DataFrame, columns: list[str], new_name: str, separator: str = " ") -> pd.DataFrame:
    df = df.copy()
    df[new_name] = df[columns].apply(to_object_str).agg(separator.join, axis=1)
    return df
