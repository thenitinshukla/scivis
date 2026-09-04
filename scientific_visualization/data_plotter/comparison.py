from __future__ import annotations

import numpy as np


def finite_pair(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


def normalize_to_first(x, y):
    x, y = finite_pair(x, y)
    if y.size == 0:
        return x, y
    p0 = y[0]
    if p0 == 0:
        raise ValueError("Cannot normalize Y because the first value is zero")
    return x, y / p0


def speedup(x, y):
    x, y = finite_pair(x, y)
    if y.size == 0:
        return x, y
    p0 = y[0]
    if p0 == 0:
        raise ValueError("Cannot compute speedup because the baseline is zero")
    return x, p0 / y


def efficiency(x, y):
    x, y = finite_pair(x, y)
    if y.size == 0:
        return x, y
    p0 = y[0]
    if p0 == 0:
        raise ValueError("Cannot compute efficiency because the baseline is zero")
    x0 = x[0]
    if x0 == 0:
        raise ValueError("Cannot compute efficiency because the baseline resource count is zero")
    return x, (p0 / y) / (x / x0)


def transform_for_preset(x, y, preset: str):
    if preset == "Normalize Y to first":
        return normalize_to_first(x, y)
    if preset == "Strong scaling: speedup":
        return speedup(x, y)
    if preset == "Strong scaling: efficiency":
        return efficiency(x, y)
    return finite_pair(x, y)
