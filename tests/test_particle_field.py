import numpy as np
import pytest

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.physics import particle_field as pf


def _linear_field_dataset(a, b, c, d, shape=(20, 18, 16), origin=(0.0, -1.0, 2.0), spacing=(0.05, 0.1, 0.07)):
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=origin[i] + spacing[i] * np.arange(shape[i]))
        for i in range(3)
    )
    X = coords[0].values[:, None, None]
    Y = coords[1].values[None, :, None]
    Z = coords[2].values[None, None, :]
    data = np.broadcast_to(a * X + b * Y + c * Z + d, shape).copy()
    return Dataset(name="e1", data=data, axes=("x1", "x2", "x3"), coordinates=coords,
                    units="V/m", time=0.0, time_units="s", metadata={}, source="synthetic")


def test_sample_dataset_along_trajectory_exact_on_linear_field():
    field = _linear_field_dataset(2.0, -1.0, 0.5, 3.0)
    rng = np.random.RandomState(0)
    n = 50
    x1 = rng.uniform(0.0, 0.05 * 19, n)
    x2 = rng.uniform(-1.0, -1.0 + 0.1 * 17, n)
    x3 = rng.uniform(2.0, 2.0 + 0.07 * 15, n)
    sampled = pf.sample_dataset_along_trajectory(field, x1, x2, x3)
    expected = 2.0 * x1 - 1.0 * x2 + 0.5 * x3 + 3.0
    assert np.allclose(sampled, expected, atol=1e-9)


def test_sample_dataset_along_trajectory_rejects_non_uniform_grid():
    coords = (
        CoordinateAxis(name="x1", values=np.array([0.0, 1.0, 3.0, 10.0])),
        CoordinateAxis(name="x2", values=np.linspace(0, 1, 4)),
        CoordinateAxis(name="x3", values=np.linspace(0, 1, 4)),
    )
    data = np.zeros((4, 4, 4))
    field = Dataset("e1", data, ("x1", "x2", "x3"), coords, "V/m", 0.0, "s", {}, "s")
    with pytest.raises(ValueError, match="uniform"):
        pf.sample_dataset_along_trajectory(field, [0.0], [0.0], [0.0])


def test_sample_dataset_along_trajectory_rejects_2d_field():
    coords = (CoordinateAxis(name="x1", values=np.linspace(0, 1, 4)), CoordinateAxis(name="x2", values=np.linspace(0, 1, 4)))
    field = Dataset("e1", np.zeros((4, 4)), ("x1", "x2"), coords, "V/m", 0.0, "s", {}, "s")
    with pytest.raises(ValueError, match="3D"):
        pf.sample_dataset_along_trajectory(field, [0.0], [0.0], [0.0])


def test_sample_fields_along_trajectory_multiple_components():
    e1 = _linear_field_dataset(1.0, 0.0, 0.0, 0.0)
    e2 = _linear_field_dataset(0.0, 1.0, 0.0, 0.0)
    e3 = _linear_field_dataset(0.0, 0.0, 1.0, 0.0)
    x1 = np.array([0.1, 0.2])
    x2 = np.array([-0.9, -0.8])
    x3 = np.array([2.1, 2.2])
    result = pf.sample_fields_along_trajectory({"E1": e1, "E2": e2, "E3": e3}, x1, x2, x3)
    assert set(result) == {"E1", "E2", "E3"}
    assert np.allclose(result["E1"], x1, atol=1e-9)
    assert np.allclose(result["E2"], x2, atol=1e-9)
    assert np.allclose(result["E3"], x3, atol=1e-9)


def test_magnitude_dot_cross():
    a = (np.array([1.0]), np.array([0.0]), np.array([0.0]))
    b = (np.array([0.0]), np.array([1.0]), np.array([0.0]))
    assert np.allclose(pf.magnitude3(3.0, 4.0, 0.0), 5.0)
    assert np.allclose(pf.dot3(*a, *b), 0.0)
    cx, cy, cz = pf.cross3(*a, *b)
    assert np.allclose(np.array([cx, cy, cz]).ravel(), [0.0, 0.0, 1.0])  # x_hat cross y_hat = z_hat


def test_velocity_and_kinetic_energy_from_momentum_zero_momentum_at_rest():
    v1, v2, v3, gamma = pf.velocity_from_momentum(0.0, 0.0, 0.0)
    assert np.allclose([v1, v2, v3], 0.0)
    assert np.allclose(gamma, 1.0)
    ke = pf.kinetic_energy_from_momentum(0.0, 0.0, 0.0)
    assert np.allclose(ke, 0.0)


def test_kinetic_energy_increases_with_momentum():
    ke_low = pf.kinetic_energy_from_momentum(0.1, 0.0, 0.0)
    ke_high = pf.kinetic_energy_from_momentum(1.0, 0.0, 0.0)
    assert ke_high > ke_low > 0


def test_lorentz_force_pure_electric_field_no_velocity():
    fx, fy, fz = pf.lorentz_force(1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, charge=1.0)
    assert np.allclose([fx, fy, fz], [1.0, 2.0, 3.0])


def test_lorentz_force_magnetic_only_perpendicular_to_velocity():
    # v = x_hat, B = z_hat -> v x B = -y_hat, F should be along -y with no E
    fx, fy, fz = pf.lorentz_force(0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, charge=1.0)
    assert np.allclose([fx, fy, fz], [0.0, -1.0, 0.0])


def test_energy_gain():
    energy = np.array([1.0, 1.5, 2.5, 2.0])
    gain = pf.energy_gain(energy)
    assert np.allclose(gain, [0.5, 1.0, -0.5])


def test_energy_gain_requires_two_points():
    with pytest.raises(ValueError):
        pf.energy_gain([1.0])
