import numpy as np
from matplotlib.colors import LogNorm
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QRadioButton, QSpinBox, QVBoxLayout,
)

from .. import style
from ..io.particles import ParticleFile
from .base_tab import BaseTab


class ParticlesTab(BaseTab):
    """View particle phase-space: scatter, hexbin, 2D histogram, or 1D
    histogram/spectrum, with density coloring and log-scale options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pf = None

        self.file_list = self.add_open_buttons(folder=True, label="particle file")
        self.file_list.currentRowChanged.connect(self.on_file_selected)

        opts_box = QGroupBox("Display")
        form = QFormLayout(opts_box)

        self.mode_scatter = QRadioButton("Scatter")
        self.mode_scatter_density = QRadioButton("Scatter (colored by local density)")
        self.mode_hexbin = QRadioButton("Hexbin")
        self.mode_hist2d = QRadioButton("2D histogram")
        self.mode_hist1d = QRadioButton("1D histogram / spectrum")
        self.mode_scatter.setChecked(True)
        for rb in (self.mode_scatter, self.mode_scatter_density, self.mode_hexbin, self.mode_hist2d, self.mode_hist1d):
            rb.toggled.connect(self._update_mode_widgets)
            rb.toggled.connect(self.refresh_plot)

        mode_row = QVBoxLayout()
        for rb in (self.mode_scatter, self.mode_scatter_density, self.mode_hexbin, self.mode_hist2d, self.mode_hist1d):
            mode_row.addWidget(rb)
        form.addRow("Mode:", mode_row)

        self.x_quant = QComboBox()
        self.y_quant = QComboBox()
        self.x_quant.currentTextChanged.connect(self.refresh_plot)
        self.y_quant.currentTextChanged.connect(self.refresh_plot)
        form.addRow("X quantity:", self.x_quant)
        self.y_row_label = QLabel("Y quantity:")
        form.addRow(self.y_row_label, self.y_quant)

        self.control_layout.addWidget(opts_box)

        color_box = QGroupBox("Color")
        color_form = QFormLayout(color_box)
        self.cmap_category = QComboBox()
        self.cmap_category.addItems(list(style.COLORMAPS.keys()))
        self.cmap_category.currentTextChanged.connect(self._populate_cmaps)
        color_form.addRow("Colormap group:", self.cmap_category)

        self.cmap_combo = QComboBox()
        self.cmap_combo.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Colormap:", self.cmap_combo)
        self._populate_cmaps(select="viridis")

        self.reverse_cmap = QCheckBox("Reverse colormap")
        self.reverse_cmap.stateChanged.connect(self.refresh_plot)
        color_form.addRow(self.reverse_cmap)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 16)
        self._update_color_preview()
        color_btn = self.add_color_picker_button(self._on_color_picked, "Pick plain-scatter color…")
        color_form.addRow(self.color_preview, color_btn)

        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.05, 1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setValue(0.4)
        self.alpha_spin.valueChanged.connect(self.refresh_plot)
        color_form.addRow("Point opacity:", self.alpha_spin)

        self.log_color = QCheckBox("Log color scale (counts)")
        self.log_color.stateChanged.connect(self.refresh_plot)
        color_form.addRow(self.log_color)

        self.control_layout.addWidget(color_box)

        binning_box = QGroupBox("Binning / sampling")
        binning_form = QFormLayout(binning_box)
        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(5, 500)
        self.bins_spin.setValue(80)
        self.bins_spin.valueChanged.connect(self.refresh_plot)
        binning_form.addRow("Bins:", self.bins_spin)

        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(100, 2_000_000)
        self.max_points_spin.setValue(20000)
        self.max_points_spin.setSingleStep(1000)
        self.max_points_spin.valueChanged.connect(self.refresh_plot)
        binning_form.addRow("Max points (scatter):", self.max_points_spin)
        self.control_layout.addWidget(binning_box)

        axes_box = QGroupBox("Axes")
        axes_form = QFormLayout(axes_box)
        self.log_x = QCheckBox("Log X axis")
        self.log_y = QCheckBox("Log Y axis")
        self.log_x.stateChanged.connect(self.refresh_plot)
        self.log_y.stateChanged.connect(self.refresh_plot)
        log_row = QHBoxLayout()
        log_row.addWidget(self.log_x)
        log_row.addWidget(self.log_y)
        axes_form.addRow("Scale:", log_row)

        self.show_stats = QCheckBox("Show statistics box")
        self.show_stats.setChecked(True)
        self.show_stats.stateChanged.connect(self.refresh_plot)
        axes_form.addRow(self.show_stats)
        self.control_layout.addWidget(axes_box)

        self.info_label = QLabel("No file loaded.")
        self.info_label.setWordWrap(True)
        self.control_layout.addWidget(self.info_label)

        self.finish_layout()
        self._update_mode_widgets()

    def _populate_cmaps(self, select=None):
        cat = self.cmap_category.currentText()
        self.cmap_combo.blockSignals(True)
        self.cmap_combo.clear()
        items = style.COLORMAPS.get(cat, style.ALL_COLORMAPS)
        self.cmap_combo.addItems(items)
        if select and select in items:
            self.cmap_combo.setCurrentText(select)
        self.cmap_combo.blockSignals(False)
        self.refresh_plot()

    def _on_color_picked(self, color):
        self._update_color_preview()
        self.refresh_plot()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(f"background-color: {self.accent_hex()}; border: 1px solid #888;")

    def _update_mode_widgets(self):
        need_y = not self.mode_hist1d.isChecked()
        self.y_quant.setEnabled(need_y)
        self.y_row_label.setEnabled(need_y)
        is_plain_scatter = self.mode_scatter.isChecked()
        needs_bins = not is_plain_scatter and not self.mode_scatter_density.isChecked()
        self.bins_spin.setEnabled(needs_bins)
        needs_maxpts = is_plain_scatter or self.mode_scatter_density.isChecked()
        self.max_points_spin.setEnabled(needs_maxpts)
        self.log_color.setEnabled(not is_plain_scatter)
        self.cmap_combo.setEnabled(not is_plain_scatter)
        self.cmap_category.setEnabled(not is_plain_scatter)
        self.reverse_cmap.setEnabled(not is_plain_scatter)

    # -- file handling -----------------------------------------------
    def on_file_selected(self, row):
        if row < 0 or row >= len(self.files):
            return
        try:
            self.pf = ParticleFile.info(self.files[row])
        except Exception as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>Error reading file:<br>{exc}</span>")
            return

        quants = self.pf.quants
        for combo, default in ((self.x_quant, "x1"), (self.y_quant, "p1" if "p1" in quants else quants[-1] if quants else "")):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(quants)
            if default in quants:
                combo.setCurrentText(default)
            combo.blockSignals(False)

        self.info_label.setText(
            f"<b>{self.pf.name}</b><br>"
            f"N particles: {self.pf.npar}<br>"
            f"quantities: {', '.join(quants)}<br>"
            f"time: {self.pf.time:g}  iter: {self.pf.iteration}"
        )
        self.refresh_plot()

    def _cmap_name(self):
        name = self.cmap_combo.currentText() or "viridis"
        if self.reverse_cmap.isChecked() and not name.endswith("_r"):
            name += "_r"
        return name

    # -- plotting ------------------------------------------------------
    def refresh_plot(self):
        if self.pf is None or not self.x_quant.currentText():
            return
        self.canvas.clear()
        ax = self.canvas.figure.add_subplot(111)

        xq = self.x_quant.currentText()
        x = self.pf.get(xq)
        xlabel = f"{self.pf.label(xq)} [{self.pf.unit(xq)}]" if self.pf.unit(xq) else self.pf.label(xq)
        cmap = self._cmap_name()
        color_norm = LogNorm() if self.log_color.isChecked() else None

        if self.mode_hist1d.isChecked():
            bins = np.geomspace(max(x.min(), 1e-12), x.max(), self.bins_spin.value()) if self.log_x.isChecked() and x.min() > 0 else self.bins_spin.value()
            ax.hist(x, bins=bins, color=self.accent_hex(), edgecolor="none")
            ax.set_xlabel(xlabel)
            ax.set_ylabel("count")
            if self.log_y.isChecked():
                ax.set_yscale("log")
            if self.log_x.isChecked():
                ax.set_xscale("log")
            if self.show_stats.isChecked():
                self._add_stats_box(ax, x)
        else:
            yq = self.y_quant.currentText()
            if not yq:
                self.canvas.draw()
                return
            y = self.pf.get(yq)
            ylabel = f"{self.pf.label(yq)} [{self.pf.unit(yq)}]" if self.pf.unit(yq) else self.pf.label(yq)

            if self.mode_scatter.isChecked() or self.mode_scatter_density.isChecked():
                n = len(x)
                max_pts = self.max_points_spin.value()
                if n > max_pts:
                    idx = np.random.default_rng(0).choice(n, max_pts, replace=False)
                    x_plot, y_plot = x[idx], y[idx]
                else:
                    x_plot, y_plot = x, y

                alpha = self.alpha_spin.value()
                if self.mode_scatter_density.isChecked() and len(x_plot) > 2:
                    density = self._point_density(x_plot, y_plot)
                    order = np.argsort(density)
                    sc = ax.scatter(x_plot[order], y_plot[order], c=density[order], s=4, cmap=cmap, alpha=alpha)
                    self.canvas.figure.colorbar(sc, ax=ax, label="local density")
                else:
                    ax.scatter(x_plot, y_plot, s=2, alpha=alpha, color=self.accent_hex())
            elif self.mode_hexbin.isChecked():
                hb = ax.hexbin(x, y, gridsize=self.bins_spin.value(), cmap=cmap, norm=color_norm, mincnt=1)
                self.canvas.figure.colorbar(hb, ax=ax, label="count")
            else:  # 2D histogram
                h = ax.hist2d(x, y, bins=self.bins_spin.value(), cmap=cmap, norm=color_norm)
                self.canvas.figure.colorbar(h[3], ax=ax, label="count")

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            if self.log_x.isChecked():
                ax.set_xscale("log")
            if self.log_y.isChecked():
                ax.set_yscale("log")

        ax.set_title(f"t = {self.pf.time:g}  (iter {self.pf.iteration})")
        self.canvas.draw()

    @staticmethod
    def _point_density(x, y):
        """Fast approximate point density via a coarse 2D histogram lookup
        (much cheaper than a full Gaussian KDE for large particle counts)."""
        bins = 60
        h, xedges, yedges = np.histogram2d(x, y, bins=bins)
        xi = np.clip(np.digitize(x, xedges) - 1, 0, bins - 1)
        yi = np.clip(np.digitize(y, yedges) - 1, 0, bins - 1)
        return h[xi, yi]

    @staticmethod
    def _add_stats_box(ax, x):
        text = f"mean = {np.mean(x):.3g}\nstd = {np.std(x):.3g}\nmin = {np.min(x):.3g}\nmax = {np.max(x):.3g}"
        ax.text(0.97, 0.97, text, transform=ax.transAxes, ha="right", va="top",
                fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.85))
