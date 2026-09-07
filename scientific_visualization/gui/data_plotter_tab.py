from __future__ import annotations

from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import numpy as np

from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from .. import style
from ..data_plotter.batch import parse_many
from ..data_plotter.figure_modes import (
    FIGURE_MODES, SINGLE_DATASET_MODES, SINGLE_PANEL_TRANSFORMS, FigureOptions, render_figure,
)
from ..data_plotter.fitting import FIT_KINDS
from ..data_plotter.scaling import infer_scaling_columns
from ..data_plotter.model import DatasetPlotConfig, DatasetTable
from ..data_plotter.parser import Delimiter
from ..data_plotter.renderer import DataPlotRenderer
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
        self._has_plotted_once = False
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

        paper_box = QGroupBox("Figure")
        pfm = QFormLayout(paper_box)
        self.preset = QComboBox()
        self.preset.addItems(list(FIGURE_MODES))
        self.preset.currentTextChanged.connect(self._preset_changed)
        self.figure_mode_info = QLabel("")
        self.figure_mode_info.setWordWrap(True)
        pfm.addRow("Figure mode:", self.preset)
        pfm.addRow(self.figure_mode_info)

        self.x_column = QComboBox()
        self.y_column = QComboBox()
        self.x_column.currentIndexChanged.connect(self._column_choice_changed)
        self.y_column.currentIndexChanged.connect(self._column_choice_changed)
        pfm.addRow("X column:", self.x_column)
        pfm.addRow("Y column:", self.y_column)

        self.extra_y_columns = QListWidget()
        self.extra_y_columns.setSelectionMode(QListWidget.MultiSelection)
        self.extra_y_columns.setToolTip(
            "Line / Scatter mode only. Plot these additional columns from the same file as "
            "their own lines against the same X column -- e.g. a CSV with \"year, price, salary\" "
            "columns can show both price and salary on one chart without splitting files."
        )
        self.extra_y_columns.setMaximumHeight(90)
        self.extra_y_columns.itemSelectionChanged.connect(self._extra_y_columns_changed)
        pfm.addRow("Additional Y columns\n(same file):", self.extra_y_columns)

        self.xy_plot_type = QComboBox()
        self.xy_plot_type.addItems(["Line", "Scatter", "Line + Scatter"])
        self.xy_plot_type.currentTextChanged.connect(self._mark_configured_and_refresh)
        pfm.addRow("Line/Scatter style:", self.xy_plot_type)

        self.hist_bins = QSpinBox(); self.hist_bins.setRange(2, 500); self.hist_bins.setValue(30)
        self.hist_bins.valueChanged.connect(self._mark_configured_and_refresh)
        self.hist_normalization = QComboBox(); self.hist_normalization.addItems(["Count", "Density", "Probability"])
        self.hist_normalization.currentTextChanged.connect(self._mark_configured_and_refresh)
        pfm.addRow("Histogram bins:", self.hist_bins)
        pfm.addRow("Histogram scale:", self.hist_normalization)

        self.workload_factor = QDoubleSpinBox()
        self.workload_factor.setRange(1e-6, 1e9); self.workload_factor.setDecimals(6); self.workload_factor.setValue(1.0)
        self.workload_factor.setToolTip(
            "Relative problem size for the selected dataset (e.g. grid cells, particles). "
            "Weak scaling divides runtime by this before comparing datasets, since problem "
            "size cannot be inferred from a filename."
        )
        self.workload_factor.valueChanged.connect(self._workload_factor_changed)
        pfm.addRow("Workload factor (selected):", self.workload_factor)

        self.panels = QComboBox()
        self.panels.addItems(["Double", "Single"])
        self.panels.setToolTip(
            "Paper scaling figures only. Double: two stacked panels (metric + efficiency). "
            "Single: one panel with efficiency on a secondary right-hand axis."
        )
        self.panels.currentTextChanged.connect(self._mark_configured_and_refresh)
        pfm.addRow("Panels:", self.panels)

        self.legend_loc = QComboBox()
        self.legend_loc.addItems(list(self.renderer.LEGEND_LOCATIONS))
        self.legend_loc.setToolTip(
            "Starting legend position. Every legend can also be dragged to any spot "
            "with the mouse directly on the plot, regardless of this setting."
        )
        self.legend_loc.currentTextChanged.connect(self._mark_configured_and_refresh)
        pfm.addRow("Legend position:", self.legend_loc)

        self.plot_btn = QPushButton("Plot \u25b6")
        self.plot_btn.setToolTip("Render the current selection. Nothing is plotted automatically until you do this once.")
        self.plot_btn.clicked.connect(self._mark_configured_and_refresh)
        pfm.addRow(self.plot_btn)

        self.control_layout.addWidget(paper_box)

        self.fit_box = QGroupBox("Curve fit and annotations (Line / Scatter mode)")
        fit_form = QFormLayout(self.fit_box)
        self.fit_enabled = QCheckBox("Show fit")
        self.fit_enabled.toggled.connect(self._mark_configured_and_refresh)
        fit_form.addRow(self.fit_enabled)
        self.fit_kind = QComboBox(); self.fit_kind.addItems(list(FIT_KINDS))
        self.fit_kind.currentTextChanged.connect(self._update_fit_controls)
        self.fit_kind.currentTextChanged.connect(self._mark_configured_and_refresh)
        fit_form.addRow("Fit type:", self.fit_kind)
        self.fit_order = QSpinBox(); self.fit_order.setRange(1, 10); self.fit_order.setValue(2)
        self.fit_order.valueChanged.connect(self._mark_configured_and_refresh)
        fit_form.addRow("Polynomial order:", self.fit_order)
        self.fit_expression = QLineEdit()
        self.fit_expression.setPlaceholderText("e.g. a*exp(b*x)+c  (needs scipy)")
        self.fit_expression.editingFinished.connect(self._mark_configured_and_refresh)
        fit_form.addRow("Custom formula:", self.fit_expression)
        self._update_fit_controls(self.fit_kind.currentText())
        self.control_layout.addWidget(self.fit_box)

        self.annotate_changes = QCheckBox("Annotate first \u2192 last change (\u0394 and %) per series")
        self.annotate_changes.setToolTip(
            "Line / Scatter mode only. For each series, draws a callout showing the absolute and "
            "percent change from its first to last data point, plus light reference lines at the "
            "start/end -- the classic \"how much did this grow\" trend-chart annotation."
        )
        self.annotate_changes.toggled.connect(self._mark_configured_and_refresh)
        self.fit_box.layout().addRow(self.annotate_changes)

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

        edit_box = QGroupBox("Edit data (selected dataset)")
        ef2 = QFormLayout(edit_box)
        row_buttons = QHBoxLayout()
        add_row_btn = QPushButton("Add row"); add_row_btn.clicked.connect(self._add_row)
        remove_rows_btn = QPushButton("Remove selected rows"); remove_rows_btn.clicked.connect(self._remove_selected_rows)
        row_buttons.addWidget(add_row_btn); row_buttons.addWidget(remove_rows_btn)
        ef2.addRow(row_buttons)

        self.new_column_name = QLineEdit(); self.new_column_name.setPlaceholderText("New column name")
        self.new_column_expr = QLineEdit(); self.new_column_expr.setPlaceholderText('Formula, e.g. "c / b" or "log(a)"')
        add_column_btn = QPushButton("Add computed column"); add_column_btn.clicked.connect(self._add_computed_column)
        ef2.addRow(self.new_column_name)
        ef2.addRow(self.new_column_expr)
        ef2.addRow(add_column_btn)

        self.remove_column_choice = QComboBox()
        remove_column_btn = QPushButton("Remove column"); remove_column_btn.clicked.connect(self._remove_column)
        col_row = QHBoxLayout(); col_row.addWidget(self.remove_column_choice); col_row.addWidget(remove_column_btn)
        ef2.addRow(col_row)

        self.sort_column_choice = QComboBox()
        self.sort_descending = QCheckBox("Descending")
        sort_btn = QPushButton("Sort by column"); sort_btn.clicked.connect(self._sort_by_column)
        sort_row = QHBoxLayout(); sort_row.addWidget(self.sort_column_choice); sort_row.addWidget(self.sort_descending); sort_row.addWidget(sort_btn)
        ef2.addRow(sort_row)
        self.control_layout.addWidget(edit_box)

        exp = QGroupBox("Export")
        ef = QFormLayout(exp)
        self.dpi = QSpinBox(); self.dpi.setRange(72, 1200); self.dpi.setValue(300)
        self.width = QDoubleSpinBox(); self.width.setRange(1, 30); self.width.setValue(8.5); self.width.setSuffix(" cm")
        self.height = QDoubleSpinBox(); self.height.setRange(1, 30); self.height.setValue(10.5); self.height.setSuffix(" cm")
        export = QPushButton("Export PNG/SVG/PDF…"); export.clicked.connect(self.export_plot)
        ef.addRow("DPI:", self.dpi); ef.addRow("Width:", self.width); ef.addRow("Height:", self.height); ef.addRow(export)
        self.control_layout.addWidget(exp)

        self._update_mode_controls(self.preset.currentText())

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
            # Loading data never auto-selects a figure for the user -- the
            # canvas shows a placeholder until they explicitly choose a
            # figure mode / column / click Plot (see _mark_configured_and_refresh).
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

    def add_dataset(self, ds: DatasetTable):
        """Add an already-constructed DatasetTable directly, bypassing file
        parsing -- the hand-off point for other tabs (e.g. the Data
        Workspace's "Open in Data Plotter") that already hold data in
        memory rather than on disk.
        """
        index = len(self._datasets)
        self._datasets.append(ds)
        self._configs.append(self._default_config(ds, index))
        self._rebuild_dataset_list()
        self.dataset_list.setCurrentRow(index)
        self.detect_scaling_columns()

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
        self._populate_column_combos(self._datasets[i], self._configs[i])
        self._update_scaling_info()

    def _populate_column_combos(self, ds, cfg):
        """Sync the X/Y column pickers to the selected dataset's own columns
        and its current (auto-detected or user-set) column choice."""
        for combo, index in ((self.x_column, cfg.x), (self.y_column, cfg.y)):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(ds.columns)
            if 0 <= index < combo.count():
                combo.setCurrentIndex(index)
            combo.blockSignals(False)
        for combo in (self.remove_column_choice, self.sort_column_choice):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(ds.columns)
            combo.blockSignals(False)
        self.extra_y_columns.blockSignals(True)
        self.extra_y_columns.clear()
        self.extra_y_columns.addItems(ds.columns)
        for i in range(self.extra_y_columns.count()):
            self.extra_y_columns.item(i).setSelected(i in cfg.extra_y)
        self.extra_y_columns.blockSignals(False)
        self.workload_factor.blockSignals(True)
        self.workload_factor.setValue(cfg.workload_factor)
        self.workload_factor.blockSignals(False)

    def _extra_y_columns_changed(self):
        i = self.dataset_list.currentRow()
        if i < 0 or i >= len(self._configs):
            return
        self._configs[i].extra_y = [self.extra_y_columns.row(item) for item in self.extra_y_columns.selectedItems()]
        self._mark_configured_and_refresh()

    def _column_choice_changed(self, _index):
        i = self.dataset_list.currentRow()
        if i < 0 or i >= len(self._configs):
            return
        cfg = self._configs[i]
        if self.x_column.currentIndex() >= 0:
            cfg.x = self.x_column.currentIndex()
        if self.y_column.currentIndex() >= 0:
            cfg.y = self.y_column.currentIndex()
        self._mark_configured_and_refresh()

    def _workload_factor_changed(self, value):
        i = self.dataset_list.currentRow()
        if 0 <= i < len(self._configs):
            self._configs[i].workload_factor = value
            self._mark_configured_and_refresh()

    def _current_dataset(self):
        i = self.dataset_list.currentRow()
        if 0 <= i < len(self._datasets):
            return i, self._datasets[i]
        return -1, None

    def _after_edit(self, ds):
        """Common bookkeeping after any in-memory edit: refresh the table
        preview, the column pickers (names/count may have changed), the
        stats panel, and the plot."""
        self._populate_data_table(ds)
        i, _ = self._current_dataset()
        if i >= 0:
            self._populate_column_combos(ds, self._configs[i])
        self._show_stats(ds)
        self._mark_configured_and_refresh()

    def _add_row(self):
        i, ds = self._current_dataset()
        if ds is None:
            return
        ds.add_row()
        self._after_edit(ds)

    def _remove_selected_rows(self):
        i, ds = self._current_dataset()
        if ds is None:
            return
        rows = sorted({index.row() for index in self.data_table.selectedIndexes()})
        if not rows:
            QMessageBox.information(self, "No rows selected", "Select one or more rows in the table first.")
            return
        try:
            ds.remove_rows(rows)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not remove rows", str(exc))
            return
        self._after_edit(ds)

    def _add_computed_column(self):
        i, ds = self._current_dataset()
        if ds is None:
            return
        name = self.new_column_name.text().strip()
        expr = self.new_column_expr.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Enter a name for the new column.")
            return
        try:
            ds.add_computed_column(name, expr)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not add column", str(exc))
            return
        self.new_column_name.clear()
        self.new_column_expr.clear()
        self._after_edit(ds)

    def _remove_column(self):
        i, ds = self._current_dataset()
        if ds is None:
            return
        idx = self.remove_column_choice.currentIndex()
        if idx < 0:
            return
        try:
            ds.remove_column(idx)
        except (ValueError, IndexError) as exc:
            QMessageBox.warning(self, "Could not remove column", str(exc))
            return
        cfg = self._configs[i]
        cfg.x = min(cfg.x, ds.column_count - 1)
        cfg.y = min(cfg.y, ds.column_count - 1)
        self._after_edit(ds)

    def _sort_by_column(self):
        i, ds = self._current_dataset()
        if ds is None:
            return
        idx = self.sort_column_choice.currentIndex()
        if idx < 0:
            return
        ds.sort_by(idx, ascending=not self.sort_descending.isChecked())
        self._after_edit(ds)

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

    def _mark_configured_and_refresh(self):
        """Call this from any control that represents 'the user has chosen
        what to plot' (figure mode, X/Y column, plot style, panels, legend
        position, the Plot button, ...). Nothing renders automatically just
        because data was loaded -- only once the user has made at least one
        such choice does refresh_plot() actually draw a figure instead of
        the idle placeholder.
        """
        self._has_plotted_once = True
        self._schedule_refresh()

    _MODE_DESCRIPTIONS = {
        "Line / Scatter": "Raw X vs Y for every enabled dataset, using each dataset's own column choice.",
        "Paper Strong Scaling": "Two synchronized panels showing speedup and parallel efficiency, "
                                 "with GPUs on the top axis, nodes on the bottom axis, and ideal scaling references.",
        "Paper Weak Scaling": "Two panels with the same dual GPU/Node axis layout as Paper Strong Scaling: "
                               "workload-normalized runtime (top, ideal = flat line at 1.0) and efficiency "
                               "(bottom). Set each dataset's relative problem size below (Workload factor) first.",
        "Normalize Y to first": "Y divided by its first finite value, so every dataset starts at 1.0.",
        "Strong scaling: speedup": "T(P0)/T(P) using the smallest positive X as the baseline P0.",
        "Strong scaling: efficiency": "Speedup divided by (P/P0), i.e. parallel efficiency alone.",
        "Histogram": "Distribution of the Y column for each enabled dataset.",
        "Empirical CDF": "Cumulative distribution of the Y column for each enabled dataset.",
        "Bar summary": "Last finite Y value per dataset, as a compact bar comparison.",
        "Box plot": "Box-and-whisker summary of the Y column per dataset.",
        "Violin plot": "Kernel-density distribution of the Y column per dataset.",
        "Mean \u00b1 1\u03c3 errorbar": "Mean and standard deviation of Y at each distinct X value.",
        "Hexbin density": "2D point density of X vs Y, useful for large point clouds.",
        "Correlation heatmap": "Pearson correlation matrix across all numeric columns of the selected dataset only.",
    }

    def _update_mode_controls(self, mode):
        self.figure_mode_info.setText(self._MODE_DESCRIPTIONS.get(mode, ""))
        self.xy_plot_type.setEnabled(mode == "Line / Scatter" or mode in SINGLE_PANEL_TRANSFORMS)
        self.hist_bins.setEnabled(mode == "Histogram")
        self.hist_normalization.setEnabled(mode == "Histogram")
        is_scaling_paper = mode in ("Paper Strong Scaling", "Paper Weak Scaling")
        self.workload_factor.setEnabled(mode == "Paper Weak Scaling")
        self.panels.setEnabled(is_scaling_paper)
        uses_columns = mode not in SINGLE_DATASET_MODES
        self.x_column.setEnabled(uses_columns)
        self.y_column.setEnabled(uses_columns)
        self.fit_box.setEnabled(mode == "Line / Scatter")
        self.extra_y_columns.setEnabled(mode == "Line / Scatter")

    def _update_fit_controls(self, kind):
        self.fit_order.setEnabled(kind == "Polynomial")
        self.fit_expression.setEnabled(kind == "Custom")

    def _preset_changed(self, mode):
        self._update_mode_controls(mode)
        self._mark_configured_and_refresh()

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
        if not self._has_plotted_once:
            self._show_idle_placeholder()
            return

        mode = self.preset.currentText()
        options = FigureOptions(
            plot_type=self.xy_plot_type.currentText(),
            bins=self.hist_bins.value(),
            histogram_normalization=self.hist_normalization.currentText(),
            selected_dataset_index=max(0, self.dataset_list.currentRow()),
            panels=self.panels.currentText(),
            legend_loc=self.legend_loc.currentText(),
            fit_enabled=self.fit_enabled.isChecked(),
            fit_kind=self.fit_kind.currentText(),
            fit_order=self.fit_order.value(),
            fit_expression=self.fit_expression.text(),
            annotate_changes=self.annotate_changes.isChecked(),
        )
        fig = self.canvas.figure
        # No `set_size_inches(..., forward=True)` here: the canvas widget's
        # on-screen size belongs to this tab's Qt layout, and previously
        # resizing the Figure directly for the "paper" modes fought that
        # layout on the next repaint, producing corrupted/ghosted renders.
        # A fixed publication aspect ratio remains available at export time
        # via the Export panel's width/height/DPI fields.
        message = render_figure(fig, self.renderer, mode, self._datasets, self._configs, options)
        if message:
            self.stats_label.setText(message)
        self.canvas.mark_theme_dirty()
        self.canvas.draw_idle()

    def _show_idle_placeholder(self):
        """Shown after loading data but before the user has chosen what to
        plot. Nothing is auto-plotted -- the default figure mode is only a
        starting point in the dropdown, not an implicit choice."""
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(1, 1, 1)
        ax.axis("off")
        ax.text(0.5, 0.5,
                f"{len(self._datasets)} dataset(s) loaded.\n\n"
                "Choose a figure mode, X/Y columns, etc. above,\n"
                "or click \u201cPlot \u25b6\u201d, to render your data.",
                ha="center", va="center", fontsize=11, color="#666666", transform=ax.transAxes)
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
        fig = self.canvas.figure
        original_size = fig.get_size_inches().copy()
        try:
            # forward=False: only the raster/vector output written by
            # export_figure() below should use these dimensions. Forwarding
            # would resize the live on-screen canvas widget outside of Qt's
            # own layout management, which is what previously corrupted the
            # interactive plot (see refresh_plot).
            fig.set_size_inches(self.width.value() / 2.54, self.height.value() / 2.54, forward=False)
            export_figure(fig, path, dpi=self.dpi.value(), background=style.THEMES[self.theme]["figure_facecolor"])
        finally:
            fig.set_size_inches(*original_size, forward=False)
            self.canvas.draw_idle()
