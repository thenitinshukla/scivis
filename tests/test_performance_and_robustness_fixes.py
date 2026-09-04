"""Regression tests for issues found and fixed during a robustness/performance review.

Each test documents the bug it guards against so a future refactor doesn't
silently reintroduce it.
"""
import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.ml.features import sample_grid_features, dataset_to_features


def _make_grid_dataset(shape, seed=0):
    rng = np.random.RandomState(seed)
    data = rng.rand(*shape).astype(np.float32)
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.linspace(0.0, 1.0, shape[i]), units="m", label=f"x{i+1}")
        for i in range(len(shape))
    )
    return Dataset(
        name="e1", data=data, axes=tuple(f"x{i+1}" for i in range(len(shape))),
        coordinates=coords, units="V/m", time=0.0, time_units="s", metadata={}, source="synthetic",
    )


def test_sample_grid_features_matches_brute_force_subsample():
    """sample_grid_features must select the same rows/values as the original
    'materialize everything then subsample' implementation, just without
    building the full (N, 1+ndim) array and coordinate meshgrid first."""
    ds = _make_grid_dataset((20, 24, 18), seed=1)
    max_samples = 500

    fast = sample_grid_features(ds, max_samples=max_samples, seed=7)

    full = dataset_to_features(ds)
    rng = np.random.default_rng(7)
    idx = np.sort(rng.choice(full.values.shape[0], size=max_samples, replace=False))
    expected_values = full.values[idx]

    assert fast.values.shape == (max_samples, 1 + ds.ndim)
    np.testing.assert_allclose(fast.values, expected_values)
    assert fast.feature_names == full.feature_names
    np.testing.assert_array_equal(fast.metadata["sample_indices"], idx)


def test_sample_grid_features_small_grid_returns_all_points():
    """When the grid already fits under max_samples, behavior is unchanged:
    every point is returned (this path is untouched by the optimization)."""
    ds = _make_grid_dataset((4, 5))
    fs = sample_grid_features(ds, max_samples=1000)
    assert fs.values.shape[0] == 20


def test_sample_grid_features_large_grid_is_fast():
    """A 200^3 field (8,000,000 points) sampling 10,000 points must not
    materialize the full grid's coordinate mesh; this used to take several
    seconds and should now be near-instant."""
    import time
    ds = _make_grid_dataset((200, 200, 200))
    t0 = time.time()
    fs = sample_grid_features(ds, max_samples=10_000, seed=0)
    elapsed = time.time() - t0
    assert fs.values.shape == (10_000, 4)
    assert elapsed < 1.0, f"sample_grid_features took {elapsed:.2f}s; expected well under 1s"


def test_export_grid_movie_uses_thread_safe_agg_figure(tmp_path):
    """export_grid_movie must not depend on pyplot's global current-figure
    state, since it can be invoked from a background worker thread while the
    Qt GUI thread is simultaneously drawing its own embedded canvas."""
    import h5py
    from scientific_visualization.export.animation import export_grid_movie

    paths = []
    for i in range(3):
        p = tmp_path / f"e1-{i:06d}.h5"
        with h5py.File(p, "w") as f:
            f.attrs["NAME"] = "e1"; f.attrs["TIME"] = float(i); f.attrs["ITER"] = i
            d = f.create_dataset("e1", data=np.random.rand(16, 20).astype(np.float32))
            d.attrs["UNITS"] = "V/m"
            g = f.create_group("AXIS")
            a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
            a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
        paths.append(str(p))

    out = tmp_path / "movie.gif"
    n = export_grid_movie([str(p) for p in paths], str(out))
    assert n == 3
    assert out.exists() and out.stat().st_size > 0

    import matplotlib.pyplot as plt
    assert plt.get_fignums() == [], "export_grid_movie must not leak a figure into pyplot's global state"


def test_three_d_tab_reset_camera_does_not_raise():
    """Regression test for a NameError: reset_camera() referenced a bare
    name `clear_scene` (the sibling method's parameter name) instead of
    always resetting the camera, so clicking 'Reset camera' in the 3D tab
    crashed whenever a renderer was active."""
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.three_d_tab import ThreeDTab

    calls = {"reset": 0, "render": 0}

    class FakePlotter:
        def reset_camera(self):
            calls["reset"] += 1

        def render(self):
            calls["render"] += 1

    class FakeRenderer:
        plotter = FakePlotter()

    tab = ThreeDTab()
    tab.renderer = FakeRenderer()
    tab.reset_camera()  # must not raise NameError
    assert calls == {"reset": 1, "render": 1}


def test_run_in_background_success_and_error():
    """Smoke test for the generic worker helper used by ML training and
    movie export: it must call on_success with the callable's return value,
    and on_error with the exception, back on the calling (GUI) thread."""
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import QEventLoop, QTimer
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.workers import run_in_background

    parent = QWidget()

    # -- success path --
    result_box = {}

    def ok_job():
        return 42

    loop = QEventLoop()
    run_in_background(parent, ok_job, on_success=lambda r: (result_box.setdefault("v", r), loop.quit()),
                       on_error=lambda e: loop.quit())
    QTimer.singleShot(5000, loop.quit)  # safety timeout
    loop.exec_()
    assert result_box.get("v") == 42

    # -- error path --
    error_box = {}

    def bad_job():
        raise ValueError("boom")

    loop2 = QEventLoop()
    run_in_background(parent, bad_job, on_success=lambda r: loop2.quit(),
                       on_error=lambda e: (error_box.setdefault("e", e), loop2.quit()))
    QTimer.singleShot(5000, loop2.quit)
    loop2.exec_()
    assert isinstance(error_box.get("e"), ValueError)
    assert str(error_box["e"]) == "boom"


def test_run_in_background_does_not_destroy_qthread_while_running():
    """Regression test for a real crash: an earlier version of this module
    connected the worker's finished/failed signals directly to plain Python
    closures instead of a QObject's bound methods. Qt can only tell a
    connection needs to be auto-queued back to the GUI thread by checking
    the *receiver object's* thread affinity -- a bare closure has none, so
    PyQt ran the "GUI thread" cleanup callback on the worker thread itself.
    That made `thread.wait()` wait on its own thread (a documented Qt no-op
    that just warns and returns immediately), so the QThread could still be
    tearing itself down after Python considered it finished and dropped the
    last reference -- observed as an intermittent "QThread: Destroyed while
    thread is still running" crash under load. This runs many trials with
    immediate post-completion deletion to make that race, if reintroduced,
    show up reliably rather than depending on system timing/load."""
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import QEventLoop, QTimer
    import sys
    import warnings
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.workers import run_in_background

    for trial in range(30):
        parent = QWidget()
        result = {}

        def ok_job(trial=trial):
            return trial

        loop = QEventLoop()
        run_in_background(
            parent, ok_job,
            on_success=lambda r: (result.setdefault("v", r), loop.quit()),
            on_error=lambda e: (result.setdefault("e", e), loop.quit()),
        )
        QTimer.singleShot(2000, loop.quit)
        loop.exec_()
        assert result.get("v") == trial, f"trial {trial}: unexpected result {result}"
        # Immediately drop every reference the test holds, right after
        # completion, to maximize the chance of exposing a premature-
        # destruction race if the underlying bug were reintroduced.
        del parent, loop, result


def _make_grid_series(tmp_path, count=3, shape=(24, 24), name="e1"):
    import h5py
    import numpy as np
    paths = []
    for i in range(count):
        p = tmp_path / f"{name}-{i:06d}.h5"
        with h5py.File(p, "w") as f:
            f.attrs["NAME"] = name; f.attrs["TIME"] = float(i); f.attrs["ITER"] = i
            d = f.create_dataset(name, data=np.random.RandomState(i).rand(*shape).astype(np.float32))
            d.attrs["UNITS"] = "V/m"
            g = f.create_group("AXIS")
            a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
            a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
        paths.append(str(p))
    return paths


def test_frame_navigation_reuses_lazy_series_cache_not_a_fresh_disk_read(tmp_path):
    """Regression test: on_file_selected() used to unconditionally call
    GridFile.info() (a fresh HDF5 open) and _ensure_grid_loaded() used to
    unconditionally call GridFile.load() (another fresh open), even when
    the exact same frame's fully-loaded GridFile was already sitting in
    self._series's bounded cache from a recent visit. Revisiting a
    recently-seen frame must now come from the cache, not from disk."""
    import os
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab
    from scientific_visualization.io.grid import GridFile

    paths = _make_grid_series(tmp_path, count=3)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()

    tab._select_relative(1)  # visit frame 1 -> now cached
    cached_grid = tab._series._cache.get(1)
    assert cached_grid is not None and cached_grid.data is not None

    read_count = {"n": 0}
    original_load = GridFile.load

    def counting_load(path):
        read_count["n"] += 1
        return original_load(path)

    GridFile.load = staticmethod(counting_load)
    original_info = GridFile.info

    def counting_info(path):
        read_count["n"] += 1
        return original_info(path)

    GridFile.info = staticmethod(counting_info)
    try:
        tab._select_relative(-1)  # back to frame 0 (cached from initial load)
        tab._select_relative(1)   # forward to frame 1 (cached from the visit above)
    finally:
        GridFile.load = original_load
        GridFile.info = original_info

    assert read_count["n"] == 0, (
        f"expected zero fresh HDF5 opens when revisiting cached frames, got {read_count['n']}"
    )


def test_frame_navigation_does_not_force_full_axes_rebuild_every_time(tmp_path):
    """Regression test: on_file_selected() used to unconditionally reset
    _active_plot_mode to None, forcing refresh_plot() to treat every
    single frame change as a "mode change" -- tearing down the axes,
    rebuilding the colorbar from scratch, and re-applying the full theme
    -- even when scrubbing between frames of the same quantity/shape.
    The image object (and colorbar) must now be reused via set_data(),
    not recreated, when only the frame (not the plot type) changes."""
    import os
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    paths = _make_grid_series(tmp_path, count=3)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()

    image_before = tab._image
    cbar_before = tab._cbar
    assert image_before is not None and cbar_before is not None

    tab._select_relative(1)  # same shape/quantity -> should reuse, not recreate

    assert tab._image is image_before, "AxesImage was recreated for a same-shape frame change"
    assert tab._cbar is cbar_before, "Colorbar was recreated for a same-shape frame change"


def test_genuine_mode_switch_still_rebuilds_axes_correctly(tmp_path):
    """The fix above must not break the legitimate case: switching between
    plot *types* (2D image vs. line plot) still needs a full axes rebuild,
    since those artist sets are incompatible on the same Axes."""
    import os
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    paths = _make_grid_series(tmp_path, count=2)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    assert tab._image is not None

    tab.mode_line_index.setChecked(True)
    tab.refresh_plot()
    ax = tab.canvas.figure.axes[0]
    assert len(ax.images) == 0
    assert tab._line_artist is not None

    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    assert tab._image is not None
    assert len(ax.images) == 1


def test_frame_navigation_still_updates_correctly_across_different_shapes(tmp_path):
    """A different-shaped/different-quantity file must still produce a
    correctly updated plot (new image, new extent, new colorbar label),
    even though same-shape frame changes now skip the full rebuild."""
    import os
    import sys
    import h5py
    import numpy as np
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    p1 = tmp_path / "e1-000000.h5"
    with h5py.File(p1, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.random.rand(20, 20).astype(np.float32)); d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    p2 = tmp_path / "b3-000000.h5"
    with h5py.File(p2, "w") as f:
        f.attrs["NAME"] = "b3"; f.attrs["TIME"] = 1.0; f.attrs["ITER"] = 1
        d = f.create_dataset("b3", data=np.random.rand(35, 40).astype(np.float32)); d.attrs["UNITS"] = "T"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 2.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 3.0]); a2.attrs["NAME"] = "x2 axis"

    tab = GridTab()
    tab.files = [str(p1)]
    tab.file_list.addItem("e1-000000.h5")
    tab.file_list.setCurrentRow(0); tab.on_file_selected(0); tab.mode_2d.setChecked(True); tab.refresh_plot()
    assert tab._image.get_array().shape == (20, 20)

    tab.files = [str(p2)]
    tab.file_list.clear(); tab.file_list.addItem("b3-000000.h5")
    tab.file_list.setCurrentRow(0); tab.on_file_selected(0); tab.refresh_plot()

    assert tab._image.get_array().shape == (35, 40)
    assert tab._image.get_extent() == [0.0, 2.0, 0.0, 3.0]
    label = tab._cbar.ax.get_ylabel() or tab._cbar.ax.get_xlabel()
    assert "b3" in label and "T" in label


def test_plot_canvas_skips_theme_reapplication_on_routine_redraw():
    """Regression test: PlotCanvas.draw() used to unconditionally re-apply
    the full theme (walking every axes/tick/spine/label, including the
    colorbar's own axes) on every single redraw, even when nothing about
    the theme had changed. Only actual theme changes, figure clears, or
    explicit mark_theme_dirty() calls should trigger it now."""
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.plot_canvas import PlotCanvas
    from unittest.mock import patch

    canvas = PlotCanvas()
    with patch("scientific_visualization.gui.plot_canvas.style.apply_theme") as mock_apply:
        canvas.draw()  # first draw: dirty by default
        assert mock_apply.call_count == 1
        canvas.draw()  # routine redraw: nothing changed, should be skipped
        canvas.draw()
        assert mock_apply.call_count == 1

        canvas.mark_theme_dirty()
        canvas.draw()
        assert mock_apply.call_count == 2

        canvas.set_theme("Dark")  # actual theme change marks dirty
        canvas.draw()
        assert mock_apply.call_count == 3

        canvas.set_theme("Dark")  # setting the same theme again should not
        canvas.draw()
        assert mock_apply.call_count == 3

        canvas.clear()  # clearing the figure marks dirty (fresh axes need it)
        canvas.draw()
        assert mock_apply.call_count == 4


def test_contour_overlay_is_not_recomputed_for_unrelated_setting_changes(tmp_path):
    """Regression test: contour overlays (which dominate redraw time on
    large fields -- matplotlib/contourpy's marching-squares pass) used to
    be unconditionally removed and recreated on every single redraw, even
    when the trigger was a pure display remap (gamma/contrast/black
    floor/colormap) that cannot possibly change the contour geometry.
    They must now be reused unless something that actually affects the
    contour lines changed."""
    import sys
    import h5py
    import numpy as np
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=(np.random.RandomState(0).rand(64, 64)).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"

    tab = GridTab()
    tab.files = [str(p)]
    tab.file_list.addItem("e1-000000.h5")
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    tab.contour_overlay.setChecked(True)
    tab.refresh_plot()
    contour_before = tab._contour_artists[0]

    # Pure display remaps: must NOT recompute the contour.
    tab.gamma_spin.setValue(1.3)
    tab.refresh_plot()
    assert tab._contour_artists[0] is contour_before
    tab.contrast_spin.setValue(1.2)
    tab.refresh_plot()
    assert tab._contour_artists[0] is contour_before
    tab.black_floor_spin.setValue(0.1)
    tab.refresh_plot()
    assert tab._contour_artists[0] is contour_before

    # Settings that DO affect contour geometry/levels: must recompute.
    tab.n_contours.setValue(tab.n_contours.value() + 2)
    tab.refresh_plot()
    assert tab._contour_artists[0] is not contour_before
