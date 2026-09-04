"""Tests for the 2D colorbar fixes/features and 3D scalar-bar options.

Covers:
  * The reverse-colormap bug: `_plot_2d` used to unconditionally overwrite
    the plain matplotlib colormap selection with a hard-coded custom
    palette, so the "Reverse legacy matplotlib colormap" checkbox had no
    visible effect. Fixed by adding a sentinel ("use Colormap dropdown")
    to the palette preset list, defaulted so the plain colormap path is
    live out of the box.
  * 2D colorbar position (right/left/top/bottom) and box/outline toggle.
  * 2D colorbar drag-to-move via mouse press/motion/release, without
    breaking the existing "plain click opens the color-range dialog"
    behavior.
  * 3D scalar bar position/box/interactive options (PyVista backend).
"""
import os
import tempfile

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])


def _make_sample_grid_file(tmp_path, shape=(20, 16)):
    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.linspace(0, 1, shape[0] * shape[1]).reshape(shape).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    return str(p)


class _FakeMplEvent:
    def __init__(self, x, y, inaxes=None, xdata=None, ydata=None):
        self.x = x; self.y = y; self.inaxes = inaxes; self.xdata = xdata; self.ydata = ydata


@pytest.fixture
def grid_tab(tmp_path):
    from scientific_visualization.gui.grid_tab import GridTab, USE_LEGACY_CMAP
    from scientific_visualization.io.grid import GridFile

    path = _make_sample_grid_file(tmp_path)
    tab = GridTab()
    tab.grid = GridFile.load(path)
    tab.files = [path]
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    return tab


def test_palette_combo_defaults_to_legacy_colormap_sentinel(grid_tab):
    from scientific_visualization.gui.grid_tab import USE_LEGACY_CMAP
    assert grid_tab.palette_combo.currentText() == USE_LEGACY_CMAP


def test_reverse_legacy_colormap_checkbox_actually_changes_the_plot(grid_tab):
    """Regression test: this checkbox used to be silently overridden and
    had zero effect on the rendered colormap."""
    cmap_before = grid_tab._image.get_cmap().name
    grid_tab.reverse_cmap.setChecked(True)
    grid_tab.refresh_plot()
    cmap_after = grid_tab._image.get_cmap().name
    assert cmap_after != cmap_before
    assert cmap_after.endswith("_r")

    grid_tab.reverse_cmap.setChecked(False)
    grid_tab.refresh_plot()
    assert grid_tab._image.get_cmap().name == cmap_before


def test_custom_palette_preset_still_works_when_explicitly_selected(grid_tab):
    """Choosing an actual palette preset (not the sentinel) should still
    render via the custom palette system, unaffected by reverse_cmap."""
    from scientific_visualization.rendering_colors import ALL_PALETTES
    preset_name = next(iter(ALL_PALETTES))
    grid_tab.palette_combo.setCurrentText(preset_name)
    grid_tab.refresh_plot()
    cmap_before = grid_tab._image.get_cmap()
    grid_tab.palette_reverse.setChecked(True)
    grid_tab.refresh_plot()
    cmap_after = grid_tab._image.get_cmap()
    # Reversing a custom palette changes its color sequence.
    assert not np.array_equal(cmap_before(np.linspace(0, 1, 8)), cmap_after(np.linspace(0, 1, 8)))


@pytest.mark.parametrize("position,expected_orientation", [
    ("right", "vertical"), ("left", "vertical"), ("top", "horizontal"), ("bottom", "horizontal"),
])
def test_colorbar_position_sets_orientation(grid_tab, position, expected_orientation):
    grid_tab.cbar_position.setCurrentText(position)
    assert grid_tab._cbar is not None
    assert grid_tab._cbar.orientation == expected_orientation


def test_colorbar_box_toggle_controls_outline_visibility(grid_tab):
    grid_tab.cbar_box.setChecked(False)
    grid_tab.refresh_plot()
    assert grid_tab._cbar.outline.get_visible() is False
    grid_tab.cbar_box.setChecked(True)
    grid_tab.refresh_plot()
    assert grid_tab._cbar.outline.get_visible() is True


def test_dragging_the_colorbar_moves_it_and_suppresses_the_click_dialog(grid_tab, monkeypatch):
    cbar_ax = grid_tab._cbar.ax
    orig_bounds = cbar_ax.get_position().bounds

    dialog_opened = {"count": 0}
    from scientific_visualization.gui import grid_tab as grid_tab_module

    class _ExplodingDialog:
        def __init__(self, *a, **kw):
            dialog_opened["count"] += 1
        def exec_(self):
            raise AssertionError("Color-range dialog should not open for a drag")

    monkeypatch.setattr(grid_tab_module, "ColorRangeDialog", _ExplodingDialog)

    grid_tab._on_canvas_press(_FakeMplEvent(100, 100, inaxes=cbar_ax))
    assert grid_tab._cbar_drag is not None
    grid_tab._on_canvas_motion(_FakeMplEvent(150, 130, inaxes=cbar_ax))
    assert grid_tab._press_info["moved"] is True
    moved_bounds = cbar_ax.get_position().bounds
    assert moved_bounds != orig_bounds

    grid_tab._on_canvas_release(_FakeMplEvent(150, 130, inaxes=cbar_ax))
    assert dialog_opened["count"] == 0
    # position persists after release
    assert tuple(cbar_ax.get_position().bounds) == moved_bounds


def test_plain_click_without_drag_still_opens_color_range_dialog(grid_tab, monkeypatch):
    cbar_ax = grid_tab._cbar.ax
    dialog_opened = {"count": 0}
    from scientific_visualization.gui import grid_tab as grid_tab_module

    class _FakeDialog:
        Accepted = 1
        def __init__(self, *a, **kw):
            dialog_opened["count"] += 1
        def exec_(self):
            return 0  # Rejected, so refresh_plot's state isn't touched further
        vmin = type("W", (), {"value": lambda self: 0.0})()
        vmax = type("W", (), {"value": lambda self: 1.0})()

    monkeypatch.setattr(grid_tab_module, "ColorRangeDialog", _FakeDialog)

    grid_tab._on_canvas_press(_FakeMplEvent(100, 100, inaxes=cbar_ax))
    # no motion event at all -> not a drag
    grid_tab._on_canvas_release(_FakeMplEvent(100, 100, inaxes=cbar_ax))
    assert dialog_opened["count"] == 1


def test_colorbar_drag_does_not_move_when_clicking_outside_colorbar(grid_tab):
    ax = grid_tab.canvas.figure.axes[0]
    grid_tab._on_canvas_press(_FakeMplEvent(10, 10, inaxes=ax))
    assert grid_tab._cbar_drag is None


# --- 3D scalar bar (PyVista) ---

def test_three_d_scalar_bar_position_and_box_options():
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.core.configuration import RenderingConfig
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")

    c1 = CoordinateAxis("x1", np.linspace(0, 1, 4))
    c2 = CoordinateAxis("x2", np.linspace(-1, 1, 3))
    ds = Dataset("E1", np.arange(12, dtype=float).reshape(4, 3), ("x1", "x2"), (c1, c2))

    # Reuse a single off-screen plotter across positions rather than
    # creating/destroying many VTK render windows in one process, which is
    # unnecessary here and can be unreliable under software rendering.
    plotter = pv.Plotter(off_screen=True)
    try:
        for position in ("right", "left", "top", "bottom"):
            plotter.clear()
            renderer = ThreeDRenderer(plotter)
            cfg = RenderingConfig(colorbar_position=position, colorbar_box=True, colorbar_interactive=True)
            renderer.add_2d_plane(ds, plane_axis="x3", position=0.0, config=cfg)
            assert "E1" in plotter.scalar_bars
    finally:
        plotter.close()


def test_three_d_scalar_bar_can_be_hidden():
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.core.configuration import RenderingConfig
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")
    c1 = CoordinateAxis("x1", np.linspace(0, 1, 4))
    c2 = CoordinateAxis("x2", np.linspace(-1, 1, 3))
    ds = Dataset("E1", np.arange(12, dtype=float).reshape(4, 3), ("x1", "x2"), (c1, c2))
    plotter = pv.Plotter(off_screen=True)
    renderer = ThreeDRenderer(plotter)
    cfg = RenderingConfig(show_colorbar=False)
    renderer.add_2d_plane(ds, plane_axis="x3", position=0.0, config=cfg)
    assert "E1" not in plotter.scalar_bars
    plotter.close()


def test_rendering_config_rejects_invalid_colorbar_position():
    from scientific_visualization.core.configuration import RenderingConfig
    with pytest.raises(ValueError, match="colorbar_position"):
        RenderingConfig(colorbar_position="diagonal").validate()
