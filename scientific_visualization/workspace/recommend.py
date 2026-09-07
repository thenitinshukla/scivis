"""Suggest chart types from the columns a user picks (or from the whole
dataset), based on detected semantic type -- not just dtype -- so a
currency column suggests the same charts a plain numeric column would,
and a date stored as text still triggers a time-series suggestion.

This mirrors (and stays independent of) the Data Plotter's own
`figure_modes.FIGURE_MODES`; the two aren't merged because the workspace
operates on a general pandas DataFrame with mixed types, while the Data
Plotter is purely numeric. `session.WorkspaceSession.to_numeric_dataset`
is the bridge between them once a chart choice needs the Data Plotter's
richer rendering (fits, annotations, paper scaling, ...).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .types import ColumnType, detect_column_type

NUMERIC_LIKE = (ColumnType.NUMERIC, ColumnType.CURRENCY, ColumnType.PERCENTAGE)


@dataclass
class ChartSuggestion:
    chart_type: str
    x: str | None
    y: str | None
    reason: str
    color: str | None = None


def _types(df: pd.DataFrame, columns: list[str]) -> dict[str, ColumnType]:
    return {c: detect_column_type(df[c], c) for c in columns}


def suggest_for_pair(df: pd.DataFrame, x: str, y: str | None = None) -> list[ChartSuggestion]:
    """Suggestions for one or two specifically chosen columns."""
    tx = detect_column_type(df[x], x)
    if y is None:
        if tx in NUMERIC_LIKE:
            return [ChartSuggestion("Histogram", x, None, f"'{x}' is numeric -- see its distribution.")]
        if tx in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN, ColumnType.GEOGRAPHIC):
            return [ChartSuggestion("Bar chart", x, "count", f"'{x}' has a small set of repeated values -- count them.")]
        return []

    ty = detect_column_type(df[y], y)
    suggestions = []
    if tx in NUMERIC_LIKE and ty in NUMERIC_LIKE:
        suggestions.append(ChartSuggestion("Scatter plot", x, y, "Two numeric columns -- look for a relationship."))
    elif tx == ColumnType.DATETIME and ty in NUMERIC_LIKE:
        suggestions.append(ChartSuggestion("Line chart", x, y, "A date/time column against a numeric value -- a trend over time."))
    elif ty == ColumnType.DATETIME and tx in NUMERIC_LIKE:
        suggestions.append(ChartSuggestion("Line chart", y, x, "A date/time column against a numeric value -- a trend over time."))
    elif tx in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN, ColumnType.GEOGRAPHIC) and ty in NUMERIC_LIKE:
        suggestions.append(ChartSuggestion("Bar chart", x, y, f"'{x}' groups the data -- compare '{y}' across groups."))
    elif ty in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN, ColumnType.GEOGRAPHIC) and tx in NUMERIC_LIKE:
        suggestions.append(ChartSuggestion("Bar chart", y, x, f"'{y}' groups the data -- compare '{x}' across groups."))
    elif tx in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN) and ty in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN):
        suggestions.append(ChartSuggestion("Cross-tab heatmap", x, y, "Two categorical columns -- see how their categories co-occur."))
    return suggestions


def suggest_for_dataset(df: pd.DataFrame, max_suggestions: int = 8) -> list[ChartSuggestion]:
    """Broad suggestions from the dataset's overall column-type mix, for
    when the user hasn't picked specific columns yet."""
    types = _types(df, list(df.columns))
    numeric = [c for c, t in types.items() if t in NUMERIC_LIKE]
    categorical = [c for c, t in types.items() if t in (ColumnType.CATEGORICAL, ColumnType.BOOLEAN, ColumnType.GEOGRAPHIC)]
    datetime_cols = [c for c, t in types.items() if t == ColumnType.DATETIME]

    suggestions: list[ChartSuggestion] = []
    if len(numeric) >= 2:
        suggestions.append(ChartSuggestion(
            "Correlation heatmap", None, None,
            f"{len(numeric)} numeric columns -- a correlation heatmap shows how they relate at a glance.",
        ))
        suggestions.append(ChartSuggestion("Scatter plot", numeric[0], numeric[1],
                                            f"'{numeric[0]}' vs '{numeric[1]}' -- both numeric."))
    if datetime_cols and numeric:
        suggestions.append(ChartSuggestion("Line chart", datetime_cols[0], numeric[0],
                                            f"'{datetime_cols[0]}' looks like a date -- trend of '{numeric[0]}' over time."))
    if categorical and numeric:
        suggestions.append(ChartSuggestion("Bar chart", categorical[0], numeric[0],
                                            f"Compare '{numeric[0]}' across '{categorical[0]}' groups."))
    for col in categorical[:2]:
        suggestions.append(ChartSuggestion("Pie / donut chart", col, "count", f"See the share of each category in '{col}'."))
    for col in numeric[:2]:
        suggestions.append(ChartSuggestion("Histogram", col, None, f"See the distribution of '{col}'."))
    return suggestions[:max_suggestions]
