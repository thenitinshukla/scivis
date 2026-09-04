"""Optional accelerated backends for uniform-grid physics operators.

This module is the single place that knows which of three interchangeable
backends is active for the physics differential operators used by
`physics/engine.py` and `physics/particle_field.py`:

  * **numpy** -- always available, the reference implementation every
    other backend is verified against (see the test suite).
  * **native** -- the compiled C++/OpenMP extension in
    `native/src/native_physics.cpp` (built by `native/build.sh`).
  * **jax** -- `physics/jax_backend.py`, JIT-compiled with JAX. Needs
    only `pip install jax` (no compiler), and transparently uses a GPU/TPU
    if `jax.devices()` reports one and jaxlib was built for it.

All three produce numerically equivalent results (see
`tests/test_native_physics_backend.py` and `tests/test_jax_physics_backend.py`)
so switching backends never changes a scientific result, only how fast it
runs. Per the project's design rules, none of the accelerated backends are
required: the pure-NumPy path always works.

**Which one is actually fastest depends on your hardware and problem
size -- there is no universally-correct default.** Measured on a
single-core, GPU-less CI sandbox with representative grid sizes, the
native C++/OpenMP backend was consistently fastest, including after JAX's
JIT warm-up cost was excluded, because the C++ code hand-fuses multiple
passes into single-pass loops in a way this project's JAX kernels
currently do not, and because JAX's per-call dispatch overhead is
comparatively higher for these kernel sizes. JAX's own documented
advantages -- automatic GPU/TPU execution, and being the natural
foundation for autodiff-based features (e.g. physics-informed loss
functions, gradient-based uncertainty quantification) -- are real but
were not things this sandbox could measure (no GPU present here). If you
have a CUDA-capable GPU, benchmark `set_backend("jax")` against the
default yourself; it is very plausible it wins there even though it did
not in this environment.

The default is "auto", which behaves exactly as before this module
supported multiple backends: native C++ if compiled, else pure NumPy.
JAX is never selected automatically -- call `set_backend("jax")` to opt in.
"""
from __future__ import annotations

import importlib.util

import numpy as np

try:
    from . import _native as _ext  # compiled extension, built by native/build.sh
    NATIVE_AVAILABLE = True
except ImportError:
    _ext = None
    NATIVE_AVAILABLE = False

# JAX is *never* imported here at module load time, even though it's a
# valid backend choice. Importing `jax` triggers jaxlib/XLA runtime
# initialization (hardware backend discovery, plugin scanning, etc.),
# which is genuinely slow -- multiple seconds, observed directly in this
# project. Since `physics.engine` (and therefore this module) is imported
# by essentially every GUI tab at application startup, an eager `import
# jax_backend` here meant *every user paid that multi-second cost on every
# launch*, regardless of whether they ever selected the JAX backend (which
# is opt-in-only by design -- see set_backend() below). `JAX_AVAILABLE` is
# answered with `importlib.util.find_spec`, which only checks whether the
# package *could* be imported (fast, no execution); the actual `import
# jax_backend` (and therefore `import jax`) happens lazily, only inside
# `_jax_module()`, the first time a caller actually requests the JAX
# backend via `set_backend("jax")`.
_jax = None
JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _jax_module():
    """Import and cache `jax_backend` on first actual use of the JAX
    backend. Not called at module import time -- see note above."""
    global _jax
    if _jax is None:
        from . import jax_backend as _jax_mod
        _jax = _jax_mod
    return _jax

_VALID_BACKENDS = ("auto", "numpy", "native", "jax")
_backend = "auto"


def set_backend(name: str) -> None:
    """Choose which backend the functions below dispatch to.

    - "auto" (default): native C++ if compiled, else pure NumPy. Never
      selects JAX automatically (see module docstring for why).
    - "numpy": always use the pure-NumPy reference implementation,
      regardless of what's installed/compiled. Useful for comparison/
      debugging, or on hardware where the accelerated paths are slower.
    - "native": require the compiled C++/OpenMP extension; raises if it
      isn't built.
    - "jax": require JAX; raises if it isn't installed.
    """
    if name not in _VALID_BACKENDS:
        raise ValueError(f"Unknown physics backend {name!r}; expected one of {_VALID_BACKENDS}")
    if name == "native" and not NATIVE_AVAILABLE:
        raise RuntimeError("The native C++ backend isn't built. Run native/build.sh, or choose a different backend.")
    if name == "jax" and not JAX_AVAILABLE:
        raise RuntimeError("JAX isn't installed. `pip install jax`, or choose a different backend.")
    global _backend
    _backend = name


def get_backend() -> str:
    """The backend name last passed to `set_backend` (default: "auto")."""
    return _backend


def _active_backend() -> str:
    """Which backend a call will actually use right now, resolving "auto"."""
    if _backend == "auto":
        return "native" if NATIVE_AVAILABLE else "numpy"
    return _backend


def openmp_enabled() -> bool:
    """Whether the compiled extension was itself built with OpenMP support."""
    return bool(NATIVE_AVAILABLE and _ext.openmp_enabled())


def max_threads() -> int:
    """OpenMP's reported max thread count (1 if native/OpenMP unavailable)."""
    if NATIVE_AVAILABLE:
        return int(_ext.omp_max_threads())
    return 1


def backend_name() -> str:
    active = _active_backend()
    if active == "jax":
        return f"JAX ({_jax_module().backend_summary()})"
    if active == "native":
        if openmp_enabled():
            return f"Native C++ (OpenMP, up to {max_threads()} threads)"
        return "Native C++ (single-threaded, OpenMP not available at build time)"
    return "Pure NumPy" + ("" if _backend != "auto" else " (native extension not built -- see native/build.sh)")


# ---------------------------------------------------------------------
# Pure-NumPy fallbacks. These exist independently of the C++ extension
# and are exercised directly by tests to prove every backend agrees.
# ---------------------------------------------------------------------

def _np_gradient_pass(data: np.ndarray, h: float, axis: int, edge_order: int) -> np.ndarray:
    coord = np.arange(data.shape[axis]) * h
    order = 2 if data.shape[axis] > 2 else 1
    if edge_order < order:
        order = edge_order if data.shape[axis] > 2 else 1
    return np.gradient(data, coord, axis=axis, edge_order=order)


def gradient_uniform(data: np.ndarray, h: float, axis: int, edge_order: int = 2) -> np.ndarray:
    active = _active_backend()
    if active == "jax":
        return _jax_module().gradient_uniform(data, h, axis, edge_order)
    if active == "native":
        return _ext.gradient_uniform(np.ascontiguousarray(data, dtype=float), float(h), int(axis), int(edge_order))
    return _np_gradient_pass(np.asarray(data, dtype=float), h, axis, edge_order)


def divergence_uniform(components: list[np.ndarray], spacings: list[float], edge_order: int = 2) -> np.ndarray:
    active = _active_backend()
    if active == "jax":
        return _jax_module().divergence_uniform(components, spacings, edge_order)
    components = [np.ascontiguousarray(c, dtype=float) for c in components]
    if active == "native":
        return _ext.divergence_uniform(components, [float(h) for h in spacings], int(edge_order))
    total = np.zeros_like(components[0])
    for axis, (comp, h) in enumerate(zip(components, spacings)):
        total += _np_gradient_pass(comp, h, axis, edge_order)
    return total


def laplacian_uniform(data: np.ndarray, spacings: list[float], edge_order: int = 2) -> np.ndarray:
    active = _active_backend()
    if active == "jax":
        return _jax_module().laplacian_uniform(data, spacings, edge_order)
    data = np.ascontiguousarray(data, dtype=float)
    if active == "native":
        return _ext.laplacian_uniform(data, [float(h) for h in spacings], int(edge_order))
    total = np.zeros_like(data)
    for axis, h in enumerate(spacings):
        first = _np_gradient_pass(data, h, axis, edge_order)
        total += _np_gradient_pass(first, h, axis, edge_order)
    return total


def curl_uniform_3d(c1, c2, c3, h1: float, h2: float, h3: float, edge_order: int = 2):
    active = _active_backend()
    if active == "jax":
        return _jax_module().curl_uniform_3d(c1, c2, c3, h1, h2, h3, edge_order)
    c1 = np.ascontiguousarray(c1, dtype=float)
    c2 = np.ascontiguousarray(c2, dtype=float)
    c3 = np.ascontiguousarray(c3, dtype=float)
    if active == "native":
        return _ext.curl_uniform_3d(c1, c2, c3, float(h1), float(h2), float(h3), int(edge_order))
    d = lambda arr, axis, h: _np_gradient_pass(arr, h, axis, edge_order)
    out_a = d(c3, 1, h2) - d(c2, 2, h3)
    out_b = d(c1, 2, h3) - d(c3, 0, h1)
    out_c = d(c2, 0, h1) - d(c1, 1, h2)
    return out_a, out_b, out_c


def sample_field_trilinear(field: np.ndarray, origin, spacing, points: np.ndarray) -> np.ndarray:
    """Sample a 3D scalar field at arbitrary physical points via trilinear
    interpolation, clamping out-of-bounds points to the grid boundary.

    `origin`/`spacing` are the (x1, x2, x3) minimum coordinate and grid
    spacing; `points` is an (N, 3) array of physical (x1, x2, x3) positions,
    e.g. a particle trajectory's x1(t), x2(t), x3(t).
    """
    active = _active_backend()
    if active == "jax":
        if field.ndim != 3:
            raise ValueError("sample_field_trilinear requires a 3D field")
        if np.asarray(points).ndim != 2 or np.asarray(points).shape[1] != 3:
            raise ValueError("points must have shape (N, 3)")
        if any(float(h) == 0.0 for h in spacing):
            raise ValueError("grid spacing must be non-zero")
        return _jax_module().sample_field_trilinear(field, origin, spacing, points)

    field = np.ascontiguousarray(field, dtype=float)
    points = np.ascontiguousarray(points, dtype=float)
    if field.ndim != 3:
        raise ValueError("sample_field_trilinear requires a 3D field")
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    origin = tuple(float(v) for v in origin)
    spacing = tuple(float(v) for v in spacing)
    if any(h == 0.0 for h in spacing):
        raise ValueError("grid spacing must be non-zero")

    if active == "native":
        return _ext.sample_field_trilinear(field, origin, spacing, points)

    n0, n1, n2 = field.shape
    g = (points - np.asarray(origin)) / np.asarray(spacing)
    g[:, 0] = np.clip(g[:, 0], 0, n0 - 1)
    g[:, 1] = np.clip(g[:, 1], 0, n1 - 1)
    g[:, 2] = np.clip(g[:, 2], 0, n2 - 1)

    i0 = np.floor(g[:, 0]).astype(int); i1 = np.minimum(i0 + 1, n0 - 1)
    j0 = np.floor(g[:, 1]).astype(int); j1 = np.minimum(j0 + 1, n1 - 1)
    k0 = np.floor(g[:, 2]).astype(int); k1 = np.minimum(k0 + 1, n2 - 1)
    tx = g[:, 0] - i0
    ty = g[:, 1] - j0
    tz = g[:, 2] - k0

    c00 = field[i0, j0, k0] * (1 - tx) + field[i1, j0, k0] * tx
    c01 = field[i0, j0, k1] * (1 - tx) + field[i1, j0, k1] * tx
    c10 = field[i0, j1, k0] * (1 - tx) + field[i1, j1, k0] * tx
    c11 = field[i0, j1, k1] * (1 - tx) + field[i1, j1, k1] * tx
    c0 = c00 * (1 - ty) + c10 * ty
    c1 = c01 * (1 - ty) + c11 * ty
    return c0 * (1 - tz) + c1 * tz
