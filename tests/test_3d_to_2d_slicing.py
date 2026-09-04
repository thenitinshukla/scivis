"""Tests for opening 3D grid files in the 2D view.

Regression coverage for a real crash: a 3D Simulation file (e.g. a "thin"
run with only a couple of grid points along one axis) selected while the
Grid tab was in "2D map" mode used to be passed straight to
`ax.imshow()` as a 3D array, raising "Invalid shape (...) for image data"
instead of being viewable at all.

The fix has two parts, tested separately:
  * `GridFile.slice2d` (io/grid.py): a pure, GUI-independent slicing
    operation on the data model.
  * `GridTab._effective_2d_grid` / the new "3D slice" control group
    (gui/grid_tab.py): wires user-selected slice axis/index into the
    existing 2D plotting code path.
"""
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from scientific_visualization.io.grid import GridFile


def _make_3d_grid_file(tmp_path, shape=(2, 6, 5), axis_names=("x", "y", "z")):
    """shape is in numpy/HDF5 order: (n_x3, n_x2, n_x1)."""
    p = tmp_path / "b1-000005.h5"
    n_x3, n_x2, n_x1 = shape
    data = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "b1"; f.attrs["TIME"] = 0.14; f.attrs["ITER"] = 5
        f.attrs["LABEL"] = "B_1"; f.attrs["UNITS"] = "m_e omega_p e^-1"
        d = f.create_dataset("b1", data=data)
        d.attrs["UNITS"] = "m_e omega_p e^-1"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, float(n_x1)]); a1.attrs["NAME"] = axis_names[0]
        a2 = g.create_dataset("AXIS2", data=[0.0, float(n_x2)]); a2.attrs["NAME"] = axis_names[1]
        a3 = g.create_dataset("AXIS3", data=[0.0, float(n_x3)]); a3.attrs["NAME"] = axis_names[2]
    return str(p)


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


# --- GridFile.slice2d ---

def test_slice2d_matches_raw_numpy_indexing(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))  # x3 has only 2 points
    gf = GridFile.load(path)
    assert gf.ndim == 3
    assert gf.axes[2].n == 2  # x3 (the outermost/slowest numpy axis) is the thin one

    for idx in range(gf.axes[2].n):
        sliced = gf.slice2d(axis=2, index=idx)
        assert sliced.ndim == 2
        assert sliced.shape == (gf.axes[1].n, gf.axes[0].n)
        np.testing.assert_array_equal(sliced.data, gf.data[idx, :, :])
        # remaining axes preserve order: fastest-varying first
        assert [a.name for a in sliced.axes] == [gf.axes[0].name, gf.axes[1].name]


def test_slice2d_all_three_axes_are_consistent_with_raw_indexing(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(3, 4, 5))
    gf = GridFile.load(path)
    for axis in (0, 1, 2):
        np_axis = gf.ndim - 1 - axis
        for idx in range(gf.axes[axis].n):
            sliced = gf.slice2d(axis=axis, index=idx)
            expected = np.take(gf.data, idx, axis=np_axis)
            np.testing.assert_array_equal(sliced.data, expected)


def test_slice2d_to_dataset_has_correct_shape_and_axes(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    sliced = gf.slice2d(axis=2, index=0)
    ds = sliced.to_dataset()
    assert ds.data.shape == (5, 6)  # physical order: (x1, x2)
    assert ds.axes == ("x", "y")


def test_slice2d_label_records_the_fixed_axis_and_value(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    sliced = gf.slice2d(axis=2, index=1)
    assert "z" in sliced.label
    assert "slice" in sliced.label.lower()


def test_slice2d_rejects_wrong_dimensionality(tmp_path):
    path = _make_2d_grid_file(tmp_path)
    gf = GridFile.load(path)
    with pytest.raises(ValueError, match="3D"):
        gf.slice2d(axis=0, index=0)


def test_slice2d_rejects_out_of_range_index(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    with pytest.raises(ValueError, match="out of range"):
        gf.slice2d(axis=2, index=99)
    with pytest.raises(ValueError):
        gf.slice2d(axis=2, index=-1)


def test_slice2d_rejects_invalid_axis(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    with pytest.raises(ValueError, match="axis"):
        gf.slice2d(axis=5, index=0)


def test_slice2d_requires_loaded_data(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.info(path)  # metadata only
    with pytest.raises(ValueError, match="not loaded"):
        gf.slice2d(axis=2, index=0)


# --- GridTab wiring ---

@pytest.fixture
def grid_tab_3d(tmp_path):
    from scientific_visualization.gui.grid_tab import GridTab
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    tab = GridTab()
    tab.files = [path]
    tab.file_list.addItem("b1-000005.h5")
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    return tab


def test_grid_tab_shows_slice_controls_for_3d_file(grid_tab_3d):
    assert grid_tab_3d.grid.ndim == 3
    # auto-selects the axis with the fewest points (x3, the "thin" one)
    assert grid_tab_3d.slice_axis.currentIndex() == 2
    assert grid_tab_3d.slice_index.maximum() == 1


def test_grid_tab_hides_slice_controls_for_2d_file(tmp_path):
    from scientific_visualization.gui.grid_tab import GridTab
    path = _make_2d_grid_file(tmp_path)
    tab = GridTab()
    tab.files = [path]
    tab.file_list.addItem("e1-000000.h5")
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    assert tab.grid.ndim == 2
    assert tab.slice_box.property("_auto_selected_for") is None or not tab.slice_box.isVisibleTo(tab.slice_box.window())


def test_grid_tab_2d_mode_renders_a_3d_file_without_crashing(grid_tab_3d):
    grid_tab_3d.mode_2d.setChecked(True)
    grid_tab_3d.refresh_plot()
    assert grid_tab_3d._image is not None
    assert grid_tab_3d._image.get_array().shape == (6, 5)  # x2 by x1, sliced at x3


def test_grid_tab_changing_slice_axis_updates_the_rendered_shape(grid_tab_3d):
    grid_tab_3d.mode_2d.setChecked(True)
    grid_tab_3d.slice_axis.setCurrentIndex(0)  # slice out x1 (5 points) instead
    grid_tab_3d.refresh_plot()
    assert grid_tab_3d._image.get_array().shape == (2, 6)  # x3 by x2


def test_grid_tab_changing_slice_index_changes_the_data(grid_tab_3d):
    grid_tab_3d.mode_2d.setChecked(True)
    grid_tab_3d.refresh_plot()
    data_at_0 = grid_tab_3d._image.get_array().copy()
    grid_tab_3d.slice_index.setValue(1)
    grid_tab_3d.refresh_plot()
    data_at_1 = grid_tab_3d._image.get_array()
    assert not np.array_equal(data_at_0, data_at_1)


def test_grid_tab_manual_ranges_track_the_remaining_axes_after_slicing(grid_tab_3d):
    # Default slice axis is x3 (index 2); remaining axes are x(=x1), y(=x2).
    assert grid_tab_3d.x_range_min.value() == pytest.approx(0.0)
    assert grid_tab_3d.x_range_max.value() == pytest.approx(5.0)
    assert grid_tab_3d.y_range_min.value() == pytest.approx(0.0)
    assert grid_tab_3d.y_range_max.value() == pytest.approx(6.0)

    grid_tab_3d.slice_axis.setCurrentIndex(0)  # now slicing out x1; remaining (in order) are x2, x3
    assert grid_tab_3d.x_range_max.value() == pytest.approx(6.0)
    assert grid_tab_3d.y_range_max.value() == pytest.approx(2.0)


def test_grid_tab_slice_coord_label_reports_physical_position(grid_tab_3d):
    text = grid_tab_3d.slice_coord_label.text()
    assert "z" in text
    assert "index 0 of 2" in text
