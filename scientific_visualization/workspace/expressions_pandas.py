"""Restricted expression evaluation over a pandas DataFrame's columns.

Same safety model as `data_plotter.expressions` (no `eval` of arbitrary
Python, no builtins, a fixed set of NumPy math functions) -- see that
module's docstring for the details and the rationale. This version
operates directly on pandas Series instead of a plain float matrix, so a
calculated column works naturally alongside a workspace DataFrame's
non-numeric columns without forcing the whole frame to numeric up front;
only the columns actually referenced by the expression get coerced.
"""
from __future__ import annotations

import re

import pandas as pd

from ..data_plotter.expressions import SAFE_FUNCTIONS, _DISALLOWED_PATTERN, _placeholder


def evaluate_pandas_expression(expression: str, df: pd.DataFrame) -> pd.Series:
    expression = (expression or "").strip()
    if not expression:
        raise ValueError('Enter a formula, e.g. "revenue / units_sold" or "log(price)"')
    if _DISALLOWED_PATTERN.search(expression):
        raise ValueError("Formula contains characters that aren't allowed (only column names, numbers, and math functions/operators)")

    substituted = expression
    namespace = dict(SAFE_FUNCTIONS)
    for i, name in sorted(enumerate(df.columns), key=lambda kv: -len(kv[1])):
        if not name:
            continue
        pattern = re.compile(re.escape(name))
        if pattern.search(substituted):
            placeholder = _placeholder(i)
            substituted = pattern.sub(placeholder, substituted)
            namespace[placeholder] = pd.to_numeric(df[name], errors="coerce")

    leftover_names = set(re.findall(r"\b[A-Za-z_]\w*\b", substituted)) - set(namespace)
    if leftover_names:
        raise ValueError(f"Unknown name(s) in formula: {', '.join(sorted(leftover_names))}")

    try:
        code = compile(substituted, "<column expression>", "eval")
    except SyntaxError as exc:
        raise ValueError(f"Could not parse formula: {exc.msg}") from exc

    try:
        result = eval(code, {"__builtins__": {}}, namespace)  # noqa: S307 -- restricted namespace above
    except Exception as exc:
        raise ValueError(f"Could not evaluate formula: {exc}") from exc

    if not isinstance(result, pd.Series):
        result = pd.Series([result] * len(df), index=df.index)
    return result
