"""Smart column-type detection.

Pandas' own dtypes (int64, object, ...) are a storage detail, not what a
data analyst means by "type" -- an ``object`` column might be free text,
a categorical label, a date stored as a string, a currency amount like
"$1,234.56", or a percentage like "12.5%". This module looks at the
*values*, not just the dtype, to classify each column into one of
``ColumnType`` and, where useful, proposes a concrete conversion the user
can accept or reject (see ``DataWorkspaceTab`` / ``session.py``).

Nothing here mutates the DataFrame; `detect_column_type` and
`suggest_conversion` are pure functions of a Series.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd


class ColumnType(str, Enum):
    NUMERIC = "Numeric"
    BOOLEAN = "Boolean"
    DATETIME = "Date/time"
    CATEGORICAL = "Categorical"
    IDENTIFIER = "Identifier"
    CURRENCY = "Currency"
    PERCENTAGE = "Percentage"
    GEOGRAPHIC = "Geographic"
    TEXT = "Text"
    EMPTY = "Empty"


_BOOL_TOKENS = {"true", "false", "yes", "no", "y", "n", "t", "f", "1", "0"}
_CURRENCY_SYMBOLS = "$\u20ac\u00a3\u00a5"  # $, EUR, GBP, JPY signs
_CURRENCY_RE = (
    rf"^\s*[-+]?[{_CURRENCY_SYMBOLS}]\s?[\d.,]+\s*$"
    rf"|^\s*[-+]?[\d.,]+\s?[{_CURRENCY_SYMBOLS}]\s*$"
)
_PERCENTAGE_RE = r"^\s*[-+]?[\d,]+(\.\d+)?\s?%\s*$"

# Common geographic-sounding column names (a name-based heuristic is
# necessary here -- geographic values like "France" or "94103" have no
# reliable value-based signature the way a currency symbol or an ISO date
# do).
_GEO_NAME_HINTS = re.compile(
    r"\b(country|countries|state|province|region|city|town|latitude|lat|longitude|lon|lng|zip|postal|iso[_ ]?code|continent)\b",
    re.IGNORECASE,
)

# A conservative set of ID-like name hints, used only to break ties when the
# value-based signature (uniqueness) is already consistent with an
# identifier -- name alone never promotes an otherwise-numeric/text column.
_ID_NAME_HINTS = re.compile(r"(^|_)(id|uuid|guid|key|code|number|no)$", re.IGNORECASE)


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    detected_type: ColumnType
    count: int
    missing: int
    missing_pct: float
    unique: int
    cardinality_ratio: float
    sample_values: list
    # Populated only for the relevant detected_type; others stay None.
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_mean: float | None = None
    numeric_median: float | None = None
    numeric_std: float | None = None
    outlier_count: int | None = None
    min_length: int | None = None
    max_length: int | None = None


def to_object_str(series: pd.Series) -> pd.Series:
    """Convert to a plain object-dtype Series of Python `str`, preserving
    missing values as NaN/None rather than stringifying them.

    Needed because pandas' `.astype(str)` round-trips back through its
    PyArrow-backed "str" extension dtype regardless of a prior
    `.astype(object)`, and that dtype's `.str.*` accessor dispatches to
    PyArrow's RE2 regex engine -- which rejects patterns Python's `re`
    happily accepts (e.g. `\\uXXXX` escapes) and would otherwise turn
    missing values into the literal text "nan". Every string/regex
    operation in this package goes through this helper instead of
    `.astype(str)` directly, to stay on the predictable, classic
    Python-`re`-backed path.
    """
    obj = series.astype(object)
    return obj.map(lambda v: v if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v))


def _non_null_sample(series: pd.Series, n: int = 200) -> pd.Series:
    values = series.dropna()
    if len(values) > n:
        values = values.sample(n, random_state=0)
    return values


def _looks_boolean(values: pd.Series) -> bool:
    if pd.api.types.is_bool_dtype(values):
        return True
    if not pd.api.types.is_object_dtype(values) and not pd.api.types.is_string_dtype(values):
        uniq = set(pd.unique(values.dropna()))
        return uniq.issubset({0, 1})
    tokens = set(str(v).strip().lower() for v in values.dropna().unique())
    return 0 < len(tokens) <= 2 and tokens.issubset(_BOOL_TOKENS)


def _looks_datetime(values: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(values):
        return True
    if not (pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values)):
        return False
    sample = _non_null_sample(values, 50)
    if sample.empty:
        return False
    try:
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    except (ValueError, TypeError):
        parsed = pd.to_datetime(sample, errors="coerce")
    return parsed.notna().mean() >= 0.85


def _looks_currency(values: pd.Series) -> bool:
    sample = to_object_str(_non_null_sample(values, 50))
    if sample.empty:
        return False
    return sample.str.match(_CURRENCY_RE).mean() >= 0.85


def _looks_percentage(values: pd.Series) -> bool:
    sample = to_object_str(_non_null_sample(values, 50))
    if sample.empty:
        return False
    return sample.str.match(_PERCENTAGE_RE).mean() >= 0.85


def detect_column_type(series: pd.Series, name: str | None = None) -> ColumnType:
    """Classify a single column by inspecting its values (and, only as a
    tie-breaker for identifiers, its name)."""
    name = name if name is not None else (series.name or "")
    non_null = series.dropna()
    if non_null.empty:
        return ColumnType.EMPTY

    if _looks_boolean(non_null):
        return ColumnType.BOOLEAN
    if _looks_datetime(non_null):
        return ColumnType.DATETIME
    if pd.api.types.is_numeric_dtype(non_null):
        n = len(non_null)
        unique = non_null.nunique()
        # Small samples make "every value is unique" a meaningless signal
        # (trivially true for almost any tiny column) rather than evidence
        # of being an identifier, so this heuristic only kicks in with
        # enough rows to matter.
        if unique == n and n >= 10 and _ID_NAME_HINTS.search(str(name)):
            return ColumnType.IDENTIFIER
        return ColumnType.NUMERIC
    if pd.api.types.is_object_dtype(non_null) or pd.api.types.is_string_dtype(non_null):
        if _looks_currency(non_null):
            return ColumnType.CURRENCY
        if _looks_percentage(non_null):
            return ColumnType.PERCENTAGE
        if _GEO_NAME_HINTS.search(str(name)):
            return ColumnType.GEOGRAPHIC
        n = len(non_null)
        unique = non_null.nunique()
        as_text = to_object_str(non_null)
        avg_len = as_text.str.len().mean()
        avg_words = as_text.str.split().str.len().mean()
        is_long_free_text = avg_len > 30 or avg_words > 4
        if unique == n and n >= 10:
            return ColumnType.TEXT if is_long_free_text else ColumnType.IDENTIFIER
        if is_long_free_text:
            return ColumnType.TEXT
        ratio = unique / n if n else 0.0
        # A small, repeated set of labels is categorical; a mostly-unique
        # set of short strings is text. 0.5 is a deliberately simple,
        # explicit cutoff rather than a learned threshold -- it's meant to
        # be an easy default to override, not a claim of statistical rigor.
        if unique <= 50 or ratio <= 0.5:
            return ColumnType.CATEGORICAL
        return ColumnType.TEXT
    return ColumnType.TEXT


@dataclass
class ConversionSuggestion:
    column: str
    from_type: ColumnType
    to_dtype: str
    reason: str


def suggest_conversion(series: pd.Series, detected: ColumnType) -> ConversionSuggestion | None:
    """Propose a concrete pandas conversion for a detected type that isn't
    already stored that way (e.g. dates held as strings), or None if the
    column's storage already matches its detected type."""
    name = str(series.name)
    if detected == ColumnType.DATETIME and not pd.api.types.is_datetime64_any_dtype(series):
        return ConversionSuggestion(name, detected, "datetime64[ns]",
                                     "Values look like dates but are stored as text.")
    if detected == ColumnType.BOOLEAN and not pd.api.types.is_bool_dtype(series):
        return ConversionSuggestion(name, detected, "boolean",
                                     "Only two distinct values found (e.g. yes/no, true/false).")
    if detected == ColumnType.CATEGORICAL and not isinstance(series.dtype, pd.CategoricalDtype):
        return ConversionSuggestion(name, detected, "category",
                                     "A small, repeated set of labels -- category dtype is more memory-efficient and enables ordering.")
    if detected in (ColumnType.CURRENCY, ColumnType.PERCENTAGE) and not pd.api.types.is_numeric_dtype(series):
        return ConversionSuggestion(name, detected, "float64",
                                     f"Looks like a {detected.value.lower()} value stored as text; strip symbols and convert to a number.")
    return None


def classify_dataframe(df: pd.DataFrame) -> dict[str, ColumnType]:
    return {col: detect_column_type(df[col], col) for col in df.columns}
