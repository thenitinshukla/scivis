from pathlib import Path

import numpy as np
import pytest

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.io.hdf5.generic import discover_hdf5_datasets, validate_file
from scientific_visualization.io.simulation import SimulationReader
from scientific_visualization.analysis import DerivedQuantityEngine, LineoutAnalyzer, statistics, reduce_grid_series
from scientific_visualization.visualization.two_d import plot_2d

DATA = Path(__file__).parent / "sample_data"


def test_simulation_grid_to_dataset_physical_axis_order():
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    assert ds.ndim == 2
    assert ds.axes == ("x1", "x2")
    assert ds.shape == (128, 64)
    assert ds.coordinates[0].size == 128
    assert ds.coordinates[1].size == 64


def test_coordinate_lineout_and_statistics():
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    x, y = LineoutAnalyzer().lineout(ds, axis="x1", position=0.0)
    assert x.shape == (128,)
    assert y.shape == (128,)
    stats = statistics(y)
    assert stats["count"] == 128


def test_derived_quantity():
    c = CoordinateAxis("x1", np.arange(4.0))
    a = Dataset("A", np.arange(4.0), ("x1",), (c,))
    b = Dataset("B", np.ones(4), ("x1",), (c,))
    out = DerivedQuantityEngine().binary("add", a, b)
    np.testing.assert_allclose(out.data, [1,2,3,4])


def test_generic_discovery():
    result = discover_hdf5_datasets(DATA / "e1-000200.h5")
    assert any(d.name == "e1" for d in result)



def test_simulation_scalar_array_metadata(tmp_path):
    import h5py
    import numpy as np
    p = tmp_path / "array_metadata.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"
        f.attrs["TIME"] = np.asarray([2.5])
        f.attrs["ITER"] = np.asarray([123])
        f.attrs["UNITS"] = "arb"
        f.create_dataset("e1", data=np.ones((4, 8), dtype=np.float32))
        axis = f.create_group("AXIS")
        axis.create_dataset("AXIS1", data=np.asarray([0.0, 1.0]))
        axis.create_dataset("AXIS2", data=np.asarray([0.0, 2.0]))
    from scientific_visualization.io.grid import GridFile
    info = GridFile.info(p)
    assert info.time == 2.5
    assert info.iteration == 123


def test_invalid_hdf5_is_reported(tmp_path):
    p = tmp_path / "bad.h5"
    p.write_bytes(b"not an hdf5 file")
    with pytest.raises(ValueError, match="Invalid or truncated HDF5"):
        validate_file(p)


def test_time_series_reduction():
    files = sorted((DATA / "b3_series").glob("*.h5"))
    times, _, values, _ = reduce_grid_series(files, reduction="mean")
    assert len(times) == len(files)
    assert values.shape == times.shape


def test_plot_2d_noninteractive():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    ax = plot_2d(ds)
    assert len(ax.images) == 0
    fig = ax.figure
    fig.savefig(Path("/tmp/scientific_visualization_test_plot.png"), dpi=80)
    plt.close(fig)


def test_ml_feature_extraction():
    from scientific_visualization.ml import dataset_to_features
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    fs = dataset_to_features(ds, include_coordinates=True)
    assert fs.values.shape[0] == ds.data.size
    assert fs.values.shape[1] == 3


def test_ml_pca_optional():
    from scientific_visualization.ml import PCAAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    fs = FeatureSet(np.random.default_rng(0).normal(size=(20, 3)), ("a", "b", "c"))
    result = PCAAnalyzer(2).fit_transform(fs)
    assert result.output.shape == (20, 2)


def test_main_application_imports():
    pytest.importorskip("PyQt5")
    from scientific_visualization.app import main
    assert callable(main)


def test_ml_regression_training():
    from scientific_visualization.ml import RegressionAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    rng = np.random.default_rng(1)
    X = rng.normal(size=(60, 3))
    y = X[:, 0] * 2.0 + X[:, 1] * 0.5 + rng.normal(scale=0.1, size=60)
    result = RegressionAnalyzer(test_size=0.25).fit_predict(FeatureSet(X, ("x", "y", "z")), y)
    assert result.output.shape[0] == 15
    assert result.metadata["metrics"]["r2"] > 0.5


def test_animation_gif_export(tmp_path):
    from scientific_visualization.export.animation import export_grid_movie
    files = sorted((DATA / "b3_series").glob("*.h5"))[:3]
    out = tmp_path / "movie.gif"
    n = export_grid_movie(files, out, fps=4, dpi=50)
    assert n == 3
    assert out.exists() and out.stat().st_size > 0


def test_2d_to_3d_geometry_helpers():
    import numpy as np
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")
    c1 = CoordinateAxis("x1", np.linspace(0, 1, 4))
    c2 = CoordinateAxis("x2", np.linspace(-1, 1, 3))
    ds = Dataset("E1", np.arange(12, dtype=float).reshape(4, 3), ("x1", "x2"), (c1, c2))
    r = ThreeDRenderer(pv.Plotter(off_screen=True))
    plane = r.add_2d_plane(ds, plane_axis="x3", position=2.0)
    surf = r.add_2d_surface(ds, height_axis="x3", base_position=0.5, z_scale=2.0)
    ext = r.add_2d_extrusion(ds, extrusion_axis="x3", depth=3.0)
    assert plane is not None and surf is not None and ext is not None


def test_ml_gradient_boosting_and_neural_network():
    from scientific_visualization.ml import GradientBoostingRegressorAnalyzer, NeuralNetworkRegressorAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    rng = np.random.default_rng(5)
    X = rng.normal(size=(90, 4))
    y = 2 * X[:, 0] - 0.7 * X[:, 1] + 0.3 * X[:, 2] ** 2
    fs = FeatureSet(X, ("x1", "x2", "x3", "x4"))
    gb = GradientBoostingRegressorAnalyzer(n_estimators=50).fit_predict(fs, y, test_size=0.2, cv_folds=3)
    assert gb.metadata["metrics"]["r2"] > 0.5
    assert len(gb.metadata["feature_importances"]) == 4
    nn = NeuralNetworkRegressorAnalyzer(hidden_layers=(24, 12), max_iter=250, early_stopping=False).fit_predict(fs, y, test_size=0.2, cv_folds=0)
    assert nn.metadata["metrics"]["r2"] > 0.5
    assert len(nn.metadata["loss_curve"]) > 0


def test_ml_autoencoder():
    from scientific_visualization.ml import AutoencoderAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    rng = np.random.default_rng(6)
    X = rng.normal(size=(50, 5))
    result = AutoencoderAnalyzer(bottleneck=3, max_iter=60).fit_transform(FeatureSet(X, tuple(f"x{i}" for i in range(5))))
    assert result.output.shape == X.shape
    assert result.metadata["reconstruction_error"].shape == (50,)

def test_simulation_series_ai_and_spectral():
    from pathlib import Path
    from scientific_visualization.analysis.ai import AIAnalysisEngine
    from scientific_visualization.analysis.spectral import fft_1d, k_omega
    files = sorted(str(p) for p in Path('tests/sample_data/b3_series').glob('*.h5'))
    report = AIAnalysisEngine().analyze_series(files=files, quantity='b3', max_frames=100)
    assert report['n_files_discovered'] == 10
    assert report['n_frames_analyzed'] == 10
    assert report['times'].size == 10

    x = np.linspace(0, 1, 128, endpoint=False)
    y = np.sin(2*np.pi*5*x)
    spec = fft_1d(y, x)
    assert abs(float(spec.frequencies[np.argmax(spec.power[1:])+1]) - 5.0) < 1e-9


def test_coordinate_aware_integral_and_komega():
    import numpy as np
    from scientific_visualization.analysis.spectral import k_omega
    from scientific_visualization.io.grid import GridFile
    gf = GridFile.load('tests/sample_data/b3_series/b3-000000.h5')
    # The integral path must use physical coordinates and remain finite.
    from scientific_visualization.analysis.time_series import reduce_grid_series
    t, it, vals, meta = reduce_grid_series([gf.filename], reduction='integral', quantity='b3')
    assert np.isfinite(vals[0])
    x = np.linspace(0, 1, 64, endpoint=False)
    times = np.arange(32)*0.1
    field = np.sin(2*np.pi*2*times)[:, None] * np.sin(2*np.pi*4*x)[None, :]
    omega, k, power = k_omega(field, x, times)
    assert power.shape == (len(omega), len(k))
