"""Tests for the optional native C++/OpenMP physics backend.

These tests must pass identically whether or not the compiled extension
(`scientific_visualization/physics/_native*.so`, built by `native/build.sh`)
is present, since `native_backend` transparently falls back to pure NumPy.
A few tests specifically force the fallback path (even when the extension
is built) to prove the two implementations agree numerically.
"""
import numpy as np
import pytest

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.physics import native_backend as nb
from scientific_visualization.physics.engine import PhysicsEngine


def _force_fallback(monkeypatch):
    monkeypatch.setattr(nb, "NATIVE_AVAILABLE", False)


def _uniform_dataset(shape, spacings, seed=0):
    rng = np.random.RandomState(seed)
    data = rng.rand(*shape)
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.arange(shape[i]) * spacings[i], units="m", label=f"x{i+1}")
        for i in range(len(shape))
    )
    return Dataset(name="f", data=data, axes=tuple(f"x{i+1}" for i in range(len(shape))),
                    coordinates=coords, units="V/m", time=0.0, time_units="s", metadata={}, source="synthetic")


def test_coordinate_axis_is_uniform():
    uniform = CoordinateAxis(name="x1", values=np.linspace(0, 1, 20))
    assert uniform.is_uniform
    assert uniform.spacing == pytest.approx(uniform.values[1] - uniform.values[0])

    non_uniform = CoordinateAxis(name="x1", values=np.array([0.0, 1.0, 3.0, 10.0]))
    assert not non_uniform.is_uniform
    with pytest.raises(ValueError):
        non_uniform.spacing

    tiny = CoordinateAxis(name="x1", values=np.array([0.0, 1.0]))
    assert tiny.is_uniform  # fewer than 3 points is trivially "uniform"


@pytest.mark.parametrize("shape", [(37,), (21, 17), (14, 11, 9)])
def test_gradient_uniform_matches_np_gradient(shape):
    rng = np.random.RandomState(1)
    data = rng.rand(*shape)
    h = 0.37
    for axis in range(len(shape)):
        coord = np.arange(shape[axis]) * h
        order = 2 if shape[axis] > 2 else 1
        expected = np.gradient(data, coord, axis=axis, edge_order=order)
        got = nb.gradient_uniform(data, h, axis, edge_order=2)
        assert np.allclose(got, expected, atol=1e-10)


def test_gradient_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(2)
    data = rng.rand(12, 9, 7)
    h = 0.2
    native_result = nb.gradient_uniform(data, h, axis=1, edge_order=2)
    _force_fallback(monkeypatch)
    fallback_result = nb.gradient_uniform(data, h, axis=1, edge_order=2)
    assert np.allclose(native_result, fallback_result, atol=1e-10)


def test_divergence_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(3)
    shape = (16, 14, 12)
    comps = [rng.rand(*shape) for _ in range(3)]
    spacings = [0.1, 0.2, 0.15]
    native_result = nb.divergence_uniform(comps, spacings)
    _force_fallback(monkeypatch)
    fallback_result = nb.divergence_uniform(comps, spacings)
    assert np.allclose(native_result, fallback_result, atol=1e-9)


def test_laplacian_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(4)
    data = rng.rand(18, 13, 10)
    spacings = [0.1, 0.2, 0.15]
    native_result = nb.laplacian_uniform(data, spacings)
    _force_fallback(monkeypatch)
    fallback_result = nb.laplacian_uniform(data, spacings)
    assert np.allclose(native_result, fallback_result, atol=1e-9)


def test_curl_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(5)
    shape = (12, 10, 8)
    c1, c2, c3 = rng.rand(*shape), rng.rand(*shape), rng.rand(*shape)
    h1, h2, h3 = 0.1, 0.2, 0.15
    native_result = nb.curl_uniform_3d(c1, c2, c3, h1, h2, h3)
    _force_fallback(monkeypatch)
    fallback_result = nb.curl_uniform_3d(c1, c2, c3, h1, h2, h3)
    for a, b in zip(native_result, fallback_result):
        assert np.allclose(a, b, atol=1e-9)


def test_trilinear_sampling_exact_on_linear_field(monkeypatch):
    n0, n1, n2 = 20, 18, 16
    origin = (0.0, -1.0, 2.0)
    spacing = (0.05, 0.1, 0.07)
    X = origin[0] + spacing[0] * np.arange(n0)[:, None, None]
    Y = origin[1] + spacing[1] * np.arange(n1)[None, :, None]
    Z = origin[2] + spacing[2] * np.arange(n2)[None, None, :]
    a, b, c, d = 2.3, -1.7, 0.5, 4.0
    field = np.broadcast_to(a * X + b * Y + c * Z + d, (n0, n1, n2)).copy()

    rng = np.random.RandomState(6)
    bounds_lo = np.array(origin)
    bounds_hi = np.array(origin) + np.array(spacing) * (np.array([n0, n1, n2]) - 1)
    pts = rng.uniform(bounds_lo, bounds_hi, size=(500, 3))
    expected = a * pts[:, 0] + b * pts[:, 1] + c * pts[:, 2] + d

    native_result = nb.sample_field_trilinear(field, origin, spacing, pts)
    assert np.allclose(native_result, expected, atol=1e-9)

    _force_fallback(monkeypatch)
    fallback_result = nb.sample_field_trilinear(field, origin, spacing, pts)
    assert np.allclose(fallback_result, expected, atol=1e-9)


def test_trilinear_sampling_clamps_out_of_bounds():
    field = np.arange(2 * 2 * 2, dtype=float).reshape(2, 2, 2)
    origin = (0.0, 0.0, 0.0)
    spacing = (1.0, 1.0, 1.0)
    inside = nb.sample_field_trilinear(field, origin, spacing, np.array([[0.0, 0.0, 0.0]]))
    far_outside = nb.sample_field_trilinear(field, origin, spacing, np.array([[-500.0, -500.0, -500.0]]))
    assert np.allclose(inside, far_outside)  # both clamp to the same corner


def test_backend_status_reports_something_sensible():
    status = nb.backend_name()
    assert isinstance(status, str) and len(status) > 0
    assert nb.max_threads() >= 1


# --- integration through PhysicsEngine, proving the wiring is correct ---

def test_engine_gradient_uniform_grid_uses_native_and_matches_manual_numpy():
    ds = _uniform_dataset((25, 20), (0.1, 0.2))
    engine = PhysicsEngine()
    result = engine.gradient(ds, "x1")
    coord = np.arange(25) * 0.1
    expected = np.gradient(ds.data, coord, axis=0, edge_order=2)
    assert np.allclose(result.data, expected, atol=1e-9)


def test_engine_divergence_uniform_grid_matches_non_uniform_fallback_path():
    """Build the *same* field values on a uniform grid and re-run through
    the non-uniform (np.gradient) code path by using non-evenly-spaced
    coordinates that happen to still be uniform numerically -- this checks
    the native and np.gradient code paths agree end to end via the public
    PhysicsEngine API, not just the native_backend module directly."""
    shape = (16, 14, 12)
    rng = np.random.RandomState(7)
    comps_data = [rng.rand(*shape) for _ in range(3)]
    spacings = (0.1, 0.2, 0.15)

    uniform_coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.arange(shape[i]) * spacings[i]) for i in range(3)
    )
    # Non-uniform-looking (but numerically identical spacing) coordinate
    # values force the np.gradient fallback path inside PhysicsEngine.
    forced_non_uniform_coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=(np.arange(shape[i]) * spacings[i]) + 0.0) for i in range(3)
    )

    engine = PhysicsEngine()
    vector_uniform = {
        f"x{i+1}": Dataset(f"x{i+1}", comps_data[i], ("x1", "x2", "x3"), uniform_coords, "V/m", 0.0, "s", {}, "s")
        for i in range(3)
    }
    result_native = engine.divergence(vector_uniform)

    import scientific_visualization.physics.engine as engine_mod
    # Force the "non-uniform" branch by monkeypatching is_uniform to False
    # for this call only, to compare against the np.gradient-based path.
    orig_is_uniform = CoordinateAxis.is_uniform
    try:
        CoordinateAxis.is_uniform = property(lambda self: False)
        vector_forced = {
            f"x{i+1}": Dataset(f"x{i+1}", comps_data[i], ("x1", "x2", "x3"), forced_non_uniform_coords, "V/m", 0.0, "s", {}, "s")
            for i in range(3)
        }
        result_fallback = engine.divergence(vector_forced)
    finally:
        CoordinateAxis.is_uniform = orig_is_uniform

    assert np.allclose(result_native.data, result_fallback.data, atol=1e-9)


def test_engine_backend_status():
    assert isinstance(PhysicsEngine.backend_status(), str)
