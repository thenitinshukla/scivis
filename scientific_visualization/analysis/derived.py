from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import numpy as np

from ..core.data import CoordinateAxis, Dataset


@dataclass(frozen=True)
class Operation:
    name: str
    function: Callable
    description: str = ""


class DerivedQuantityEngine:
    def __init__(self):
        self.operations: dict[str, Operation] = {
            "add": Operation("add", lambda a, b: a + b),
            "subtract": Operation("subtract", lambda a, b: a - b),
            "multiply": Operation("multiply", lambda a, b: a * b),
            "divide": Operation("divide", lambda a, b: np.divide(a, b)),
            "abs": Operation("abs", np.abs),
            "log": Operation("log", np.log),
        }

    def register(self, operation: Operation):
        self.operations[operation.name] = operation

    def binary(self, op: str, a: Dataset, b: Dataset, name=None, units="") -> Dataset:
        if a.shape != b.shape or a.axes != b.axes:
            raise ValueError("Derived operands must have compatible shapes and axes")
        if op not in self.operations or op in {"abs", "log"}:
            raise ValueError(f"'{op}' is not a binary operation")
        return Dataset(name or f"({a.name} {op} {b.name})", self.operations[op].function(a.data, b.data), a.axes, a.coordinates, units or a.units, a.time, a.time_units, {"operation": op}, a.source, a.simulation_metadata, derived_from=(a.name,b.name))

    def unary(self, op: str, a: Dataset, name=None, units="") -> Dataset:
        if op not in {"abs", "log"}:
            raise ValueError(f"'{op}' is not a unary operation")
        if op == "log" and np.any(a.data <= 0):
            raise ValueError("logarithm is only defined for positive values")
        return Dataset(name or f"{op}({a.name})", self.operations[op].function(a.data), a.axes, a.coordinates, units or a.units, a.time, a.time_units, {"operation": op}, a.source, a.simulation_metadata, derived_from=(a.name,))

    def vector_magnitude(self, components: Mapping[str, Dataset], name="|A|") -> Dataset:
        if not components:
            raise ValueError("At least one component is required")
        items = list(components.values())
        base = items[0]
        if any(x.shape != base.shape or x.axes != base.axes for x in items[1:]):
            raise ValueError("Vector components must have compatible shapes and axes")
        data = np.sqrt(sum(np.asarray(x.data) ** 2 for x in items))
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units, {"operation": "vector_magnitude", "components": tuple(components)}, base.source, base.simulation_metadata, derived_from=tuple(components))

    def gradient(self, dataset: Dataset, axis: str | int) -> Dataset:
        ai = dataset.axis_index(axis)
        coord = dataset.coordinates[ai].values
        if coord.size < 2:
            raise ValueError("At least two coordinate points are required for a gradient")
        edge_order = 2 if coord.size > 2 else 1
        data = np.gradient(dataset.data, coord, axis=ai, edge_order=edge_order)
        unit = f"{dataset.units}/{dataset.coordinates[ai].units}" if dataset.units and dataset.coordinates[ai].units else dataset.units
        return Dataset(f"d({dataset.name})/d{dataset.axes[ai]}", data, dataset.axes, dataset.coordinates, unit, dataset.time, dataset.time_units, {"operation": "gradient", "axis": dataset.axes[ai]}, dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    def integrate(self, dataset: Dataset, axis: str | int) -> Dataset:
        ai = dataset.axis_index(axis)
        coord = dataset.coordinates[ai].values
        data = np.trapz(dataset.data, coord, axis=ai)
        new_axes = tuple(x for i, x in enumerate(dataset.axes) if i != ai)
        new_coords = tuple(x for i, x in enumerate(dataset.coordinates) if i != ai)
        return Dataset(f"int {dataset.name} d{dataset.axes[ai]}", data, new_axes, new_coords, dataset.units, dataset.time, dataset.time_units, {"operation": "integral", "axis": dataset.axes[ai]}, dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    def average(self, dataset: Dataset, axis: str | int) -> Dataset:
        ai = dataset.axis_index(axis)
        data = np.mean(dataset.data, axis=ai)
        return Dataset(f"avg({dataset.name})", data, tuple(x for i,x in enumerate(dataset.axes) if i != ai), tuple(x for i,x in enumerate(dataset.coordinates) if i != ai), dataset.units, dataset.time, dataset.time_units, {"operation":"average","axis":dataset.axes[ai]}, dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    def directional_average(self, dataset: Dataset, direction: str, name=None) -> Dataset:
        """Average a field over one or more physical axes.

        ``direction`` accepts ``x``, ``y``, ``z`` or a parenthesized tuple such
        as ``(x,y,z)``. Axes that are not present are rejected explicitly.
        For a 3D ``(x,y,z)`` average the result is a scalar Dataset, which can
        naturally be accumulated across a Simulation frame series.
        """
        axes = parse_average_direction(direction)
        indices = [dataset.axis_index("x" + str(ord(i) - ord("x") + 1)) for i in axes]
        data = np.mean(dataset.data, axis=tuple(indices))
        keep = [i for i in range(dataset.ndim) if i not in set(indices)]
        return Dataset(
            name or f"average,dir={format_average_direction(axes)}({dataset.name})",
            data,
            tuple(dataset.axes[i] for i in keep),
            tuple(dataset.coordinates[i] for i in keep),
            dataset.units, dataset.time, dataset.time_units,
            {**dict(dataset.metadata), "operation": "directional_average", "directions": axes},
            dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,),
        )


def parse_average_direction(direction: str) -> tuple[str, ...]:
    """Parse the supported directional-average syntax."""
    text = str(direction).strip().lower()
    if text.startswith("average,dir="):
        text = text.split("=", 1)[1].strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    parts = tuple(p.strip() for p in text.split(",") if p.strip())
    if not parts:
        raise ValueError("average direction must be x, y, z, or a comma-separated tuple such as (x,y,z)")
    if any(p not in {"x", "y", "z"} for p in parts):
        raise ValueError("average direction entries must be x, y, or z")
    if len(set(parts)) != len(parts):
        raise ValueError("average direction cannot contain duplicate axes")
    return parts


def format_average_direction(direction: tuple[str, ...]) -> str:
    return direction[0] if len(direction) == 1 else "(" + ",".join(direction) + ")"
