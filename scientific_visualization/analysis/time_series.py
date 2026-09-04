from __future__ import annotations

from pathlib import Path
import numpy as np

from ..io.simulation import SimulationReader


class TimeSeriesAnalyzer:
    def __init__(self, reader=None):
        self.reader = reader or SimulationReader()

    def track_point(self, files, quantity, positions=None):
        times, values = [], []
        for path in files:
            ds = self.reader.load(path, quantity=quantity)
            if ds.ndim == 0:
                value = float(ds.data)
            elif positions is None:
                value = float(np.mean(ds.data))
            else:
                idx = []
                for i, p in enumerate(positions):
                    c = ds.coordinates[i].values
                    idx.append(int(np.argmin(np.abs(c - p))))
                value = float(ds.data[tuple(idx)])
            times.append(ds.time if ds.time is not None else len(times))
            values.append(value)
        return np.asarray(times), np.asarray(values)

    def reduce(self, files, quantity, reduction="mean"):
        times, vals = [], []
        reducers = {"mean": np.mean, "sum": np.sum, "max": np.max, "min": np.min, "rms": lambda a: np.sqrt(np.mean(np.asarray(a)**2))}
        if reduction not in reducers:
            raise ValueError(f"Unsupported reduction '{reduction}'")
        for path in files:
            ds = self.reader.load(path, quantity=quantity)
            times.append(ds.time if ds.time is not None else len(times))
            vals.append(float(reducers[reduction](ds.data)))
        return np.asarray(times), np.asarray(vals)


def reduce_grid_series(files, reduction="mean", smoothing=None, quantity=None):
    """Compatibility wrapper for Simulation grid-field time-series reductions."""
    from ..io.grid import GridFile
    allowed = {"mean", "sum", "integral", "max", "min", "rms"}
    if reduction not in allowed:
        raise ValueError(f"unknown reduction '{reduction}'. Choose from {sorted(allowed)}")
    times, iters, values = [], [], []
    label = units = ""
    selected_name = selected_shape = None
    for fname in files:
        try:
            gf = GridFile.load(fname)
        except Exception:
            continue
        if quantity and gf.dataset_name != quantity and gf.name != quantity and gf.label != quantity:
            continue
        if selected_name is None:
            selected_name, selected_shape = gf.dataset_name, gf.shape
        if gf.dataset_name != selected_name or gf.shape != selected_shape:
            continue
        data = np.asarray(gf.data)
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            value = np.nan
        elif reduction == "mean":
            value = np.mean(finite)
        elif reduction == "sum":
            value = np.sum(finite)
        elif reduction == "integral":
            # Integrate using the actual physical cell-centre coordinates.
            # Do not assume unit or uniform spacing.
            arr = np.asarray(gf.data, dtype=float)
            for physical_axis in range(gf.ndim):
                np_axis = gf.ndim - 1 - physical_axis
                coords = gf.axes[physical_axis].values()
                arr = np.trapezoid(arr, coords, axis=np_axis)
            value = float(arr)
        elif reduction == "max":
            value = np.max(finite)
        elif reduction == "min":
            value = np.min(finite)
        else:
            value = np.sqrt(np.mean(finite ** 2))
        times.append(float(gf.time)); iters.append(int(gf.iteration)); values.append(float(value))
        label, units = gf.label, gf.units
    if not values:
        raise ValueError("No compatible grid frames were found for the selected quantity.")
    order = np.argsort(times)
    times, iters, values = np.asarray(times)[order], np.asarray(iters)[order], np.asarray(values)[order]
    if smoothing and smoothing.get("method") not in (None, "None"):
        from .smoothing import smooth_1d
        values = smooth_1d(values, smoothing["method"], smoothing.get("window", 5))
    return times, iters, values, {"label": label, "units": units, "reduction": reduction, "quantity": selected_name}
