"""Analysis-oriented transforms, registered into the same operation
registry as cleaning.py (see that module's docstring for the pipeline
model). These change the *shape* or *encoding* of the data rather than
fixing data-quality problems -- filtering, sorting, calculated columns,
group/aggregate, pivot/unpivot, normalization, categorical encoding, and
binning.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .cleaning import operation
from .types import to_object_str

_COMPARATORS = {
    "==": lambda s, v: s == v, "!=": lambda s, v: s != v,
    ">": lambda s, v: s > v, ">=": lambda s, v: s >= v,
    "<": lambda s, v: s < v, "<=": lambda s, v: s <= v,
    "contains": lambda s, v: to_object_str(s).str.contains(str(v), case=False, na=False),
    "not contains": lambda s, v: ~to_object_str(s).str.contains(str(v), case=False, na=False),
    "is null": lambda s, v: s.isna(),
    "is not null": lambda s, v: s.notna(),
}


@operation("filter_rows")
def filter_rows(df: pd.DataFrame, column: str, comparator: str, value=None) -> pd.DataFrame:
    func = _COMPARATORS.get(comparator)
    if func is None:
        raise ValueError(f"Unknown comparator: {comparator!r}")
    series = df[column]
    if comparator in (">", ">=", "<", "<=") :
        series = pd.to_numeric(series, errors="coerce")
        value = float(value)
    mask = func(series, value)
    return df.loc[mask.fillna(False)].reset_index(drop=True)


@operation("sort_rows")
def sort_rows(df: pd.DataFrame, columns: list[str], ascending: bool = True) -> pd.DataFrame:
    return df.sort_values(by=columns, ascending=ascending, na_position="last", kind="stable").reset_index(drop=True)


@operation("select_columns")
def select_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Column(s) not found: {', '.join(missing)}")
    return df.loc[:, columns]


@operation("drop_columns")
def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return df.drop(columns=[c for c in columns if c in df.columns])


@operation("calculated_column")
def calculated_column(df: pd.DataFrame, new_name: str, expression: str) -> pd.DataFrame:
    """`expression` references existing column names verbatim, e.g.
    "revenue / units_sold" -- evaluated with the same restricted-namespace
    safety model as the Data Plotter's computed columns (see
    expressions_pandas.py), just operating on a pandas DataFrame (which may
    have non-numeric columns) instead of a plain float matrix.
    """
    from .expressions_pandas import evaluate_pandas_expression
    df = df.copy()
    df[new_name] = evaluate_pandas_expression(expression, df)
    return df


@operation("group_aggregate")
def group_aggregate(df: pd.DataFrame, group_by: list[str], aggregations: dict[str, str]) -> pd.DataFrame:
    """`aggregations`: {column: agg_name}, agg_name in
    {'sum','mean','median','min','max','count','std','nunique'}."""
    grouped = df.groupby(group_by, dropna=False, observed=True)
    result = grouped.agg(aggregations)
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = ["_".join(map(str, c)) for c in result.columns]
    return result.reset_index()


@operation("pivot")
def pivot(df: pd.DataFrame, index: str, columns: str, values: str, aggfunc: str = "mean") -> pd.DataFrame:
    result = df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc, observed=True)
    result.columns = [str(c) for c in result.columns]
    return result.reset_index()


@operation("unpivot")
def unpivot(df: pd.DataFrame, id_vars: list[str], value_vars: list[str] | None = None,
           var_name: str = "variable", value_name: str = "value") -> pd.DataFrame:
    return df.melt(id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name)


@operation("normalize")
def normalize(df: pd.DataFrame, columns: list[str], method: str = "minmax") -> pd.DataFrame:
    """method: 'minmax' (0-1) | 'zscore' (mean 0, std 1)"""
    df = df.copy()
    for col in columns:
        values = pd.to_numeric(df[col], errors="coerce")
        if method == "minmax":
            lo, hi = values.min(), values.max()
            df[col] = (values - lo) / (hi - lo) if hi != lo else 0.0
        elif method == "zscore":
            mean, std = values.mean(), values.std()
            df[col] = (values - mean) / std if std else 0.0
        else:
            raise ValueError(f"Unknown normalization method: {method!r}")
    return df


@operation("encode_categorical")
def encode_categorical(df: pd.DataFrame, column: str, method: str = "onehot") -> pd.DataFrame:
    """method: 'onehot' | 'label' (integer codes, alphabetical order)"""
    df = df.copy()
    if method == "onehot":
        dummies = pd.get_dummies(df[column], prefix=column, dtype=int)
        df = pd.concat([df.drop(columns=[column]), dummies], axis=1)
    elif method == "label":
        codes, _uniques = pd.factorize(df[column], sort=True)
        df[f"{column}_code"] = codes
    else:
        raise ValueError(f"Unknown encoding method: {method!r}")
    return df


@operation("bin_column")
def bin_column(df: pd.DataFrame, column: str, bins: int = 5, new_name: str | None = None,
               labels: list[str] | None = None) -> pd.DataFrame:
    df = df.copy()
    values = pd.to_numeric(df[column], errors="coerce")
    df[new_name or f"{column}_bin"] = pd.cut(values, bins=bins, labels=labels)
    return df
