"""Correctness tests for the optional JAX physics backend.

`jax_backend.py`'s own docstring promises these checks exist; they didn't
(this file was missing entirely, discovered while investigating a startup
performance bug -- see native_backend.py's lazy-import fix). Every JAX
kernel here is checked against the same pure-NumPy reference formulas used
to validate the native C++ backend, so switching backends is guaranteed to
never silently change a scientific result.

All tests are skipped (not failed) if JAX isn't installed, since it's an
optional dependency.
"""
import numpy as np
import pytest

from scientific_visualization.physics import native_backend as nb

jax_backend = pytest.importorskip(
    "scientific_visualization.physics.jax_backend",
    reason="JAX is an optional dependency",
)

if not jax_backend.JAX_AVAILABLE:
    pytest.skip("jax package not installed", allow_module_level=True)


@pytest.fixture(autouse=True)
def _restore_backend():
    """Every test in this file explicitly selects a backend; always
    restore the global default afterwards so other test modules aren't
    affected by test execution order."""
    original = nb.get_backend()
    yield
    nb.set_backend(original)


def test_jax_available_flag_matches_actual_import():
    assert nb.JAX_AVAILABLE is True
    assert jax_backend.JAX_AVAILABLE is True


def test_set_backend_jax_then_auto_round_trips():
    nb.set_backend("jax")
    assert nb.get_backend() == "jax"
    assert "JAX" in nb.backend_name()
    nb.set_backend("auto")
    assert nb.get_backend() == "auto"


def test_backend_summary_reports_a_device():
    summary = jax_backend.backend_summary()
    assert "JAX" in summary
    assert jax_backend.device_name() != "unavailable"


@pytest.mark.parametrize("shape", [(37,), (21, 17), (14, 11, 9)])
def test_jax_gradient_matches_np_gradient(shape):
    rng = np.random.RandomState(1)
    data = rng.rand(*shape)
    h = 0.37
    for axis in range(len(shape)):
        coord = np.arange(shape[axis]) * h
        order = 2 if shape[axis] > 2 else 1
        expected = np.gradient(data, coord, axis=axis, edge_order=order)
        got = jax_backend.gradient_uniform(data, h, axis, edge_order=2)
        assert np.allclose(got, expected, atol=1e-8)


def test_jax_gradient_matches_numpy_fallback_exactly():
    rng = np.random.RandomState(2)
    data = rng.rand(12, 9, 7)
    h = 0.2
    jax_result = jax_backend.gradient_uniform(data, h, axis=1, edge_order=2)
    numpy_result = nb._np_gradient_pass(data, h, axis=1, edge_order=2)
    assert np.allclose(jax_result, numpy_result, atol=1e-8)


def test_jax_divergence_matches_numpy_fallback():
    rng = np.random.RandomState(3)
    shape = (16, 14, 12)
    comps = [rng.rand(*shape) for _ in range(3)]
    spacings = [0.1, 0.2, 0.15]
    jax_result = jax_backend.divergence_uniform(comps, spacings)
    numpy_result = sum(
        nb._np_gradient_pass(c, h, axis, 2) for axis, (c, h) in enumerate(zip(comps, spacings))
    )
    assert np.allclose(jax_result, numpy_result, atol=1e-8)


def test_jax_divergence_matches_native_backend():
    rng = np.random.RandomState(3)
    shape = (16, 14, 12)
    comps = [rng.rand(*shape) for _ in range(3)]
    spacings = [0.1, 0.2, 0.15]
    jax_result = jax_backend.divergence_uniform(comps, spacings)
    native_result = nb.divergence_uniform(comps, spacings)  # uses whatever backend was active
    assert np.allclose(jax_result, native_result, atol=1e-8)


def test_jax_laplacian_matches_numpy_fallback():
    rng = np.random.RandomState(4)
    data = rng.rand(18, 13, 10)
    spacings = [0.1, 0.2, 0.15]
    jax_result = jax_backend.laplacian_uniform(data, spacings)
    total = np.zeros_like(data)
    for axis, h in enumerate(spacings):
        first = nb._np_gradient_pass(data, h, axis, 2)
        total += nb._np_gradient_pass(first, h, axis, 2)
    assert np.allclose(jax_result, total, atol=1e-7)


def test_jax_curl_matches_numpy_fallback():
    rng = np.random.RandomState(5)
    shape = (12, 10, 8)
    c1, c2, c3 = rng.rand(*shape), rng.rand(*shape), rng.rand(*shape)
    h1, h2, h3 = 0.1, 0.2, 0.15
    jax_result = jax_backend.curl_uniform_3d(c1, c2, c3, h1, h2, h3)

    d = lambda arr, axis, h: nb._np_gradient_pass(arr, h, axis, 2)
    expected = (
        d(c3, 1, h2) - d(c2, 2, h3),
        d(c1, 2, h3) - d(c3, 0, h1),
        d(c2, 0, h1) - d(c1, 1, h2),
    )
    for got, exp in zip(jax_result, expected):
        assert np.allclose(got, exp, atol=1e-8)


def test_jax_trilinear_sampling_exact_on_linear_field():
    n0, n1, n2 = 20, 18, 16
    origin = (0.0, -1.0, 2.0)
    spacing = (0.05, 0.1, 0.07)
    X = origin[0] + spacing[0] * np.arange(n0)[:, None, None]
    Y = origin[1] + spacing[1] * np.arange(n1)[None, :, None]
    Z = origin[2] + spacing[2] * np.arange(n2)[None, None, :]
    a, b, c, d_ = 2.3, -1.7, 0.5, 4.0
    field = np.broadcast_to(a * X + b * Y + c * Z + d_, (n0, n1, n2)).copy()

    rng = np.random.RandomState(6)
    bounds_lo = np.array(origin)
    bounds_hi = np.array(origin) + np.array(spacing) * (np.array([n0, n1, n2]) - 1)
    pts = rng.uniform(bounds_lo, bounds_hi, size=(200, 3))
    expected = a * pts[:, 0] + b * pts[:, 1] + c * pts[:, 2] + d_

    result = jax_backend.sample_field_trilinear(field, origin, spacing, pts)
    assert np.allclose(result, expected, atol=1e-6)


def test_engine_dispatches_to_jax_when_selected():
    """End-to-end: PhysicsEngine itself, not just the backend module
    directly, must route through JAX once selected."""
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.physics.engine import PhysicsEngine

    shape = (10, 9, 8)
    rng = np.random.RandomState(0)
    data = rng.rand(*shape)
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.arange(shape[i]) * 0.1) for i in range(3)
    )
    ds = Dataset("f", data, ("x1", "x2", "x3"), coords, "V/m", 0.0, "s", {}, "s")

    nb.set_backend("numpy")
    numpy_result = PhysicsEngine().gradient(ds, "x1")
    nb.set_backend("jax")
    jax_result = PhysicsEngine().gradient(ds, "x1")
    assert np.allclose(numpy_result.data, jax_result.data, atol=1e-8)
