import numpy as np
import pytest


def test_advanced_surrogate_uq_and_acquisition():
    from scientific_visualization.ml import FeatureSet, AdvancedSurrogate, estimator_available
    if not estimator_available():
        pytest.skip('scikit-learn not installed')
    rng = np.random.default_rng(11)
    X = rng.uniform(-1, 1, (90, 3))
    y = 1.5 * X[:, 0] - 0.8 * X[:, 1] ** 2 + 0.15 * X[:, 2]
    fs = FeatureSet(X, ('p1','p2','p3'))
    model = AdvancedSurrogate('Extra Trees').fit(fs, y)
    mean, std, ens = model.predict_with_uncertainty(X[:10])
    assert mean.shape == (10,) and std.shape == (10,) and ens.shape[1] == 10
    rec = model.recommend(X, batch_size=5, criterion='Maximum uncertainty')
    assert len(rec['indices']) == 5
    report = model.report(fs, y, criterion='Upper confidence bound')
    assert report.metrics['rmse'] >= 0
    assert set(report.feature_importance) == {'p1','p2','p3'}


def test_edge_workspace_removed():
    from pathlib import Path
    root = Path(__file__).parents[1] / 'scientific_visualization'
    assert not (root / 'edge_compute.py').exists()
    assert not (root / 'gui' / 'edge_tab.py').exists()
