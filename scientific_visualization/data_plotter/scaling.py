from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .model import DatasetTable


@dataclass(frozen=True)
class ScalingColumns:
    x: int
    y: int


def _normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def infer_scaling_columns(dataset: DatasetTable) -> ScalingColumns:
    """Infer GPU/node/runtime columns from common scientific header names.

    The inference is deliberately conservative. Generic fallbacks are used only
    when no standard aliases are found.
    """
    names = [_normalize_name(c) for c in dataset.columns]
    x_aliases = (
        "totalgpus", "gpus", "gpu", "ngpus", "numgpus", "processors",
        "processes", "nprocesses", "cores", "ncores", "ranks", "nranks",
        "nodes", "node", "nnode",
    )
    y_aliases = (
        "simulationtime", "runtime", "time", "elapsedtime", "walltime",
        "executiontime", "elapsed", "seconds", "simtime",
    )

    def find(aliases: Sequence[str], exclude: set[int] | None = None) -> int | None:
        exclude = exclude or set()
        for alias in aliases:
            for i, name in enumerate(names):
                if i not in exclude and (name == alias or alias in name):
                    return i
        return None

    x = find(x_aliases)
    y = find(y_aliases, {x} if x is not None else set())
    if x is None:
        x = 0
    if y is None:
        y = 1 if dataset.column_count > 1 else 0
    return ScalingColumns(x, y)


def finite_sorted(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if not np.any(mask):
        return np.empty(0, dtype=float), np.empty(0, dtype=float)
    x, y = x[mask], y[mask]
    order = np.argsort(x, kind="stable")
    return x[order], y[order]


def strong_scaling(x: np.ndarray, runtime: np.ndarray, *, metric: str = "Runtime") -> tuple[np.ndarray, np.ndarray]:
    """Return standard strong-scaling metrics for one dataset.

    Baseline is the smallest available positive resource count. Speedup is
    T0/Tp and efficiency is speedup/(P/P0).
    """
    x, runtime = finite_sorted(x, runtime)
    positive = (x > 0) & (runtime > 0)
    x, runtime = x[positive], runtime[positive]
    if x.size == 0:
        return x, runtime
    p0, t0 = float(x[0]), float(runtime[0])
    if metric == "Runtime":
        return x, runtime
    speed = t0 / runtime
    if metric == "Speedup":
        return x, speed
    if metric == "Efficiency":
        return x, speed / (x / p0)
    if metric == "Parallel cost":
        return x, runtime * x
    raise ValueError(f"Unknown strong-scaling metric: {metric}")


def weak_scaling(x: np.ndarray, runtime: np.ndarray, workload_factor: float, *, metric: str = "Normalized runtime") -> tuple[np.ndarray, np.ndarray]:
    """Return workload-normalized weak-scaling metrics.

    ``workload_factor`` describes relative problem size for this dataset. It
    must be supplied by the user because problem size cannot safely be inferred
    from a filename alone.
    """
    x, runtime = finite_sorted(x, runtime)
    positive = (x > 0) & (runtime > 0)
    x, runtime = x[positive], runtime[positive]
    factor = float(workload_factor)
    if factor <= 0:
        raise ValueError("Weak-scaling workload factor must be greater than zero")
    if metric == "Runtime per workload":
        return x, runtime / factor
    if metric == "Normalized runtime":
        normalized = runtime / factor
        finite = normalized[np.isfinite(normalized)]
        if finite.size == 0 or finite[0] == 0:
            return x, normalized
        return x, normalized / finite[0]
    if metric == "Efficiency":
        normalized = runtime / factor
        finite = normalized[np.isfinite(normalized)]
        if finite.size == 0 or finite[0] == 0:
            return x, normalized
        return x, finite[0] / normalized
    raise ValueError(f"Unknown weak-scaling metric: {metric}")
