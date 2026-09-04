from __future__ import annotations

from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import numpy as np

from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from .. import style
from ..data_plotter.batch import parse_many
from ..data_plotter.comparison import transform_for_preset
from ..data_plotter.scaling import infer_scaling_columns, strong_scaling, weak_scaling
from ..data_plotter.model import DatasetPlotConfig, DatasetTable
from ..data_plotter.parser import Delimiter
from ..data_plotter.renderer import DataPlotRenderer, RenderSeries
from ..data_plotter.transform import TransformPipeline
from ..export.image import export_figure
from .base_tab import BaseTab


class DataPlotterTab(BaseTab):
    """Fast multi-file scientific plotting and scaling comparison workflow."""

    file_filter = "Data files (*.csv *.txt);;CSV files (*.csv);;Text files (*.txt);;All files (*)"

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(7.0, 5.5))
        self._datasets: list[DatasetTable] = []
        self._configs: list[DatasetPlotConfig] = []
        self.renderer = DataPlotRenderer()
        self._updating = False
        self._replot_pending = False
        self._build_controls()
        self._enable_drop()
        self.finish_layout()
        self.refresh_plot()

    def _build_controls(self):
        row = QHBoxLayout()
        open_btn = QPushButton("Open CSV/TXT…")
        open_btn.clicked.connect(self.open_files)
        remove = QPushButton("Remove")
        remove.clicked.connect(self.remove_selected)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_datasets)
        row.addWidget(open_btn); row.addWidget(remove); row.addWidget(clear)
        self.control_layout.addLayout(row)

        self.dataset_list = QListWidget()
        self.dataset_list.itemSelectionChanged.connect(self._select_dataset)
        self.dataset_list.itemChanged.connect(self._item_changed)
        self.control_layout.addWidget(self.dataset_list, stretch=1)

        parser_box = QGroupBox("Input")
        pf = QFormLayout(parser_box)
        self.delimiter = QComboBox(); self.delimiter.addItems([d.value for d in Delimiter]); self.delimiter.setCurrentText(Delimiter.AUTO.value)
        reload_btn = QPushButton("Reload selected")
        reload_btn.clicked.connect(self.reload_selected)
        pf.addRow("Delimiter:", self.delimiter); pf.addRow(reload_btn)
        self.control_layout.addWidget(parser_box)

        paper_box = QGroupBox("Scientific paper figure")
        pfm = QFormLayout(paper_box)
        self.preset = QComboBox()
        self.preset.addItems(["Paper Strong Scaling"])
        self.preset.currentTextChanged.connect(self._preset_changed)
        self.paper_mode_info = QLabel(
            "Paper Strong Scaling: two synchronized panels showing speedup and parallel efficiency, "
            "with GPUs on the top axis, nodes on the bottom axis, and ideal scaling references."
        )
        self.paper_mode_info.setWordWrap(True)
        pfm.addRow("Figure mode:", self.preset)
        pfm.addRow(self.paper_mode_info)
        self.control_layout.addWidget(paper_box)

        scaling = QGroupBox("Scaling experiment")
        sfm = QFormLayout(scaling)
        self.resource_info = QLabel("Automatic column detection: resource count + runtime")
        self.resource_info.setWordWrap(True)
        detect_btn = QPushButton("Detect scaling columns")
        detect_btn.clicked.connect(self.detect_scaling_columns)
        sfm.addRow(self.resource_info)
        sfm.addRow(detect_btn)
        self.control_layout.addWidget(scaling)

        style_box = QGroupBox("Dataset style")
        sf = QFormLayout(style_box)
        self.palette = QComboBox(); self.palette.addItems(list(self.renderer.PALETTES)); self.palette.currentTextChanged.connect(self.apply_palette)
        self.line_style = QComboBox(); self.line_style.addItems(["-", "--", ":", "-."])
        self.marker = QComboBox(); self.marker.addItems(["None", "Circle", "Square", "Triangle", "Diamond", "Cross"])
        self.line_width = QDoubleSpinBox(); self.line_width.setRange(0.2, 12); self.line_width.setValue(1.8); self.line_width.setSingleStep(0.2)
        self.marker_size = QDoubleSpinBox(); self.marker_size.setRange(1, 20); self.marker_size.setValue(4); self.marker_size.setSingleStep(0.5)
        self.apply_style_btn = QPushButton("Apply style to selected")
        self.apply_style_btn.clicked.connect(self.apply_selected_style)
        self.color_btn = QPushButton("Choose color…"); self.color_btn.clicked.connect(self.choose_color)
        self.current_color = QColor(self.renderer.DEFAULT_COLORS[0])
        sf.addRow("Palette:", self.palette); sf.addRow("Line style:", self.line_style); sf.addRow("Marker:", self.marker)
        sf.addRow("Line width:", self.line_width); sf.addRow("Marker size:", self.marker_size); sf.addRow(self.color_btn); sf.addRow(self.apply_style_btn)
        self.control_layout.addWidget(style_box)

        self.stats_label = QLabel("Select a dataset to inspect it."); self.stats_label.setWordWrap(True)
        inspect = QGroupBox("Data inspection")
        iv = QVBoxLayout(inspect)
        iv.addWidget(self.stats_label)
        self.data_table = QTableWidget()
        self.data_table.setToolTip("Edit numeric values directly in the preview. Changes are kept in memory and do not modify the source file.")
        self.data_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.SelectedClicked)
        self.data_table.cellChanged.connect(self._cell_changed)
        iv.addWidget(self.data_table, 1)
        self.apply_edits_btn = QPushButton("Apply table edits to plot")
        self.apply_edits_btn.clicked.connect(self._apply_table_edits)
        self.apply_edits_btn.setEnabled(False)
        iv.addWidget(self.apply_edits_btn)
        self.control_layout.addWidget(inspect)

        exp = QGroupBox("Export")
        ef = QFormLayout(exp)
        self.dpi = QSpinBox(); self.dpi.setRange(72, 1200); self.dpi.setValue(300)
        self.width = QDoubleSpinBox(); self.width.setRange(1, 30); self.width.setValue(8.5); self.width.setSuffix(" cm")
        self.height = QDoubleSpinBox(); self.height.setRange(1, 30); self.height.setValue(10.5); self.height.setSuffix(" cm")
        export = QPushButton("Export PNG/SVG/PDF…"); export.clicked.connect(self.export_plot)
        ef.addRow("DPI:", self.dpi); ef.addRow("Width:", self.width); ef.addRow("Height:", self.height); ef.addRow(export)
        self.control_layout.addWidget(exp)

    def _populate_data_table(self, dataset):
        """Show a bounded editable preview rather than allocating a GUI item
        for every cell of a potentially huge scientific table."""
        self.data_table.blockSignals(True)
        try:
            max_rows, max_cols = 500, 20
            rows = min(dataset.row_count, max_rows)
            cols = min(dataset.column_count, max_cols)
            self.data_table.clear()
            self.data_table.setRowCount(rows)
            self.data_table.setColumnCount(cols)
            self.data_table.setHorizontalHeaderLabels(dataset.columns[:cols])
            for r in range(rows):
                for c in range(cols):
                    value = dataset.values[r, c]
                    text = "" if not np.isfinite(value) else f"{float(value):.12g}"
                    self.data_table.setItem(r, c, QTableWidgetItem(text))
            self.data_table.resizeColumnsToContents()
            self.apply_edits_btn.setEnabled(rows > 0 and cols > 0)
        finally:
            self.data_table.blockSignals(False)

    def _cell_changed(self, row, column):
        # Validation is deferred until Apply, which prevents a half-entered
        # value from repeatedly triggering expensive redraws.
        item = self.data_table.item(row, column)
        if item is not None:
            item.setToolTip("Edited value pending Apply")

    def _apply_table_edits(self):
        if not self._datasets:
            return
        row = self.dataset_list.currentRow()
        if row < 0 or row >= len(self._datasets):
            return
        ds = self._datasets[row]
        errors = []
        for r in range(min(ds.row_count, self.data_table.rowCount())):
            for c in range(min(ds.column_count, self.data_table.columnCount())):
                item = self.data_table.item(r, c)
                if item is None:
                    continue
                text = item.text().strip()
                try:
                    ds.set_value(r, c, float(text))
                except ValueError:
                    errors.append(f"row {r + 1}, column {c + 1}")
        if errors:
            QMessageBox.warning(self, "Invalid table values",
                                "These cells were not applied: " + ", ".join(errors[:10]))
        self._update_stats(ds)
        self.refresh_plot()

    def _enable_drop(self):
        self.setAcceptDrops(True); self.canvas.setAcceptDrops(True); self.canvas.installEventFilter(self)
        self.setToolTip("Drop one or more CSV/TXT files to compare them on the same axes.")

    @staticmethod
    def _urls_are_supported(mime: QMimeData):
        return any(u.isLocalFile() and Path(u.toLocalFile()).suffix.lower() in {".csv", ".txt"} for u in mime.urls())

    def dragEnterEvent(self, event):
        event.acceptProposedAction() if self._urls_are_supported(event.mimeData()) else event.ignore()

    def dropEvent(self, event):
        self._load_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]); event.acceptProposedAction()

    def eventFilter(self, obj, event):
        if event.type() == event.DragEnter and self._urls_are_supported(event.mimeData()): event.acceptProposedAction(); return True
        if event.type() == event.Drop:
            self._load_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]); event.acceptProposedAction(); return True
        return super().eventFilter(obj, event)

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open data files", "", self.file_filter)
        self._load_paths(paths)

    def _selected_delimiter(self):
        try: return Delimiter(self.delimiter.currentText())
        except ValueError: return Delimiter.AUTO

    def _load_paths(self, paths):
        existing = {str(Path(d.path).resolve()) for d in self._datasets}
        paths = [p for p in paths if p and str(Path(p).resolve()) not in existing]
        if not paths:
            return
        delimiter = self._selected_delimiter()
        self._replot_pending = True

        def job():
            # Parsing is pure Python/NumPy and deliberately runs outside the
            # GUI thread. Large CSV/TXT imports therefore do not block painting
            # or mouse interaction.
            return parse_many(paths, delimiter)

        def done(result):
            start = len(self._datasets)
            self._datasets.extend(result.datasets)
            for i, ds in enumerate(result.datasets):
                self._configs.append(self._default_config(ds, start + i))
            self._rebuild_dataset_list()
            if self._datasets:
                self.dataset_list.setCurrentRow(start if start < self.dataset_list.count() else 0)
            self.detect_scaling_columns()
            self._replot_pending = False
            if result.errors:
                QMessageBox.warning(self, "Some files could not be loaded", "\n".join(result.errors))
            self.refresh_plot()

        from .workers import run_in_background
        run_in_background(
            self, job, on_success=done,
            on_error=lambda exc: (setattr(self, "_replot_pending", False),
                                  QMessageBox.warning(self, "Data loading failed", str(exc))),
            label=f"Loading {len(paths)} data file(s)…",
        )

    def _default_config(self, ds, index):
        colors = self.renderer.DEFAULT_COLORS
        return DatasetPlotConfig(x=0, y=min(1, ds.column_count - 1), label=ds.name, color=colors[index % len(colors)])

    def _rebuild_dataset_list(self):
        current = self.dataset_list.currentRow()
        self.dataset_list.blockSignals(True); self.dataset_list.clear()
        for cfg in self._configs:
            item = QListWidgetItem(cfg.label); item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if cfg.enabled else Qt.Unchecked); self.dataset_list.addItem(item)
        self.dataset_list.blockSignals(False)
        if self.dataset_list.count(): self.dataset_list.setCurrentRow(min(max(0, current), self.dataset_list.count()-1))

    def _item_changed(self, item):
        i = self.dataset_list.row(item)
        if 0 <= i < len(self._configs):
            self._configs[i].enabled = item.checkState() == Qt.Checked; self._configs[i].label = item.text(); self._schedule_refresh()

    def _select_dataset(self):
        i = self.dataset_list.currentRow()
        if i < 0 or i >= len(self._datasets):
            return
        self._load_style_controls(self._configs[i])
        self._show_stats(self._datasets[i])
        self._populate_data_table(self._datasets[i])
        self._update_scaling_info()

    def _load_style_controls(self, cfg):
        self.line_style.setCurrentText(cfg.line_style); self.marker.setCurrentText(cfg.marker); self.line_width.setValue(cfg.line_width); self.marker_size.setValue(cfg.marker_size); self.current_color = QColor(cfg.color)
        self.color_btn.setStyleSheet(f"background-color: {cfg.color};")

    def _show_stats(self, ds):
        cols = infer_scaling_columns(ds)
        lines = [f"<b>{ds.name}</b>", f"Rows: {ds.row_count}, columns: {ds.column_count}",
                 f"Delimiter: {repr(ds.delimiter)}, header: {'yes' if ds.has_header else 'no'}"]
        for label, ci in (("Resource", cols.x), ("Runtime", cols.y)):
            if 0 <= ci < ds.column_count:
                st = ds.statistics(ci)
                if st["count"]:
                    lines.append(f"{label} <b>{ds.columns[ci]}</b>: n={st['count']}, min={st['min']:.6g}, max={st['max']:.6g}, mean={st['mean']:.6g}, std={st['std']:.6g}")
        self.stats_label.setText("<br>".join(lines))

    def apply_palette(self, name):
        palette = self.renderer.PALETTES[name]
        for i, cfg in enumerate(self._configs): cfg.color = palette[i % len(palette)]
        self._load_style_controls(self._configs[self.dataset_list.currentRow()]) if 0 <= self.dataset_list.currentRow() < len(self._configs) else None
        self.refresh_plot()

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Choose dataset color")
        if color.isValid(): self.current_color = color; self.color_btn.setStyleSheet(f"background-color: {color.name()};"); self.apply_selected_style()

    def apply_selected_style(self):
        i = self.dataset_list.currentRow()
        if i < 0 or i >= len(self._configs): return
        cfg = self._configs[i]; cfg.color = self.current_color.name(); cfg.line_style = self.line_style.currentText(); cfg.marker = self.marker.currentText(); cfg.line_width = self.line_width.value(); cfg.marker_size = self.marker_size.value(); self.refresh_plot()

    def _toggle_grid(self, checked): self.grid_check.setText("Grid: On" if checked else "Grid: Off"); self.refresh_plot()

    def _schedule_refresh(self):
        if self._replot_pending: return
        self._replot_pending = True
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._deferred_refresh)

    def _deferred_refresh(self): self._replot_pending = False; self.refresh_plot()

    def _preset_changed(self, _name):
        # The selected paper mode is exclusive. No prior raw-plot state is
        # consulted when the figure is rebuilt.
        self.canvas.figure.clear()
        self.canvas.mark_theme_dirty()
        self.refresh_plot()

    def _apply_preset_defaults(self):
        # Kept as a compatibility hook for existing callers.
        self._preset_changed(self.preset.currentText())

    def detect_scaling_columns(self):
        if not self._datasets:
            return
        self._update_scaling_info()
        self.refresh_plot()

    def _update_scaling_info(self):
        i = self.dataset_list.currentRow()
        if i < 0 or i >= len(self._datasets):
            self.resource_info.setText("Automatic column detection: resource count + runtime")
            return
        ds = self._datasets[i]
        cols = infer_scaling_columns(ds)
        self.resource_info.setText(f"Detected for {ds.name}: X = {ds.columns[cols.x]!r}, Y = {ds.columns[cols.y]!r}")

    def refresh_plot(self):
        if self._updating:
            return
        if not self._datasets:
            self.canvas.clear()
            return

        # Paper Strong Scaling is an exclusive figure mode. The figure is
        # rebuilt as a two-panel scientific figure on every mode change, so
        # no generic/raw Matplotlib axes or previous plot type can survive.
        result = []
        for i, (ds, cfg) in enumerate(zip(self._datasets, self._configs)):
            if not cfg.enabled:
                continue
            cols = infer_scaling_columns(ds)
            x0 = ds.column_values(cols.x)
            y0 = ds.column_values(cols.y)
            try:
                x, speedup = strong_scaling(x0, y0, metric="Speedup")
                _, efficiency = strong_scaling(x0, y0, metric="Efficiency")
            except ValueError as exc:
                self.stats_label.setText(str(exc))
                continue
            if x.size:
                result.append((x, speedup, efficiency, cfg))

        if not result:
            self.canvas.clear()
            self.stats_label.setText("No valid positive resource/runtime data were found for paper strong scaling.")
            return

        fig = self.canvas.figure
        fig.clear()
        fig.set_size_inches(7.0 / 2.54, 8.8 / 2.54, forward=True)
        ax_speed = fig.add_subplot(2, 1, 1)
        ax_eff = fig.add_subplot(2, 1, 2)

        self.renderer.render_paper_strong_scaling(ax_speed, ax_eff, result)
        self.renderer.apply_paper_style(ax_speed)
        self.renderer.apply_paper_style(ax_eff)
        fig.subplots_adjust(left=0.17, right=0.97, top=0.90, bottom=0.14, hspace=0.10)
        self.canvas.mark_theme_dirty()
        self.canvas.draw_idle()

    def remove_selected(self):
        i = self.dataset_list.currentRow()
        if i < 0: return
        self._datasets.pop(i); self._configs.pop(i); self._rebuild_dataset_list(); self.refresh_plot()

    def clear_datasets(self):
        self._datasets.clear(); self._configs.clear(); self._rebuild_dataset_list(); self.refresh_plot()

    def reload_selected(self):
        i = self.dataset_list.currentRow()
        if i < 0: return
        result = parse_many([self._datasets[i].path], self._selected_delimiter())
        if result.errors: QMessageBox.warning(self, "Reload failed", "\n".join(result.errors)); return
        cfg = self._configs[i]; self._datasets[i] = result.datasets[0]
        cfg.x = min(cfg.x, self._datasets[i].column_count-1); cfg.y = min(cfg.y, self._datasets[i].column_count-1)
        detected = infer_scaling_columns(self._datasets[i]); cfg.x, cfg.y = detected.x, detected.y
        self._update_scaling_info(); self.refresh_plot()

    def export_plot(self):
        if not self._datasets: return
        path, _ = QFileDialog.getSaveFileName(self, "Export figure", "figure.png", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if not path: return
        fig = self.canvas.figure; fig.set_size_inches(self.width.value()/2.54, self.height.value()/2.54)
        export_figure(fig, path, dpi=self.dpi.value(), background=style.THEMES[self.theme]["figure_facecolor"])
