"""Tests for the 3D tab's panel-position control.

`ThreeDTab` used to be a standalone QWidget that never inherited the
"Panel: Left/Right/Top/Bottom" placement feature already available on the
2D Fields/Grid tab (via BaseTab). This verifies ThreeDTab now shares that
same, single implementation -- and that every existing 3D-tab behavior
(file loading, rendering, camera controls, colorbar options) still works
after the refactor that made it possible.

Testing note: `pyvistaqt` (needed for the *interactive* Qt-embedded 3D
widget) is not required to run these tests, and may not be installed.
Without it, `ThreeDTab.renderer` is `None` and `render()` is a silent
no-op -- so tests that only assert "render() doesn't raise" can pass
without ever actually exercising the renderer. Tests below that need to
verify real rendering behavior explicitly inject a `ThreeDRenderer`
backed by an off-screen `pv.Plotter` (no pyvistaqt needed for that), the
same pattern already used for the pure-renderer tests in
test_colorbar_features.py.
"""
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from scientific_visualization.gui.three_d_tab import ThreeDTab
from scientific_visualization.gui.base_tab import BaseTab


def _make_2d_grid_file(tmp_path, shape=(10, 10)):
    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.random.RandomState(0).rand(*shape).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    return str(p)


def _give_real_offscreen_renderer(tab):
    """Inject a real ThreeDRenderer backed by an off-screen pv.Plotter, so
    render() actually renders instead of being a no-op when pyvistaqt
    isn't installed. Returns the renderer so callers can inspect
    `renderer.plotter` (e.g. actor counts) for real assertions."""
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")
    tab.renderer = ThreeDRenderer(pv.Plotter(off_screen=True))
    return tab.renderer


def _actor_count(renderer):
    return len(renderer.plotter.renderer.actors)


def test_three_d_tab_inherits_base_tab():
    assert issubclass(ThreeDTab, BaseTab)


def test_three_d_tab_has_panel_position_control():
    tab = ThreeDTab()
    assert hasattr(tab, "_panel_position")
    options = [tab._panel_position.itemText(i) for i in range(tab._panel_position.count())]
    assert options == ["Left", "Right", "Top", "Bottom"]


@pytest.mark.parametrize("position,expect_horizontal,expect_panel_first", [
    ("Left", True, True),
    ("Right", True, False),
    ("Top", False, True),
    ("Bottom", False, False),
])
def test_three_d_tab_panel_position_moves_the_view(position, expect_horizontal, expect_panel_first):
    tab = ThreeDTab()
    tab.show()
    tab._panel_position.setCurrentText(position)
    orientation_ok = (tab._splitter.orientation() == Qt.Horizontal) == expect_horizontal
    panel_is_first = tab._splitter.widget(0) is not tab.canvas
    assert orientation_ok
    assert panel_is_first == expect_panel_first


def test_three_d_tab_set_theme_does_not_crash_without_a_dataset():
    tab = ThreeDTab()
    tab.set_theme("Dark")  # must not raise even though canvas isn't a PlotCanvas
    tab.set_theme("Light")


def test_three_d_tab_set_theme_rerenders_when_a_dataset_is_loaded(tmp_path):
    tab = ThreeDTab()
    renderer = _give_real_offscreen_renderer(tab)
    path = _make_2d_grid_file(tmp_path)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("e1-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()
    assert tab.dataset is not None
    before = _actor_count(renderer)
    assert before > 0  # apply_selection() already rendered something real
    tab.set_theme("Dark")  # must not raise; refresh_plot() re-renders via render()
    assert _actor_count(renderer) > 0


def test_three_d_tab_reset_camera_still_works_after_refactor():
    """Regression guard: an earlier bug made reset_camera() raise NameError.
    Re-verify it's still fine after moving ThreeDTab onto BaseTab."""
    tab = ThreeDTab()

    class FakePlotter:
        def __init__(self):
            self.reset_calls = 0
            self.render_calls = 0
        def reset_camera(self):
            self.reset_calls += 1
        def render(self):
            self.render_calls += 1

    class FakeRenderer:
        def __init__(self):
            self.plotter = FakePlotter()

    tab.renderer = FakeRenderer()
    tab.reset_camera()
    assert tab.renderer.plotter.reset_calls == 1
    assert tab.renderer.plotter.render_calls == 1


def test_three_d_tab_file_open_and_apply_flow_still_works(tmp_path):
    tab = ThreeDTab()
    path = _make_2d_grid_file(tmp_path)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("e1-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()
    assert tab.dataset is not None
    assert tab.dataset.shape == (10, 10)
    assert "shape=(10, 10)" in tab.info.text()


def test_three_d_tab_colorbar_controls_still_present_and_wired(tmp_path):
    tab = ThreeDTab()
    renderer = _give_real_offscreen_renderer(tab)
    path = _make_2d_grid_file(tmp_path)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("e1-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()  # calls render() once already
    for position in ("right", "left", "top", "bottom"):
        tab.colorbar_position.setCurrentText(position)
        tab.render()
        assert _actor_count(renderer) > 0
        assert "e1 [V/m]" in renderer.plotter.scalar_bars
