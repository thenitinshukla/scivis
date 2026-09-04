from __future__ import annotations

from pathlib import Path
import numpy as np
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog, QCheckBox, QListWidget,
    QSpinBox, QLineEdit,
)

from ..core.configuration import RenderingConfig
from ..io.simulation import SimulationReader
from ..visualization.three_d import ThreeDRenderer
from ..session import save_xml_session, load_xml_session, value_as_bool, value_as_float, value_as_int
from .base_tab import BaseTab


class ThreeDTab(BaseTab):
    open_in_2d_requested = pyqtSignal(str)
    """Interactive PyVista viewer for native 3D data and 2D-to-3D promotion.

    Inherits the same splitter + scrollable control panel + "Panel:
    Left/Right/Top/Bottom" placement control as the 2D Fields/Grid tab
    (see gui/base_tab.py) by supplying its PyVista viewport as a custom
    `view_widget` -- the panel-position feature is implemented exactly
    once, in BaseTab, and both tabs get it for free.
    """

    def __init__(self, parent=None):
        self.dataset = None
        self.reader = SimulationReader()
        self._series = None
        self.renderer = None
        self.files: list[str] = []
        self._pending_files: list[str] = []
        self.file_list = None

        view_container = self._build_view_widget()
        super().__init__(parent, view_widget=view_container)
        self._build_controls()
        self.finish_layout()

    def set_theme(self, theme_name: str):
        """Update application/viewport styling without rebuilding geometry.

        Theme changes are UI concerns. Re-rendering a volume or isosurface
        just to change the surrounding chrome can be extremely expensive, so
        the 3D scene is preserved and only its independent background is
        updated.
        """
        self.theme = theme_name
        if self.renderer is not None:
            try:
                self.renderer.set_background("#111318" if theme_name == "Dark" else "#ffffff")
            except Exception:
                pass

    def _build_view_widget(self) -> QWidget:
        """Build the 3D viewport (or a fallback message if PyVista/PyVistaQt
        aren't installed), plus the interaction hint shown just below it,
        as a single widget suitable for BaseTab's `view_widget`."""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        try:
            from pyvistaqt import QtInteractor
            self._qt_interactor = QtInteractor(container)
            self._qt_interactor.setMinimumHeight(500)
            vbox.addWidget(self._qt_interactor, 1)
            self.renderer = ThreeDRenderer(self._qt_interactor)
            try:
                self._qt_interactor.enable_trackball_style()
            except Exception:
                pass
            interaction = QLabel("3D interaction: left-drag rotate • wheel zoom • middle-drag pan. Use Isometric to reset orientation.")
            interaction.setWordWrap(True)
            vbox.addWidget(interaction)
        except ImportError:
            self._qt_interactor = None
            msg = QLabel("3D viewer unavailable. Install PyVista and PyVistaQt to enable it.")
            msg.setWordWrap(True)
            vbox.addWidget(msg, 1)
        return container

    def _build_controls(self):
        controls = QGroupBox("3D visualization")
        form = QFormLayout(controls)
        file_buttons = QHBoxLayout()
        open_btn = QPushButton("Open file…")
        open_btn.clicked.connect(self.open_file)
        folder_btn = QPushButton("Open folder…")
        folder_btn.clicked.connect(self.open_folder)
        file_buttons.addWidget(open_btn); file_buttons.addWidget(folder_btn)
        form.addRow(file_buttons)
        self.file_list = QListWidget()
        self.file_list.currentRowChanged.connect(self._pending_row_changed)
        layout_pending = QVBoxLayout()
        apply_btn = QPushButton("Apply selection")
        apply_btn.clicked.connect(self.apply_selection)
        layout_pending.addWidget(self.file_list)
        layout_pending.addWidget(apply_btn)
        nav = QHBoxLayout()
        self.prev_frame_btn = QPushButton("◀ Previous frame"); self.prev_frame_btn.clicked.connect(lambda: self._select_relative(-1))
        self.next_frame_btn = QPushButton("Next frame ▶"); self.next_frame_btn.clicked.connect(lambda: self._select_relative(1))
        nav.addWidget(self.prev_frame_btn); nav.addWidget(self.next_frame_btn)
        layout_pending.addLayout(nav)
        session_row = QHBoxLayout()
        save_session = QPushButton("Save .xml…"); save_session.clicked.connect(self.save_session)
        load_session = QPushButton("Restore .xml…"); load_session.clicked.connect(self.load_session)
        session_row.addWidget(save_session); session_row.addWidget(load_session)
        layout_pending.addLayout(session_row)
        self.mode = QComboBox(); self.mode.addItems([
            "2D plane", "2D surface", "2D extrusion",
            "3D orthogonal slices", "3D single slice", "3D volume", "3D isosurfaces", "3D threshold", "3D clip plane", "3D box clip",
        ])
        self.mode.currentTextChanged.connect(self._update_mode_controls)
        form.addRow("Mode:", self.mode)
        self.plane_axis = QComboBox(); self.plane_axis.addItems(["x1", "x2", "x3"])
        form.addRow("Plane normal / height axis:", self.plane_axis)
        self.slice_value = QDoubleSpinBox(); self.slice_value.setRange(-1e12, 1e12); self.slice_value.setDecimals(8); self.slice_value.setValue(0.0)
        form.addRow("3D slice coordinate:", self.slice_value)
        self.position = QDoubleSpinBox(); self.position.setRange(-1e12,1e12); self.position.setDecimals(6); self.position.setValue(0.0)
        form.addRow("Plane/base position:", self.position)
        self.z_scale = QDoubleSpinBox(); self.z_scale.setRange(-1e6,1e6); self.z_scale.setDecimals(6); self.z_scale.setValue(1.0)
        form.addRow("Surface height scale:", self.z_scale)
        self.depth = QDoubleSpinBox(); self.depth.setRange(-1e12,1e12); self.depth.setDecimals(6); self.depth.setValue(1.0)
        form.addRow("Extrusion depth:", self.depth)

        self.isosurface_box = QGroupBox("Isosurface options")
        iso_form = QFormLayout(self.isosurface_box)
        self.isovalue_mode = QComboBox(); self.isovalue_mode.addItems(["Auto (percentiles)", "Manual list"])
        self.isovalue_mode.currentTextChanged.connect(self._update_isovalue_controls)
        iso_form.addRow("Isovalues:", self.isovalue_mode)
        self.isovalue_count = QSpinBox(); self.isovalue_count.setRange(1, 10); self.isovalue_count.setValue(3)
        iso_form.addRow("Number of surfaces:", self.isovalue_count)
        self.isovalue_manual = QLineEdit(); self.isovalue_manual.setPlaceholderText("e.g. 0.1, 0.3, 0.6")
        iso_form.addRow("Values (comma-separated):", self.isovalue_manual)
        self.isovalue_suggest_btn = QPushButton("Suggest values from data")
        self.isovalue_suggest_btn.clicked.connect(self._fill_suggested_isovalues)
        iso_form.addRow(self.isovalue_suggest_btn)
        form.addRow(self.isosurface_box)

        self.threshold_box = QGroupBox("Threshold options")
        th_form = QFormLayout(self.threshold_box)
        self.threshold_min = QDoubleSpinBox(); self.threshold_min.setRange(-1e300, 1e300); self.threshold_min.setDecimals(8)
        self.threshold_max = QDoubleSpinBox(); self.threshold_max.setRange(-1e300, 1e300); self.threshold_max.setDecimals(8); self.threshold_max.setValue(1.0)
        th_form.addRow("Lower:", self.threshold_min); th_form.addRow("Upper:", self.threshold_max)
        form.addRow(self.threshold_box)

        self.clip_box = QGroupBox("Clip plane options")
        clip_form = QFormLayout(self.clip_box)
        self.clip_normal = QComboBox(); self.clip_normal.addItems(["x", "y", "z"])
        clip_form.addRow("Plane normal:", self.clip_normal)
        self.clip_interactive = QCheckBox("Interactive (drag the plane widget in the viewport)")
        self.clip_interactive.setChecked(True)
        clip_form.addRow(self.clip_interactive)
        form.addRow(self.clip_box)

        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0.05,1.0); self.opacity.setSingleStep(0.05); self.opacity.setValue(1.0)
        form.addRow("Opacity:", self.opacity)
        self.cmap = QComboBox(); self.cmap.addItems(["viridis","plasma","inferno","magma","cividis","turbo","coolwarm","RdBu_r","twilight","gray"])
        form.addRow("Colormap:", self.cmap)
        self.reverse_colors = QCheckBox("Reverse colormap"); form.addRow(self.reverse_colors)
        self.symmetric = QCheckBox("Symmetric color limits"); self.symmetric.setChecked(False); form.addRow(self.symmetric)
        self.vmin = QDoubleSpinBox(); self.vmin.setRange(-1e300, 1e300); self.vmin.setDecimals(10); form.addRow("Color minimum:", self.vmin)
        self.vmax = QDoubleSpinBox(); self.vmax.setRange(-1e300, 1e300); self.vmax.setDecimals(10); form.addRow("Color maximum:", self.vmax)
        self.use_limits = QCheckBox("Use manual color limits"); form.addRow(self.use_limits)
        self.colorbar_position = QComboBox(); self.colorbar_position.addItems(["right", "left", "top", "bottom"])
        form.addRow("Colorbar position:", self.colorbar_position)
        self.colorbar_box = QCheckBox("Colorbar box/outline"); form.addRow(self.colorbar_box)
        self.colorbar_interactive = QCheckBox("Draggable colorbar (drag/resize with mouse)")
        self.colorbar_interactive.setChecked(True)
        form.addRow(self.colorbar_interactive)
        self.colorbar_width = QDoubleSpinBox(); self.colorbar_width.setRange(0.02, 1.0); self.colorbar_width.setDecimals(3); self.colorbar_width.setValue(0.10); self.colorbar_width.setSingleStep(0.01); form.addRow("Colorbar width:", self.colorbar_width)
        self.colorbar_height = QDoubleSpinBox(); self.colorbar_height.setRange(0.02, 1.0); self.colorbar_height.setDecimals(3); self.colorbar_height.setValue(0.80); self.colorbar_height.setSingleStep(0.01); form.addRow("Colorbar height:", self.colorbar_height)
        self.smooth_shading = QCheckBox("Smooth shading"); self.smooth_shading.setChecked(True); form.addRow(self.smooth_shading)
        self.show_edges = QCheckBox("Show mesh edges"); form.addRow(self.show_edges)
        advanced3d = QGroupBox("Advanced 3D rendering")
        adv_form = QFormLayout(advanced3d)
        self.render_quality = QComboBox(); self.render_quality.addItems(["High", "Balanced", "Fast"]); self.render_quality.setCurrentText("Balanced")
        adv_form.addRow("Render quality:", self.render_quality)
        self.lighting = QCheckBox("Surface lighting"); self.lighting.setChecked(True); adv_form.addRow(self.lighting)
        self.eye_dome_lighting = QCheckBox("Eye-dome lighting (depth enhancement)"); adv_form.addRow(self.eye_dome_lighting)
        self.depth_peeling = QCheckBox("Depth peeling (high-quality transparency)"); adv_form.addRow(self.depth_peeling)
        self.ssao = QCheckBox("SSAO (ambient occlusion)"); adv_form.addRow(self.ssao)
        self.stereo = QCheckBox("Stereo render") ; adv_form.addRow(self.stereo)
        self.hidden_line_removal = QCheckBox("Hidden-line geometry mode"); adv_form.addRow(self.hidden_line_removal)
        self.antialiasing = QCheckBox("Anti-aliasing"); self.antialiasing.setChecked(True); adv_form.addRow(self.antialiasing)
        self.show_edges_strength = QDoubleSpinBox(); self.show_edges_strength.setRange(0, 1); self.show_edges_strength.setValue(1); self.show_edges_strength.setSingleStep(0.1); adv_form.addRow("Edge opacity:", self.show_edges_strength)
        self.camera_preset = QComboBox(); self.camera_preset.addItems(["Current", "Isometric", "Front", "Back", "Left", "Right", "Top", "Bottom", "Fit to data"]); adv_form.addRow("Camera preset:", self.camera_preset)
        apply_cam = QPushButton("Apply camera preset"); apply_cam.clicked.connect(self.apply_camera_preset); adv_form.addRow(apply_cam)
        form.addRow(advanced3d)
        self.fast_render = QComboBox(); self.fast_render.addItems(["Full resolution", "75% resolution", "50% resolution", "25% resolution"]); self.fast_render.setToolTip("Render a lower-resolution copy for interactive exploration. Source data are unchanged."); form.addRow("Interactive resolution:", self.fast_render)
        self.show_bounding_box = QCheckBox("Show bounding box / axis ticks")
        self.show_bounding_box.stateChanged.connect(self._toggle_bounding_box)
        form.addRow(self.show_bounding_box)
        self.show_orientation_axes = QCheckBox("Show orientation widget")
        self.show_orientation_axes.setChecked(True)
        self.show_orientation_axes.stateChanged.connect(self._toggle_orientation_axes)
        form.addRow(self.show_orientation_axes)
        buttons = QHBoxLayout()
        render = QPushButton("Render / replace scene")
        render.clicked.connect(self.render)
        buttons.addWidget(render)
        add = QPushButton("Add to scene")
        add.clicked.connect(lambda: self.render(clear_scene=False))
        buttons.addWidget(add)
        clear = QPushButton("Clear scene")
        clear.clicked.connect(self.clear_scene)
        buttons.addWidget(clear)
        form.addRow(buttons)
        camera = QHBoxLayout()
        reset = QPushButton("Reset camera")
        reset.clicked.connect(self.reset_camera)
        camera.addWidget(reset)
        iso = QPushButton("Isometric")
        iso.clicked.connect(self.isometric_camera)
        camera.addWidget(iso)
        screenshot = QPushButton("Save screenshot…")
        screenshot.clicked.connect(self.save_screenshot)
        camera.addWidget(screenshot)
        form.addRow(camera)
        move_row = QHBoxLayout()
        self.move_left_btn = QPushButton("←"); self.move_left_btn.setToolTip("Move 3D view left"); self.move_left_btn.clicked.connect(lambda: self.move_camera(-1, 0))
        self.move_right_btn = QPushButton("→"); self.move_right_btn.setToolTip("Move 3D view right"); self.move_right_btn.clicked.connect(lambda: self.move_camera(1, 0))
        self.move_up_btn = QPushButton("↑"); self.move_up_btn.setToolTip("Move 3D view up"); self.move_up_btn.clicked.connect(lambda: self.move_camera(0, 1))
        self.move_down_btn = QPushButton("↓"); self.move_down_btn.setToolTip("Move 3D view down"); self.move_down_btn.clicked.connect(lambda: self.move_camera(0, -1))
        for b in (self.move_left_btn, self.move_right_btn, self.move_up_btn, self.move_down_btn): move_row.addWidget(b)
        form.addRow("Move view:", move_row)
        self.info = QLabel("No dataset loaded.")
        self.info.setWordWrap(True)
        form.addRow(self.info)
        self.control_layout.addWidget(controls)
        self.control_layout.addLayout(layout_pending)
        self._update_mode_controls(self.mode.currentText())

    def refresh_plot(self):
        """BaseTab (e.g. after a theme change) calls this expecting every
        tab to be able to re-render itself. The 3D tab otherwise renders
        only on explicit user action (the Render/Add/Clear buttons), so
        this just re-renders the current dataset with existing settings
        if one is already loaded, and is a no-op otherwise."""
        if self.dataset is not None:
            self.render(clear_scene=True)

    def _open_current_in_2d(self):
        if self.dataset is not None and getattr(self.dataset, "source", None):
            self.open_in_2d_requested.emit(str(self.dataset.source))

    def _pending_row_changed(self, row):
        if 0 <= row < len(self._pending_files):
            self.info.setText(f"Selected: {Path(self._pending_files[row]).name}. Click Apply selection to load it.")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HDF5 file", "", "HDF5 files (*.h5 *.hdf5);;All files (*)")
        if not path:
            return
        self._pending_files = [path]
        self.file_list.clear(); self.file_list.addItem(Path(path).name); self.file_list.setCurrentRow(0)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open data folder")
        if not folder:
            return
        files = sorted(str(p) for p in Path(folder).iterdir() if p.suffix.lower() in {".h5", ".hdf5"})
        if not files:
            QMessageBox.warning(self, "No files found", "No HDF5 files were found in that folder.")
            return
        self._pending_files = files
        self.file_list.clear()
        self.file_list.addItems([Path(f).name for f in files])
        self.file_list.setCurrentRow(0)

    def apply_selection(self):
        row = self.file_list.currentRow() if self.file_list is not None else -1
        if not (0 <= row < len(self._pending_files)):
            return
        path = self._pending_files[row]
        try:
            self.files = list(self._pending_files)
            from ..io.lazy import LazyGridSeries
            self._series = LazyGridSeries(self.files, cache_size=3) if len(self.files) > 1 else None
            if self._series is not None:
                row = self.file_list.currentRow()
                self.dataset = self._series.load(max(0, row)).to_dataset()
            else:
                self.dataset = self.reader.load(path)
            self.info.setText(self.dataset.summary() + " | 2D data can be rendered as plane, surface, or extrusion in 3D; 3D data can be sliced into 2D in the Fields / Grid tab.")
            self._configure_2d_axis_options()
            if self.dataset.ndim == 3:
                finite = self.dataset.data[np.isfinite(self.dataset.data)]
                if finite.size:
                    lo, hi = float(finite.min()), float(finite.max())
                    self.threshold_min.setRange(lo, hi); self.threshold_max.setRange(lo, hi)
                    self.threshold_min.setValue(lo + 0.20 * (hi - lo)); self.threshold_max.setValue(lo + 0.80 * (hi - lo))
                self.mode.blockSignals(True); self.mode.setCurrentText("3D orthogonal slices"); self.mode.blockSignals(False)
                self._update_mode_controls(self.mode.currentText())
            elif self.dataset.ndim == 2:
                self.mode.blockSignals(True); self.mode.setCurrentText("2D plane"); self.mode.blockSignals(False)
                self._update_mode_controls(self.mode.currentText())
            self.prev_frame_btn.setEnabled(self.file_list.currentRow() > 0)
            self.next_frame_btn.setEnabled(self.file_list.currentRow() < len(self.files) - 1)
            self.render()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load dataset", str(exc))

    def _select_relative(self, delta: int):
        count = self.file_list.count() if self.file_list is not None else 0
        if count == 0: return
        row = max(0, self.file_list.currentRow())
        new_row = max(0, min(count - 1, row + int(delta)))
        if new_row != row:
            self.file_list.blockSignals(True); self.file_list.setCurrentRow(new_row); self.file_list.blockSignals(False)
            self.apply_selection()

    def move_camera(self, dx: int, dy: int):
        if self.renderer is not None:
            try: self.renderer.move_camera_screen(dx, dy)
            except Exception as exc: QMessageBox.warning(self, "Camera movement failed", str(exc))

    def _camera_state(self):
        if self.renderer is None: return {}
        cam = self.renderer.plotter.camera
        return {"camera_position": list(cam.position), "camera_focal_point": list(cam.focal_point), "camera_up": list(cam.up)}

    def _session_state(self):
        state = {
            "tab": "3d", "files": list(self.files), "pending_files": list(self._pending_files),
            "current_index": self.file_list.currentRow(), "mode": self.mode.currentText(),
            "plane_axis": self.plane_axis.currentText(), "position": self.position.value(), "slice_value": self.slice_value.value(), "z_scale": self.z_scale.value(), "depth": self.depth.value(),
            "opacity": self.opacity.value(), "cmap": self.cmap.currentText(), "reverse_colors": self.reverse_colors.isChecked(),
            "symmetric": self.symmetric.isChecked(), "use_limits": self.use_limits.isChecked(), "vmin": self.vmin.value(), "vmax": self.vmax.value(),
            "colorbar_position": self.colorbar_position.currentText(), "smooth_shading": self.smooth_shading.isChecked(),
            "render_quality": self.render_quality.currentText(), "fast_render": self.fast_render.currentText(),
            "show_bounding_box": self.show_bounding_box.isChecked(), "show_orientation_axes": self.show_orientation_axes.isChecked(),
            "isovalue_mode": self.isovalue_mode.currentText(), "isovalue_count": self.isovalue_count.value(), "isovalue_manual": self.isovalue_manual.text(),
        }
        state.update(self._camera_state()); return state

    def save_session(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save 3D session", "session_3d.xml", "XML session (*.xml)")
        if not path: return
        try: save_xml_session(path, self._session_state()); self.info.setText(f"3D session saved: {path}")
        except Exception as exc: QMessageBox.warning(self, "Could not save session", str(exc))

    def load_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore 3D session", "", "XML session (*.xml)")
        if not path: return
        try:
            state = load_xml_session(path)
            self._pending_files = [str(x) for x in state.get("files", []) if Path(str(x)).exists()]
            if not self._pending_files: raise ValueError("None of the session's data files are currently available.")
            self.file_list.clear(); self.file_list.addItems([Path(f).name for f in self._pending_files])
            row = max(0, min(value_as_int(state.get("current_index"), 0), len(self._pending_files)-1)); self.file_list.setCurrentRow(row)
            self.mode.setCurrentText(str(state.get("mode", self.mode.currentText()))); self.plane_axis.setCurrentText(str(state.get("plane_axis", self.plane_axis.currentText())))
            self.position.setValue(value_as_float(state.get("position"), self.position.value())); self.slice_value.setValue(value_as_float(state.get("slice_value"), self.slice_value.value())); self.z_scale.setValue(value_as_float(state.get("z_scale"), self.z_scale.value())); self.depth.setValue(value_as_float(state.get("depth"), self.depth.value()))
            self.opacity.setValue(value_as_float(state.get("opacity"), self.opacity.value())); self.cmap.setCurrentText(str(state.get("cmap", self.cmap.currentText()))); self.reverse_colors.setChecked(value_as_bool(state.get("reverse_colors")))
            self.symmetric.setChecked(value_as_bool(state.get("symmetric"))); self.use_limits.setChecked(value_as_bool(state.get("use_limits"))); self.vmin.setValue(value_as_float(state.get("vmin"), self.vmin.value())); self.vmax.setValue(value_as_float(state.get("vmax"), self.vmax.value()))
            self.colorbar_position.setCurrentText(str(state.get("colorbar_position", self.colorbar_position.currentText()))); self.smooth_shading.setChecked(value_as_bool(state.get("smooth_shading"))); self.render_quality.setCurrentText(str(state.get("render_quality", self.render_quality.currentText()))); self.fast_render.setCurrentText(str(state.get("fast_render", self.fast_render.currentText())))
            self.show_bounding_box.setChecked(value_as_bool(state.get("show_bounding_box"))); self.show_orientation_axes.setChecked(value_as_bool(state.get("show_orientation_axes")))
            self.isovalue_mode.setCurrentText(str(state.get("isovalue_mode", self.isovalue_mode.currentText()))); self.isovalue_count.setValue(value_as_int(state.get("isovalue_count"), self.isovalue_count.value())); self.isovalue_manual.setText(str(state.get("isovalue_manual", "")))
            self.apply_selection()
            if self.renderer is not None and all(k in state for k in ("camera_position", "camera_focal_point", "camera_up")):
                cam = self.renderer.plotter.camera
                cam.position = tuple(value_as_float(v) for v in state["camera_position"])
                cam.focal_point = tuple(value_as_float(v) for v in state["camera_focal_point"])
                cam.up = tuple(value_as_float(v) for v in state["camera_up"])
                self.renderer.plotter.reset_camera_clipping_range(); self.renderer.plotter.render()
            self.info.setText(f"3D session restored: {path}")
        except Exception as exc: QMessageBox.warning(self, "Could not restore 3D session", str(exc))

    def _configure_2d_axis_options(self):
        if self.dataset is None or self.dataset.ndim != 2:
            return
        present = [a.name.lower() for a in self.dataset.coordinates]
        missing = [a for a in ("x1", "x2", "x3") if a not in present]
        self.plane_axis.blockSignals(True)
        self.plane_axis.clear()
        self.plane_axis.addItems(missing or ["x3"])
        self.plane_axis.blockSignals(False)
        if missing:
            self.position.setRange(-1e12, 1e12)
            self.position.setValue(0.0)

    def _update_mode_controls(self, mode):
        is2d_plane_mode = mode in ("2D plane", "2D surface", "2D extrusion")
        self.plane_axis.setEnabled(is2d_plane_mode or mode == "3D single slice")
        self.position.setEnabled(is2d_plane_mode)
        self.slice_value.setEnabled(mode == "3D single slice")
        self.z_scale.setEnabled(mode == "2D surface")
        self.depth.setEnabled(mode == "2D extrusion")
        self.isosurface_box.setVisible(mode == "3D isosurfaces")
        self.clip_box.setVisible(mode == "3D clip plane")
        self.threshold_box.setVisible(mode == "3D threshold")
        if mode == "3D isosurfaces":
            self._update_isovalue_controls(self.isovalue_mode.currentText())

    def _update_isovalue_controls(self, isovalue_mode_text):
        manual = isovalue_mode_text == "Manual list"
        self.isovalue_manual.setEnabled(manual)
        self.isovalue_count.setEnabled(not manual)
        self.isovalue_suggest_btn.setEnabled(manual)

    def _fill_suggested_isovalues(self):
        if self.dataset is None or self.dataset.ndim != 3:
            QMessageBox.information(self, "No 3D dataset", "Load a 3D dataset first.")
            return
        try:
            values = self.renderer.suggest_isovalues(self.dataset, n=self.isovalue_count.value())
        except Exception as exc:
            QMessageBox.warning(self, "Could not suggest isovalues", str(exc))
            return
        self.isovalue_manual.setText(", ".join(f"{v:.6g}" for v in values))

    def _toggle_bounding_box(self, _state=None):
        if self.renderer is not None:
            self.renderer.set_show_bounding_box(self.show_bounding_box.isChecked())
            self.renderer.plotter.render()

    def _toggle_orientation_axes(self, _state=None):
        if self.renderer is not None:
            self.renderer.set_show_orientation_axes(self.show_orientation_axes.isChecked())
            self.renderer.plotter.render()

    def save_screenshot(self):
        if self.renderer is None:
            QMessageBox.information(self, "3D viewer unavailable", "Install PyVista and PyVistaQt to enable screenshots.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save screenshot", "screenshot.png", "PNG image (*.png)")
        if not path:
            return
        try:
            self.renderer.save_screenshot(path)
            self.info.setText(f"Screenshot saved to {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Could not save screenshot", str(exc))

    def clear_scene(self):
        if self.renderer is not None:
            self.renderer.plotter.clear()
            self.renderer.plotter.render()

    def reset_camera(self):
        if self.renderer is not None:
            self.renderer.plotter.reset_camera()
            self.renderer.plotter.render()

    def isometric_camera(self):
        if self.renderer is not None:
            self.renderer.plotter.view_isometric()
            self.renderer.plotter.render()

    def apply_camera_preset(self):
        """Move the camera to a standard view. Directions follow the same
        convention as Blender's numpad views (verified empirically against
        PyVista's camera_position, not guessed):
          Front/Back look along the Y axis, Left/Right along X, Top/Bottom
          along Z. "Fit to data" re-frames the current camera direction so
          the whole scene is visible, without changing which way it faces.
        """
        if self.renderer is None:
            return
        preset = self.camera_preset.currentText()
        try:
            if preset == "Isometric": self.renderer.plotter.view_isometric()
            elif preset == "Front": self.renderer.plotter.view_xz()
            elif preset == "Back": self.renderer.plotter.view_xz(negative=True)
            elif preset == "Right": self.renderer.plotter.view_yz()
            elif preset == "Left": self.renderer.plotter.view_yz(negative=True)
            elif preset == "Top": self.renderer.plotter.view_xy()
            elif preset == "Bottom": self.renderer.plotter.view_xy(negative=True)
            elif preset == "Fit to data": pass  # just reset_camera_clipping_range()+reset_camera() below
            if preset in ("Fit to data", "Current"):
                self.renderer.plotter.reset_camera()
            self.renderer.plotter.reset_camera_clipping_range(); self.renderer.plotter.render()
        except Exception as exc:
            QMessageBox.warning(self, "Camera preset failed", str(exc))

    def render(self, clear_scene=True):
        if self.dataset is None or self.renderer is None:
            return
        if clear_scene:
            self.renderer.plotter.clear()
        cmap = self.cmap.currentText() + ("_r" if self.reverse_colors.isChecked() and not self.cmap.currentText().endswith("_r") else "")
        vmin = self.vmin.value() if self.use_limits.isChecked() else None
        vmax = self.vmax.value() if self.use_limits.isChecked() else None
        if self.use_limits.isChecked() and vmin >= vmax:
            QMessageBox.warning(self, "Invalid color range", "Color minimum must be smaller than color maximum.")
            return
        cfg = RenderingConfig(
            colormap=cmap, opacity=self.opacity.value(), vmin=vmin, vmax=vmax,
            symmetric_limits=self.symmetric.isChecked(),
            colorbar_position=self.colorbar_position.currentText(),
            colorbar_box=self.colorbar_box.isChecked(),
            colorbar_interactive=self.colorbar_interactive.isChecked(),
            colorbar_width=self.colorbar_width.value(), colorbar_height=self.colorbar_height.value(),
            smooth_shading=self.smooth_shading.isChecked(), show_edges=self.show_edges.isChecked(),
            lighting=self.lighting.isChecked(), eye_dome_lighting=self.eye_dome_lighting.isChecked(),
            depth_peeling=self.depth_peeling.isChecked(), ssao=self.ssao.isChecked(),
            stereo=self.stereo.isChecked(), hidden_line_removal=self.hidden_line_removal.isChecked(),
            antialiasing=self.antialiasing.isChecked(),
            render_decimation={"Full resolution":1.0,"75% resolution":0.75,"50% resolution":0.5,"25% resolution":0.25}[self.fast_render.currentText()],
        )
        try:
            if self.dataset.ndim == 2:
                mode = self.mode.currentText()
                if mode == "2D plane":
                    self.renderer.add_2d_plane(self.dataset, plane_axis=self.plane_axis.currentText(), position=self.position.value(), config=cfg)
                elif mode == "2D surface":
                    self.renderer.add_2d_surface(self.dataset, z_scale=self.z_scale.value(), height_axis=self.plane_axis.currentText(), base_position=self.position.value(), config=cfg)
                elif mode == "2D extrusion":
                    self.renderer.add_2d_extrusion(self.dataset, depth=self.depth.value(), extrusion_axis=self.plane_axis.currentText(), start_position=self.position.value(), config=cfg)
                else:
                    raise ValueError(f"'{mode}' requires a native 3D dataset; this file is 2D. Choose a 2D mode instead.")
            elif self.dataset.ndim == 3:
                mode = self.mode.currentText()
                if mode == "3D volume":
                    self.renderer.add_native_3d(self.dataset, config=cfg)
                elif mode == "3D single slice":
                    self.renderer.add_slice(self.dataset, axis=self.plane_axis.currentText(), value=self.slice_value.value(), config=cfg)
                elif mode == "3D isosurfaces":
                    isovalues = self._resolve_isovalues()
                    self.renderer.add_isosurfaces(self.dataset, isovalues, config=cfg, smooth=self.smooth_shading.isChecked())
                elif mode == "3D threshold":
                    self.renderer.add_threshold(self.dataset, lower=self.threshold_min.value(), upper=self.threshold_max.value(), config=cfg)
                elif mode == "3D clip plane":
                    self.renderer.add_clipped_volume(
                        self.dataset, config=cfg, normal=self.clip_normal.currentText(),
                        interactive=self.clip_interactive.isChecked(),
                    )
                elif mode == "3D box clip":
                    self.renderer.add_box_clip(self.dataset, config=cfg)
                elif mode in ("2D plane", "2D surface", "2D extrusion"):
                    raise ValueError(f"'{mode}' requires a 2D dataset; this file is 3D. Choose a 3D mode instead.")
                else:
                    self.renderer.add_native_3d_slices(self.dataset, config=cfg)
            else:
                raise ValueError("The 3D viewer supports 2D or 3D scalar datasets")
            if clear_scene:
                self.renderer.plotter.reset_camera()
                self.renderer.set_show_bounding_box(self.show_bounding_box.isChecked())
                self.renderer.set_show_orientation_axes(self.show_orientation_axes.isChecked())
            self.renderer.set_render_quality(self.render_quality.currentText())
            self.renderer.plotter.render()
        except Exception as exc:
            QMessageBox.warning(self, "Rendering failed", str(exc))

    def _resolve_isovalues(self) -> list[float]:
        """Isovalues per the current mode ("Auto (percentiles)" or "Manual
        list"), raising a clear error for unparsable manual input rather
        than silently ignoring it."""
        if self.isovalue_mode.currentText() == "Manual list":
            text = self.isovalue_manual.text().strip()
            if not text:
                raise ValueError("Enter one or more comma-separated isovalues, or switch to 'Auto (percentiles)'.")
            try:
                return [float(v) for v in text.split(",") if v.strip()]
            except ValueError:
                raise ValueError(f"Could not parse isovalues from '{text}'; use a comma-separated list of numbers, e.g. 0.1, 0.3, 0.6")
        return self.renderer.suggest_isovalues(self.dataset, n=self.isovalue_count.value())
