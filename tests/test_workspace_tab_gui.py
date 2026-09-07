import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pandas as pd
import pytest
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from scientific_visualization.gui.workspace_tab import WorkspaceTab, CLEAN_OPS, TRANSFORM_OPS


@pytest.fixture
def sample_csv(tmp_path):
    p = tmp_path / "sales.csv"
    p.write_text(
        "region,product,revenue,units,date\n"
        "East,A,100.5,10,2020-01-01\n"
        "East,B,200.0,20,2020-02-01\n"
        "West,A,,15,2020-03-01\n"
        "West,B,80.0,8,2020-04-01\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def tab_with_data(sample_csv):
    tab = WorkspaceTab()
    tab._do_load(str(sample_csv))
    _app.processEvents()
    return tab


def _set_field(form, name, value_setter):
    for kind, field_name, widget in form._fields:
        if field_name == name:
            value_setter(widget)
            return
    raise AssertionError(f"field {name!r} not found")


def test_loading_populates_preview_and_profile(tab_with_data):
    tab = tab_with_data
    assert tab.session.loaded
    assert tab.preview_table.rowCount() == 4
    assert tab.preview_table.columnCount() == 5
    assert tab.profile_table.rowCount() == 5
    assert "duplicate" in tab.profile_summary.text()


def test_steps_disabled_before_load():
    tab = WorkspaceTab()
    for i in range(1, tab.steps.count()):
        assert tab.steps.isTabEnabled(i) is False


def test_steps_enabled_after_load(tab_with_data):
    tab = tab_with_data
    for i in range(1, tab.steps.count()):
        assert tab.steps.isTabEnabled(i) is True


def test_unsupported_extension_shows_error(tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    p = tmp_path / "bad.xyz"
    p.write_text("nope")
    tab = WorkspaceTab()
    warned = {}
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: warned.setdefault("called", True)))
    tab._do_load(str(p))
    assert warned.get("called") is True
    assert not tab.session.loaded


def test_clean_step_fill_missing_updates_pipeline_and_preview(tab_with_data):
    tab = tab_with_data
    op_index = list(CLEAN_OPS.keys()).index("fill_missing")
    tab.clean_form.op_choice.setCurrentIndex(op_index)
    _app.processEvents()
    _set_field(tab.clean_form, "columns", lambda w: w.item(2).setSelected(True))  # revenue
    _set_field(tab.clean_form, "method", lambda w: w.setCurrentText("mean"))
    tab.clean_form._emit_add()
    _app.processEvents()

    assert len(tab.session.pipeline) == 1
    assert tab.session.errors == []
    assert not tab.session.current["revenue"].isna().any()
    assert tab.pipeline_list.count() == 1


def test_transform_step_calculated_column(tab_with_data):
    tab = tab_with_data
    op_index = list(TRANSFORM_OPS.keys()).index("calculated_column")
    tab.transform_form.op_choice.setCurrentIndex(op_index)
    _app.processEvents()
    _set_field(tab.transform_form, "new_name", lambda w: w.setText("price"))
    _set_field(tab.transform_form, "expression", lambda w: w.setText("revenue / units"))
    tab.transform_form._emit_add()
    _app.processEvents()

    assert "price" in tab.session.current.columns
    assert tab.session.errors == []


def test_transform_step_invalid_expression_reports_warning(tab_with_data, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    tab = tab_with_data
    op_index = list(TRANSFORM_OPS.keys()).index("calculated_column")
    tab.transform_form.op_choice.setCurrentIndex(op_index)
    _app.processEvents()
    _set_field(tab.transform_form, "new_name", lambda w: w.setText("bad"))
    _set_field(tab.transform_form, "expression", lambda w: w.setText("__import__('os')"))
    warned = {}
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: warned.setdefault("called", True)))
    tab.transform_form._emit_add()
    _app.processEvents()
    assert warned.get("called") is True


def test_pipeline_undo_move_toggle_remove(tab_with_data):
    tab = tab_with_data
    tab.session.add_step("trim_whitespace", {"columns": ["region"]}, note="trim")
    tab.session.add_step("remove_constant_columns", {}, note="const")
    tab._refresh_all()
    assert tab.pipeline_list.count() == 2

    tab.pipeline_list.setCurrentRow(1)
    tab._move_step(-1)
    assert [s.op for s in tab.session.pipeline] == ["remove_constant_columns", "trim_whitespace"]

    tab.pipeline_list.setCurrentRow(0)
    tab._toggle_step()
    assert tab.session.pipeline[0].enabled is False

    tab.pipeline_list.setCurrentRow(0)
    tab._remove_step()
    assert len(tab.session.pipeline) == 1

    tab._undo_step()
    assert len(tab.session.pipeline) == 0


def test_analyze_describe_populates_table(tab_with_data):
    tab = tab_with_data
    tab._analyze_describe()
    assert tab.analyze_output.rowCount() > 0


def test_analyze_correlation_requires_two_numeric_columns(monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    tab = WorkspaceTab()
    tab.session.load_dataframe("t.csv", pd.DataFrame({"a": [1.0, 2.0], "b": ["x", "y"]}))
    tab._refresh_all()
    informed = {}
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: informed.setdefault("called", True)))
    tab._analyze_correlation()
    assert informed.get("called") is True


def test_analyze_groupby(tab_with_data):
    tab = tab_with_data
    tab.analyze_col_a.setCurrentText("region")
    tab._analyze_groupby()
    assert tab.analyze_output.rowCount() == 2  # East, West


def test_analyze_crosstab(tab_with_data):
    tab = tab_with_data
    tab.analyze_col_a.setCurrentText("region")
    tab.analyze_col_b.setCurrentText("product")
    tab._analyze_crosstab()
    assert tab.analyze_output.rowCount() == 2


def test_visualize_suggestions_populate(tab_with_data):
    tab = tab_with_data
    tab._suggest_charts()
    assert tab.viz_suggestions.count() > 0


def test_visualize_suggestions_for_specific_pair(tab_with_data):
    tab = tab_with_data
    tab.viz_col_x.setCurrentText("revenue")
    tab.viz_col_y.setCurrentText("units")
    tab._suggest_charts()
    assert tab.viz_suggestions.count() >= 1
    assert "Scatter" in tab.viz_suggestions.item(0).text()


def test_send_to_data_plotter_emits_dataset(tab_with_data):
    tab = tab_with_data
    received = []
    tab.send_to_data_plotter.connect(lambda ds: received.append(ds))
    tab._open_in_data_plotter()
    assert len(received) == 1
    ds = received[0]
    assert "revenue" in ds.columns
    assert "region" not in ds.columns  # non-numeric, excluded


def test_send_to_data_plotter_reaches_real_data_plotter_tab(tab_with_data):
    from scientific_visualization.gui.data_plotter_tab import DataPlotterTab
    tab = tab_with_data
    plotter = DataPlotterTab()
    tab.send_to_data_plotter.connect(plotter.add_dataset)
    tab._open_in_data_plotter()
    _app.processEvents()
    assert len(plotter._datasets) == 1
    assert "revenue" in plotter._datasets[0].columns


def test_excel_sheet_picker_flow(tmp_path):
    pytest.importorskip("openpyxl")
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"b": [3, 4, 5]})
    p = tmp_path / "book.xlsx"
    with pd.ExcelWriter(p) as writer:
        df1.to_excel(writer, sheet_name="First", index=False)
        df2.to_excel(writer, sheet_name="Second", index=False)

    tab = WorkspaceTab()
    tab._excel_path = str(p)
    from scientific_visualization.workspace.io_formats import list_excel_sheets
    tab.sheet_choice.addItems(list_excel_sheets(p))
    tab.sheet_choice.setCurrentText("Second")
    tab._load_selected_sheet()
    _app.processEvents()
    assert tab.session.loaded
    assert list(tab.session.current.columns) == ["b"]
    assert tab.session.current.shape[0] == 3
