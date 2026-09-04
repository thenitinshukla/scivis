import numpy as np
from scientific_visualization.data_plotter.transform import TransformPipeline, apply_transforms

def test_transform_pipeline_does_not_modify_inputs():
    x = np.array([1., 2., 3.])
    y = np.array([2., 4., 8.])
    xx, yy = apply_transforms(x, y, TransformPipeline(x_scale=0.1, y_scale=2, y_offset=-1))
    assert np.allclose(x, [1, 2, 3])
    assert np.allclose(y, [2, 4, 8])
    assert np.allclose(xx, [0.1, 0.2, 0.3])
    assert np.allclose(yy, [3, 7, 15])

def test_normalization():
    _, yy = apply_transforms([0, 1], [2, 4], TransformPipeline(normalize_y="max"))
    assert np.allclose(yy, [0.5, 1.0])

def test_invalid_normalization_fails():
    try:
        apply_transforms([0, 1], [1, 2], TransformPipeline(normalize_y="bad"))
    except ValueError as exc:
        assert "Unknown Y normalization" in str(exc)
    else:
        raise AssertionError("invalid normalization was accepted")
