from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Mapping
from ..core.data import Dataset
from . import native_backend as _native

@dataclass(frozen=True)
class PhysicsAnalysis:
    name: str
    result: Dataset

class PhysicsEngine:
    """Coordinate-aware vector calculus and common field operations.

    Differential operators (gradient/divergence/curl/laplacian) use the
    OpenMP-parallelized native backend automatically whenever every
    coordinate axis involved is confirmed uniformly spaced (see
    `CoordinateAxis.is_uniform`); otherwise they fall back to the
    np.gradient-based implementation below, which correctly handles
    non-uniform spacing. Both paths produce numerically equivalent
    results -- see tests/test_native_physics_backend.py -- so this
    switch never changes a scientific result, only how fast it runs.
    Call `PhysicsEngine().backend_status()` to see which path is active.
    """

    @staticmethod
    def backend_status() -> str:
        return _native.backend_name()

    def _check_compatible(self, fields: Mapping[str, Dataset]):
        vals = list(fields.values())
        if not vals:
            raise ValueError("At least one field is required")
        base = vals[0]
        for ds in vals[1:]:
            if ds.shape != base.shape or ds.axes != base.axes:
                raise ValueError("Fields must have compatible shape and axes")
        return base

    def magnitude(self, components: Mapping[str, Dataset], name="|A|") -> Dataset:
        base = self._check_compatible(components)
        data = np.sqrt(sum(np.asarray(ds.data, dtype=float) ** 2 for ds in components.values()))
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {**dict(base.metadata), "physics_operation":"magnitude", "components":tuple(components)},
                       base.source, base.simulation_metadata, derived_from=tuple(components))

    def dot(self, a: Mapping[str, Dataset], b: Mapping[str, Dataset], name="A·B") -> Dataset:
        names = set(a) & set(b)
        if not names: raise ValueError("Dot product requires matching component names")
        base = self._check_compatible({k:a[k] for k in names})
        self._check_compatible({k:b[k] for k in names})
        data = sum(np.asarray(a[k].data) * np.asarray(b[k].data) for k in names)
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {"physics_operation":"dot", "components":tuple(sorted(names))}, base.source, base.simulation_metadata,
                       derived_from=tuple(sorted(names)))

    def cross(self, a: Mapping[str, Dataset], b: Mapping[str, Dataset], names=("x1","x2","x3")):
        if any(k not in a or k not in b for k in names): raise ValueError("Cross product requires x1, x2, x3 components")
        base = self._check_compatible({k:a[k] for k in names})
        self._check_compatible({k:b[k] for k in names})
        out = np.cross(np.stack([a[k].data for k in names], axis=-1), np.stack([b[k].data for k in names], axis=-1), axis=-1)
        return {
            k: Dataset(f"(A×B)_{k}", out[...,i], base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {"physics_operation":"cross", "component":k}, base.source, base.simulation_metadata)
            for i,k in enumerate(names)
        }

    def gradient(self, dataset: Dataset, axis: str|int):
        ai = dataset.axis_index(axis)
        coord = dataset.coordinates[ai]
        if len(coord.values) < 2: raise ValueError("At least two coordinate points are required")
        if coord.is_uniform:
            data = _native.gradient_uniform(np.asarray(dataset.data, dtype=float), coord.spacing, ai,
                                             edge_order=2 if coord.size > 2 else 1)
        else:
            order = 2 if len(coord.values) > 2 else 1
            data = np.gradient(dataset.data, coord.values, axis=ai, edge_order=order)
        return Dataset(f"∂{dataset.name}/∂{dataset.axes[ai]}", data, dataset.axes, dataset.coordinates, dataset.units,
                       dataset.time, dataset.time_units, {"physics_operation":"gradient", "axis":dataset.axes[ai]},
                       dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    @staticmethod
    def _edge_order(coord) -> int:
        return 2 if coord.size > 2 else 1

    def divergence(self, vector: Mapping[str, Dataset], name="div(A)") -> Dataset:
        base = self._check_compatible(vector)
        comps, coords = [], []
        for i, axis in enumerate(base.axes):
            comp_key = axis.lower()
            ds = vector.get(comp_key) or vector.get(f"x{i+1}")
            if ds is None: raise ValueError(f"Missing vector component for axis {axis}")
            comps.append(ds)
            coords.append(base.coordinates[i])
        if all(c.is_uniform for c in coords):
            edge_orders = [self._edge_order(c) for c in coords]
            if len(set(edge_orders)) == 1:
                # Common case (all axes have >2 or all have exactly 2 points):
                # one fused, single-pass native call across every axis.
                data = _native.divergence_uniform(
                    [np.asarray(ds.data, dtype=float) for ds in comps],
                    [c.spacing for c in coords], edge_order=edge_orders[0],
                )
            else:
                # Rare: axes disagree on edge order (e.g. one axis has only 2
                # points). Still native-accelerated per axis, just summed in
                # Python instead of fused in C++, to keep each axis's exact
                # edge handling.
                data = sum(
                    _native.gradient_uniform(np.asarray(ds.data, dtype=float), c.spacing, i, edge_order=eo)
                    for i, (ds, c, eo) in enumerate(zip(comps, coords, edge_orders))
                )
        else:
            terms = []
            for i, (ds, coord) in enumerate(zip(comps, coords)):
                order = 2 if len(coord.values) > 2 else 1
                terms.append(np.gradient(ds.data, coord.values, axis=i, edge_order=order))
            data = sum(terms)
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {"physics_operation":"divergence"}, base.source, base.simulation_metadata)


    def curl(self, vector: Mapping[str, Dataset], name="curl(A)"):
        base = self._check_compatible(vector)
        if base.ndim != 3:
            raise ValueError("Curl requires a 3D vector field")
        comps = {}
        for k in ("x1", "x2", "x3"):
            if k in vector: comps[k] = vector[k]
        if len(comps) != 3:
            raise ValueError("Curl requires x1, x2, x3 components")
        c1, c2, c3 = comps["x1"], comps["x2"], comps["x3"]
        coords = base.coordinates
        if all(coord.is_uniform for coord in coords):
            edge_orders = [self._edge_order(c) for c in coords]
            d1, d2, d3 = (np.asarray(c.data, dtype=float) for c in (c1, c2, c3))
            if len(set(edge_orders)) == 1:
                out1, out2, out3 = _native.curl_uniform_3d(
                    d1, d2, d3, coords[0].spacing, coords[1].spacing, coords[2].spacing,
                    edge_order=edge_orders[0],
                )
            else:
                g = lambda arr, axis: _native.gradient_uniform(arr, coords[axis].spacing, axis, edge_order=edge_orders[axis])
                out1 = g(d3, 1) - g(d2, 2)
                out2 = g(d1, 2) - g(d3, 0)
                out3 = g(d2, 0) - g(d1, 1)
            out = np.stack([out1, out2, out3], axis=-1)
        else:
            d = lambda ds, axis: np.gradient(ds.data, base.coordinates[base.axis_index(axis)].values, axis=base.axis_index(axis), edge_order=2 if ds.shape[base.axis_index(axis)] > 2 else 1)
            out = np.stack([d(c3, "x2") - d(c2, "x3"), d(c1, "x3") - d(c3, "x1"), d(c2, "x1") - d(c1, "x2")], axis=-1)
        return {k: Dataset(f"({name})_{k}", out[..., i], base.axes, base.coordinates, base.units, base.time, base.time_units, {"physics_operation":"curl","component":k}, base.source, base.simulation_metadata) for i,k in enumerate(("x1","x2","x3"))}

    def electric_magnitude(self, fields: Mapping[str, Dataset]):
        return self.magnitude(fields, name="|E|")

    def magnetic_magnitude(self, fields: Mapping[str, Dataset]):
        return self.magnitude(fields, name="|B|")

    def laplacian(self, dataset: Dataset, name=None) -> Dataset:
        if dataset.coordinates and all(c.is_uniform for c in dataset.coordinates):
            edge_orders = [self._edge_order(c) for c in dataset.coordinates]
            data_arr = np.asarray(dataset.data, dtype=float)
            if len(set(edge_orders)) == 1:
                result = _native.laplacian_uniform(data_arr, [c.spacing for c in dataset.coordinates], edge_order=edge_orders[0])
            else:
                result = np.zeros_like(data_arr)
                for axis, (coord, eo) in enumerate(zip(dataset.coordinates, edge_orders)):
                    first = _native.gradient_uniform(data_arr, coord.spacing, axis, edge_order=eo)
                    result += _native.gradient_uniform(first, coord.spacing, axis, edge_order=eo)
        else:
            result = np.zeros_like(np.asarray(dataset.data,dtype=float))
            for axis in dataset.axes:
                first=self.gradient(dataset, axis)
                result += np.gradient(first.data, dataset.coordinates[dataset.axis_index(axis)].values, axis=dataset.axis_index(axis), edge_order=2 if dataset.shape[dataset.axis_index(axis)]>2 else 1)
        return Dataset(name or f"∇²({dataset.name})", result, dataset.axes, dataset.coordinates, dataset.units,
                       dataset.time, dataset.time_units, {"physics_operation":"laplacian"}, dataset.source, dataset.simulation_metadata)
