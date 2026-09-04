import numpy as np
from scientific_visualization.data_plotter.model import DatasetTable
from scientific_visualization.data_plotter.scaling import infer_scaling_columns, strong_scaling, weak_scaling


def test_scaling_columns_are_inferred_from_hpc_headers():
    ds = DatasetTable("results1.txt", ["Node", "Total GPUs", "Simulation time"], np.zeros((2, 3)), " ", True)
    cols = infer_scaling_columns(ds)
    assert cols.x == 1
    assert cols.y == 2


def test_strong_scaling_metrics_match_standard_definitions():
    x = np.array([4, 16, 32, 64], float)
    t = np.array([100, 25, 12.5, 12.5], float)
    _, speed = strong_scaling(x, t, metric="Speedup")
    _, eff = strong_scaling(x, t, metric="Efficiency")
    assert np.allclose(speed, [1, 4, 8, 8])
    assert np.allclose(eff, [1, 1, 1, 0.5])


def test_weak_scaling_requires_explicit_positive_workload_factor():
    with np.testing.assert_raises(ValueError):
        weak_scaling([4, 8], [10, 10], 0, metric="Normalized runtime")


def test_weak_scaling_normalizes_runtime_by_workload():
    _, y = weak_scaling([4, 8], [10, 20], 2, metric="Normalized runtime")
    assert np.allclose(y, [1, 2])
