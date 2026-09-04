"""
Reader for Simulation grid/field HDF5 files (e1, e2, b3, charge density, etc.)

Simulation grid files follow this layout (mirrors z_data_grid / hdf5_gridfileinfo.pro
from the original Scientific Visualization IDL package):

    /                       (root group)
        attrs: NAME, TYPE, TIME, ITER, UNITS, LABEL
        <quantity dataset(s)>   e.g. "e1", or several time-tagged datasets
            attrs: UNITS, LONG_NAME (a.k.a LABEL), TAG
    /AXIS/
        AXIS1, AXIS2, [AXIS3]   each a 2-element [min, max] dataset
            attrs: NAME, UNITS, LONG_NAME

Older files sometimes store UNITS/LABEL on the dataset instead of the root
group; both are checked, dataset-level attributes win.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np

from ..core.data import CoordinateAxis, Dataset


def _attr(obj, name, default=""):
    """Read an HDF5 attribute and normalize scalar/one-element arrays.

    Simulation files in the wild use both true scalar attributes and one-element
    NumPy arrays for metadata such as TIME and ITER. Returning a Python scalar
    for size-one arrays prevents ``float(array([...] ))`` / ``int(array([...] ))``
    conversion failures while preserving genuinely multi-valued attributes.
    """
    if name not in obj.attrs:
        return default
    val = obj.attrs[name]
    if isinstance(val, bytes):
        return val.decode("utf-8", "replace").strip()
    if isinstance(val, np.ndarray):
        if val.ndim == 0:
            val = val.item()
        elif val.size == 1:
            val = val.reshape(-1)[0]
            if isinstance(val, bytes):
                return val.decode("utf-8", "replace").strip()
            if isinstance(val, np.generic):
                return val.item()
            return val
        elif val.dtype.kind in ("S", "O", "U"):
            return [v.decode("utf-8", "replace").strip() if isinstance(v, bytes) else str(v) for v in val.reshape(-1)]
        else:
            return val
    if isinstance(val, np.generic):
        return val.item()
    if isinstance(val, str):
        return val.strip()
    return val


def _scalar_attr(obj, name, default, cast):
    """Read a scalar numeric attribute, accepting true or one-element scalars."""
    value = _attr(obj, name, default)
    if isinstance(value, np.ndarray):
        if value.size != 1:
            raise ValueError(
                f"HDF5 attribute '{name}' in '{getattr(obj, 'name', '/')}' must be scalar; "
                f"received array with shape {value.shape}"
            )
        value = value.reshape(-1)[0]
    if value is None or value == "":
        value = default
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid scalar HDF5 attribute '{name}': {value!r}") from exc


@dataclass
class AxisInfo:
    name: str
    label: str
    units: str
    min: float
    max: float
    n: int

    def values(self) -> np.ndarray:
        """Cell-centered coordinate values along this axis."""
        return self.min + (np.arange(self.n) + 0.5) * (self.max - self.min) / self.n


@dataclass
class GridFile:
    """Loaded representation of a single Simulation grid/field HDF5 file."""

    filename: str
    name: str = ""
    label: str = ""
    units: str = ""
    time: float = 0.0
    time_units: str = ""
    iteration: int = 0
    ndim: int = 0
    shape: tuple = field(default_factory=tuple)
    axes: list = field(default_factory=list)   # list[AxisInfo], axes[0] is fastest-varying (x1)
    data: Optional[np.ndarray] = None
    dataset_name: str = ""

    @classmethod
    def info(cls, filename: str) -> "GridFile":
        """Read metadata only (no field data) -- fast, for file browsing."""
        return cls._load(filename, read_data=False)

    @classmethod
    def load(cls, filename: str) -> "GridFile":
        """Read metadata and the field data array."""
        return cls._load(filename, read_data=True)

    @classmethod
    def _load(cls, filename: str, read_data: bool) -> "GridFile":
        gf = cls(filename=filename)
        with h5py.File(filename, "r") as f:
            root = f["/"]

            dataset_names = [k for k in root.keys() if isinstance(root[k], h5py.Dataset)]
            if not dataset_names:
                raise ValueError(f"'{filename}' has no datasets")

            # In Simulation files there is usually exactly one field dataset whose
            # name matches the physical quantity (e.g. "e1", "charge").
            ds_name = dataset_names[0]
            dset = root[ds_name]
            gf.dataset_name = ds_name

            gf.name = _attr(root, "NAME", ds_name) or ds_name
            gf.label = _attr(dset, "LONG_NAME", _attr(root, "LABEL", gf.name))
            gf.units = _attr(dset, "UNITS", _attr(root, "UNITS", ""))
            gf.time = _scalar_attr(root, "TIME", 0.0, float)
            gf.time_units = _attr(root, "TIME UNITS", "") or _attr(root, "TIME_UNITS", "")
            gf.iteration = _scalar_attr(root, "ITER", 0, int)
            gf.shape = tuple(dset.shape)
            gf.ndim = len(gf.shape)

            if "AXIS" in root and isinstance(root["AXIS"], h5py.Group):
                axgroup = root["AXIS"]
                axis_keys = sorted(axgroup.keys())  # AXIS1, AXIS2, AXIS3
                axes = []
                # numpy/HDF5 stores fastest-varying axis last in `shape`,
                # AXIS1 corresponds to the last shape index.
                for i, key in enumerate(axis_keys):
                    axds = axgroup[key]
                    rng = np.asarray(axds[()], dtype=float).flatten()
                    aname = _attr(axds, "NAME", key)
                    if isinstance(aname, str) and aname.endswith(" axis"):
                        aname = aname[: -len(" axis")]
                    n = gf.shape[gf.ndim - 1 - i] if gf.ndim >= i + 1 else 0
                    axes.append(
                        AxisInfo(
                            name=aname or key,
                            label=_attr(axds, "LONG_NAME", aname or key),
                            units=_attr(axds, "UNITS", ""),
                            min=float(rng[0]),
                            max=float(rng[1]) if len(rng) > 1 else float(rng[0]),
                            n=int(n),
                        )
                    )
                gf.axes = axes
            else:
                # No axis info -- fall back to plain index axes
                gf.axes = [
                    AxisInfo(name=f"x{i+1}", label=f"x{i+1}", units="", min=0.0, max=float(n), n=n)
                    for i, n in enumerate(reversed(gf.shape))
                ]

            if read_data:
                gf.data = np.asarray(dset[()])

        return gf

    # -- convenience -----------------------------------------------------
    def lineout(self, axis: int = 0, index: Optional[int] = None) -> tuple:
        """
        Extract a 1D lineout along `axis` (0 = x1, 1 = x2, ...), holding the
        other coordinate(s) fixed at `index` (defaults to the middle of the
        array). Returns (coord_values, data_values).
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load(), not .info()")

        data = self.data
        ndim = data.ndim
        # numpy axis order is reversed relative to Simulation x1,x2,... ordering
        np_axis = ndim - 1 - axis

        if index is None:
            index = tuple(s // 2 for s in data.shape)

        if ndim == 1:
            values = data
        else:
            slicer = list(index) if isinstance(index, (list, tuple)) else [index] * ndim
            slicer[np_axis] = slice(None)
            values = data[tuple(slicer)]

        coord = self.axes[axis].values()
        return coord, values

    def lineout_at(self, along_axis: int, fixed_value: float, fixed_axis: Optional[int] = None):
        """
        1D lineout along `along_axis`, holding the other axis at the
        *physical* coordinate `fixed_value` (linearly interpolated between
        the two nearest grid points -- no need to know array indices).
        For 2D data `fixed_axis` is inferred automatically.
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load(), not .info()")

        ndim = self.data.ndim
        if fixed_axis is None:
            remaining = [a for a in range(ndim) if a != along_axis]
            if len(remaining) != 1:
                raise ValueError("fixed_axis must be given explicitly when ndim > 2")
            fixed_axis = remaining[0]

        axis_info = self.axes[fixed_axis]
        coords = axis_info.values()
        frac_idx = float(np.interp(fixed_value, coords, np.arange(axis_info.n)))
        frac_idx = min(max(frac_idx, 0.0), axis_info.n - 1)
        i0 = int(np.floor(frac_idx))
        i1 = min(i0 + 1, axis_info.n - 1)
        w = frac_idx - i0

        np_axis = ndim - 1 - fixed_axis
        slicer0 = [slice(None)] * ndim
        slicer0[np_axis] = i0
        slicer1 = [slice(None)] * ndim
        slicer1[np_axis] = i1
        v0 = self.data[tuple(slicer0)]
        v1 = self.data[tuple(slicer1)]
        values = v0 * (1 - w) + v1 * w

        along_coords = self.axes[along_axis].values()
        return along_coords, values

    def to_dataset(self) -> Dataset:
        """Convert the legacy reader representation to the shared Dataset model.

        Simulation stores x1 in the last NumPy/HDF5 dimension, so the returned
        Dataset is transposed into physical axis order (x1, x2, ...).
        No additional copy is requested by NumPy where a view is possible.
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load() first")
        data = self.data
        axes = tuple(self.axes)
        if self.ndim > 1:
            data = np.transpose(data, axes=tuple(reversed(range(self.ndim))))
        coordinates = tuple(
            CoordinateAxis(name=ax.name, values=ax.values(), units=ax.units, label=ax.label)
            for ax in axes
        )
        return Dataset(
            name=self.name or self.dataset_name,
            data=data,
            axes=tuple(ax.name for ax in axes),
            coordinates=coordinates,
            units=self.units,
            time=self.time,
            time_units=self.time_units,
            metadata={"dataset_name": self.dataset_name, "label": self.label, "iteration": self.iteration},
            source=self.filename,
            simulation_metadata={"format": "Simulation", "iteration": self.iteration},
        )

    def extent(self) -> list:
        """Return [xmin, xmax, ymin, ymax] suitable for matplotlib imshow."""
        if len(self.axes) >= 2:
            return [self.axes[0].min, self.axes[0].max, self.axes[1].min, self.axes[1].max]
        elif len(self.axes) == 1:
            return [self.axes[0].min, self.axes[0].max, 0, 1]
        return [0, 1, 0, 1]

    def slice2d(self, axis: int, index: int) -> "GridFile":
        """Extract a 2D slice from a 3D grid, holding `axis` (0=x1, 1=x2,
        2=x3) fixed at grid index `index`. Returns a new GridFile carrying
        only the remaining two axes, so every existing 2D code path
        (plotting, lineouts, colorbar, derived quantities, ...) can consume
        it exactly like a genuinely 2D dataset -- no special-casing needed
        downstream. Does not modify `self` or its underlying array (the
        slice is a NumPy view, not a copy).

        This is what lets 3D Simulation files (e.g. a "thin" 3D run with
        only a couple of points along one axis) be opened and viewed in
        the 2D tab instead of failing outright.
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load(), not .info()")
        if self.ndim != 3:
            raise ValueError(f"slice2d requires a 3D dataset; this dataset is {self.ndim}D")
        if axis not in (0, 1, 2):
            raise ValueError("axis must be 0, 1, or 2 (corresponding to x1, x2, x3)")
        fixed_axis = self.axes[axis]
        if not (0 <= index < fixed_axis.n):
            raise ValueError(
                f"slice index {index} is out of range for axis {fixed_axis.name} "
                f"which has {fixed_axis.n} point(s) (valid range 0..{fixed_axis.n - 1})"
            )
        # numpy axis order is reversed relative to Simulation x1,x2,... ordering
        np_axis = self.ndim - 1 - axis
        slicer = [slice(None)] * self.ndim
        slicer[np_axis] = index
        data2d = self.data[tuple(slicer)]
        remaining_axes = [a for i, a in enumerate(self.axes) if i != axis]
        fixed_value = float(fixed_axis.values()[index])

        return GridFile(
            filename=self.filename,
            name=self.name,
            label=f"{self.label} (slice: {fixed_axis.name}={fixed_value:.6g} {fixed_axis.units})".strip(),
            units=self.units,
            time=self.time,
            time_units=self.time_units,
            iteration=self.iteration,
            ndim=2,
            shape=tuple(data2d.shape),
            axes=remaining_axes,
            data=data2d,
            dataset_name=self.dataset_name,
        )


def is_grid_file(filename: str) -> bool:
    """Best-effort check for whether an HDF5 file looks like an Simulation grid file."""
    try:
        with h5py.File(filename, "r") as f:
            has_dataset = any(isinstance(f[k], h5py.Dataset) for k in f.keys())
            return has_dataset and "AXIS" in f
    except Exception:
        return False
