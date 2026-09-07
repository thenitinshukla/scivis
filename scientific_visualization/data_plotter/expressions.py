"""Restricted expression evaluation for user-defined computed columns.

Used by ``DatasetTable.add_computed_column`` (editing) and, with the same
safety model, by curve fitting's custom-formula option. Column names are
referenced by their exact header text; names containing characters that
aren't valid Python identifiers (spaces, punctuation, ...) are matched by
substituting a safe placeholder before evaluation, so a header like
"Total GPUs" works without the user having to rename anything.

Only a fixed, explicit set of NumPy math functions is exposed, `__builtins__`
is removed from the evaluation namespace entirely, and the input is
pre-scanned for anything that looks like attribute access, subscripting, or
a double-underscore name (the usual `eval` sandbox-escape vectors) before
it's ever handed to Python's parser.
"""
from __future__ import annotations

import re

import numpy as np

# Deliberately small and explicit: enough for everyday scientific formulas
# without exposing anything that touches the filesystem, imports, or
# process state.
SAFE_FUNCTIONS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan, "atan2": np.arctan2,
    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
    "exp": np.exp, "log": np.log, "log10": np.log10, "log2": np.log2,
    "sqrt": np.sqrt, "abs": np.abs, "sign": np.sign,
    "min": np.minimum, "max": np.maximum, "clip": np.clip,
    "round": np.round, "floor": np.floor, "ceil": np.ceil,
    "pi": np.pi, "e": np.e,
}

_DISALLOWED_PATTERN = re.compile(r"__|\.\s*\w|\[|\]|;|:=|\bimport\b|\blambda\b")


def _placeholder(index: int) -> str:
    return f"_col{index}_"


def evaluate_column_expression(expression: str, columns: list[str], values: np.ndarray) -> np.ndarray:
    """Evaluate `expression` against `columns`/`values` (as from a
    DatasetTable) and return the resulting 1D array.

    Raises ValueError for an empty/unsafe expression, an unknown name, or
    any evaluation error (e.g. a shape or domain error from NumPy), with a
    message meant to be shown directly to the user.
    """
    expression = (expression or "").strip()
    if not expression:
        raise ValueError("Enter a formula, e.g. \"c / b\" or \"log(a) + 2*b\"")
    if _DISALLOWED_PATTERN.search(expression):
        raise ValueError("Formula contains characters that aren't allowed (only column names, numbers, and math functions/operators)")

    # Replace each column name with a safe placeholder identifier, longest
    # names first so "Total GPUs" is matched whole before "GPUs" would be.
    substituted = expression
    namespace = dict(SAFE_FUNCTIONS)
    for i, name in sorted(enumerate(columns), key=lambda kv: -len(kv[1])):
        if not name:
            continue
        pattern = re.compile(re.escape(name))
        if pattern.search(substituted):
            placeholder = _placeholder(i)
            substituted = pattern.sub(placeholder, substituted)
            namespace[placeholder] = values[:, i].astype(float)

    # Anything left that looks like an identifier and isn't a known function
    # or placeholder is an unrecognized column/name -- fail with a clear
    # message rather than letting NameError leak a confusing traceback, and
    # rather than silently evaluating to garbage.
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

    result = np.asarray(result, dtype=float)
    if result.ndim == 0:
        result = np.full(values.shape[0], float(result))
    if result.shape != (values.shape[0],):
        raise ValueError(f"Formula must produce one value per row ({values.shape[0]}), got shape {result.shape}")
    return result
