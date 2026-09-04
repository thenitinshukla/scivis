"""Tests for the ROI/measurement tool's GUI wiring in gui/grid_tab.py
(plan.md section 4.4). The underlying analysis logic (masks, statistics,
time series, export) is tested independently in test_roi_analysis.py --
this file covers mouse-driven drawing, list management, persistence
across frame navigation, and the export/time-evolution actions.
"""
import json
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

_app = QApplication.instance() or QApplication([])

from scientific_visualization.gui.grid_tab import GridTab


class _FakeMplEvent:
    def __init__(self, xdata=None, ydata=None, inaxes=None, x=100, y=100):
        self.xdata = xdata; self.ydata = ydata; self.inaxes = inaxes; self.x = x; self.y = y


def _make_grid_series(tmp_path, count=2, shape=(20, 20), name="e1"):
    paths = []
    for i in range(count):
        p = tmp_path / f"{name}-{i:06d}.h5"
        with h5py.File(p, "w") as f:
            f.attrs["NAME"] = name; f.attrs["TIME"] = float(i); f.attrs["ITER"] = i
            d = f.create_dataset(name, data=np.arange(shape[0] * shape[1]).reshape(shape).astype(np.float32))
            d.attrs["UNITS"] = "V/m"
            g = f.create_group("AXIS")
            a1 = g.create_dataset("AXIS1", data=[0.0, float(shape[1])]); a1.attrs["NAME"] = "x1 axis"
            a2 = g.create_dataset("AXIS2", data=[0.0, float(shape[0])]); a2.attrs["NAME"] = "x2 axis"
        paths.append(str(p))
    return paths


@pytest.fixture
def tab_with_grid(tmp_path):
    paths = _make_grid_series(tmp_path)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    return tab


def _draw_rectangle_roi(tab, x0=2.0, y0=3.0, x1=8.0, y1=10.0):
    ax = tab.canvas.figure.axes[0]
    tab.start_roi_draw()
    tab._on_canvas_press(_FakeMplEvent(x0, y0, inaxes=ax))
    tab._on_canvas_motion(_FakeMplEvent(x1, y1, inaxes=ax))
    tab._on_canvas_release(_FakeMplEvent(x1, y1, inaxes=ax))


def test_start_roi_draw_without_data_shows_info_not_crash(monkeypatch):
    tab = GridTab()
    infos = []
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a) or QMessageBox.Ok))
    tab.start_roi_draw()
    assert len(infos) == 1
    assert tab._roi_mode is None


def test_drawing_a_rectangle_roi_adds_it_to_the_list(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    assert len(tab_with_grid._rois) == 1
    assert tab_with_grid._rois[0].shape == "rectangle"
    assert tab_with_grid.roi_list.count() == 1
    assert tab_with_grid.roi_list.currentRow() == 0


def test_drawing_an_ellipse_roi(tab_with_grid):
    tab_with_grid.roi_shape.setCurrentText("Ellipse")
    _draw_rectangle_roi(tab_with_grid, 2, 2, 8, 8)
    assert tab_with_grid._rois[0].shape == "ellipse"


def test_roi_preview_patch_is_cleaned_up_after_finalizing(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    assert tab_with_grid._roi_preview_patch is None
    assert tab_with_grid._roi_draft is None
    assert tab_with_grid._roi_mode is None


def test_roi_statistics_populate_after_drawing(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    text = tab_with_grid.roi_stats_label.text()
    assert "min=" in text and "mean=" in text
    assert tab_with_grid._last_roi_results is not None


def test_multiple_simultaneous_rois(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 5, 5)
    tab_with_grid.roi_shape.setCurrentText("Ellipse")
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 15)
    assert len(tab_with_grid._rois) == 2
    assert tab_with_grid.roi_list.count() == 2


def test_selecting_a_different_roi_updates_stats(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 3, 3)
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 18)
    tab_with_grid.roi_list.setCurrentRow(0)
    stats0 = tab_with_grid.roi_stats_label.text()
    tab_with_grid.roi_list.setCurrentRow(1)
    stats1 = tab_with_grid.roi_stats_label.text()
    assert stats0 != stats1


def test_remove_selected_roi(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 3, 3)
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 18)
    tab_with_grid.roi_list.setCurrentRow(0)
    tab_with_grid.remove_selected_roi()
    assert len(tab_with_grid._rois) == 1
    assert tab_with_grid.roi_list.count() == 1


def test_clear_all_rois(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 3, 3)
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 18)
    tab_with_grid.clear_rois()
    assert tab_with_grid._rois == []
    assert tab_with_grid.roi_list.count() == 0
    assert tab_with_grid._last_roi_results is None


def test_roi_too_small_shows_error_not_crash(tab_with_grid):
    ax = tab_with_grid.canvas.figure.axes[0]
    tab_with_grid.start_roi_draw()
    tab_with_grid._on_canvas_press(_FakeMplEvent(5.0, 5.0, inaxes=ax))
    tab_with_grid._on_canvas_release(_FakeMplEvent(5.0, 5.0, inaxes=ax))  # zero-size
    assert tab_with_grid._rois == []
    assert "not created" in tab_with_grid.info_label.text()


def test_roi_persists_across_frame_navigation(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    assert len(tab_with_grid._rois) == 1
    tab_with_grid._select_relative(1)
    assert len(tab_with_grid._rois) == 1  # ROI survives moving to the next frame
    tab_with_grid._show_roi_stats(tab_with_grid._rois[0])
    assert "min=" in tab_with_grid.roi_stats_label.text()  # still computable on the new frame's data


def test_roi_drawn_patches_appear_on_the_axes(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    ax = tab_with_grid.canvas.figure.axes[0]
    assert len(tab_with_grid._roi_patches) == 1
    assert tab_with_grid._roi_patches[0] in ax.patches


def test_export_roi_stats_without_selection_shows_info(monkeypatch):
    tab = GridTab()
    infos = []
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a) or QMessageBox.Ok))
    tab.export_roi_stats()
    assert len(infos) == 1


def test_export_roi_stats_writes_json(tab_with_grid, tmp_path, monkeypatch):
    _draw_rectangle_roi(tab_with_grid)
    out = tmp_path / "roi.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "")))
    tab_with_grid.export_roi_stats()
    assert out.exists()
    data = json.loads(out.read_text())
    assert "mean" in data


def test_compute_time_evolution_without_selection_shows_info(monkeypatch):
    tab = GridTab()
    infos = []
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a) or QMessageBox.Ok))
    tab.compute_roi_time_evolution()
    assert len(infos) == 1


def test_compute_time_evolution_runs_in_background_and_reports_results(tab_with_grid):
    """Uses the same run_in_background worker as ML training/movie export
    (see gui/workers.py), so this drives the Qt event loop briefly to let
    the background thread finish rather than mocking it away."""
    from PyQt5.QtCore import QEventLoop, QTimer
    _draw_rectangle_roi(tab_with_grid)
    loop = QEventLoop()
    orig_done = tab_with_grid._on_roi_time_evolution_done

    def wrapped(results):
        orig_done(results)
        loop.quit()

    tab_with_grid._on_roi_time_evolution_done = wrapped
    tab_with_grid.compute_roi_time_evolution()
    QTimer.singleShot(10000, loop.quit)  # safety timeout
    loop.exec_()
    assert tab_with_grid._last_roi_results is not None
    assert isinstance(tab_with_grid._last_roi_results, list)
    assert len(tab_with_grid._last_roi_results) == len(tab_with_grid.files)
    assert "computed for" in tab_with_grid.info_label.text()


def test_deactivate_mouse_tools_cancels_in_progress_roi_draw(tab_with_grid):
    ax = tab_with_grid.canvas.figure.axes[0]
    tab_with_grid.start_roi_draw()
    tab_with_grid._on_canvas_press(_FakeMplEvent(2.0, 2.0, inaxes=ax))
    tab_with_grid._on_canvas_motion(_FakeMplEvent(5.0, 5.0, inaxes=ax))
    assert tab_with_grid._roi_preview_patch is not None
    tab_with_grid._deactivate_mouse_tools()
    assert tab_with_grid._roi_mode is None
    assert tab_with_grid._roi_draft is None
    assert tab_with_grid._roi_preview_patch is None
