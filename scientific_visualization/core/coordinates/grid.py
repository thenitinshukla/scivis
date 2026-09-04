from __future__ import annotations

import numpy as np


def coordinate_centers(vmin: float, vmax: float, n: int) -> np.ndarray:
    if n <= 0:
        return np.empty(0, dtype=float)
    return np.linspace(float(vmin), float(vmax), int(n), endpoint=False) + (vmax - vmin) / (2 * n)


def coordinate_edges(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    if values.size == 1:
        d = 0.5
        return np.array([values[0] - d, values[0] + d])
    mid = 0.5 * (values[:-1] + values[1:])
    return np.concatenate(([values[0] - (mid[0] - values[0])], mid, [values[-1] + (values[-1] - mid[-1])]))
