"""Tests for the advanced 3D features: isosurfaces, volume rendering,
interactive clip planes, bounding box/orientation-axes toggles, and
screenshot export.

Covers both layers:
  * `ThreeDRenderer` directly (pure, GUI-independent) -- correctness of
    the geometry/values produced.
  * `ThreeDTab` (GUI wiring) -- mode dispatch, isovalue parsing/validation,
    and error handling, using a real off-screen-rendered `ThreeDRenderer`
    injected into the tab (pyvistaqt, needed only for the *interactive*
    embedded widget, is not required for this).
"""
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QMessageBox

_app = QApplication.instance() or QApplication([])

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.core.configuration import RenderingConfig
from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv


def _gaussian_blob_dataset(n=24, name="blob"):
    coords = tuple(CoordinateAxis(f"x{i+1}", np.linspace(-2, 2, n)) for i in range(3))
    X, Y, Z = np.meshgrid(coords[0].values, coords[1].values, coords[2].values, indexing="ij")
    data = np.exp(-(X ** 2 + Y ** 2 + Z ** 2))
    return Dataset(name, data, ("x1", "x2", "x3"), coords, "a.u.", 0.0, "s", {}, "synthetic")


def _make_3d_hdf5_file(tmp_path, n=16, name="blob"):
    p = tmp_path / f"{name}-000000.h5"
    x = np.linspace(-2, 2, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    data = np.exp(-(X ** 2 + Y ** 2 + Z ** 2)).astype(np.float32)
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = name; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset(name, data=data); d.attrs["UNITS"] = "a.u."
        g = f.create_group("AXIS")
        for i in range(3):
            a = g.create_dataset(f"AXIS{i+1}", data=[-2.0, 2.0]); a.attrs["NAME"] = f"x{i+1}"
    return str(p)


@pytest.fixture
def offscreen_plotter():
    if pv is None:
        pytest.skip("pyvista not installed")
    plotter = pv.Plotter(off_screen=True)
    yield plotter
    plotter.close()


# --- ThreeDRenderer: _build_3d_grid ---

def test_build_3d_grid_uses_imagedata_for_uniform_spacing(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=10)
    r = ThreeDRenderer(offscreen_plotter)
    grid = r._build_3d_grid(ds)
    assert isinstance(grid, pv.ImageData)
    assert grid.n_points == 10 ** 3
    np.testing.assert_allclose(grid["blob"].reshape(10, 10, 10, order="F"), ds.data)


def test_build_3d_grid_falls_back_to_structured_grid_for_non_uniform_spacing(offscreen_plotter):
    values = np.array([0.0, 1.0, 3.0, 10.0])  # non-uniform
    coords = (
        CoordinateAxis("x1", values),
        CoordinateAxis("x2", np.linspace(0, 1, 4)),
        CoordinateAxis("x3", np.linspace(0, 1, 4)),
    )
    data = np.random.RandomState(0).rand(4, 4, 4)
    ds = Dataset("f", data, ("x1", "x2", "x3"), coords, "", 0.0, "s", {}, "s")
    r = ThreeDRenderer(offscreen_plotter)
    grid = r._build_3d_grid(ds)
    assert isinstance(grid, pv.StructuredGrid)
    assert grid.n_points == 64


# --- suggest_isovalues ---

def test_suggest_isovalues_returns_sorted_values_within_data_range():
    ds = _gaussian_blob_dataset(n=12)
    values = ThreeDRenderer.suggest_isovalues(ds, n=3)
    assert len(values) == 3
    assert values == sorted(values)
    lo, hi = float(ds.data.min()), float(ds.data.max())
    assert all(lo <= v <= hi for v in values)


def test_suggest_isovalues_respects_n():
    ds = _gaussian_blob_dataset(n=12)
    for n in (1, 2, 5):
        assert len(ThreeDRenderer.suggest_isovalues(ds, n=n)) == n


def test_suggest_isovalues_rejects_n_less_than_one():
    ds = _gaussian_blob_dataset(n=8)
    with pytest.raises(ValueError):
        ThreeDRenderer.suggest_isovalues(ds, n=0)


def test_suggest_isovalues_rejects_all_nan_data():
    ds = _gaussian_blob_dataset(n=6)
    ds.data[:] = np.nan
    with pytest.raises(ValueError, match="no finite"):
        ThreeDRenderer.suggest_isovalues(ds)


# --- add_isosurfaces ---

def test_add_isosurfaces_produces_a_visible_mesh(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=20)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=2)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig())
    assert actor is not None
    assert f"{ds.name} [{ds.units}]" in offscreen_plotter.scalar_bars


def test_add_isosurfaces_rejects_2d_dataset(offscreen_plotter):
    coords = (CoordinateAxis("x1", np.linspace(0, 1, 5)), CoordinateAxis("x2", np.linspace(0, 1, 5)))
    ds = Dataset("f", np.random.rand(5, 5), ("x1", "x2"), coords, "", 0.0, "s", {}, "s")
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError, match="3D"):
        r.add_isosurfaces(ds, [0.5])


def test_add_isosurfaces_rejects_empty_isovalue_list(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=8)
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError, match="at least one"):
        r.add_isosurfaces(ds, [])


def test_add_isosurfaces_out_of_range_value_raises_actionable_error(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=12)
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError) as excinfo:
        r.add_isosurfaces(ds, [999.0])
    msg = str(excinfo.value)
    assert "999" in msg
    assert "range" in msg  # reports the actual data range, not just "failed"


# --- add_clipped_volume ---

def test_add_clipped_volume_interactive(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=12)
    r = ThreeDRenderer(offscreen_plotter)
    actor = r.add_clipped_volume(ds, config=RenderingConfig(), normal="x", interactive=True)
    assert actor is not None


def test_add_clipped_volume_noninteractive_actually_clips_geometry(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=16)
    r = ThreeDRenderer(offscreen_plotter)
    full_grid = r._build_3d_grid(ds)
    actor = r.add_clipped_volume(ds, config=RenderingConfig(), normal="x", interactive=False)
    assert actor is not None
    # A one-shot clip should produce strictly fewer points than the full grid.
    clipped_mesh = actor.mapper.dataset
    assert clipped_mesh.n_points < full_grid.n_points


def test_add_clipped_volume_rejects_2d_dataset(offscreen_plotter):
    coords = (CoordinateAxis("x1", np.linspace(0, 1, 5)), CoordinateAxis("x2", np.linspace(0, 1, 5)))
    ds = Dataset("f", np.random.rand(5, 5), ("x1", "x2"), coords, "", 0.0, "s", {}, "s")
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError, match="3D"):
        r.add_clipped_volume(ds)


# --- volume rendering, bounding box, axes, screenshot ---

def test_add_native_3d_volume_render(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=10)
    r = ThreeDRenderer(offscreen_plotter)
    actor = r.add_native_3d(ds, config=RenderingConfig())
    assert actor is not None


def test_bounding_box_and_axes_toggles_do_not_raise(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=8)
    r = ThreeDRenderer(offscreen_plotter)
    r.add_native_3d_slices(ds, config=RenderingConfig())
    r.set_show_bounding_box(True)
    r.set_show_bounding_box(False)
    r.set_show_orientation_axes(True)
    r.set_show_orientation_axes(False)


def test_save_screenshot_writes_a_real_image(offscreen_plotter, tmp_path):
    ds = _gaussian_blob_dataset(n=10)
    r = ThreeDRenderer(offscreen_plotter)
    r.add_native_3d_slices(ds, config=RenderingConfig())
    out = tmp_path / "shot.png"
    r.save_screenshot(str(out))
    assert out.exists() and out.stat().st_size > 0


# --- GUI wiring: ThreeDTab ---

@pytest.fixture
def tab_with_3d_dataset(tmp_path):
    from scientific_visualization.gui.three_d_tab import ThreeDTab
    if pv is None:
        pytest.skip("pyvista not installed")
    tab = ThreeDTab()
    tab.renderer = ThreeDRenderer(pv.Plotter(off_screen=True))
    # Pick a 3D-compatible mode *before* apply_selection() (which renders
    # immediately on load) -- the mode combo defaults to "2D plane" for
    # newly-constructed tabs, and applying a 3D file under a 2D-only mode
    # correctly raises a validation error that pops a blocking QMessageBox,
    # which would otherwise hang this fixture.
    tab.mode.setCurrentText("3D orthogonal slices")
    path = _make_3d_hdf5_file(tmp_path, n=16)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("blob-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()
    assert tab.dataset is not None and tab.dataset.ndim == 3
    return tab


def _actor_count(tab):
    return len(tab.renderer.plotter.renderer.actors)


def test_mode_combo_offers_all_3d_modes(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    options = [tab.mode.itemText(i) for i in range(tab.mode.count())]
    for expected in ("3D orthogonal slices", "3D volume", "3D isosurfaces", "3D clip plane"):
        assert expected in options


def test_gui_volume_mode_renders(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D volume")
    tab.render()
    assert _actor_count(tab) > 0


def test_gui_isosurfaces_auto_mode_renders(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Auto (percentiles)")
    tab.isovalue_count.setValue(3)
    tab.render()
    assert _actor_count(tab) > 0


def test_gui_isosurfaces_manual_mode_with_suggested_values(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Manual list")
    tab._fill_suggested_isovalues()
    assert tab.isovalue_manual.text().strip() != ""
    tab.render()
    assert _actor_count(tab) > 0


def test_gui_isosurfaces_bad_manual_input_shows_warning_not_crash(tab_with_3d_dataset, monkeypatch):
    tab = tab_with_3d_dataset
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else "") or QMessageBox.Ok))
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Manual list")
    tab.isovalue_manual.setText("not,a,number")
    tab.render()
    assert len(warnings) == 1
    assert "Could not parse" in warnings[0]


def test_gui_clip_plane_modes_render(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D clip plane")
    for interactive in (False, True):
        tab.clip_interactive.setChecked(interactive)
        tab.render()
        assert _actor_count(tab) > 0


def test_gui_2d_mode_on_3d_dataset_warns_instead_of_crashing(tab_with_3d_dataset, monkeypatch):
    tab = tab_with_3d_dataset
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else "") or QMessageBox.Ok))
    tab.mode.setCurrentText("2D plane")
    tab.render()
    assert len(warnings) == 1
    assert "2D" in warnings[0] and "3D" in warnings[0]


def test_gui_bounding_box_and_axes_checkboxes_wired(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.show_bounding_box.setChecked(True)   # must not raise
    tab.show_bounding_box.setChecked(False)
    tab.show_orientation_axes.setChecked(False)
    tab.show_orientation_axes.setChecked(True)


def test_gui_save_screenshot_writes_real_file(tab_with_3d_dataset, tmp_path, monkeypatch):
    tab = tab_with_3d_dataset
    out = tmp_path / "shot.png"
    from PyQt5.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "")))
    tab.save_screenshot()
    assert out.exists() and out.stat().st_size > 0
    assert str(out) in tab.info.text()


def test_isovalue_mode_toggle_enables_correct_widgets(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Manual list")
    assert tab.isovalue_manual.isEnabled()
    assert not tab.isovalue_count.isEnabled()
    tab.isovalue_mode.setCurrentText("Auto (percentiles)")
    assert not tab.isovalue_manual.isEnabled()
    assert tab.isovalue_count.isEnabled()


def test_mode_switch_shows_correct_option_groups(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.show()  # setVisible()'s effect only shows up in isVisible() once the top-level window is shown
    tab.mode.setCurrentText("3D isosurfaces")
    assert tab.isosurface_box.isVisible()
    assert not tab.clip_box.isVisible()
    tab.mode.setCurrentText("3D clip plane")
    assert tab.clip_box.isVisible()
    assert not tab.isosurface_box.isVisible()
    tab.mode.setCurrentText("3D volume")
    assert not tab.isosurface_box.isVisible()
    assert not tab.clip_box.isVisible()


# --- Camera presets (plan.md 6.6) ---

def test_camera_preset_options_include_all_six_directions_plus_isometric_and_fit(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    options = [tab.camera_preset.itemText(i) for i in range(tab.camera_preset.count())]
    for expected in ("Isometric", "Front", "Back", "Left", "Right", "Top", "Bottom", "Fit to data"):
        assert expected in options


@pytest.mark.parametrize("preset,expected_direction", [
    ("Top", (0, 0, 1)),
    ("Bottom", (0, 0, -1)),
    ("Front", (0, -1, 0)),
    ("Back", (0, 1, 0)),
    ("Right", (1, 0, 0)),
    ("Left", (-1, 0, 0)),
])
def test_camera_preset_points_the_camera_in_the_correct_direction(tab_with_3d_dataset, preset, expected_direction):
    """Regression test: the previous Top/Bottom mapping was backwards
    (labeled "Top" actually looked from below, and vice versa), and
    Front/Back/Left/Right didn't exist at all. Directions are verified
    against PyVista's actual camera_position, not assumed -- matches the
    same convention as Blender's numpad views (Front/Back along Y,
    Left/Right along X, Top/Bottom along Z)."""
    tab = tab_with_3d_dataset
    tab.camera_preset.setCurrentText(preset)
    tab.apply_camera_preset()
    pos, focal, up = tab.renderer.plotter.camera_position
    vec = np.array(pos) - np.array(focal)
    vec = vec / np.linalg.norm(vec)
    assert np.allclose(vec, expected_direction, atol=1e-2), (
        f"{preset}: camera direction {tuple(vec)} does not match expected {expected_direction}"
    )


def test_camera_preset_isometric_and_fit_to_data_do_not_raise(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.camera_preset.setCurrentText("Isometric")
    tab.apply_camera_preset()
    tab.camera_preset.setCurrentText("Fit to data")
    tab.apply_camera_preset()


def test_camera_preset_no_renderer_does_not_raise():
    from scientific_visualization.gui.three_d_tab import ThreeDTab
    tab = ThreeDTab()  # renderer may be None (no pyvistaqt installed)
    tab.renderer = None
    tab.camera_preset.setCurrentText("Top")
    tab.apply_camera_preset()  # must not raise


# --- Isosurface performance guards ---
# Regression tests for a real, severe bottleneck: add_isosurfaces() used to
# unconditionally call mesh.smooth(n_iter=20, ...) and request
# smooth_shading (which triggers VTK's compute_normals) on *any* resulting
# isosurface mesh, regardless of size. For a noisy or high-resolution 3D
# field, the extracted isosurface can have millions of points, and both of
# those operations scale with mesh size -- measured 34.7s total (23.3s in
# .smooth() alone, 11.3s more in compute_normals) for a 150^3 noisy volume,
# against ~2.5s for the actual (already VTK/C++) isosurface extraction.
# Both are now skipped above a size threshold, with a printed explanation,
# rather than silently stalling.

def _noisy_large_dataset(n=70, seed=0):
    """Deliberately noisy (not smooth) data: an isosurface of this has a
    large, highly-detailed point count even at a modest grid resolution,
    which is what actually triggers the slow path -- not raw voxel count."""
    coords = tuple(CoordinateAxis(f"x{i+1}", np.linspace(-2, 2, n)) for i in range(3))
    rng = np.random.RandomState(seed)
    data = rng.rand(n, n, n)  # pure noise: maximally complex isosurface
    return Dataset("noisy", data, ("x1", "x2", "x3"), coords, "a.u.", 0.0, "s", {}, "synthetic")


def test_isosurface_smoothing_is_skipped_for_a_very_large_mesh(offscreen_plotter, capsys):
    ds = _noisy_large_dataset(n=70)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig(), max_smooth_points=1000)
    assert actor is not None
    out = capsys.readouterr().out
    assert "Skipping isosurface smoothing" in out


def test_isosurface_smoothing_still_applies_for_a_small_mesh(offscreen_plotter, capsys):
    ds = _gaussian_blob_dataset(n=20)  # smooth data -> small, simple isosurface
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig())
    assert actor is not None
    out = capsys.readouterr().out
    assert "Skipping isosurface smoothing" not in out


def test_isosurface_flat_shading_kicks_in_for_a_very_large_mesh(offscreen_plotter, capsys):
    ds = _noisy_large_dataset(n=70)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    r.add_isosurfaces(ds, values, config=RenderingConfig(), max_smooth_points=1000)
    out = capsys.readouterr().out
    assert "Using flat shading for a large mesh" in out


def test_isosurface_smooth_shading_preserved_for_a_small_mesh(offscreen_plotter, capsys):
    ds = _gaussian_blob_dataset(n=20)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    r.add_isosurfaces(ds, values, config=RenderingConfig())
    out = capsys.readouterr().out
    assert "Using flat shading" not in out


def test_isosurface_disabling_smooth_flag_never_calls_smooth(offscreen_plotter, capsys):
    ds = _gaussian_blob_dataset(n=20)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig(), smooth=False)
    assert actor is not None
    out = capsys.readouterr().out
    assert "Skipping isosurface smoothing" not in out  # smoothing was never attempted, not "skipped"


def test_isosurface_large_noisy_volume_completes_quickly(offscreen_plotter):
    """The actual performance assertion: this used to take 30+ seconds."""
    import time
    ds = _noisy_large_dataset(n=70)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    t0 = time.perf_counter()
    r.add_isosurfaces(ds, values, config=RenderingConfig())
    elapsed = time.perf_counter() - t0
    assert elapsed < 10.0, f"isosurface rendering took {elapsed:.1f}s; expected well under 10s"
