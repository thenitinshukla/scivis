import numpy as np
from pathlib import Path
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLabel, QRadioButton, QSpinBox, QVBoxLayout, QLineEdit, QHBoxLayout,
    QPushButton, QDialog, QDialogButtonBox, QFileDialog, QMessageBox, QListWidget,
)

from .. import style
from ..rendering_colors import ALL_PALETTES, make_palette
from ..analysis import reduce_grid_series, smooth_1d, smooth_2d
from ..analysis.roi import RegionOfInterest, roi_statistics, roi_time_series, export_roi_results
from ..io.grid import GridFile
from ..session import save_xml_session, load_xml_session, value_as_bool, value_as_float, value_as_int
from ..io.lazy import LazyGridSeries
from .base_tab import BaseTab

# Sentinel shown in the "Palette preset" dropdown meaning "don't use a
# custom palette -- use the plain Colormap group/Colormap dropdowns (and
# their own Reverse checkbox) instead". This is the default, so the
# ordinary matplotlib colormap picker and its reverse toggle work
# out of the box.
USE_LEGACY_CMAP = "(use Colormap dropdown)"


class ColorRangeDialog(QDialog):
    def __init__(self, vmin, vmax, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Colorbar range")
        form = QFormLayout(self)
        self.vmin = QDoubleSpinBox()
        self.vmax = QDoubleSpinBox()
        for w, value in ((self.vmin, vmin), (self.vmax, vmax)):
            w.setRange(-1e300, 1e300)
            w.setDecimals(10)
            w.setValue(float(value))
        form.addRow("Minimum:", self.vmin)
        form.addRow("Maximum:", self.vmax)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class MovieDialog(QDialog):
    def __init__(self, count, current_row=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create movie")
        form = QFormLayout(self)
        self.start = QSpinBox(); self.start.setRange(0, count - 1); self.start.setValue(0)
        self.end = QSpinBox(); self.end.setRange(0, count - 1); self.end.setValue(count - 1)
        self.step = QSpinBox(); self.step.setRange(1, count); self.step.setValue(1)
        self.fps = QDoubleSpinBox(); self.fps.setRange(0.1, 120.0); self.fps.setDecimals(1); self.fps.setValue(10.0)
        self.format = QComboBox(); self.format.addItems(["MP4 (OpenCV)", "MP4 (FFmpeg/Matplotlib)", "GIF"])
        self.output = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        out_row = QHBoxLayout(); out_row.addWidget(self.output); out_row.addWidget(browse)
        form.addRow("Start frame:", self.start)
        form.addRow("End frame:", self.end)
        form.addRow("Frame step:", self.step)
        form.addRow("Frames per second:", self.fps)
        form.addRow("Format:", self.format)
        form.addRow("Output:", out_row)
        note = QLabel("A fixed color range is recommended for quantitative movies. MP4 requires ffmpeg; GIF does not.")
        note.setWordWrap(True); form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self):
        suffix = ".gif" if self.format.currentText() == "GIF" else ".mp4"
        path, _ = QFileDialog.getSaveFileName(self, "Save movie", "simulation_movie" + suffix, f"Movie (*{suffix})")
        if path: self.output.setText(path)

    def values(self):
        return self.output.text().strip(), self.start.value(), self.end.value(), self.step.value(), self.fps.value(), self.format.currentText()


class TextAnnotationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Add plot text")
        form=QFormLayout(self); self.text=QLineEdit(); self.text.setPlaceholderText("Annotation text")
        form.addRow("Text:", self.text)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)

class AnnotationStyleDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent); self.setWindowTitle(title); form=QFormLayout(self)
        self.value=QLineEdit(); form.addRow("Label:", self.value)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)


class GridTab(BaseTab):
    dataset_changed = pyqtSignal(object)
    series_changed = pyqtSignal(object)
    open_in_3d_requested = pyqtSignal(str)
    """View Simulation field/grid files with robust frame navigation and interactive plotting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = None
        self._cbar = None
        self._cbar_user_position = None  # figure-fraction [x0,y0,w,h] after a manual drag, or None
        self._cbar_drag = None
        self._press_info = None
        self._press_connection = self.canvas.canvas.mpl_connect("button_press_event", self._on_canvas_press)
        self._motion_connection = self.canvas.canvas.mpl_connect("motion_notify_event", self._on_canvas_motion)
        self._release_connection = self.canvas.canvas.mpl_connect("button_release_event", self._on_canvas_release)
        self._last_limits = None
        self._default_limits = None
        self._manual_limits_update = False
        self._annotations = []
        self._rectangle_selector = None
        self._annotation_mode = None
        self._arrow_start = None
        self._series = None
        self._gpu_dialog = None
        self._gpu_widget = None
        self._image = None
        self._line_artist = None
        self._contour_artists = []
        self._last_contour_sig = None
        self._annotation_artists = []
        self._active_plot_mode = None
        self._force_full_view = False
        self._time_series_cache = {}
        self._rois = []            # list[RegionOfInterest], persists across frames (physical coords)
        self._roi_mode = None      # "rectangle" | "ellipse" | None while drawing
        self._roi_draft = None     # {"x0","y0","ax"} during an active drag
        self._roi_preview_patch = None
        self._roi_patches = []
        self._last_roi_results = None  # dict or list[dict], for Export
        self._rois = []            # list[RegionOfInterest], persists across frames (physical coords)
        self._roi_mode = None      # "rectangle" | "ellipse" | None, when actively drawing
        self._roi_draft = None     # {"x0":..., "y0":..., "ax":...} during drag
        self._roi_preview_patch = None
        self._roi_patches = []
        self._last_roi_results = None

        self.file_list = self.add_open_buttons(folder=True, label="field file")
        self.file_list.currentRowChanged.connect(self._pending_selection_changed)
        apply_btn = QPushButton("Apply selection")
        apply_btn.clicked.connect(self.apply_selection)
        self.control_layout.addWidget(apply_btn)
        open3d_btn = QPushButton("Open selected frame in 3D…")
        open3d_btn.clicked.connect(self._open_current_in_3d)
        self.control_layout.addWidget(open3d_btn)

        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous frame")
        self.next_btn = QPushButton("Next frame ▶")
        self.prev_btn.clicked.connect(lambda: self._select_relative(-1))
        self.next_btn.clicked.connect(lambda: self._select_relative(1))
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.next_btn)
        movie_btn = QPushButton("🎞 Create movie…")
        movie_btn.clicked.connect(self.open_movie_dialog)
        nav_row.addWidget(movie_btn)
        gpu_btn = QPushButton("GPU 2D viewer")
        gpu_btn.clicked.connect(self.open_gpu_viewer)
        nav_row.addWidget(gpu_btn)
        self.control_layout.addLayout(nav_row)
        zoom_row = QHBoxLayout()
        zoom_btn = QPushButton("Select region and zoom")
        zoom_btn.clicked.connect(self.enable_region_zoom)
        reset_zoom_btn = QPushButton("Reset view")
        reset_zoom_btn.clicked.connect(self.reset_view)
        zoom_row.addWidget(zoom_btn); zoom_row.addWidget(reset_zoom_btn)
        self.control_layout.addLayout(zoom_row)
        ann_row = QHBoxLayout()
        text_btn = QPushButton("Add text")
        text_btn.clicked.connect(self.start_text_annotation)
        arrow_btn = QPushButton("Add arrow")
        arrow_btn.clicked.connect(self.start_arrow_annotation)
        clear_ann_btn = QPushButton("Clear annotations")
        clear_ann_btn.clicked.connect(self.clear_annotations)
        ann_row.addWidget(text_btn); ann_row.addWidget(arrow_btn); ann_row.addWidget(clear_ann_btn)
        self.control_layout.addLayout(ann_row)

        roi_box = QGroupBox("Measurement (ROI)")
        roi_layout = QVBoxLayout(roi_box)
        roi_shape_row = QHBoxLayout()
        roi_shape_row.addWidget(QLabel("Shape:"))
        self.roi_shape = QComboBox(); self.roi_shape.addItems(["Rectangle", "Ellipse"])
        roi_shape_row.addWidget(self.roi_shape)
        draw_roi_btn = QPushButton("Draw ROI"); draw_roi_btn.clicked.connect(self.start_roi_draw)
        roi_shape_row.addWidget(draw_roi_btn)
        roi_layout.addLayout(roi_shape_row)
        self.roi_list = QListWidget(); self.roi_list.setMaximumHeight(90)
        self.roi_list.currentRowChanged.connect(self._on_roi_selected)
        roi_layout.addWidget(self.roi_list)
        roi_btn_row = QHBoxLayout()
        remove_roi_btn = QPushButton("Remove selected"); remove_roi_btn.clicked.connect(self.remove_selected_roi)
        clear_roi_btn = QPushButton("Clear all"); clear_roi_btn.clicked.connect(self.clear_rois)
        roi_btn_row.addWidget(remove_roi_btn); roi_btn_row.addWidget(clear_roi_btn)
        roi_layout.addLayout(roi_btn_row)
        self.roi_stats_label = QLabel("Click 'Draw ROI' then click-drag on the plot to measure a region.")
        self.roi_stats_label.setWordWrap(True)
        roi_layout.addWidget(self.roi_stats_label)
        roi_action_row = QHBoxLayout()
        export_roi_btn = QPushButton("Export stats (JSON)…"); export_roi_btn.clicked.connect(self.export_roi_stats)
        time_evo_btn = QPushButton("Time evolution across frames…"); time_evo_btn.clicked.connect(self.compute_roi_time_evolution)
        roi_action_row.addWidget(export_roi_btn); roi_action_row.addWidget(time_evo_btn)
        roi_layout.addLayout(roi_action_row)
        self.control_layout.addWidget(roi_box)
        self.frame_label = QLabel("Frame: - / -")
        self.control_layout.addWidget(self.frame_label)

        mode_box = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_box)
        self.mode_2d = QRadioButton("2D map")
        self.mode_line_index = QRadioButton("Lineout (grid index)")
        self.mode_line_coord = QRadioButton("Lineout (physical coordinate)")
        self.mode_time_series = QRadioButton("Time series (reduced over space)")
        self.mode_2d.setChecked(True)
        for rb in (self.mode_2d, self.mode_line_index, self.mode_line_coord, self.mode_time_series):
            rb.toggled.connect(self._update_mode_widgets)
            rb.toggled.connect(self.refresh_plot)
            mode_layout.addWidget(rb)
        self.control_layout.addWidget(mode_box)

        self.slice_box = QGroupBox("3D slice (this file has 3 axes)")
        slice_form = QFormLayout(self.slice_box)
        self.slice_axis = QComboBox(); self.slice_axis.addItems(["x1", "x2", "x3"])
        self.slice_axis.currentIndexChanged.connect(self._update_slice_controls)
        self.slice_axis.currentIndexChanged.connect(self.refresh_plot)
        self.slice_index = QSpinBox(); self.slice_index.setMinimum(0)
        self.slice_index.valueChanged.connect(self._update_slice_coord_label)
        self.slice_index.valueChanged.connect(self.refresh_plot)
        self.slice_coord_label = QLabel("")
        slice_form.addRow("Fix axis:", self.slice_axis)
        slice_form.addRow("At grid index:", self.slice_index)
        slice_form.addRow("Physical position:", self.slice_coord_label)
        slice_hint = QLabel("3D data can't be shown directly as an image, so the axis above is "
                             "held fixed at one grid index and the remaining two axes are plotted.")
        slice_hint.setWordWrap(True)
        slice_form.addRow(slice_hint)
        self.slice_box.setVisible(False)
        self.control_layout.addWidget(self.slice_box)

        line_box = QGroupBox("Lineout")
        line_form = QFormLayout(line_box)
        self.lineout_axis = QComboBox(); self.lineout_axis.addItems(["x1", "x2", "x3"]); self.lineout_axis.currentTextChanged.connect(self._update_lineout_controls); self.lineout_axis.currentTextChanged.connect(self.refresh_plot)
        self.lineout_index = QSpinBox(); self.lineout_index.setMinimum(0); self.lineout_index.valueChanged.connect(self.refresh_plot)
        self.lineout_coord = QDoubleSpinBox(); self.lineout_coord.setRange(-1e9, 1e9); self.lineout_coord.setDecimals(6); self.lineout_coord.valueChanged.connect(self.refresh_plot)
        line_form.addRow("Along axis:", self.lineout_axis)
        line_form.addRow("Fixed index:", self.lineout_index)
        line_form.addRow("Fixed coordinate:", self.lineout_coord)
        self.control_layout.addWidget(line_box)

        ts_box = QGroupBox("Time series (needs a folder open)")
        ts_form = QFormLayout(ts_box)
        self.reduction_combo = QComboBox(); self.reduction_combo.addItems(["mean", "sum", "integral", "max", "min", "rms", "directional average"]); self.reduction_combo.currentTextChanged.connect(self.refresh_plot)
        ts_form.addRow("Reduction:", self.reduction_combo)
        self.average_direction = QComboBox(); self.average_direction.addItems(["x", "y", "z", "(x,y,z)"]); self.average_direction.setToolTip("Supports average,dir=x/y/z/(x,y,z)")
        self.average_direction.currentTextChanged.connect(self.refresh_plot)
        ts_form.addRow("Direction:", self.average_direction)
        export_ts = QPushButton("Export time series (CSV)…"); export_ts.clicked.connect(self.export_time_series)
        ts_form.addRow(export_ts)
        self.control_layout.addWidget(ts_box)

        session_box = QGroupBox("Session")
        session_row = QHBoxLayout(session_box)
        save_session = QPushButton("Save .xml…"); save_session.clicked.connect(self.save_session)
        load_session = QPushButton("Restore .xml…"); load_session.clicked.connect(self.load_session)
        session_row.addWidget(save_session); session_row.addWidget(load_session)
        self.control_layout.addWidget(session_box)

        smooth_box = QGroupBox("Smoothing (1D)")
        smooth_form = QFormLayout(smooth_box)
        self.smooth_method = QComboBox(); self.smooth_method.addItems(["None", "Moving average", "Gaussian"]); self.smooth_method.currentTextChanged.connect(self.refresh_plot)
        self.smooth_window = QSpinBox(); self.smooth_window.setRange(1, 200); self.smooth_window.setValue(5); self.smooth_window.valueChanged.connect(self.refresh_plot)
        smooth_form.addRow("Method:", self.smooth_method); smooth_form.addRow("Window / sigma:", self.smooth_window)
        self.control_layout.addWidget(smooth_box)

        map_box = QGroupBox("2D map rendering")
        map_form = QFormLayout(map_box)
        self.cmap_category = QComboBox(); self.cmap_category.addItems(list(style.COLORMAPS.keys())); self.cmap_category.currentTextChanged.connect(self._populate_cmaps)
        self.cmap_combo = QComboBox(); self.cmap_combo.currentTextChanged.connect(self.refresh_plot)
        self._populate_cmaps()
        map_form.addRow("Colormap group:", self.cmap_category); map_form.addRow("Colormap:", self.cmap_combo)
        self.palette_combo = QComboBox(); self.palette_combo.addItem(USE_LEGACY_CMAP); self.palette_combo.addItems(list(ALL_PALETTES.keys())); self.palette_combo.setCurrentText(USE_LEGACY_CMAP); self.palette_combo.currentTextChanged.connect(self.refresh_plot)
        self.mapping_combo = QComboBox(); self.mapping_combo.addItems(["Scalar", "Cyclic phase"]); self.mapping_combo.currentTextChanged.connect(self.refresh_plot)
        self.palette_reverse = QCheckBox("Reverse palette"); self.palette_reverse.stateChanged.connect(self.refresh_plot)
        self.phase_offset = QDoubleSpinBox(); self.phase_offset.setRange(0.0, 1.0); self.phase_offset.setDecimals(3); self.phase_offset.setSingleStep(0.01); self.phase_offset.valueChanged.connect(self.refresh_plot)
        self.gamma_spin = QDoubleSpinBox(); self.gamma_spin.setRange(0.1, 4.0); self.gamma_spin.setDecimals(2); self.gamma_spin.setValue(1.0); self.gamma_spin.setSingleStep(0.1); self.gamma_spin.valueChanged.connect(self.refresh_plot)
        self.contrast_spin = QDoubleSpinBox(); self.contrast_spin.setRange(0.5, 2.5); self.contrast_spin.setDecimals(2); self.contrast_spin.setValue(1.0); self.contrast_spin.setSingleStep(0.1); self.contrast_spin.valueChanged.connect(self.refresh_plot)
        self.black_floor_spin = QDoubleSpinBox(); self.black_floor_spin.setRange(0.0, 0.5); self.black_floor_spin.setDecimals(3); self.black_floor_spin.setValue(0.0); self.black_floor_spin.setSingleStep(0.01); self.black_floor_spin.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Palette preset:", self.palette_combo); map_form.addRow("Mapping:", self.mapping_combo); map_form.addRow("Reverse palette:", self.palette_reverse)
        map_form.addRow("Phase offset:", self.phase_offset); map_form.addRow("Gamma:", self.gamma_spin); map_form.addRow("Contrast:", self.contrast_spin); map_form.addRow("Black floor:", self.black_floor_spin)
        self.palette_note = QLabel("Palette controls affect the rendered field without changing the underlying data."); self.palette_note.setWordWrap(True); map_form.addRow(self.palette_note)
        self.reverse_cmap = QCheckBox("Reverse legacy matplotlib colormap"); self.reverse_cmap.stateChanged.connect(self.refresh_plot); map_form.addRow(self.reverse_cmap)
        self.cbar_position = QComboBox(); self.cbar_position.addItems(["right", "left", "top", "bottom"])
        self.cbar_position.currentTextChanged.connect(self._on_cbar_position_changed)
        map_form.addRow("Colorbar position:", self.cbar_position)
        self.cbar_box = QCheckBox("Colorbar box/outline"); self.cbar_box.setChecked(True)
        self.cbar_box.stateChanged.connect(self.refresh_plot)
        map_form.addRow(self.cbar_box)
        self.cbar_width = QDoubleSpinBox(); self.cbar_width.setRange(0.02, 1.0); self.cbar_width.setDecimals(3); self.cbar_width.setValue(0.10); self.cbar_width.setSingleStep(0.01); self.cbar_width.valueChanged.connect(self.refresh_plot)
        self.cbar_height = QDoubleSpinBox(); self.cbar_height.setRange(0.02, 1.0); self.cbar_height.setDecimals(3); self.cbar_height.setValue(0.80); self.cbar_height.setSingleStep(0.01); self.cbar_height.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar width:", self.cbar_width); map_form.addRow("Colorbar height:", self.cbar_height)
        self.cbar_label_position = QComboBox(); self.cbar_label_position.addItems(["auto", "left", "right", "top", "bottom"]); self.cbar_label_position.currentTextChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar label side:", self.cbar_label_position)
        self.cbar_label_rotation = QDoubleSpinBox(); self.cbar_label_rotation.setRange(-360, 360); self.cbar_label_rotation.setValue(90); self.cbar_label_rotation.setDecimals(1); self.cbar_label_rotation.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar label rotation:", self.cbar_label_rotation)
        self.cbar_label_pad = QDoubleSpinBox(); self.cbar_label_pad.setRange(0, 60); self.cbar_label_pad.setValue(8); self.cbar_label_pad.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar label spacing:", self.cbar_label_pad)
        cbar_hint = QLabel("Tip: click-drag the colorbar itself to move it anywhere on the figure. "
                            "A plain click (no drag) opens the color-range dialog as before.")
        cbar_hint.setWordWrap(True)
        map_form.addRow(cbar_hint)
        self.symmetric_cbar = QCheckBox("Symmetric color limits"); self.symmetric_cbar.setChecked(True); self.symmetric_cbar.stateChanged.connect(self.refresh_plot); map_form.addRow(self.symmetric_cbar)
        self.clip_percentile = QDoubleSpinBox(); self.clip_percentile.setRange(0, 49); self.clip_percentile.setSuffix(" %"); self.clip_percentile.valueChanged.connect(self.refresh_plot); map_form.addRow("Clip outliers:", self.clip_percentile)
        self.contour_overlay = QCheckBox("Overlay contour lines"); self.contour_overlay.stateChanged.connect(self.refresh_plot); map_form.addRow(self.contour_overlay)
        self.n_contours = QSpinBox(); self.n_contours.setRange(2, 30); self.n_contours.setValue(8); self.n_contours.valueChanged.connect(self.refresh_plot); map_form.addRow("Contour levels:", self.n_contours)
        self.contour_cmap = QComboBox(); self.contour_cmap.addItems(["black", "white", "viridis", "plasma", "turbo", "coolwarm", "RdBu_r"]); self.contour_cmap.currentTextChanged.connect(self.refresh_plot); map_form.addRow("Contour colors:", self.contour_cmap)
        self.contour_limits = QCheckBox("Separate contour color limits"); self.contour_limits.stateChanged.connect(self.refresh_plot); map_form.addRow(self.contour_limits)
        self.contour_vmin = QDoubleSpinBox(); self.contour_vmin.setRange(-1e300, 1e300); self.contour_vmin.setDecimals(10); self.contour_vmin.setValue(-1.0); self.contour_vmin.valueChanged.connect(self.refresh_plot)
        self.contour_vmax = QDoubleSpinBox(); self.contour_vmax.setRange(-1e300, 1e300); self.contour_vmax.setDecimals(10); self.contour_vmax.setValue(1.0); self.contour_vmax.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Contour vmin:", self.contour_vmin); map_form.addRow("Contour vmax:", self.contour_vmax)
        self.interp_combo = QComboBox(); self.interp_combo.addItems(["nearest", "bilinear", "bicubic", "gaussian"]); self.interp_combo.currentTextChanged.connect(self.refresh_plot); map_form.addRow("Shading:", self.interp_combo)
        self.aspect_combo = QComboBox(); self.aspect_combo.addItems(["auto", "equal"]); self.aspect_combo.currentTextChanged.connect(self.refresh_plot); map_form.addRow("Aspect:", self.aspect_combo)
        self.smooth_2d_check = QCheckBox("Apply smoothing to 2D map too"); self.smooth_2d_check.stateChanged.connect(self.refresh_plot); map_form.addRow(self.smooth_2d_check)
        self.control_layout.addWidget(map_box)

        backend_box = QGroupBox("Interactive rendering backend")
        backend_form = QFormLayout(backend_box)
        self.backend_combo = QComboBox(); self.backend_combo.addItems(["Matplotlib (compatible)", "VisPy (GPU, optional)"])
        self.backend_combo.currentTextChanged.connect(self._on_backend_changed)
        backend_form.addRow("Backend:", self.backend_combo)
        backend_note = QLabel("Matplotlib remains the publication-quality default. VisPy is used for GPU-backed interactive 2D fields when installed.")
        backend_note.setWordWrap(True); backend_form.addRow(backend_note)
        self.control_layout.addWidget(backend_box)

        view_box = QGroupBox("View and axes")
        view_form = QFormLayout(view_box)
        self.x_range_check = QCheckBox("Manual x range")
        self.x_range_min = QDoubleSpinBox(); self.x_range_min.setRange(-1e12, 1e12); self.x_range_min.setDecimals(6)
        self.x_range_max = QDoubleSpinBox(); self.x_range_max.setRange(-1e12, 1e12); self.x_range_max.setDecimals(6)
        self.x_range_check.stateChanged.connect(self.refresh_plot); self.x_range_min.valueChanged.connect(self.refresh_plot); self.x_range_max.valueChanged.connect(self.refresh_plot)
        view_form.addRow(self.x_range_check); view_form.addRow("x min:", self.x_range_min); view_form.addRow("x max:", self.x_range_max)
        self.y_range_check = QCheckBox("Manual y range")
        self.y_range_min = QDoubleSpinBox(); self.y_range_min.setRange(-1e12, 1e12); self.y_range_min.setDecimals(6)
        self.y_range_max = QDoubleSpinBox(); self.y_range_max.setRange(-1e12, 1e12); self.y_range_max.setDecimals(6)
        self.y_range_check.stateChanged.connect(self.refresh_plot); self.y_range_min.valueChanged.connect(self.refresh_plot); self.y_range_max.valueChanged.connect(self.refresh_plot)
        view_form.addRow(self.y_range_check); view_form.addRow("y min:", self.y_range_min); view_form.addRow("y max:", self.y_range_max)
        self.title_edit = QLineEdit(); self.title_edit.textChanged.connect(self.refresh_plot); view_form.addRow("Title:", self.title_edit)
        self.tick_format = QComboBox(); self.tick_format.addItems(["Auto", "Scientific", "Plain"]); self.tick_format.currentTextChanged.connect(self.refresh_plot); view_form.addRow("Tick format:", self.tick_format)
        self.fig_width = QDoubleSpinBox(); self.fig_width.setRange(3, 20); self.fig_width.setValue(7); self.fig_width.setSuffix(" in"); self.fig_width.valueChanged.connect(self._resize_figure)
        self.fig_height = QDoubleSpinBox(); self.fig_height.setRange(3, 20); self.fig_height.setValue(5.5); self.fig_height.setSuffix(" in"); self.fig_height.valueChanged.connect(self._resize_figure)
        view_form.addRow("Figure width:", self.fig_width); view_form.addRow("Figure height:", self.fig_height)
        self.control_layout.addWidget(view_box)

        lim_box = QGroupBox("Color normalization")
        lim_form = QFormLayout(lim_box)
        self.norm_combo = QComboBox(); self.norm_combo.addItems(["linear", "log"]); self.norm_combo.currentTextChanged.connect(self.refresh_plot); lim_form.addRow("Normalization:", self.norm_combo)
        self.vmin_check = QCheckBox("Manual minimum"); self.vmin = QDoubleSpinBox(); self.vmin.setRange(-1e300, 1e300); self.vmin.setDecimals(10)
        self.vmax_check = QCheckBox("Manual maximum"); self.vmax = QDoubleSpinBox(); self.vmax.setRange(-1e300, 1e300); self.vmax.setDecimals(10)
        self.vmin_check.stateChanged.connect(self.refresh_plot); self.vmin.valueChanged.connect(self.refresh_plot); self.vmax_check.stateChanged.connect(self.refresh_plot); self.vmax.valueChanged.connect(self.refresh_plot)
        lim_form.addRow(self.vmin_check); lim_form.addRow("vmin:", self.vmin); lim_form.addRow(self.vmax_check); lim_form.addRow("vmax:", self.vmax)
        self.control_layout.addWidget(lim_box)

        color_box = QGroupBox("Line color")
        color_form = QFormLayout(color_box)
        self.color_preview = QLabel(); self.color_preview.setFixedSize(24, 16); self._update_color_preview()
        color_btn = self.add_color_picker_button(self._on_color_picked, "Pick line color…")
        color_form.addRow(self.color_preview, color_btn)
        self.control_layout.addWidget(color_box)

        self.info_label = QLabel("No file loaded"); self.info_label.setWordWrap(True); self.control_layout.addWidget(self.info_label)
        self._update_mode_widgets()
        self.finish_layout()


    def _on_backend_changed(self, name):
        if "VisPy" in name and self.grid is not None:
            self.open_gpu_viewer()

    def open_gpu_viewer(self):
        if self.grid is None:
            QMessageBox.information(self, "GPU viewer", "Open a 2D field first.")
            return
        if self.grid.ndim != 2:
            QMessageBox.information(self, "GPU viewer", "GPU interactive rendering currently supports 2D scalar fields.")
            return
        try:
            from .gpu_viewer import GPUViewerDialog
            if self._gpu_dialog is None:
                self._gpu_dialog = GPUViewerDialog(self)
                self._gpu_dialog.finished.connect(lambda _=0: setattr(self, "_gpu_dialog", None))
            self._ensure_grid_loaded()
            self._gpu_dialog.set_field(self.grid.data, self.grid.extent(), self._cmap_name())
            self._gpu_dialog.show(); self._gpu_dialog.raise_(); self._gpu_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.warning(self, "GPU viewer unavailable", str(exc))

    def open_movie_dialog(self):
        if len(self.files) < 2:
            QMessageBox.information(self, "Movie export", "Open a folder containing at least two time-step files first.")
            return
        if not self.mode_2d.isChecked() or self.grid is None or self.grid.ndim != 2:
            QMessageBox.information(self, "Movie export", "Switch to 2D map mode with a 2D scalar dataset before creating a movie.")
            return
        dlg = MovieDialog(len(self.files), self.file_list.currentRow(), self)
        if dlg.exec_() != QDialog.Accepted:
            return
        output, start, end, step, fps, fmt = dlg.values()
        if not output:
            suffix = ".mp4" if fmt == "MP4" else ".gif"
            output, _ = QFileDialog.getSaveFileName(self, "Save movie", "simulation_movie" + suffix, f"{fmt} (*{suffix})")
            if not output:
                return
        # Capture every widget value up front -- the export itself runs on a
        # worker thread (encoding dozens/hundreds of frames can take a while
        # and used to freeze the whole window), so nothing below this point
        # may touch a Qt widget from the job() closure.
        cmap = self._cmap_name()
        vmin = self.vmin.value() if self.vmin_check.isChecked() else None
        vmax = self.vmax.value() if self.vmax_check.isChecked() else None
        symmetric = self.symmetric_cbar.isChecked()
        clip_percentile = self.clip_percentile.value()
        title_prefix = self.title_edit.text()
        files = list(self.files)
        use_opencv = fmt.startswith("MP4 (OpenCV)")
        normalization = self.norm_combo.currentText()
        aspect = self.aspect_combo.currentText()
        interpolation = self.interp_combo.currentText()
        figsize = (self.fig_width.value(), self.fig_height.value())

        def job():
            if use_opencv:
                from ..export.opencv_movie import export_grid_movie_opencv
                return export_grid_movie_opencv(
                    files, output, frame_start=start, frame_end=end, frame_step=step, fps=fps,
                    cmap=cmap, vmin=vmin, vmax=vmax, symmetric=symmetric,
                    clip_percentile=clip_percentile, title_prefix=title_prefix,
                    loader=GridFile.load,
                )
            from ..export.animation import export_grid_movie
            return export_grid_movie(
                files, output, frame_start=start, frame_end=end, frame_step=step, fps=fps,
                cmap=cmap, normalization=normalization, vmin=vmin, vmax=vmax,
                symmetric=symmetric, clip_percentile=clip_percentile,
                aspect=aspect, interpolation=interpolation,
                title_prefix=title_prefix, figsize=figsize,
                dpi=150,
            )

        from .workers import run_in_background
        run_in_background(
            self, job,
            on_success=lambda n: QMessageBox.information(self, "Movie export complete", f"Rendered {n} frames to:\n{output}"),
            on_error=lambda exc: QMessageBox.critical(self, "Movie export failed", str(exc)),
            label="Exporting movie… this keeps the window responsive.",
        )

    def _populate_cmaps(self):
        current = self.cmap_combo.currentText()
        self.cmap_combo.blockSignals(True); self.cmap_combo.clear()
        self.cmap_combo.addItems(style.COLORMAPS.get(self.cmap_category.currentText(), ["viridis"]))
        if current in [self.cmap_combo.itemText(i) for i in range(self.cmap_combo.count())]: self.cmap_combo.setCurrentText(current)
        self.cmap_combo.blockSignals(False)
        self.refresh_plot()

    def _on_color_picked(self, color): self._update_color_preview(); self.refresh_plot()
    def _update_color_preview(self): self.color_preview.setStyleSheet(f"background:{self.accent_hex()}; border:1px solid #777;")

    def _update_lineout_controls(self):
        """Keep lineout index/coordinate controls tied to the selected physical axis."""
        if self.grid is None or self.grid.ndim < 2:
            return
        along_axis = min(self.lineout_axis.currentIndex(), self.grid.ndim - 1)
        # For an index lineout, the controlled index belongs to the first
        # non-lineout physical axis. For a 2D field this is simply the other axis.
        fixed_axis = 1 - along_axis if self.grid.ndim == 2 else next((i for i in range(self.grid.ndim) if i != along_axis), 0)
        fixed_np_axis = self.grid.ndim - 1 - fixed_axis
        self.lineout_index.blockSignals(True)
        self.lineout_index.setMaximum(max(0, int(self.grid.shape[fixed_np_axis] - 1)))
        self.lineout_index.setValue(min(self.lineout_index.value(), self.lineout_index.maximum()))
        self.lineout_index.blockSignals(False)
        coords = self.grid.axes[fixed_axis].values()
        if coords.size:
            self.lineout_coord.blockSignals(True)
            self.lineout_coord.setRange(float(coords.min()), float(coords.max()))
            if not (coords.min() <= self.lineout_coord.value() <= coords.max()):
                self.lineout_coord.setValue(float(0.5 * (coords.min() + coords.max())))
            self.lineout_coord.blockSignals(False)

    def _update_slice_controls(self):
        """Show/hide and range-limit the 3D-slice controls based on the
        currently loaded file's dimensionality, and pick a sensible default
        slice axis (the axis with the fewest grid points, since that's
        almost always the one a user wants to hold fixed -- e.g. a "thin"
        3D Simulation run with only 2 points along one axis)."""
        if self.grid is None:
            self.slice_box.setVisible(False)
            return
        is_3d = self.grid.ndim == 3
        self.slice_box.setVisible(is_3d)
        if not is_3d:
            return
        if self.slice_axis.property("_auto_selected_for") != id(self.grid):
            smallest_axis = min(range(3), key=lambda i: self.grid.axes[i].n)
            self.slice_axis.blockSignals(True)
            self.slice_axis.setCurrentIndex(smallest_axis)
            self.slice_axis.blockSignals(False)
            self.slice_axis.setProperty("_auto_selected_for", id(self.grid))
        axis = self.grid.axes[self.slice_axis.currentIndex()]
        self.slice_index.blockSignals(True)
        self.slice_index.setMaximum(max(0, axis.n - 1))
        self.slice_index.setValue(min(self.slice_index.value(), self.slice_index.maximum()))
        self.slice_index.blockSignals(False)
        self._update_slice_coord_label()
        # The manual X/Y-range controls must track whichever two axes are
        # actually displayed after slicing, not the original three.
        remaining = [self.grid.axes[i] for i in range(3) if i != self.slice_axis.currentIndex()]
        self.x_range_min.setValue(float(remaining[0].min)); self.x_range_max.setValue(float(remaining[0].max))
        self.y_range_min.setValue(float(remaining[1].min)); self.y_range_max.setValue(float(remaining[1].max))

    def _update_slice_coord_label(self):
        if self.grid is None or self.grid.ndim != 3:
            return
        axis = self.grid.axes[self.slice_axis.currentIndex()]
        idx = min(self.slice_index.value(), axis.n - 1)
        value = float(axis.values()[idx]) if axis.n else 0.0
        self.slice_coord_label.setText(f"{axis.name} = {value:.6g} {axis.units} (index {idx} of {axis.n})")

    def _effective_2d_grid(self):
        """The GridFile that 2D-mode plotting/analysis should actually use:
        the loaded file itself if it's already 2D, or a 2D slice through it
        if it's 3D (see GridFile.slice2d). Centralizing this here means
        `_plot_2d` and friends never need to special-case 3D data."""
        if self.grid is None:
            return None
        if self.grid.ndim == 2:
            return self.grid
        if self.grid.ndim == 3:
            axis = self.slice_axis.currentIndex()
            index = min(self.slice_index.value(), self.grid.axes[axis].n - 1)
            return self.grid.slice2d(axis=axis, index=index)
        raise ValueError(f"2D view requires a 2D or 3D dataset; this file is {self.grid.ndim}D")

    def _update_mode_widgets(self):
        is_2d = self.mode_2d.isChecked(); is_line_index = self.mode_line_index.isChecked(); is_line_coord = self.mode_line_coord.isChecked(); is_ts = self.mode_time_series.isChecked()
        self.lineout_index.setEnabled(is_line_index); self.lineout_coord.setEnabled(is_line_coord); self.lineout_axis.setEnabled(is_line_index or is_line_coord); self.reduction_combo.setEnabled(is_ts); self.average_direction.setEnabled(is_ts and self.reduction_combo.currentText() == "directional average")
        for w in (self.cmap_category, self.cmap_combo, self.palette_combo, self.mapping_combo, self.palette_reverse, self.phase_offset, self.gamma_spin, self.contrast_spin, self.black_floor_spin, self.reverse_cmap, self.symmetric_cbar, self.clip_percentile, self.contour_overlay, self.n_contours, self.cbar_label_position, self.cbar_label_rotation, self.cbar_label_pad, self.contour_cmap, self.contour_limits, self.contour_vmin, self.contour_vmax, self.interp_combo, self.aspect_combo, self.smooth_2d_check, self.norm_combo, self.vmin_check, self.vmin, self.vmax_check, self.vmax): w.setEnabled(is_2d)

    def _open_current_in_3d(self):
        row = self.file_list.currentRow()
        if 0 <= row < len(self.files):
            self.open_in_3d_requested.emit(self.files[row])

    def _pending_selection_changed(self, row):
        if row >= 0 and row < len(self.files):
            self.info_label.setText(f"Selected: {Path(self.files[row]).name}. Click Apply selection to load the frame.")

    def apply_selection(self):
        row = self.file_list.currentRow()
        if 0 <= row < len(self.files):
            self.on_file_selected(row)

    def _select_relative(self, delta):
        count = self.file_list.count()
        if count == 0: return
        row = self.file_list.currentRow()
        if row < 0: row = 0
        new_row = max(0, min(count - 1, row + delta))
        if new_row != row:
            self.file_list.blockSignals(True)
            self.file_list.setCurrentRow(new_row)
            self.file_list.blockSignals(False)
            self.apply_selection()

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.files): return
        try:
            if self._series is None or list(self._series.paths) != list(self.files):
                self._series = LazyGridSeries(self.files)
            cached = self._series._cache.get(row)
            if cached is not None:
                # Already have the full GridFile (data included) from a
                # recent visit -- reuse it directly instead of paying for
                # another HDF5 open just to re-read metadata we already
                # have. This is what makes scrubbing back and forth
                # between recently-visited frames actually fast, not just
                # the later `_ensure_grid_loaded()` data-cache lookup.
                self.grid = cached
            else:
                self.grid = GridFile.info(self.files[row])
        except Exception as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>Error reading file:<br>{exc}</span>"); return
        self._update_lineout_controls()
        self._update_slice_controls()
        if self.grid.ndim != 3:
            # For a 3D file, _update_slice_controls() above already set
            # x_range/y_range to whichever two axes remain after slicing.
            if self.grid.axes:
                ax0 = self.grid.axes[0]; self.x_range_min.setValue(float(ax0.min)); self.x_range_max.setValue(float(ax0.max))
            if len(self.grid.axes) > 1:
                ax1 = self.grid.axes[1]; self.y_range_min.setValue(float(ax1.min)); self.y_range_max.setValue(float(ax1.max))
        # Color limits are intentionally computed lazily on first 2D render.
        self.frame_label.setText(f"Frame: {row + 1} / {len(self.files)}")
        self.prev_btn.setEnabled(row > 0); self.next_btn.setEnabled(row < len(self.files) - 1)
        self.info_label.setText(f"<b>{self.grid.name}</b> ({self.grid.label})<br>units: {self.grid.units}<br>shape: {self.grid.shape}<br>time: {self.grid.time:g} {self.grid.time_units}  iter: {self.grid.iteration}<br>{len(self.files)} file(s) in current folder")
        self._last_limits = None
        self._default_limits = None
        self._force_full_view = True
        # NOTE: deliberately NOT resetting self._active_plot_mode here.
        # refresh_plot() already recomputes `mode` from the current radio
        # button + the new grid's ndim, so a genuine mode change (e.g. a
        # newly selected file collapses from 2D to 1D, or the user
        # switches radio buttons) is still detected and still forces the
        # full ax.cla() + colorbar-rebuild path where it's actually
        # needed. Forcing that reset unconditionally on every frame change
        # -- the single most common interactive action -- meant every
        # "next frame" click paid for a full axes teardown, a brand new
        # colorbar, and a full theme re-application, even for the totally
        # ordinary case of scrubbing through frames of the same quantity
        # with unchanged shape/axes. _plot_2d()'s `needs_new_image` check
        # already handles the case where shape *does* change between
        # files by rebuilding the image (and colorbar) then; there is
        # nothing left for this reset to protect against.
        self._time_series_cache.clear()
        self._deactivate_mouse_tools()
        # Public signal contract: always emit the shared Dataset abstraction.
        # Keep metadata-only GridFile internal to this tab so consumers never
        # accidentally call Dataset-only APIs on a legacy wrapper.
        try:
            self.dataset_changed.emit(self.grid.to_dataset())
        except Exception:
            # A metadata-only frame is valid during folder browsing; loading is
            # deferred until the plot/analysis operation requests the field.
            self.dataset_changed.emit(self.grid)
        self.series_changed.emit(list(self.files))
        self.refresh_plot()

    def _deactivate_mouse_tools(self):
        self._annotation_mode = None
        self._arrow_start = None
        self._roi_mode = None
        self._roi_draft = None
        if self._roi_preview_patch is not None:
            try: self._roi_preview_patch.remove()
            except Exception: pass
            self._roi_preview_patch = None
        try:
            self.canvas.deactivate_navigation()
        except Exception:
            pass
        try:
            if self._rectangle_selector is not None:
                self._rectangle_selector.set_active(False)
                self._rectangle_selector.disconnect_events()
        except Exception:
            pass
        self._rectangle_selector = None
        try:
            self.canvas.deactivate_navigation()
        except Exception:
            pass

    def _ensure_grid_loaded(self):
        if self.grid is None:
            return None
        if getattr(self.grid, "data", None) is None:
            row = max(0, self.file_list.currentRow())
            # Route through the bounded LazyGridSeries cache rather than
            # re-reading the HDF5 file from disk every time: scrubbing
            # back and forth between recently-visited frames (the most
            # common interactive pattern) then hits the cache instead of
            # paying a full read again.
            if self._series is not None and list(self._series.paths) == list(self.files):
                self.grid = self._series.load(row)
            else:
                self.grid = GridFile.load(self.files[row])
            self._update_lineout_controls()
            self._update_slice_controls()
        return self.grid

    def refresh_plot(self):
        if self.grid is None:
            return
        self._ensure_grid_loaded()
        mode = (
            "time_series" if self.mode_time_series.isChecked() else
            "2d" if self.mode_2d.isChecked() and self.grid.ndim >= 2 else
            "line_coord" if self.mode_line_coord.isChecked() and self.grid.ndim >= 2 else
            "line_index"
        )
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else self.canvas.figure.add_subplot(111)
        mode_changed = self._active_plot_mode != mode
        if mode_changed:
            self._clear_plot_artists(ax)
            self._active_plot_mode = mode
            self.canvas.mark_theme_dirty()  # ax.cla() reset styling to matplotlib defaults
        elif self._last_limits is not None and not self.x_range_check.isChecked() and not self.y_range_check.isChecked() and not self._force_full_view:
            self._last_limits = (ax.get_xlim(), ax.get_ylim())

        try:
            if mode == "time_series":
                self._plot_time_series(ax)
            elif mode == "2d":
                self._plot_2d(ax)
            elif mode == "line_coord":
                self._plot_lineout_coord(ax)
            else:
                self._plot_lineout_index(ax)
        except Exception as exc:
            ax.cla()
            self._clear_colorbar()
            self._image = None
            self._line_artist = None
            ax.text(0.5, 0.5, f"Unable to compute this view:\n{exc}", ha="center", va="center", transform=ax.transAxes)
            self.info_label.setText(f"Analysis error: {exc}")

        if self._last_limits and not self.x_range_check.isChecked() and not self.y_range_check.isChecked() and not self._force_full_view:
            try:
                ax.set_xlim(*self._last_limits[0]); ax.set_ylim(*self._last_limits[1])
            except Exception:
                pass
        elif self._force_full_view:
            try:
                if mode == "2d" and self.grid.ndim >= 2:
                    ext = self.grid.extent()
                    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
                else:
                    ax.relim(); ax.autoscale_view()
            except Exception:
                pass
            self._force_full_view = False
        self._draw_annotations(ax)
        self._draw_rois(ax)
        self.canvas.draw_idle()
        self._last_limits = (ax.get_xlim(), ax.get_ylim())

    def _clear_colorbar(self):
        if self._cbar is not None:
            try:
                self._cbar.remove()
            except Exception:
                try: self._cbar.ax.remove()
                except Exception: pass
        self._cbar = None

    def _clear_plot_artists(self, ax):
        self._clear_colorbar()
        for artist in list(getattr(ax, "images", [])):
            try: artist.remove()
            except Exception: pass
        if self._line_artist is not None:
            try: self._line_artist.remove()
            except Exception: pass
        self._line_artist = None
        for c in self._contour_artists:
            try: c.remove()
            except Exception: pass
        self._contour_artists = []
        self._last_contour_sig = None
        for artist in self._annotation_artists:
            try: artist.remove()
            except Exception: pass
        self._annotation_artists = []
        ax.cla()
        self._image = None

    def _resize_figure(self): self.canvas.figure.set_size_inches(self.fig_width.value(), self.fig_height.value(), forward=True); self.refresh_plot()
    def _cmap_name(self):
        name = self.cmap_combo.currentText() or "viridis"
        return name + "_r" if self.reverse_cmap.isChecked() and not name.endswith("_r") else name

    def _plot_2d(self, ax):
        from matplotlib.colors import LogNorm, Normalize
        grid2d = self._effective_2d_grid()
        data = grid2d.data
        if self.smooth_2d_check.isChecked():
            data = smooth_2d(data, self.smooth_method.currentText(), self.smooth_window.value())
        extent = grid2d.extent()
        palette_choice = self.palette_combo.currentText()
        if not palette_choice or palette_choice == USE_LEGACY_CMAP:
            # Plain matplotlib colormap picker (Colormap group/Colormap +
            # its own Reverse checkbox). This is the default path.
            cmap_name = self._cmap_name()
        else:
            # A custom palette preset was explicitly chosen; it has its own
            # independent reverse checkbox ("Reverse palette").
            cmap_name = make_palette(palette_choice, reverse=self.palette_reverse.isChecked(), phase=self.phase_offset.value())
        finite = data[np.isfinite(data)] if self.clip_percentile.value() > 0 else None
        if finite is not None and finite.size == 0:
            raise ValueError("No finite values in selected field")
        if finite is None:
            try:
                vmin, vmax = float(np.nanmin(data)), float(np.nanmax(data))
            except ValueError:
                raise ValueError("No finite values in selected field")
        else:
            vmin, vmax = float(finite.min()), float(finite.max())
        # Visual-only contrast controls. These alter the normalization, not the Dataset.
        pct = self.clip_percentile.value()
        if pct > 0:
            vmin, vmax = np.percentile(finite, [pct, 100 - pct])
        if self.vmin_check.isChecked(): vmin = self.vmin.value()
        if self.vmax_check.isChecked(): vmax = self.vmax.value()
        if self.symmetric_cbar.isChecked() and not (self.vmin_check.isChecked() or self.vmax_check.isChecked()):
            m = max(abs(vmin), abs(vmax)); vmin, vmax = -m, m
        if vmin == vmax:
            delta = max(abs(vmin) * 1e-12, 1e-12)
            vmin -= delta; vmax += delta
        if self.norm_combo.currentText() == "log":
            if vmin <= 0 or vmax <= 0:
                raise ValueError("Log normalization requires positive color limits")
            norm = LogNorm(vmin=vmin, vmax=vmax)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)

        # Apply palette-shaping through a lightweight custom normalization wrapper.
        base_norm = norm
        gamma = float(self.gamma_spin.value())
        contrast = float(self.contrast_spin.value())
        floor = float(self.black_floor_spin.value())
        if self.norm_combo.currentText() == "linear" and (abs(gamma-1.0) > 1e-12 or abs(contrast-1.0) > 1e-12 or floor > 0):
            from matplotlib.colors import Normalize as _Normalize
            class _StyledNorm(_Normalize):
                def __call__(self, value, clip=None):
                    a = super().__call__(value, clip=clip)
                    a = np.asarray(a, dtype=float)
                    a = np.clip(a, 0.0, 1.0)
                    if floor > 0:
                        a = np.where(a < floor, 0.0, (a - floor) / max(1.0-floor, 1e-12))
                    a = np.clip((a - 0.5) * contrast + 0.5, 0.0, 1.0)
                    if gamma != 1.0:
                        a = np.power(a, gamma)
                    return a
                def inverse(self, value):
                    a = np.asarray(value, dtype=float)
                    if gamma != 1.0: a = np.power(np.clip(a,0,1), 1.0/gamma)
                    a = np.clip((a-0.5)/max(contrast,1e-12)+0.5,0,1)
                    if floor > 0: a = a*(1.0-floor)+floor
                    return self.vmin + a*(self.vmax-self.vmin)
            norm = _StyledNorm(vmin=vmin, vmax=vmax)

        needs_new_image = self._image is None or tuple(getattr(self._image.get_array(), "shape", ())) != tuple(data.shape)
        if needs_new_image:
            self._clear_colorbar()
            self._image = ax.imshow(data, origin="lower", extent=extent, aspect=self.aspect_combo.currentText(), cmap=cmap_name, norm=norm, interpolation=self.interp_combo.currentText())
        else:
            self._image.set_data(data)
            self._image.set_extent(extent)
            self._image.set_cmap(cmap_name)
            self._image.set_norm(norm)
            self._image.set_interpolation(self.interp_combo.currentText())
            ax.set_aspect(self.aspect_combo.currentText())

        contour_sig = (
            id(self.grid), self.grid.ndim,
            self.slice_axis.currentIndex() if self.grid.ndim == 3 else None,
            self.slice_index.value() if self.grid.ndim == 3 else None,
            self.smooth_2d_check.isChecked(), self.smooth_method.currentText(), self.smooth_window.value(),
            self.contour_overlay.isChecked(), self.n_contours.value(),
            self.contour_limits.isChecked(), round(self.contour_vmin.value(), 10), round(self.contour_vmax.value(), 10),
            self.contour_cmap.currentText(), round(vmin, 10), round(vmax, 10),
        )
        if self.contour_overlay.isChecked() and self._contour_artists and contour_sig == getattr(self, "_last_contour_sig", None):
            # Nothing that affects contour geometry or levels changed since
            # the last render (gamma/contrast/black_floor/colormap/aspect/
            # interpolation are pure display remaps and don't reach this
            # signature) -- reuse the existing ContourSet instead of paying
            # for another marching-squares pass, which dominates redraw
            # time on large fields (~100ms+ on a 1024x1024 image).
            pass
        else:
            for c in self._contour_artists:
                try: c.remove()
                except Exception: pass
            self._contour_artists = []
            if self.contour_overlay.isChecked():
                x = np.asarray(grid2d.axes[0].values(), dtype=float)
                y = np.asarray(grid2d.axes[1].values(), dtype=float)
                if x.size != data.shape[0] or y.size != data.shape[1]:
                    x = np.linspace(extent[0], extent[1], data.shape[0])
                    y = np.linspace(extent[2], extent[3], data.shape[1])
                X, Y = np.meshgrid(x, y, indexing="ij")
                levels = self.n_contours.value()
                if self.contour_limits.isChecked() and self.contour_vmin.value() < self.contour_vmax.value():
                    levels = np.linspace(self.contour_vmin.value(), self.contour_vmax.value(), self.n_contours.value())
                else:
                    levels = np.linspace(vmin, vmax, self.n_contours.value())
                cchoice = self.contour_cmap.currentText()
                if cchoice in {"black", "white"}:
                    contour = ax.contour(X, Y, data, levels=levels, colors=cchoice, linewidths=0.55, alpha=0.75)
                else:
                    contour = ax.contour(X, Y, data, levels=levels, cmap=cchoice, linewidths=0.55, alpha=0.85)
                # Modern Matplotlib exposes a ContourSet as one removable artist;
                # older versions exposed child collections. Store the ContourSet
                # itself so contour overlays work across both APIs.
                self._contour_artists = [contour]
            self._last_contour_sig = contour_sig if self.contour_overlay.isChecked() else None
        ax.set_aspect(self.aspect_combo.currentText())
        if self._cbar is None:
            self._cbar = self.canvas.figure.colorbar(self._image, ax=ax, location=self.cbar_position.currentText())
            self.canvas.mark_theme_dirty()  # a fresh colorbar axes needs its own theme styling
            # Apply user-controlled size in normalized figure coordinates.
            bbox = self._cbar.ax.get_position().bounds
            pos = self.cbar_position.currentText()
            w = float(self.cbar_width.value())
            h = float(self.cbar_height.value())
            if pos in ("left", "right"):
                self._cbar.ax.set_position([bbox[0], bbox[1] + (bbox[3]-h)/2, w, h])
            else:
                self._cbar.ax.set_position([bbox[0] + (bbox[2]-w)/2, bbox[1], w, h])
        else:
            self._cbar.update_normal(self._image)
            # Keep width/height responsive when the user changes them after
            # the colorbar has already been created. A manually dragged bar
            # retains its center while being resized.
            try:
                bx, by, bw, bh = self._cbar.ax.get_position().bounds
                w = float(self.cbar_width.value())
                h = float(self.cbar_height.value())
                nx = bx + (bw - w) / 2.0
                ny = by + (bh - h) / 2.0
                self._cbar.ax.set_position([nx, ny, w, h])
                if self._cbar_user_position is not None:
                    self._cbar_user_position = [nx, ny, w, h]
            except Exception:
                pass
        if self._cbar_user_position is not None:
            try:
                self._cbar.ax.set_position(self._cbar_user_position)
            except Exception:
                self._cbar_user_position = None
        self._cbar.outline.set_visible(self.cbar_box.isChecked())
        label = f"{grid2d.label} [{grid2d.units}]" if grid2d.units else grid2d.label
        self._cbar.set_label(label, rotation=self.cbar_label_rotation.value(), labelpad=self.cbar_label_pad.value())
        side = self.cbar_label_position.currentText()
        if side != "auto":
            try:
                if self.cbar_position.currentText() in ("left", "right"):
                    self._cbar.ax.yaxis.set_label_position(side)
                else:
                    self._cbar.ax.xaxis.set_label_position(side)
            except Exception:
                pass
        ax.set_xlabel(self._axis_label(0, grid2d)); ax.set_ylabel(self._axis_label(1, grid2d))
        ax.set_title(self.title_edit.text() or f"t = {grid2d.time:g} {grid2d.time_units}  (iter {grid2d.iteration})")
        if self.x_range_check.isChecked() and self.x_range_min.value() < self.x_range_max.value(): ax.set_xlim(self.x_range_min.value(), self.x_range_max.value())
        if self.y_range_check.isChecked() and self.y_range_min.value() < self.y_range_max.value(): ax.set_ylim(self.y_range_min.value(), self.y_range_max.value())
        if self.tick_format.currentText() != "Auto":
            from matplotlib.ticker import ScalarFormatter
            for axis in (ax.xaxis, ax.yaxis):
                fmt = ScalarFormatter(useMathText=True); fmt.set_scientific(self.tick_format.currentText() == "Scientific"); axis.set_major_formatter(fmt)

    def _on_cbar_position_changed(self):
        """Colorbar location (left/right/top/bottom) can only be set when the
        colorbar axes is created, so force a clean recreation. Any manual
        drag offset is reset since it applied to the old location/orientation."""
        self._cbar_user_position = None
        self._clear_colorbar()
        self.refresh_plot()

    def _on_canvas_press(self, event):
        self._press_info = None
        self._cbar_drag = None
        if self.grid is None or event.inaxes is None or event.x is None or event.y is None:
            return
        self._press_info = {"moved": False}
        if self._cbar is not None and event.inaxes == self._cbar.ax:
            self._cbar_drag = {"press_x": event.x, "press_y": event.y, "orig": self._cbar.ax.get_position().bounds}
            return
        if self._roi_mode is not None and event.xdata is not None and event.ydata is not None:
            self._roi_draft = {"x0": event.xdata, "y0": event.ydata, "ax": event.inaxes}

    def _on_canvas_motion(self, event):
        if self._cbar_drag is not None and self._cbar is not None and event.x is not None and event.y is not None:
            dpx = event.x - self._cbar_drag["press_x"]
            dpy = event.y - self._cbar_drag["press_y"]
            if self._press_info is not None and (dpx * dpx + dpy * dpy) ** 0.5 > 3:
                self._press_info["moved"] = True
            fig = self.canvas.figure
            width_px, height_px = fig.get_size_inches() * fig.dpi
            if width_px <= 0 or height_px <= 0:
                return
            x0, y0, w, h = self._cbar_drag["orig"]
            new_x0 = min(max(x0 + dpx / width_px, 0.0), max(0.0, 1.0 - w))
            new_y0 = min(max(y0 + dpy / height_px, 0.0), max(0.0, 1.0 - h))
            self._cbar.ax.set_position([new_x0, new_y0, w, h])
            self._cbar_user_position = [new_x0, new_y0, w, h]
            self.canvas.draw_idle()
            return
        if self._roi_draft is not None and event.xdata is not None and event.ydata is not None:
            self._update_roi_preview(event.xdata, event.ydata)

    def _on_canvas_release(self, event):
        drag, press = self._cbar_drag, self._press_info
        self._cbar_drag, self._press_info = None, None
        if drag is not None and press is not None and press.get("moved"):
            return  # dragged the colorbar -- don't also treat this as a click
        if self._roi_draft is not None:
            self._finalize_roi(event)
            return
        self._on_figure_click(event)

    def _update_roi_preview(self, x1, y1):
        """Live-updates a dashed preview patch while dragging out a ROI,
        without triggering a full refresh_plot() (which would recompute
        and redraw the whole image on every mouse-move event)."""
        from matplotlib.patches import Rectangle, Ellipse
        x0, y0, ax = self._roi_draft["x0"], self._roi_draft["y0"], self._roi_draft["ax"]
        if self._roi_preview_patch is not None:
            try: self._roi_preview_patch.remove()
            except Exception: pass
            self._roi_preview_patch = None
        xlo, xhi = min(x0, x1), max(x0, x1)
        ylo, yhi = min(y0, y1), max(y0, y1)
        if xhi <= xlo or yhi <= ylo:
            self.canvas.draw_idle()
            return
        if self._roi_mode == "rectangle":
            patch = Rectangle((xlo, ylo), xhi - xlo, yhi - ylo, fill=False, edgecolor="yellow", linewidth=1.5, linestyle="--")
        else:
            patch = Ellipse(((xlo + xhi) / 2, (ylo + yhi) / 2), xhi - xlo, yhi - ylo, fill=False, edgecolor="yellow", linewidth=1.5, linestyle="--")
        ax.add_patch(patch)
        self._roi_preview_patch = patch
        self.canvas.draw_idle()

    def _finalize_roi(self, event):
        x0, y0 = self._roi_draft["x0"], self._roi_draft["y0"]
        self._roi_draft = None
        if self._roi_preview_patch is not None:
            try: self._roi_preview_patch.remove()
            except Exception: pass
            self._roi_preview_patch = None
        shape, self._roi_mode = self._roi_mode, None
        if event.xdata is None or event.ydata is None:
            self.canvas.draw_idle()
            return
        try:
            roi = RegionOfInterest(shape, x0=x0, y0=y0, x1=event.xdata, y1=event.ydata)
        except ValueError as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>ROI not created: {exc}</span>")
            self.canvas.draw_idle()
            return
        self._rois.append(roi)
        self.roi_list.addItem(f"{roi.label} ({roi.shape})")
        self.roi_list.setCurrentRow(self.roi_list.count() - 1)
        self.refresh_plot()

    def start_roi_draw(self):
        if self.grid is None:
            QMessageBox.information(self, "No data loaded", "Load a field file first.")
            return
        self._deactivate_mouse_tools()
        self._roi_mode = "rectangle" if self.roi_shape.currentText() == "Rectangle" else "ellipse"
        self.info_label.setText(f"Click-drag on the plot to draw a {self._roi_mode} ROI.")

    def _on_roi_selected(self, row):
        self.refresh_plot()  # re-highlight the selected ROI's outline
        if 0 <= row < len(self._rois):
            self._show_roi_stats(self._rois[row])

    def remove_selected_roi(self):
        row = self.roi_list.currentRow()
        if 0 <= row < len(self._rois):
            del self._rois[row]
            self.roi_list.takeItem(row)
            self.refresh_plot()

    def clear_rois(self):
        self._rois = []
        self.roi_list.clear()
        self.roi_stats_label.setText("Click 'Draw ROI' then click-drag on the plot to measure a region.")
        self._last_roi_results = None
        self.refresh_plot()

    def _show_roi_stats(self, roi):
        try:
            grid2d = self._effective_2d_grid()
            x = np.asarray(grid2d.axes[0].values(), dtype=float)
            y = np.asarray(grid2d.axes[1].values(), dtype=float)
            result = roi_statistics(grid2d.data, x, y, roi)
        except Exception as exc:
            self.roi_stats_label.setText(f"<span style='color:#c0392b'>{exc}</span>")
            return
        self._last_roi_results = result
        lines = [
            f"<b>{roi.label}</b> ({roi.shape}) — {result['n_points']} point(s)",
            f"min={result['min']:.4g}  max={result['max']:.4g}  mean={result['mean']:.4g}",
            f"std={result['std']:.4g}  rms={result['rms']:.4g}",
            f"p25={result['p25']:.4g}  p50={result['p50']:.4g}  p75={result['p75']:.4g}",
            f"area (nominal)={result['roi_area_nominal']:.4g}  integral={result['integral']:.4g}",
        ]
        self.roi_stats_label.setText("<br>".join(lines))

    def export_roi_stats(self):
        if self._last_roi_results is None:
            QMessageBox.information(self, "No ROI statistics", "Draw a ROI and select it in the list first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export ROI statistics", "roi_stats.json", "JSON (*.json)")
        if not path:
            return
        try:
            export_roi_results(self._last_roi_results, path)
            self.info_label.setText(f"ROI statistics exported to {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def compute_roi_time_evolution(self):
        row = self.roi_list.currentRow()
        if not (0 <= row < len(self._rois)):
            QMessageBox.information(self, "No ROI selected", "Select a ROI from the list first.")
            return
        if not self.files:
            QMessageBox.information(self, "No files", "Open a folder of files first.")
            return
        roi = self._rois[row]
        files = list(self.files)

        def job():
            print(f"[ROI] Computing '{roi.label}' across {len(files)} frame(s)…", flush=True)

            def progress(i, total, path):
                print(f"[ROI]   frame {i}/{total}: {Path(path).name}", flush=True)

            return roi_time_series(files, loader=GridFile.load, roi=roi, progress_callback=progress)

        from .workers import run_in_background
        run_in_background(
            self, job,
            on_success=self._on_roi_time_evolution_done,
            on_error=lambda exc: QMessageBox.warning(self, "ROI time evolution failed", str(exc)),
            label=f"Computing '{roi.label}' across {len(files)} frame(s)…",
        )

    def _on_roi_time_evolution_done(self, results):
        self._last_roi_results = results
        n_ok = sum(1 for r in results if "error" not in r)
        self.info_label.setText(
            f"ROI time evolution computed for {n_ok}/{len(results)} frame(s). Use 'Export stats (JSON)' to save."
        )

    def _draw_rois(self, ax):
        from matplotlib.patches import Rectangle, Ellipse
        for patch in self._roi_patches:
            try: patch.remove()
            except Exception: pass
        self._roi_patches = []
        selected_row = self.roi_list.currentRow()
        for i, roi in enumerate(self._rois):
            color = "yellow" if i == selected_row else "cyan"
            if roi.shape == "rectangle":
                patch = Rectangle((roi.x0, roi.y0), roi.width, roi.height, fill=False, edgecolor=color, linewidth=1.5)
            else:
                patch = Ellipse(((roi.x0 + roi.x1) / 2, (roi.y0 + roi.y1) / 2), roi.width, roi.height, fill=False, edgecolor=color, linewidth=1.5)
            ax.add_patch(patch)
            self._roi_patches.append(patch)

    def _on_figure_click(self, event):
        if self.grid is None or event.inaxes is None:
            return
        if self._cbar is not None and event.inaxes == self._cbar.ax:
            norm = self._cbar.mappable.norm
            dlg = ColorRangeDialog(getattr(norm, "vmin", 0.0), getattr(norm, "vmax", 1.0), self)
            if dlg.exec_() != QDialog.Accepted: return
            if dlg.vmin.value() >= dlg.vmax.value():
                QMessageBox.warning(self, "Invalid range", "Minimum must be smaller than maximum.")
                return
            self.vmin_check.setChecked(True); self.vmax_check.setChecked(True)
            self.vmin.setValue(dlg.vmin.value()); self.vmax.setValue(dlg.vmax.value())
            return
        if event.xdata is None or event.ydata is None:
            return
        if self._annotation_mode == "text":
            dlg=TextAnnotationDialog(self)
            if dlg.exec_()==QDialog.Accepted and dlg.text.text().strip():
                self._annotations.append({"type":"text","x":float(event.xdata),"y":float(event.ydata),"text":dlg.text.text().strip()})
                self._annotation_mode=None; self.refresh_plot()
        elif self._annotation_mode == "arrow":
            if self._arrow_start is None:
                self._arrow_start=(float(event.xdata),float(event.ydata))
                self.info_label.setText("Click the arrow end point on the plot.")
            else:
                x0,y0=self._arrow_start; self._annotations.append({"type":"arrow","x0":x0,"y0":y0,"x1":float(event.xdata),"y1":float(event.ydata)})
                self._arrow_start=None; self._annotation_mode=None; self.refresh_plot()

    def _draw_annotations(self, ax):
        for artist in self._annotation_artists:
            try: artist.remove()
            except Exception: pass
        self._annotation_artists = []
        for a in self._annotations:
            if a.get("type") == "text":
                artist = ax.annotate(a["text"], (a["x"], a["y"]), xytext=(6, 6), textcoords="offset points",
                                    fontsize=10, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="black", alpha=0.8))
                self._annotation_artists.append(artist)
            elif a.get("type") == "arrow":
                artist = ax.annotate("", xy=(a["x1"], a["y1"]), xytext=(a["x0"], a["y0"]),
                                    arrowprops=dict(arrowstyle="->", lw=1.8))
                self._annotation_artists.append(artist)

    def _ensure_custom_mouse_mode(self):
        try:
            self.canvas.deactivate_navigation()
        except Exception:
            pass
        try:
            if self._rectangle_selector is not None:
                self._rectangle_selector.set_active(False)
        except Exception:
            pass

    def start_text_annotation(self):
        if self.mode_2d.isChecked():
            self._deactivate_mouse_tools()
            self._annotation_mode="text"
            self.info_label.setText("Click the position where the text should be placed.")

    def start_arrow_annotation(self):
        if self.mode_2d.isChecked():
            self._deactivate_mouse_tools()
            self._annotation_mode="arrow"
            self._arrow_start=None
            self.info_label.setText("Click the arrow start point, then click the end point.")

    def clear_annotations(self):
        self._annotations=[]; self._annotation_mode=None; self._arrow_start=None; self.info_label.setText("Annotations cleared."); self.refresh_plot()

    def enable_region_zoom(self):
        if self.grid is None or not self.mode_2d.isChecked(): return
        self._annotation_mode = None
        self._arrow_start = None
        self._series = None
        self._gpu_dialog = None
        self._gpu_widget = None
        self._image = None
        self._line_artist = None
        self._contour_artists = []
        self._last_contour_sig = None
        from matplotlib.widgets import RectangleSelector
        if self._rectangle_selector is not None:
            try: self._rectangle_selector.disconnect_events()
            except Exception: pass
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        if ax is None: return
        def onselect(eclick, erelease):
            if eclick.xdata is None or erelease.xdata is None: return
            if abs(erelease.xdata-eclick.xdata)<1e-14 or abs(erelease.ydata-eclick.ydata)<1e-14: return
            ax.set_xlim(min(eclick.xdata,erelease.xdata), max(eclick.xdata,erelease.xdata))
            ax.set_ylim(min(eclick.ydata,erelease.ydata), max(eclick.ydata,erelease.ydata))
            self._last_limits=(ax.get_xlim(), ax.get_ylim()); self.canvas.draw_idle()
            try: self._rectangle_selector.set_active(False)
            except Exception: pass
        self.canvas.deactivate_navigation()
        self._rectangle_selector=RectangleSelector(ax,onselect,useblit=False,button=[1],spancoords='data',interactive=False)
        self.info_label.setText("Drag a rectangle over the plot to zoom.")

    def reset_view(self):
        self._deactivate_mouse_tools()
        self.x_range_check.setChecked(False); self.y_range_check.setChecked(False)
        self._last_limits = None
        self._force_full_view = True
        # Re-render from the physical data limits, not from the user's previous view.
        self._default_limits = None
        self.refresh_plot()
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        if ax is not None and self.grid is not None:
            try:
                if self.mode_2d.isChecked() and self.grid.ndim >= 2:
                    ext = self.grid.extent()
                    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
                else:
                    ax.relim(); ax.autoscale_view()
                self._last_limits = (ax.get_xlim(), ax.get_ylim())
                self._default_limits = self._last_limits
                self.canvas.draw_idle()
            except Exception:
                pass

    def _plot_lineout_index(self, ax):
        if self.grid.ndim < 1 or self.grid.data is None:
            raise ValueError("No grid data are loaded")
        along_axis = min(self.lineout_axis.currentIndex(), self.grid.ndim - 1)
        if self.grid.ndim == 1:
            coord, values = self.grid.lineout(axis=0, index=None)
        else:
            fixed_axis = 1 - along_axis if self.grid.ndim == 2 else next(i for i in range(self.grid.ndim) if i != along_axis)
            fixed_physical_index = int(self.lineout_index.value())
            fixed_physical_index = max(0, min(fixed_physical_index, self.grid.axes[fixed_axis].n - 1))
            physical_indices = [self.grid.axes[i].n // 2 for i in range(self.grid.ndim)]
            physical_indices[fixed_axis] = fixed_physical_index
            # GridFile.lineout accepts physical-axis indices and performs the
            # Simulation-to-NumPy axis conversion internally.
            coord, values = self.grid.lineout(axis=along_axis, index=tuple(physical_indices))
        values = smooth_1d(values, self.smooth_method.currentText(), self.smooth_window.value())
        if self._line_artist is None or self._active_plot_mode not in {"line_index", "line_coord", "time_series"}:
            self._line_artist, = ax.plot(coord, values, lw=1.6, color=self.accent_hex())
        else:
            self._line_artist.set_data(coord, values)
            self._line_artist.set_color(self.accent_hex())
        ax.set_xlabel(self._axis_label(along_axis)); ax.set_ylabel(f"{self.grid.label} [{self.grid.units}]" if self.grid.units else self.grid.label)
        ax.set_title(f"t = {self.grid.time:g} {self.grid.time_units}  (iter {self.grid.iteration}), index lineout")

    def _plot_lineout_coord(self, ax):
        if self.grid.ndim != 2:
            raise ValueError("Physical-coordinate lineouts currently support 2D grid files only.")
        along_axis = self.lineout_axis.currentIndex()
        fixed_axis = 1 - along_axis
        coords = self.grid.axes[fixed_axis].values()
        position = float(self.lineout_coord.value())
        if not np.isfinite(position) or position < float(coords.min()) or position > float(coords.max()):
            raise ValueError(f"Fixed coordinate must be between {coords.min():g} and {coords.max():g} {self.grid.axes[fixed_axis].units}")
        coord, values = self.grid.lineout_at(along_axis=along_axis, fixed_value=position, fixed_axis=fixed_axis)
        values = smooth_1d(values, self.smooth_method.currentText(), self.smooth_window.value())
        if self._line_artist is None:
            self._line_artist, = ax.plot(coord, values, lw=1.6, color=self.accent_hex())
        else:
            self._line_artist.set_data(coord, values)
            self._line_artist.set_color(self.accent_hex())
        ax.set_xlabel(self._axis_label(along_axis)); ax.set_ylabel(f"{self.grid.label} [{self.grid.units}]" if self.grid.units else self.grid.label)
        ax.set_title(f"t = {self.grid.time:g} {self.grid.time_units}   ({self.grid.axes[fixed_axis].name} = {position:g})")

    def _plot_time_series(self, ax):
        if len(self.files) < 2: ax.text(0.5,0.5,"Open a folder with multiple time-step files to use time-series mode.",ha="center",va="center",transform=ax.transAxes); return
        quantity = self.grid.dataset_name if self.grid is not None else None
        cache_key = (tuple(self.files), quantity, self.reduction_combo.currentText(), self.average_direction.currentText(), self.smooth_method.currentText(), self.smooth_window.value())
        try:
            cached = self._time_series_cache.get(cache_key)
            if cached is None:
                reduction = self.reduction_combo.currentText()
                average_direction = self.average_direction.currentText() if reduction == "directional average" else None
                if reduction == "directional average":
                    reduction = "mean"
                cached = reduce_grid_series(
                    self.files, reduction=reduction,
                    smoothing={"method":self.smooth_method.currentText(),"window":self.smooth_window.value()},
                    quantity=quantity, average_direction=average_direction,
                )
                self._time_series_cache[cache_key] = cached
            times, iters, values, meta = cached
        except Exception as exc:
            ax.text(0.5,0.5,f"Error computing time series:\n{exc}",ha="center",va="center",transform=ax.transAxes); return
        if self._line_artist is None:
            self._line_artist, = ax.plot(times, values, "o-", lw=1.6, ms=4, color=self.accent_hex())
        else:
            self._line_artist.set_data(times, values); self._line_artist.set_color(self.accent_hex())
        ax.relim(); ax.autoscale_view()
        ax.set_xlabel("time"); unit_str = f" [{meta['units']}]" if meta["units"] else ""; ax.set_ylabel(f"{self.reduction_combo.currentText()}({meta['label']}) over x1,x2{unit_str}"); ax.set_title(f"{meta['label']} — {self.reduction_combo.currentText()} over space, {len(self.files)} time steps")

    def export_time_series(self):
        if len(self.files) < 1 or self.grid is None:
            QMessageBox.information(self, "No time series", "Open at least one compatible simulation frame first.")
            return
        try:
            reduction_label = self.reduction_combo.currentText()
            reduction = "mean" if reduction_label == "directional average" else reduction_label
            direction = self.average_direction.currentText() if reduction_label == "directional average" else None
            quantity = self.grid.dataset_name if self.grid is not None else None
            cache_key = (tuple(self.files), quantity, reduction_label, self.average_direction.currentText(), self.smooth_method.currentText(), self.smooth_window.value())
            cached = self._time_series_cache.get(cache_key)
            if cached is None:
                cached = reduce_grid_series(self.files, reduction=reduction, smoothing={"method":self.smooth_method.currentText(),"window":self.smooth_window.value()}, quantity=quantity, average_direction=direction)
                self._time_series_cache[cache_key] = cached
            times, iters, values, meta = cached
            path, _ = QFileDialog.getSaveFileName(self, "Export time series", "time_series.csv", "CSV (*.csv)")
            if not path: return
            header = f"time,iteration,value\n# quantity={meta.get('quantity','')}; reduction={reduction_label}; direction={direction or ''}"
            np.savetxt(path, np.column_stack((times, iters, values)), delimiter=",", header=header, comments="")
            self.info_label.setText(f"Time series exported: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Time-series export failed", str(exc))

    def _session_state(self):
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        state = {
            "tab": "grid",
            "files": list(self.files),
            "current_index": self.file_list.currentRow(),
            "mode": "time_series" if self.mode_time_series.isChecked() else "line_coord" if self.mode_line_coord.isChecked() else "line_index" if self.mode_line_index.isChecked() else "2d",
            "slice_axis": self.slice_axis.currentText(), "slice_index": self.slice_index.value(),
            "lineout_axis": self.lineout_axis.currentText(), "lineout_index": self.lineout_index.value(), "lineout_coord": self.lineout_coord.value(),
            "reduction": self.reduction_combo.currentText(), "average_direction": self.average_direction.currentText(),
            "smooth_method": self.smooth_method.currentText(), "smooth_window": self.smooth_window.value(),
            "x_range_check": self.x_range_check.isChecked(), "x_min": self.x_range_min.value(), "x_max": self.x_range_max.value(),
            "y_range_check": self.y_range_check.isChecked(), "y_min": self.y_range_min.value(), "y_max": self.y_range_max.value(),
            "title": self.title_edit.text(), "cmap": self.cmap_combo.currentText(), "norm": self.norm_combo.currentText(),
        }
        if ax is not None:
            state["view_xlim"] = list(ax.get_xlim()); state["view_ylim"] = list(ax.get_ylim())
        return state

    def save_session(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save visualization session", "session.xml", "XML session (*.xml)")
        if not path: return
        try:
            save_xml_session(path, self._session_state())
            self.info_label.setText(f"Session saved: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Could not save session", str(exc))

    def load_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore visualization session", "", "XML session (*.xml)")
        if not path: return
        try:
            state = load_xml_session(path)
            self.files = [str(x) for x in state.get("files", []) if Path(str(x)).exists()]
            if not self.files:
                raise ValueError("None of the files recorded in this session are currently available.")
            self.file_list.clear(); self.file_list.addItems([Path(f).name for f in self.files])
            row = max(0, min(value_as_int(state.get("current_index"), 0), len(self.files)-1)); self.file_list.setCurrentRow(row)
            mode_map = {"2d": self.mode_2d, "line_index": self.mode_line_index, "line_coord": self.mode_line_coord, "time_series": self.mode_time_series}
            mode_map.get(state.get("mode"), self.mode_2d).setChecked(True)
            self.slice_axis.setCurrentText(str(state.get("slice_axis", self.slice_axis.currentText())))
            self.slice_index.setValue(value_as_int(state.get("slice_index"), self.slice_index.value()))
            self.lineout_axis.setCurrentText(str(state.get("lineout_axis", self.lineout_axis.currentText())))
            self.lineout_index.setValue(value_as_int(state.get("lineout_index"), self.lineout_index.value()))
            self.lineout_coord.setValue(value_as_float(state.get("lineout_coord"), self.lineout_coord.value()))
            self.reduction_combo.setCurrentText(str(state.get("reduction", self.reduction_combo.currentText())))
            self.average_direction.setCurrentText(str(state.get("average_direction", self.average_direction.currentText())))
            self.smooth_method.setCurrentText(str(state.get("smooth_method", self.smooth_method.currentText())))
            self.smooth_window.setValue(value_as_int(state.get("smooth_window"), self.smooth_window.value()))
            self.title_edit.setText(str(state.get("title", ""))); self.norm_combo.setCurrentText(str(state.get("norm", "linear")))
            self.apply_selection()
            self.x_range_check.setChecked(value_as_bool(state.get("x_range_check"))); self.x_range_min.setValue(value_as_float(state.get("x_min"), self.x_range_min.value())); self.x_range_max.setValue(value_as_float(state.get("x_max"), self.x_range_max.value()))
            self.y_range_check.setChecked(value_as_bool(state.get("y_range_check"))); self.y_range_min.setValue(value_as_float(state.get("y_min"), self.y_range_min.value())); self.y_range_max.setValue(value_as_float(state.get("y_max"), self.y_range_max.value()))
            ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
            if ax is not None and "view_xlim" in state and "view_ylim" in state:
                ax.set_xlim(*[value_as_float(v) for v in state["view_xlim"]]); ax.set_ylim(*[value_as_float(v) for v in state["view_ylim"]]); self.canvas.draw_idle()
            self.info_label.setText(f"Session restored: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Could not restore session", str(exc))

    def _axis_label(self, i, grid=None):
        grid = grid if grid is not None else self.grid
        if i < len(grid.axes):
            ax = grid.axes[i]; return f"{ax.label} [{ax.units}]" if ax.units else ax.label
        return f"x{i+1}"
