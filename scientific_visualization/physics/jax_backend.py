"""Optional JAX-accelerated backend for uniform-grid physics operators.

This mirrors `native_backend.py`'s pure-NumPy formulas exactly (same edge
handling, same double-differentiation definition of the Laplacian) so
switching to this backend never changes a scientific result -- only how
it's computed. See `tests/test_jax_physics_backend.py` for the numerical
equivalence checks.

Why JAX, alongside the existing C++/OpenMP native backend:
  * No compiler required -- `pip install jax` vs. a C++ toolchain + OpenMP.
    This matters on platforms where a compiler isn't readily available.
  * Transparent GPU/TPU support: the exact same Python code in this file
    runs on whatever `jax.devices()` reports (CPU here; a CUDA or TPU
    device automatically if one is present and jaxlib was built for it),
    with no code changes.
  * JIT compilation (`jax.jit`) is a good fit for this application's
    typical workload: the same operator applied to many arrays of the
    *same shape* in a row (every frame of a movie export, every timestep
    of a time-series analysis). The first call to a given (shape, axis,
    edge_order) combination pays a one-time tracing/compilation cost;
    every subsequent call with the same combination reuses the compiled
    executable. A single one-off call on an unusual shape can therefore be
    *slower* than plain NumPy -- this backend is opt-in for that reason
    (see `native_backend.set_backend`), not silently substituted by
    default.

Correctness note: JAX defaults to float32 even for float64 NumPy input,
silently discarding precision, unless 64-bit mode is enabled -- which
this module does at import time. Without this, results computed on this
backend would quietly be less precise than the NumPy/C++ backends,
exactly the kind of silent scientific-result degradation this project's
design rules forbid.
"""
from __future__ import annotations

from functools import lru_cache, partial
from typing import Sequence

try:
    import jax
    jax.config.update("jax_enable_x64", True)  # see module docstring
    import jax.numpy as jnp
    JAX_AVAILABLE = True
except ImportError:
    jax = None
    jnp = None
    JAX_AVAILABLE = False

import numpy as np


def require_jax() -> None:
    if not JAX_AVAILABLE:
        raise ImportError(
            "The JAX physics backend requires the 'jax' package. "
            "Install it with `pip install jax` (add `jax[cuda12]` etc. "
            "instead for GPU support, per JAX's own install instructions)."
        )


def device_name() -> str:
    if not JAX_AVAILABLE:
        return "unavailable"
    try:
        return str(jax.devices()[0])
    except Exception:
        return "unknown"


def backend_summary() -> str:
    if not JAX_AVAILABLE:
        return "JAX not installed"
    return f"JAX {jax.__version__} on {jax.default_backend()} ({device_name()})"


# ---------------------------------------------------------------------
# JIT-compiled kernels. `axis`/`edge_order` are static: JAX specializes
# (recompiles) per distinct value, which is exactly what we want since the
# formulas branch structurally on them.
# ---------------------------------------------------------------------

@partial(jax.jit, static_argnames=("axis", "edge_order")) if JAX_AVAILABLE else (lambda f: f)
def _gradient_uniform_jax(data, h, axis: int, edge_order: int):
    n = data.shape[axis]
    take = lambda i: jnp.take(data, jnp.asarray(i), axis=axis)

    if n == 2:
        d = (take([1]) - take([0])) / h
        return jnp.concatenate([d, d], axis=axis)

    interior = (take(np.arange(2, n)) - take(np.arange(0, n - 2))) / (2.0 * h)

    if edge_order >= 2:
        left = (-3.0 * take([0]) + 4.0 * take([1]) - take([2])) / (2.0 * h)
        right = (3.0 * take([n - 1]) - 4.0 * take([n - 2]) + take([n - 3])) / (2.0 * h)
    else:
        left = (take([1]) - take([0])) / h
        right = (take([n - 1]) - take([n - 2])) / h

    return jnp.concatenate([left, interior, right], axis=axis)


def gradient_uniform(data, h: float, axis: int, edge_order: int = 2):
    require_jax()
    result = _gradient_uniform_jax(jnp.asarray(data, dtype=jnp.float64), float(h), int(axis), int(edge_order))
    return np.asarray(result)


def divergence_uniform(components: Sequence, spacings: Sequence[float], edge_order: int = 2):
    require_jax()
    comps = [jnp.asarray(c, dtype=jnp.float64) for c in components]
    total = jnp.zeros_like(comps[0])
    for axis, (comp, h) in enumerate(zip(comps, spacings)):
        total = total + _gradient_uniform_jax(comp, float(h), axis, int(edge_order))
    return np.asarray(total)


def laplacian_uniform(data, spacings: Sequence[float], edge_order: int = 2):
    require_jax()
    arr = jnp.asarray(data, dtype=jnp.float64)
    total = jnp.zeros_like(arr)
    for axis, h in enumerate(spacings):
        first = _gradient_uniform_jax(arr, float(h), axis, int(edge_order))
        total = total + _gradient_uniform_jax(first, float(h), axis, int(edge_order))
    return np.asarray(total)


def curl_uniform_3d(c1, c2, c3, h1: float, h2: float, h3: float, edge_order: int = 2):
    require_jax()
    d1 = jnp.asarray(c1, dtype=jnp.float64)
    d2 = jnp.asarray(c2, dtype=jnp.float64)
    d3 = jnp.asarray(c3, dtype=jnp.float64)
    eo = int(edge_order)
    out1 = _gradient_uniform_jax(d3, float(h2), 1, eo) - _gradient_uniform_jax(d2, float(h3), 2, eo)
    out2 = _gradient_uniform_jax(d1, float(h3), 2, eo) - _gradient_uniform_jax(d3, float(h1), 0, eo)
    out3 = _gradient_uniform_jax(d2, float(h1), 0, eo) - _gradient_uniform_jax(d1, float(h2), 1, eo)
    return np.asarray(out1), np.asarray(out2), np.asarray(out3)


@jax.jit if JAX_AVAILABLE else (lambda f: f)
def _sample_field_trilinear_jax(field, origin, spacing, points):
    g = (points - origin) / spacing
    n0, n1, n2 = field.shape
    g0 = jnp.clip(g[:, 0], 0.0, n0 - 1)
    g1 = jnp.clip(g[:, 1], 0.0, n1 - 1)
    g2 = jnp.clip(g[:, 2], 0.0, n2 - 1)

    i0 = jnp.floor(g0).astype(jnp.int32); i1 = jnp.minimum(i0 + 1, n0 - 1)
    j0 = jnp.floor(g1).astype(jnp.int32); j1 = jnp.minimum(j0 + 1, n1 - 1)
    k0 = jnp.floor(g2).astype(jnp.int32); k1 = jnp.minimum(k0 + 1, n2 - 1)
    tx = g0 - i0; ty = g1 - j0; tz = g2 - k0

    c00 = field[i0, j0, k0] * (1 - tx) + field[i1, j0, k0] * tx
    c01 = field[i0, j0, k1] * (1 - tx) + field[i1, j0, k1] * tx
    c10 = field[i0, j1, k0] * (1 - tx) + field[i1, j1, k0] * tx
    c11 = field[i0, j1, k1] * (1 - tx) + field[i1, j1, k1] * tx
    c0 = c00 * (1 - ty) + c10 * ty
    c1 = c01 * (1 - ty) + c11 * ty
    return c0 * (1 - tz) + c1 * tz


def sample_field_trilinear(field, origin, spacing, points):
    require_jax()
    result = _sample_field_trilinear_jax(
        jnp.asarray(field, dtype=jnp.float64),
        jnp.asarray(origin, dtype=jnp.float64),
        jnp.asarray(spacing, dtype=jnp.float64),
        jnp.asarray(points, dtype=jnp.float64),
    )
    return np.asarray(result)
