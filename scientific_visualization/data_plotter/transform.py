from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class TransformPipeline:
    """Small, serializable transformation definition for plotted X/Y arrays."""

    x_scale: float = 1.0
    y_scale: float = 1.0
    x_offset: float = 0.0
    y_offset: float = 0.0
    normalize_y: str | None = None  # None, "max", "first"
    subtract_first_y: bool = False
    y_operation: str | None = None  # None, abs, square, sqrt, log
    remove_nonfinite: bool = True
    metadata: dict = field(default_factory=dict)

    def apply(self, x, y) -> tuple[np.ndarray, np.ndarray]:
        return apply_transforms(x, y, self)


def apply_transforms(x, y, pipeline: TransformPipeline | None = None):
    p = pipeline or TransformPipeline()
    xx = np.asarray(x, dtype=float).copy()
    yy = np.asarray(y, dtype=float).copy()

    xx = xx * p.x_scale + p.x_offset
    yy = yy * p.y_scale + p.y_offset

    if p.subtract_first_y and yy.size:
        finite = yy[np.isfinite(yy)]
        if finite.size:
            yy = yy - finite[0]
    if p.normalize_y:
        finite = yy[np.isfinite(yy)]
        if finite.size:
            if p.normalize_y == "max":
                denom = np.max(np.abs(finite))
            elif p.normalize_y == "first":
                denom = finite[0]
            else:
                raise ValueError(f"Unknown Y normalization: {p.normalize_y}")
            if denom == 0:
                raise ValueError("Cannot normalize Y because the normalization value is zero")
            yy = yy / denom

    operations = {
        None: lambda a: a,
        "abs": np.abs,
        "square": np.square,
        "sqrt": lambda a: np.sqrt(a),
        "log": lambda a: np.log(a),
    }
    if p.y_operation not in operations:
        raise ValueError(f"Unknown Y operation: {p.y_operation}")
    yy = operations[p.y_operation](yy)

    if p.remove_nonfinite:
        mask = np.isfinite(xx) & np.isfinite(yy)
        xx, yy = xx[mask], yy[mask]
    return xx, yy
