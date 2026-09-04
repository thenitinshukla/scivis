"""Particle <-> field correlation analysis.

Connects the three data sources the application already has separately
(grid/field snapshots, particle diagnostics, particle tracks) so a user can
answer questions like "what field did this particle actually experience
along its trajectory?" -- item #6 of the scientific-AI-workbench roadmap.

Everything here is a plain, deterministic, Qt-independent function
operating on `Dataset`/NumPy arrays, so it is callable from the GUI, from
scripts, or from the AI assistant's tool-calling layer without any of them
needing to know how the sampling is implemented.

Scope note: sampling currently requires a *uniform*, *static* 3D grid
(one time snapshot) -- the common case for a single OSIRIS/PIC dump. Time-
interpolating between multiple field snapshots to match a track's time
samples is future work and is called out explicitly rather than silently
approximated.

Unit-system note: `kinetic_energy_from_momentum` and `lorentz_force` use
the normalized-units convention common to OSIRIS/PIC codes (momentum in
units of m*c, fields already in the code's own normalized units, m=c=1 by
default). Pass explicit `rest_mass`/`c` if your data uses different
normalization -- this module does not guess or silently assume physical
(SI) units.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np

from ..core.data import Dataset
from . import native_backend as _native


def sample_dataset_along_trajectory(field: Dataset, x1: np.ndarray, x2: np.ndarray, x3: np.ndarray) -> np.ndarray:
    """Trilinearly sample a static 3D scalar field at trajectory points.

    `x1`, `x2`, `x3` are 1D arrays of physical coordinates (e.g. a
    particle track's x1(t), x2(t), x3(t)), all the same length. Points
    outside the grid are clamped to the boundary rather than raising,
    since a particle a fraction of a cell outside the box due to floating
    point error is expected, not exceptional.
    """
    if field.ndim != 3:
        raise ValueError(f"sample_dataset_along_trajectory requires a 3D field; got {field.ndim}D")
    if not field.coordinates or len(field.coordinates) != 3:
        raise ValueError("Field dataset is missing 3D coordinate axes")
    non_uniform = [c.name for c in field.coordinates if not c.is_uniform]
    if non_uniform:
        raise ValueError(
            f"Trilinear sampling requires a uniform grid; axis(es) {non_uniform} are not uniformly spaced"
        )
    x1, x2, x3 = np.asarray(x1, dtype=float), np.asarray(x2, dtype=float), np.asarray(x3, dtype=float)
    if not (x1.shape == x2.shape == x3.shape):
        raise ValueError("x1, x2, x3 must have the same shape")
    origin = tuple(c.values[0] for c in field.coordinates)
    spacing = tuple(c.spacing for c in field.coordinates)
    points = np.stack([x1, x2, x3], axis=-1)
    return _native.sample_field_trilinear(np.asarray(field.data, dtype=float), origin, spacing, points)


def sample_fields_along_trajectory(fields: Mapping[str, Dataset], x1: np.ndarray, x2: np.ndarray, x3: np.ndarray) -> dict[str, np.ndarray]:
    """Convenience wrapper: sample several fields (e.g. E1, E2, E3, B1, B2,
    B3) at the same trajectory points. Returns {name: sampled_values}."""
    return {name: sample_dataset_along_trajectory(ds, x1, x2, x3) for name, ds in fields.items()}


def magnitude3(a1: np.ndarray, a2: np.ndarray, a3: np.ndarray) -> np.ndarray:
    """|A| for per-point vector components, e.g. |E| or |B| along a track."""
    a1, a2, a3 = np.asarray(a1, dtype=float), np.asarray(a2, dtype=float), np.asarray(a3, dtype=float)
    return np.sqrt(a1 ** 2 + a2 ** 2 + a3 ** 2)


def dot3(a1, a2, a3, b1, b2, b3) -> np.ndarray:
    """A·B for per-point vector components, e.g. E·v (power delivered to the particle)."""
    return np.asarray(a1) * np.asarray(b1) + np.asarray(a2) * np.asarray(b2) + np.asarray(a3) * np.asarray(b3)


def cross3(a1, a2, a3, b1, b2, b3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A x B for per-point vector components, e.g. v x B."""
    a1, a2, a3 = np.asarray(a1, dtype=float), np.asarray(a2, dtype=float), np.asarray(a3, dtype=float)
    b1, b2, b3 = np.asarray(b1, dtype=float), np.asarray(b2, dtype=float), np.asarray(b3, dtype=float)
    return a2 * b3 - a3 * b2, a3 * b1 - a1 * b3, a1 * b2 - a2 * b1


def velocity_from_momentum(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, rest_mass: float = 1.0, c: float = 1.0):
    """Relativistic velocity (v1, v2, v3) from normalized momentum (p/mc convention).

    gamma = sqrt(1 + |p|^2), v = p*c / (gamma * rest_mass) in the same
    normalized-units convention as the rest of this module.
    """
    p1, p2, p3 = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float), np.asarray(p3, dtype=float)
    gamma = np.sqrt(1.0 + p1 ** 2 + p2 ** 2 + p3 ** 2)
    scale = c / (gamma * rest_mass)
    return p1 * scale, p2 * scale, p3 * scale, gamma


def kinetic_energy_from_momentum(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, rest_mass: float = 1.0, c: float = 1.0) -> np.ndarray:
    """Relativistic kinetic energy (gamma - 1) * m * c^2 from normalized momentum."""
    p1, p2, p3 = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float), np.asarray(p3, dtype=float)
    gamma = np.sqrt(1.0 + p1 ** 2 + p2 ** 2 + p3 ** 2)
    return (gamma - 1.0) * rest_mass * c ** 2


def lorentz_force(e1, e2, e3, b1, b2, b3, v1, v2, v3, charge: float = 1.0):
    """F = q(E + v x B), componentwise, in the caller's normalized units."""
    vxb1, vxb2, vxb3 = cross3(v1, v2, v3, b1, b2, b3)
    return (
        charge * (np.asarray(e1) + vxb1),
        charge * (np.asarray(e2) + vxb2),
        charge * (np.asarray(e3) + vxb3),
    )


def energy_gain(energy: np.ndarray) -> np.ndarray:
    """Per-step change in a scalar energy series along a trajectory (length N-1)."""
    energy = np.asarray(energy, dtype=float)
    if energy.size < 2:
        raise ValueError("Need at least two points to compute an energy gain")
    return np.diff(energy)
