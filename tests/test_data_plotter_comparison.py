import numpy as np
import pytest
from scientific_visualization.data_plotter.comparison import efficiency, speedup, transform_for_preset


def test_speedup_and_efficiency():
    x = np.array([1, 2, 4])
    y = np.array([8, 4, 2])
    assert np.allclose(speedup(x, y)[1], [1, 2, 4])
    assert np.allclose(efficiency(x, y)[1], [1, 1, 1])


def test_normalize_to_first_preset():
    x, y = transform_for_preset([1, 2], [10, 20], "Normalize Y to first")
    assert np.allclose(x, [1, 2])
    assert np.allclose(y, [1, 2])


def test_speedup_rejects_zero_baseline():
    with pytest.raises(ValueError, match="baseline"):
        speedup([1, 2], [0, 1])
