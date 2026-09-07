"""Data Science Workspace tab.

Implements the Import -> Preview -> Profile -> Clean -> Transform ->
Analyze -> Visualize workflow as sub-tabs sharing one
`workspace.session.WorkspaceSession`. All the actual logic (import,
profiling, type detection, pipeline operations, chart recommendation)
lives in the Qt-free `scientific_visualization.workspace` package; this
file only collects widget values into operation parameter dicts and
renders the session's current state back into widgets.

The Clean and Transform sub-tabs share one generic, spec-driven form
builder (`_OperationForm`) rather than one hand-written form per
operation -- see `CLEAN_OPS`/`TRANSFORM_OPS` below to add a new operation
to the UI without writing any new widget-wiring code.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
    QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from ..workspace.io_formats import SUPPORTED_EXTENSIONS, list_excel_sheets
from ..workspace.recommend import suggest_for_dataset, suggest_for_pair
from ..workspace.session import WorkspaceSession
from ..workspace.types import ColumnType

MAX_PREVIEW_ROWS = 200

# --------------------------------------------------------------------------
# Declarative operation specs for the generic pipeline-step form.
# Each field is (kind, param_name, label, extra), where `extra` is a list
# of choices for "choice" fields, a default value for "text"/"int"/
# "float"/"bool" fields, or unused (None) for "column"/"columns" fields.
# --------------------------------------------------------------------------
CLEAN_OPS = {
    "remove_duplicates": ("Remove duplicate rows", [
        ("columns_optional", "subset", "Match on columns (none = all):", None),
        ("choice", "keep", "Keep:", ["first", "last"]),
    ]),
    "drop_rows_with_missing": ("Drop rows with missing values", [
        ("columns_optional", "columns", "Only consider (none = all):", None),
        ("choice", "how", "Drop if:", ["any", "all"]),
    ]),
    "fill_missing": ("Fill missing values", [
        ("columns", "columns", "Columns:", None),
        ("choice", "method", "Method:", ["mean", "median", "mode", "constant", "ffill", "bfill"]),
        ("text", "value", "Constant value (if method = constant):", ""),
    ]),
    "replace_values": ("Replace a value", [
        ("column", "column", "Column:", None),
        ("text", "old_value", "Replace:", ""),
        ("text", "new_value", "With:", ""),
    ]),
    "rename_column": ("Rename column", [
        ("column", "column", "Column:", None),
        ("text", "new_name", "New name:", ""),
    ]),
    "change_dtype": ("Change data type", [
        ("column", "column", "Column:", None),
        ("choice", "dtype", "New type:", ["numeric", "string", "datetime", "category", "boolean"]),
    ]),
    "trim_whitespace": ("Trim whitespace", [
        ("columns_optional", "columns", "Columns (none = all text columns):", None),
    ]),
    "standardize_text": ("Standardize text case", [
        ("columns", "columns", "Columns:", None),
        ("choice", "case", "Case:", ["lower", "upper", "title"]),
    ]),
    "remove_empty_columns": ("Remove empty columns", []),
    "remove_constant_columns": ("Remove constant columns", []),
    "handle_outliers": ("Handle outliers (IQR fence)", [
        ("column", "column", "Column:", None),
        ("choice", "method", "Method:", ["clip", "remove"]),
        ("float", "factor", "IQR factor:", 1.5),
    ]),
    "parse_dates": ("Parse dates", [
        ("column", "column", "Column:", None),
        ("text", "date_format", "Format (blank = auto-detect):", ""),
    ]),
    "extract_date_component": ("Extract date component", [
        ("column", "column", "Date column:", None),
        ("choice", "component", "Component:", ["year", "month", "day", "weekday", "hour", "quarter"]),
    ]),
    "split_column": ("Split column", [
        ("column", "column", "Column:", None),
        ("text", "delimiter", "Delimiter:", " "),
    ]),
    "combine_columns": ("Combine columns", [
        ("columns", "columns", "Columns (in order):", None),
        ("text", "new_name", "New column name:", "combined"),
        ("text", "separator", "Separator:", " "),
    ]),
}

TRANSFORM_OPS = {
    "filter_rows": ("Filter rows", [
        ("column", "column", "Column:", None),
        ("choice", "comparator", "Comparator:",
         ["==", "!=", ">", ">=", "<", "<=", "contains", "not contains", "is null", "is not null"]),
        ("text", "value", "Value:", ""),
    ]),
    "sort_rows": ("Sort rows", [
        ("columns", "columns", "Sort by:", None),
        ("bool", "ascending", "Ascending", True),
    ]),
    "select_columns": ("Keep only these columns", [("columns", "columns", "Columns:", None)]),
    "drop_columns": ("Drop columns", [("columns", "columns", "Columns:", None)]),
    "calculated_column": ("Calculated column", [
        ("text", "new_name", "New column name:", ""),
        ("text", "expression", 'Formula (e.g. "revenue / units"):', ""),
    ]),
    "group_aggregate": ("Group & aggregate", [
        ("columns", "group_by", "Group by:", None),
        ("columns", "agg_columns", "Aggregate column(s):", None),
        ("choice", "agg_func", "Aggregation:", ["sum", "mean", "median", "min", "max", "count", "std", "nunique"]),
    ]),
    "pivot": ("Pivot", [
        ("column", "index", "Row index:", None),
        ("column", "columns", "Columns from:", None),
        ("column", "values", "Values:", None),
        ("choice", "aggfunc", "Aggregation:", ["mean", "sum", "count", "min", "max"]),
    ]),
    "unpivot": ("Unpivot (melt)", [
        ("columns", "id_vars", "Keep as-is (id columns):", None),
        ("columns", "value_vars", "Columns to unpivot:", None),
    ]),
    "normalize": ("Normalize / standardize", [
        ("columns", "columns", "Columns:", None),
        ("choice", "method", "Method:", ["minmax", "zscore"]),
    ]),
    "encode_categorical": ("Encode categorical", [
        ("column", "column", "Column:", None),
        ("choice", "method", "Method:", ["onehot", "label"]),
    ]),
    "bin_column": ("Create bins", [
        ("column", "column", "Column:", None),
        ("int", "bins", "Number of bins:", 5),
    ]),
}


class _OperationForm(QWidget):
    """Generic operation-parameter form driven by an OPS spec dict (see
    CLEAN_OPS/TRANSFORM_OPS above). Rebuilds its fields whenever the
    selected operation or the available columns change.
    """
    def __init__(self, ops: dict, on_add, parent=None):
        super().__init__(parent)
        self.ops = ops
        self.on_add = on_add
        self.columns: list[str] = []
        self._fields: list[tuple] = []  # (kind, param_name, widget)

        layout = QVBoxLayout(self)
        self.op_choice = QComboBox()
        self.op_choice.addItems([label for label, _fields in ops.values()])
        self.op_choice.currentIndexChanged.connect(self._rebuild_fields)
        layout.addWidget(self.op_choice)

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        layout.addWidget(self.form_container)

        add_btn = QPushButton("Add step")
        add_btn.clicked.connect(self._emit_add)
        layout.addWidget(add_btn)
        layout.addStretch(1)
        self._rebuild_fields()

    def set_columns(self, columns: list[str]):
        self.columns = list(columns)
        self._rebuild_fields()

    def _current_op_key(self) -> str:
        return list(self.ops.keys())[self.op_choice.currentIndex()]

    def _rebuild_fields(self):
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self._fields = []
        _label, fields = self.ops[self._current_op_key()]
        for kind, name, label, extra in fields:
            widget = self._make_widget(kind, extra)
            self.form_layout.addRow(label, widget)
            self._fields.append((kind, name, widget))

    def _make_widget(self, kind, extra):
        if kind == "column":
            w = QComboBox(); w.addItems(self.columns); return w
        if kind in ("columns", "columns_optional"):
            w = QListWidget(); w.setSelectionMode(QListWidget.MultiSelection)
            w.addItems(self.columns); w.setMaximumHeight(80); return w
        if kind == "text":
            w = QLineEdit()
            if extra:
                w.setText(str(extra))
            return w
        if kind == "choice":
            w = QComboBox(); w.addItems(extra or []); return w
        if kind == "float":
            w = QDoubleSpinBox(); w.setRange(-1e12, 1e12); w.setDecimals(6)
            w.setValue(float(extra) if extra is not None else 0.0)
            return w
        if kind == "int":
            w = QSpinBox(); w.setRange(-1_000_000, 1_000_000)
            w.setValue(int(extra) if extra is not None else 0)
            return w
        if kind == "bool":
            w = QCheckBox(); w.setChecked(bool(extra)); return w
        raise ValueError(f"Unknown field kind: {kind!r}")

    @staticmethod
    def _read(kind, widget):
        if kind == "column":
            return widget.currentText()
        if kind == "columns":
            return [i.text() for i in widget.selectedItems()]
        if kind == "columns_optional":
            vals = [i.text() for i in widget.selectedItems()]
            return vals or None
        if kind == "text":
            return widget.text()
        if kind == "choice":
            return widget.currentText()
        if kind == "float":
            return widget.value()
        if kind == "int":
            return widget.value()
        if kind == "bool":
            return widget.isChecked()

    @staticmethod
    def _maybe_number(text: str):
        text = text.strip()
        try:
            return float(text) if any(c in text for c in ".eE") else int(text)
        except ValueError:
            return text

    def _emit_add(self):
        op = self._current_op_key()
        raw = {name: self._read(kind, widget) for kind, name, widget in self._fields}
        try:
            params = self._assemble_params(op, raw)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid step", str(exc))
            return
        label, _ = self.ops[op]
        self.on_add(op, params, label)

    def _assemble_params(self, op: str, raw: dict) -> dict:
        """Translate raw widget values into the exact kwargs each backend
        operation expects -- most pass through unchanged, a handful need
        light reshaping (e.g. building the {column: agg} dict
        group_aggregate wants from two separate widgets)."""
        if op == "fill_missing":
            value = raw.get("value", "")
            raw["value"] = self._maybe_number(value) if value != "" else None
        elif op == "replace_values":
            old, new = raw.pop("old_value"), raw.pop("new_value")
            if old == "":
                raise ValueError("Enter a value to replace.")
            raw["mapping"] = {self._maybe_number(old): self._maybe_number(new)}
        elif op == "group_aggregate":
            agg_columns = raw.pop("agg_columns")
            agg_func = raw.pop("agg_func")
            if not agg_columns:
                raise ValueError("Choose at least one column to aggregate.")
            raw["aggregations"] = {c: agg_func for c in agg_columns}
        if op in ("rename_column", "combine_columns") and not raw.get("new_name"):
            raise ValueError("Enter a new column name.")
        if op == "calculated_column" and (not raw.get("new_name") or not raw.get("expression")):
            raise ValueError("Enter both a column name and a formula.")
        return raw


class WorkspaceTab(QWidget):
    #: Emitted with a `data_plotter.model.DatasetTable` when the user asks
    #: to send the current numeric data to the Data Plotter tab. Connected
    #: by MainWindow rather than importing DataPlotterTab here, so this
    #: package doesn't need to know the Data Plotter exists to be useful
    #: on its own (e.g. reused in a lighter-weight window).
    send_to_data_plotter = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = WorkspaceSession()
        self._excel_path: str | None = None
        self._last_numeric_dataset = None

        root = QVBoxLayout(self)
        self.status_label = QLabel("No dataset loaded. Use the Import tab to get started.")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self.steps = QTabWidget()
        root.addWidget(self.steps, 1)

        self.steps.addTab(self._build_import_tab(), "1. Import")
        self.steps.addTab(self._build_preview_profile_tab(), "2\u20133. Preview && Profile")
        self.steps.addTab(self._build_clean_tab(), "4. Clean")
        self.steps.addTab(self._build_transform_tab(), "5. Transform")
        self.steps.addTab(self._build_analyze_tab(), "6. Analyze")
        self.steps.addTab(self._build_visualize_tab(), "7. Visualize")
        self._set_steps_enabled(False)

    # -- shared refresh ---------------------------------------------------

    def _set_steps_enabled(self, enabled: bool):
        for i in range(1, self.steps.count()):
            self.steps.setTabEnabled(i, enabled)

    def _refresh_all(self):
        if not self.session.loaded:
            self._set_steps_enabled(False)
            return
        self._set_steps_enabled(True)
        columns = list(self.session.current.columns)
        self.clean_form.set_columns(columns)
        self.transform_form.set_columns(columns)
        self._populate_preview()
        self._populate_profile()
        self._populate_pipeline_list()
        self._populate_visualize_columns()
        shape = self.session.current.shape
        msg = f"{self.session.name}: {shape[0]} rows \u00d7 {shape[1]} columns"
        if self.session.errors:
            msg += "  \u2014  " + "; ".join(self.session.errors)
        self.status_label.setText(msg)

    # -- 1. Import ----------------------------------------------------------

    def _build_import_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        open_btn = QPushButton("Open dataset\u2026")
        open_btn.clicked.connect(self._open_dataset)
        layout.addWidget(open_btn)

        sheet_row = QHBoxLayout()
        sheet_row.addWidget(QLabel("Excel sheet:"))
        self.sheet_choice = QComboBox()
        self.sheet_choice.setEnabled(False)
        sheet_row.addWidget(self.sheet_choice, 1)
        load_sheet_btn = QPushButton("Load sheet")
        load_sheet_btn.clicked.connect(self._load_selected_sheet)
        sheet_row.addWidget(load_sheet_btn)
        layout.addLayout(sheet_row)

        formats = QLabel("Supported formats: " + ", ".join(SUPPORTED_EXTENSIONS))
        formats.setWordWrap(True)
        layout.addWidget(formats)
        layout.addStretch(1)
        return w

    def _open_dataset(self):
        filt = "Data files (*" + " *".join(SUPPORTED_EXTENSIONS) + ");;All files (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Open dataset", "", filt)
        if not path:
            return
        if path.lower().endswith((".xlsx", ".xls")):
            self._excel_path = path
            try:
                sheets = list_excel_sheets(path)
            except Exception as exc:
                QMessageBox.critical(self, "Could not read workbook", str(exc))
                return
            self.sheet_choice.clear()
            self.sheet_choice.addItems(sheets)
            self.sheet_choice.setEnabled(True)
            self._load_selected_sheet()
        else:
            self._excel_path = None
            self.sheet_choice.setEnabled(False)
            self._do_load(path)

    def _load_selected_sheet(self):
        if not self._excel_path:
            return
        self._do_load(self._excel_path, sheet_name=self.sheet_choice.currentText())

    def _do_load(self, path, sheet_name=0):
        try:
            self.session.load(path, sheet_name=sheet_name)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load dataset", str(exc))
            return
        self._refresh_all()
        self.steps.setCurrentIndex(1)

    # -- 2-3. Preview & Profile -----------------------------------------

    def _build_preview_profile_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        splitter = QSplitter(Qt.Vertical)

        preview_box = QGroupBox("Preview (first 200 rows of the current, pipeline-applied data)")
        pv = QVBoxLayout(preview_box)
        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pv.addWidget(self.preview_table)
        splitter.addWidget(preview_box)

        profile_box = QGroupBox("Column profile")
        pf = QVBoxLayout(profile_box)
        self.profile_table = QTableWidget()
        self.profile_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pf.addWidget(self.profile_table)
        self.profile_summary = QLabel("")
        pf.addWidget(self.profile_summary)
        splitter.addWidget(profile_box)

        layout.addWidget(splitter, 1)
        return w

    def _populate_preview(self):
        df = self.session.current.head(MAX_PREVIEW_ROWS)
        table = self.preview_table
        table.setRowCount(len(df))
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(list(df.columns))
        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                value = df.iloc[r, c]
                text = "" if pd.isna(value) else str(value)
                table.setItem(r, c, QTableWidgetItem(text))

    def _populate_profile(self):
        profile = self.session.profile()
        table = self.profile_table
        headers = ["Column", "Detected type", "Storage dtype", "Missing", "Missing %",
                   "Unique", "Min", "Max", "Mean", "Std", "Outliers"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(profile.columns))
        for r, col in enumerate(profile.columns):
            values = [
                col.name, col.detected_type.value, col.dtype, str(col.missing),
                f"{col.missing_pct:.1f}%", str(col.unique),
                "" if col.numeric_min is None else f"{col.numeric_min:.4g}",
                "" if col.numeric_max is None else f"{col.numeric_max:.4g}",
                "" if col.numeric_mean is None else f"{col.numeric_mean:.4g}",
                "" if col.numeric_std is None else f"{col.numeric_std:.4g}",
                "" if col.outlier_count is None else str(col.outlier_count),
            ]
            for c, text in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(text))
        self.profile_summary.setText(
            f"{profile.row_count} rows \u00d7 {profile.column_count} columns \u2022 "
            f"{profile.duplicate_rows} duplicate row(s) \u2022 "
            f"{profile.total_missing()} missing value(s) total \u2022 "
            f"~{profile.memory_bytes / 1024:.1f} KB in memory"
        )

    # -- 4/5. Clean & Transform (shared pipeline machinery) ---------------

    def _build_pipeline_tab(self, ops: dict) -> tuple[QWidget, _OperationForm]:
        w = QWidget()
        layout = QHBoxLayout(w)
        form = _OperationForm(ops, self._add_pipeline_step)
        layout.addWidget(form, 1)

        pipeline_box = QGroupBox("Pipeline (applies to both Clean and Transform, in this order)")
        pv = QVBoxLayout(pipeline_box)
        self.pipeline_list = getattr(self, "pipeline_list", QListWidget())
        pv.addWidget(self.pipeline_list, 1)
        btn_row = QHBoxLayout()
        up_btn = QPushButton("\u2191 Move up"); up_btn.clicked.connect(lambda: self._move_step(-1))
        down_btn = QPushButton("\u2193 Move down"); down_btn.clicked.connect(lambda: self._move_step(1))
        toggle_btn = QPushButton("Enable/disable"); toggle_btn.clicked.connect(self._toggle_step)
        remove_btn = QPushButton("Remove"); remove_btn.clicked.connect(self._remove_step)
        undo_btn = QPushButton("Undo last"); undo_btn.clicked.connect(self._undo_step)
        for b in (up_btn, down_btn, toggle_btn, remove_btn, undo_btn):
            btn_row.addWidget(b)
        pv.addLayout(btn_row)
        layout.addWidget(pipeline_box, 1)
        return w, form

    def _build_clean_tab(self) -> QWidget:
        w, self.clean_form = self._build_pipeline_tab(CLEAN_OPS)
        return w

    def _build_transform_tab(self) -> QWidget:
        w, self.transform_form = self._build_pipeline_tab(TRANSFORM_OPS)
        return w

    def _add_pipeline_step(self, op, params, label):
        self.session.add_step(op, params, note=label)
        self._refresh_all()
        if self.session.errors:
            QMessageBox.warning(self, "Step reported a problem", self.session.errors[-1])

    def _populate_pipeline_list(self):
        self.pipeline_list.clear()
        for step in self.session.pipeline:
            prefix = "\u2713" if step.enabled else "\u2717"
            self.pipeline_list.addItem(f"{prefix} {step.note or step.op}")

    def _selected_step_index(self) -> int:
        return self.pipeline_list.currentRow()

    def _move_step(self, delta: int):
        i = self._selected_step_index()
        if i < 0:
            return
        self.session.move_step(i, i + delta)
        self._refresh_all()
        self.pipeline_list.setCurrentRow(max(0, min(i + delta, self.pipeline_list.count() - 1)))

    def _toggle_step(self):
        i = self._selected_step_index()
        if i >= 0:
            self.session.toggle_step(i)
            self._refresh_all()

    def _remove_step(self):
        i = self._selected_step_index()
        if i >= 0:
            self.session.remove_step(i)
            self._refresh_all()

    def _undo_step(self):
        self.session.undo()
        self._refresh_all()

    # -- 6. Analyze --------------------------------------------------------

    def _build_analyze_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        btn_row = QHBoxLayout()
        describe_btn = QPushButton("Descriptive statistics"); describe_btn.clicked.connect(self._analyze_describe)
        corr_btn = QPushButton("Correlation matrix"); corr_btn.clicked.connect(self._analyze_correlation)
        groupby_btn = QPushButton("Group-by summary"); groupby_btn.clicked.connect(self._analyze_groupby)
        crosstab_btn = QPushButton("Cross-tabulation"); crosstab_btn.clicked.connect(self._analyze_crosstab)
        for b in (describe_btn, corr_btn, groupby_btn, crosstab_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        picker_row = QHBoxLayout()
        picker_row.addWidget(QLabel("Column A:"))
        self.analyze_col_a = QComboBox(); picker_row.addWidget(self.analyze_col_a)
        picker_row.addWidget(QLabel("Column B (for group-by/cross-tab):"))
        self.analyze_col_b = QComboBox(); picker_row.addWidget(self.analyze_col_b)
        layout.addLayout(picker_row)

        self.analyze_output = QTableWidget()
        self.analyze_output.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.analyze_output, 1)
        return w

    def _show_dataframe_result(self, df: pd.DataFrame):
        table = self.analyze_output
        df = df.reset_index() if df.index.name or not isinstance(df.index, pd.RangeIndex) else df
        table.setRowCount(len(df))
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for r in range(len(df)):
            for c in range(df.shape[1]):
                value = df.iloc[r, c]
                text = "" if pd.isna(value) else (f"{value:.6g}" if isinstance(value, float) else str(value))
                table.setItem(r, c, QTableWidgetItem(text))

    def _analyze_describe(self):
        if not self.session.loaded:
            return
        self._show_dataframe_result(self.session.current.describe(include="all").transpose())

    def _analyze_correlation(self):
        if not self.session.loaded:
            return
        numeric = self.session.current.select_dtypes(include="number")
        if numeric.shape[1] < 2:
            QMessageBox.information(self, "Not enough numeric columns", "Need at least 2 numeric columns for a correlation matrix.")
            return
        self._show_dataframe_result(numeric.corr())

    def _analyze_groupby(self):
        if not self.session.loaded:
            return
        a = self.analyze_col_a.currentText()
        if not a:
            return
        numeric_cols = [c for c in self.session.current.select_dtypes(include="number").columns if c != a]
        if not numeric_cols:
            QMessageBox.information(self, "No numeric columns", "Need at least one numeric column to summarize.")
            return
        result = self.session.current.groupby(a, dropna=False, observed=True)[numeric_cols].agg(["mean", "count"])
        result.columns = ["_".join(map(str, c)) for c in result.columns]
        self._show_dataframe_result(result.reset_index())

    def _analyze_crosstab(self):
        if not self.session.loaded:
            return
        a, b = self.analyze_col_a.currentText(), self.analyze_col_b.currentText()
        if not a or not b or a == b:
            QMessageBox.information(self, "Pick two columns", "Choose two different columns for a cross-tabulation.")
            return
        result = pd.crosstab(self.session.current[a], self.session.current[b])
        self._show_dataframe_result(result.reset_index())

    # -- 7. Visualize -------------------------------------------------------

    def _build_visualize_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel(
            "Pick columns for a targeted suggestion, or leave blank for a broad scan of the dataset."
        ))
        picker_row = QHBoxLayout()
        picker_row.addWidget(QLabel("X:"))
        self.viz_col_x = QComboBox(); self.viz_col_x.addItem("")
        picker_row.addWidget(self.viz_col_x)
        picker_row.addWidget(QLabel("Y (optional):"))
        self.viz_col_y = QComboBox(); self.viz_col_y.addItem("")
        picker_row.addWidget(self.viz_col_y)
        suggest_btn = QPushButton("Suggest charts"); suggest_btn.clicked.connect(self._suggest_charts)
        picker_row.addWidget(suggest_btn)
        layout.addLayout(picker_row)

        self.viz_suggestions = QListWidget()
        layout.addWidget(self.viz_suggestions, 1)

        open_btn = QPushButton("Open numeric columns in Data Plotter \u2192")
        open_btn.setToolTip(
            "Sends every numeric column of the current (pipeline-applied) dataset to the Data "
            "Plotter tab, which has the app's full charting toolkit: curve fits, change "
            "annotations, paper scaling figures, and more."
        )
        open_btn.clicked.connect(self._open_in_data_plotter)
        layout.addWidget(open_btn)
        return w

    def _populate_visualize_columns(self):
        columns = list(self.session.current.columns)
        for combo in (self.analyze_col_a, self.analyze_col_b, self.viz_col_x, self.viz_col_y):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            if combo in (self.viz_col_x, self.viz_col_y):
                combo.addItem("")
            combo.addItems(columns)
            if current in columns:
                combo.setCurrentText(current)
            combo.blockSignals(False)

    def _suggest_charts(self):
        if not self.session.loaded:
            return
        x, y = self.viz_col_x.currentText(), self.viz_col_y.currentText()
        if x:
            suggestions = suggest_for_pair(self.session.current, x, y or None)
        else:
            suggestions = suggest_for_dataset(self.session.current)
        self.viz_suggestions.clear()
        if not suggestions:
            self.viz_suggestions.addItem("No specific suggestion -- try different columns.")
            return
        for s in suggestions:
            cols = f" ({s.x}" + (f" vs {s.y})" if s.y else ")") if s.x else ""
            self.viz_suggestions.addItem(f"{s.chart_type}{cols}: {s.reason}")

    def _open_in_data_plotter(self):
        if not self.session.loaded:
            return
        try:
            dataset = self.session.to_numeric_dataset()
        except ValueError as exc:
            QMessageBox.information(self, "No numeric data", str(exc))
            return
        self._last_numeric_dataset = dataset
        self.send_to_data_plotter.emit(dataset)
