"""
Analysis helpers: smoothing and spatial-reduction-over-time, used by the
Fields/Grid tab's advanced options.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

try:
    from scipy.ndimage import gaussian_filter, uniform_filter1d
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False


def smooth_1d(y: np.ndarray, method: str = "None", window: int = 5) -> np.ndarray:
    """Smooth a 1D array. `method` is 'None', 'Moving average', or 'Gaussian'.
    `window` is the moving-average box size (points) or the Gaussian sigma
    (points), respectively."""
    if method in (None, "None") or window <= 1:
        return y
    if method == "Moving average":
        if _HAVE_SCIPY:
            return uniform_filter1d(y, size=int(window), mode="nearest")
        kernel = np.ones(int(window)) / int(window)
        return np.convolve(y, kernel, mode="same")
    if method == "Gaussian":
        if _HAVE_SCIPY:
            return gaussian_filter(y, sigma=float(window) / 2.0, mode="nearest")
        # crude fallback gaussian kernel
        sigma = max(float(window) / 2.0, 1e-6)
        radius = max(int(3 * sigma), 1)
        x = np.arange(-radius, radius + 1)
        kernel = np.exp(-0.5 * (x / sigma) ** 2)
        kernel /= kernel.sum()
        return np.convolve(y, kernel, mode="same")
    return y


def smooth_2d(data: np.ndarray, method: str = "None", window: int = 3) -> np.ndarray:
    """Smooth a 2D array. `method` is 'None', 'Moving average', or 'Gaussian'."""
    if method in (None, "None") or window <= 1:
        return data
    if not _HAVE_SCIPY:
        return data  # 2D smoothing without scipy is skipped rather than done poorly
    if method == "Moving average":
        from scipy.ndimage import uniform_filter
        return uniform_filter(data, size=int(window), mode="nearest")
    if method == "Gaussian":
        return gaussian_filter(data, sigma=float(window) / 2.0, mode="nearest")
    return data


def reduce_grid_series(files: list, reduction: str = "mean", smoothing: Optional[dict] = None,
                       quantity: Optional[str] = None, average_direction: str | None = None):
    """Reduce one compatible grid quantity over space for each time step.

    ``average_direction`` optionally applies the directional-average operation
    before the scalar temporal reduction. The original files are never modified.
    """
    from .io.grid import GridFile
    from .analysis.derived import parse_average_direction

    allowed = {"mean", "sum", "integral", "max", "min", "rms"}
    if reduction not in allowed:
        raise ValueError(f"unknown reduction '{reduction}'. Choose from {sorted(allowed)}")

    direction = parse_average_direction(average_direction) if average_direction else None
    times, iters, values = [], [], []
    label, units, selected_name, selected_shape = "", "", None, None
    errors = []
    for fname in files:
        try:
            gf = GridFile.load(fname)
        except Exception as exc:
            errors.append(f"{fname}: {exc}")
            continue
        if quantity and gf.dataset_name != quantity and gf.name != quantity and gf.label != quantity:
            continue
        if selected_name is None:
            selected_name, selected_shape = gf.dataset_name, gf.shape
        if gf.dataset_name != selected_name or gf.shape != selected_shape:
            continue
        data = np.asarray(gf.data, dtype=float)
        # Convert once to Dataset physical axis ordering, then average over the
        # requested axes. np.mean/max/etc. are already implemented in optimized
        # compiled NumPy loops, so moving these reductions to C++ would add
        # conversion overhead without a meaningful benefit.
        if direction:
            ds = gf.to_dataset()
            axis_indices = tuple(ds.axis_index("x" + str(ord(i) - ord("x") + 1)) for i in direction)
            data = np.mean(ds.data, axis=axis_indices)
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            values.append(np.nan)
        elif reduction == "mean":
            values.append(float(np.mean(finite)))
        elif reduction == "sum":
            values.append(float(np.sum(finite)))
        elif reduction == "integral":
            cell = 1.0
            for ax in gf.axes:
                if ax.n > 1:
                    cell *= abs((ax.max - ax.min) / ax.n)
            values.append(float(np.sum(finite) * cell))
        elif reduction == "max":
            values.append(float(np.max(finite)))
        elif reduction == "min":
            values.append(float(np.min(finite)))
        else:
            values.append(float(np.sqrt(np.mean(finite ** 2))))
        times.append(gf.time)
        iters.append(gf.iteration)
        label, units = gf.label, gf.units

    if not values:
        detail = f" Skipped {len(errors)} unreadable file(s)." if errors else ""
        raise ValueError("No compatible grid frames were found for the selected quantity." + detail)

    order = np.argsort(times)
    times = np.asarray(times)[order]
    iters = np.asarray(iters)[order]
    values = np.asarray(values)[order]
    if smoothing and smoothing.get("method") not in (None, "None"):
        values = smooth_1d(values, smoothing["method"], smoothing.get("window", 5))
    return times, iters, values, {"label": label, "units": units, "reduction": reduction,
                                  "quantity": selected_name, "skipped_files": errors,
                                  "average_direction": direction}
