from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import numpy as np


@dataclass(frozen=True)
class CoordinateAxis:
    name: str
    values: np.ndarray
    units: str = ""
    label: str = ""

    def __post_init__(self):
        values = np.asarray(self.values)
        if values.ndim != 1:
            raise ValueError(f"Coordinate axis '{self.name}' must be one-dimensional")
        object.__setattr__(self, "values", values)

    @property
    def size(self) -> int:
        return int(self.values.size)

    @property
    def is_uniform(self) -> bool:
        """True if consecutive coordinate values are evenly spaced.

        Physics operators may only use the fast, OpenMP-parallelized native
        backend (which assumes a constant grid spacing `h`) when every axis
        of a Dataset reports `is_uniform`; otherwise they must fall back to
        the `np.gradient`-based implementation, which handles non-uniform
        spacing correctly. See physics/native_backend.py.
        """
        if self.values.size < 3:
            return True
        diffs = np.diff(self.values)
        if diffs.size == 0:
            return True
        scale = max(float(np.max(np.abs(diffs))), 1e-300)
        return bool(np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-9 * scale))

    @property
    def spacing(self) -> float:
        """Grid spacing for a uniform axis. Raises if the axis isn't uniform
        (check `is_uniform` first) or has fewer than 2 points."""
        if self.values.size < 2:
            raise ValueError(f"Coordinate axis '{self.name}' needs at least 2 points to have a spacing")
        if not self.is_uniform:
            raise ValueError(f"Coordinate axis '{self.name}' is not uniformly spaced")
        return float(self.values[1] - self.values[0])


@dataclass
class Dataset:
    """Common scientific dataset abstraction shared by I/O, analysis, and renderers.

    The array is intentionally stored by reference. Renderers and analyses should slice
    or derive views instead of copying the source data unless a copy is required.
    """

    name: str
    data: np.ndarray
    axes: tuple[str, ...]
    coordinates: tuple[CoordinateAxis, ...] = ()
    units: str = ""
    time: Optional[float] = None
    time_units: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    simulation_metadata: Mapping[str, Any] = field(default_factory=dict)
    components: Mapping[str, "Dataset"] = field(default_factory=dict)
    derived_from: tuple[str, ...] = ()

    def __post_init__(self):
        self.data = np.asarray(self.data)
        if self.data.ndim != len(self.axes):
            raise ValueError(f"Dataset '{self.name}' has {self.data.ndim} dimensions but {len(self.axes)} axes")
        if self.coordinates and len(self.coordinates) != self.data.ndim:
            raise ValueError("Number of coordinates must match data dimensionality")
        if self.coordinates:
            for i, coord in enumerate(self.coordinates):
                if coord.size != self.data.shape[i]:
                    # HDF5/Simulation readers may expose numpy dimensions in reverse physical order.
                    # Such datasets should be normalized before constructing Dataset.
                    raise ValueError(f"Coordinate '{coord.name}' length {coord.size} does not match axis {i} size {self.data.shape[i]}")

    @property
    def ndim(self) -> int:
        return self.data.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.data.shape)

    @property
    def is_scalar(self) -> bool:
        return not self.components and self.ndim >= 0

    @property
    def is_vector(self) -> bool:
        return bool(self.components)

    def axis_index(self, axis: str | int) -> int:
        if isinstance(axis, int):
            if not 0 <= axis < self.ndim:
                raise IndexError(axis)
            return axis
        key = axis.lower()
        aliases = {f"x{i+1}": i for i in range(self.ndim)}
        aliases.update({name.lower(): i for i, name in enumerate(self.axes)})
        if key not in aliases:
            raise KeyError(f"Unknown axis '{axis}'")
        return aliases[key]

    def axis(self, axis: str | int) -> CoordinateAxis:
        return self.coordinates[self.axis_index(axis)]

    def summary(self) -> str:
        src = Path(self.source).name if self.source else "in-memory"
        return f"{self.name}: shape={self.shape}, axes={self.axes}, units={self.units!r}, source={src}"
