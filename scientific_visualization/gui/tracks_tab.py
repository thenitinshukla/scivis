import numpy as np
from matplotlib.collections import LineCollection
from PyQt5.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QSpinBox

from .. import style
from ..analysis import smooth_1d
from ..io.tracks import TracksFile
from .base_tab import BaseTab


class TracksTab(BaseTab):
    """View particle trajectories: quantity-vs-quantity (e.g. x1 vs x2) or
    quantity-vs-time, colored by track index, a chosen palette, or a
    physical quantity (e.g. energy) along the trajectory."""

    file_filter = "HDF5 files (*.h5 *.hdf5);;All files (*)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tf = None

        self.file_list = self.add_open_buttons(folder=False, label="tracks file")
        self.file_list.currentRowChanged.connect(self.on_file_selected)

        opts_box = QGroupBox("Display")
        form = QFormLayout(opts_box)

        self.x_quant = QComboBox()
        self.y_quant = QComboBox()
        self.x_quant.currentTextChanged.connect(self.refresh_plot)
        self.y_quant.currentTextChanged.connect(self.refresh_plot)
        form.addRow("X quantity:", self.x_quant)
        form.addRow("Y quantity:", self.y_quant)

        self.n_tracks_spin = QSpinBox()
        self.n_tracks_spin.setRange(1, 1)
        self.n_tracks_spin.valueChanged.connect(self.refresh_plot)
        form.addRow("Tracks to show:", self.n_tracks_spin)
        self.control_layout.addWidget(opts_box)

        color_box = QGroupBox("Color")
        color_form = QFormLayout(color_box)
        self.color_mode = QComboBox()
        self.color_mode.addItems(["Single color", "By track index", "By quantity along track"])
        self.color_mode.setCurrentText("By track index")
        self.color_mode.currentTextChanged.connect(self._update_color_widgets)
        self.color_mode.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Mode:", self.color_mode)

        self.palette_combo = QComboBox()
        self.palette_combo.addItems(list(style.LINE_PALETTES.keys()))
        self.palette_combo.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Index palette:", self.palette_combo)

        self.color_quant = QComboBox()
        self.color_quant.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Color by:", self.color_quant)

        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(style.ALL_COLORMAPS)
        self.cmap_combo.setCurrentText("viridis")
        self.cmap_combo.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Colormap:", self.cmap_combo)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 16)
        self._update_color_preview()
        color_btn = self.add_color_picker_button(self._on_color_picked, "Pick single color…")
        color_form.addRow(self.color_preview, color_btn)

        self.control_layout.addWidget(color_box)

        smooth_box = QGroupBox("Smoothing (per track)")
        smooth_form = QFormLayout(smooth_box)
        self.smooth_method = QComboBox()
        self.smooth_method.addItems(["None", "Moving average", "Gaussian"])
        self.smooth_method.currentTextChanged.connect(self.refresh_plot)
        smooth_form.addRow("Method:", self.smooth_method)
        self.smooth_window = QSpinBox()
        self.smooth_window.setRange(1, 200)
        self.smooth_window.setValue(5)
        self.smooth_window.valueChanged.connect(self.refresh_plot)
        smooth_form.addRow("Window / sigma:", self.smooth_window)
        self.control_layout.addWidget(smooth_box)

        self.info_label = QLabel("No file loaded.")
        self.info_label.setWordWrap(True)
        self.control_layout.addWidget(self.info_label)

        self.finish_layout()
        self._update_color_widgets()

    def _on_color_picked(self, color):
        self._update_color_preview()
        self.refresh_plot()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(f"background-color: {self.accent_hex()}; border: 1px solid #888;")

    def _update_color_widgets(self):
        mode = self.color_mode.currentText()
        self.color_quant.setEnabled(mode == "By quantity along track")
        self.cmap_combo.setEnabled(mode != "Single color")
        self.palette_combo.setEnabled(mode == "By track index")

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.files):
            return
        try:
            self.tf = TracksFile.info(self.files[row])
        except Exception as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>Error reading file:<br>{exc}</span>")
            return

        quants = self.tf.quants
        for combo, default in ((self.x_quant, "t" if "t" in quants else quants[0] if quants else ""),
                                (self.y_quant, "x1" if "x1" in quants else (quants[1] if len(quants) > 1 else ""))):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(quants)
            if default in quants:
                combo.setCurrentText(default)
            combo.blockSignals(False)

        self.color_quant.blockSignals(True)
        self.color_quant.clear()
        self.color_quant.addItems(quants)
        if "ene" in quants:
            self.color_quant.setCurrentText("ene")
        self.color_quant.blockSignals(False)

        self.n_tracks_spin.setRange(1, max(1, self.tf.ntracks))
        self.n_tracks_spin.setValue(min(self.tf.ntracks, 20))

        self.info_label.setText(
            f"<b>{self.tf.name}</b><br>"
            f"N tracks: {self.tf.ntracks}<br>"
            f"quantities: {', '.join(quants)}<br>"
            f"dt: {self.tf.dt:g}"
        )
        self.refresh_plot()

    def refresh_plot(self):
        if self.tf is None or not self.x_quant.currentText() or not self.y_quant.currentText():
            return
        self.canvas.clear()
        ax = self.canvas.figure.add_subplot(111)

        xq = self.x_quant.currentText()
        yq = self.y_quant.currentText()
        n = self.n_tracks_spin.value()
        color_mode = self.color_mode.currentText()
        cmap_name = self.cmap_combo.currentText()
        smooth_method = self.smooth_method.currentText()
        smooth_window = self.smooth_window.value()

        index_colors = None
        if color_mode == "By track index":
            index_colors = style.line_color_cycle(self.palette_combo.currentText(), n, cmap_name)

        mappable = None
        cq = self.color_quant.currentText()
        vmin = vmax = None
        if color_mode == "By quantity along track" and cq:
            all_vals = []
            for i in range(n):
                trk = self.tf.get_track(i)
                if cq in trk:
                    all_vals.append(trk[cq])
            if all_vals:
                vmin = min(v.min() for v in all_vals)
                vmax = max(v.max() for v in all_vals)

        for i in range(n):
            trk = self.tf.get_track(i)
            if xq not in trk or yq not in trk:
                continue
            xv = smooth_1d(trk[xq], smooth_method, smooth_window)
            yv = smooth_1d(trk[yq], smooth_method, smooth_window)

            if color_mode == "By quantity along track" and cq in trk and vmin is not None:
                points = np.array([xv, yv]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                lc = LineCollection(segments, cmap=cmap_name, linewidths=1.2)
                lc.set_array(trk[cq])
                lc.set_clim(vmin, vmax)
                ax.add_collection(lc)
                mappable = lc
            elif color_mode == "By track index":
                ax.plot(xv, yv, lw=0.9, alpha=0.85, color=index_colors[i])
            else:
                ax.plot(xv, yv, lw=0.9, alpha=0.85, color=self.accent_hex())

        if color_mode == "By quantity along track" and mappable is not None:
            cbar = self.canvas.figure.colorbar(mappable, ax=ax)
            label = self.tf.label(cq)
            unit = self.tf.unit(cq)
            cbar.set_label(f"{label} [{unit}]" if unit else label)

        ax.autoscale_view()

        xlabel = f"{self.tf.label(xq)} [{self.tf.unit(xq)}]" if self.tf.unit(xq) else self.tf.label(xq)
        ylabel = f"{self.tf.label(yq)} [{self.tf.unit(yq)}]" if self.tf.unit(yq) else self.tf.label(yq)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{n} of {self.tf.ntracks} tracks")

        self.canvas.draw()
