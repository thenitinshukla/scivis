from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import sklearn  # noqa: F401
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


@dataclass
class FeatureSet:
    """Numerical feature matrix plus provenance information."""
    values: np.ndarray
    feature_names: tuple[str, ...]
    sample_coordinates: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.values = np.asarray(self.values, dtype=float)
        if self.values.ndim != 2:
            raise ValueError("Feature matrix must be two-dimensional")
        if len(self.feature_names) != self.values.shape[1]:
            raise ValueError("feature_names must match the number of columns")
        if self.sample_coordinates is not None:
            coords = np.asarray(self.sample_coordinates, dtype=float)
            if coords.ndim != 2 or coords.shape[0] != self.values.shape[0]:
                raise ValueError("sample_coordinates must have one row per sample")
            self.sample_coordinates = coords


@dataclass
class MLResult:
    """Standard result container for ML operations."""
    method: str
    output: Any
    model: Any = None
    feature_set: FeatureSet | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def estimator_available() -> bool:
    return _SKLEARN_AVAILABLE


def require_sklearn() -> None:
    if not _SKLEARN_AVAILABLE:
        raise ImportError(
            "Machine-learning features require scikit-learn. "
            "Install it with `pip install scikit-learn`."
        )
