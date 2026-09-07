"""Regression tests for scientific_visualization.gui.data_plotter_tab.DataPlotterTab.

Covers four fixes/features:
  1. The canvas widget must never be resized directly (`set_size_inches(...,
     forward=True)` on the live Qt-embedded Figure), which previously
     fought the tab's own layout and produced corrupted/ghosted renders
     when switching in or out of a paper scaling mode.
  2. Loading data does not auto-render a figure -- the canvas shows an
     idle placeholder until the user makes an explicit choice (figure
     mode, column, style, or the Plot button).
  3. Paper scaling figures support a "Single" (one combined panel) mode
     in addition to the original "Double" (two stacked panels).
  4. Every legend is draggable, and its starting position is controlled
     by the "Legend position" combo box.
"""
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox

_app = QApplication.instance() or QApplication([])

from scientific_visualization.data_plotter.figure_modes import FIGURE_MODES
from scientific_visualization.gui.data_plotter_tab import DataPlotterTab


@pytest.fixture
def tab_with_data(tmp_path):
    p1 = tmp_path / "results1.txt"
    p1.write_text("Node  Total GPUs  Simulation time\n1  4  100.0\n2  8  55.0\n4  16  30.0\n", encoding="utf-8")
    p2 = tmp_path / "results2.txt"
    p2.write_text("Node  Total GPUs  Simulation time\n1  4  120.0\n2  8  65.0\n4  16  36.0\n", encoding="utf-8")
    tab = DataPlotterTab()
    tab._load_paths([str(p1), str(p2)])
    # Loading runs on a background worker thread (see gui/workers.py) so the
    # datasets only appear once its completion callback has been delivered
    # back to the Qt event loop -- a single processEvents() call is not
    # guaranteed to be enough to observe that.
    deadline = time.time() + 5.0
    while not tab._datasets and time.time() < deadline:
        _app.processEvents()
        time.sleep(0.01)
    assert tab._datasets, "background data load did not complete in time"
    return tab


def test_loading_data_does_not_auto_plot(tab_with_data):
    tab = tab_with_data
    assert len(tab._datasets) == 2
    assert tab._has_plotted_once is False
    # The placeholder is a single, empty (axis-off) axes -- not a real chart.
    assert len(tab.canvas.figure.axes) == 1
    assert tab.canvas.figure.axes[0].axison is False


def test_plot_button_triggers_first_render(tab_with_data):
    tab = tab_with_data
    tab.plot_btn.click()
    _app.processEvents()
    assert tab._has_plotted_once is True
    assert tab.canvas.figure.axes[0].axison is not False


def test_changing_figure_mode_triggers_first_render(tab_with_data):
    tab = tab_with_data
    tab.preset.setCurrentText("Histogram")
    _app.processEvents()
    assert tab._has_plotted_once is True


@pytest.mark.parametrize("mode", list(FIGURE_MODES))
def test_canvas_widget_size_is_never_resized_by_mode_switches(tab_with_data, mode):
    """The literal bug report: switching figure modes (especially in/out of
    the paper scaling modes) must never change the Qt canvas widget's own
    size. Only what's drawn *inside* it should change."""
    tab = tab_with_data
    tab.resize(900, 650)
    _app.processEvents()
    tab.plot_btn.click()
    _app.processEvents()
    size_before = tab.canvas.size()

    tab.preset.setCurrentText(mode)
    _app.processEvents()

    size_after = tab.canvas.size()
    assert (size_after.width(), size_after.height()) == (size_before.width(), size_before.height())


def test_switching_all_modes_in_sequence_keeps_canvas_size_stable(tab_with_data):
    """Same property as above, but exercised as one continuous sequence of
    switches (closer to how a user actually clicks through the dropdown),
    since the original bug only appeared after a resize+re-render cycle."""
    tab = tab_with_data
    tab.resize(900, 650)
    _app.processEvents()
    tab.plot_btn.click()
    _app.processEvents()

    sizes = set()
    for mode in FIGURE_MODES:
        tab.preset.setCurrentText(mode)
        _app.processEvents()
        s = tab.canvas.size()
        sizes.add((s.width(), s.height()))
    assert len(sizes) == 1


def test_panels_single_vs_double_for_strong_scaling(tab_with_data):
    tab = tab_with_data
    tab.preset.setCurrentText("Paper Strong Scaling")
    tab.panels.setCurrentText("Double")
    _app.processEvents()
    assert len(tab.canvas.figure.axes) == 2

    tab.panels.setCurrentText("Single")
    _app.processEvents()
    # One primary axes plus its twinned efficiency axes.
    assert len(tab.canvas.figure.axes) == 2
    ax = tab.canvas.figure.axes[0]
    assert ax.get_legend() is not None


def test_panels_control_disabled_outside_scaling_modes(tab_with_data):
    tab = tab_with_data
    tab.preset.setCurrentText("Histogram")
    _app.processEvents()
    assert tab.panels.isEnabled() is False
    tab.preset.setCurrentText("Paper Weak Scaling")
    _app.processEvents()
    assert tab.panels.isEnabled() is True


def test_legend_is_draggable_and_position_is_configurable(tab_with_data):
    tab = tab_with_data
    # "Line / Scatter" is already the dropdown's default, so setting it
    # again wouldn't fire a change signal -- switch away first, then to it,
    # to force a genuine, observable transition into a real plotted state.
    tab.preset.setCurrentText("Histogram")
    _app.processEvents()
    tab.preset.setCurrentText("Line / Scatter")
    _app.processEvents()
    ax = tab.canvas.figure.axes[0]
    legend = ax.get_legend()
    assert legend is not None
    assert legend.get_draggable() is True

    tab.legend_loc.setCurrentText("Upper left")
    _app.processEvents()
    legend2 = tab.canvas.figure.axes[0].get_legend()
    assert legend2 is not None
    assert legend2.get_draggable() is True

    tab.legend_loc.setCurrentText("None")
    _app.processEvents()
    assert tab.canvas.figure.axes[0].get_legend() is None


def test_export_does_not_resize_the_live_canvas(tab_with_data, tmp_path, monkeypatch):
    """export_plot() sets the Figure to the requested export dimensions to
    produce the output file, but must restore the on-screen size afterward
    and must never call set_size_inches with forward=True (that's what
    corrupted the interactive canvas -- see refresh_plot)."""
    from PyQt5.QtWidgets import QFileDialog
    tab = tab_with_data
    tab.plot_btn.click()
    _app.processEvents()

    original_size = tuple(tab.canvas.figure.get_size_inches())
    out_path = str(tmp_path / "export.png")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (out_path, "PNG (*.png)")))

    tab.width.setValue(12.0)
    tab.height.setValue(20.0)
    tab.export_plot()
    _app.processEvents()

    assert os.path.exists(out_path)
    restored_size = tuple(tab.canvas.figure.get_size_inches())
    assert restored_size == pytest.approx(original_size)


# --- Curve fitting wiring ---

def test_fit_overlay_adds_a_dashed_line_and_reports_equation(tab_with_data):
    tab = tab_with_data
    tab.preset.setCurrentText("Line / Scatter")
    tab.fit_enabled.setChecked(True)
    tab.fit_kind.setCurrentText("Linear")
    _app.processEvents()

    ax = tab.canvas.figure.axes[0]
    assert len(ax.lines) == 4  # 2 datasets x (data line + fit line)
    assert "y =" in tab.stats_label.text()
    assert "R\u00b2=" in tab.stats_label.text()


def test_fit_box_disabled_outside_line_scatter_mode(tab_with_data):
    tab = tab_with_data
    tab.preset.setCurrentText("Histogram")
    _app.processEvents()
    assert tab.fit_box.isEnabled() is False
    tab.preset.setCurrentText("Line / Scatter")
    _app.processEvents()
    assert tab.fit_box.isEnabled() is True


def test_polynomial_fit_order_control_enabled_only_for_polynomial(tab_with_data):
    tab = tab_with_data
    assert tab.fit_order.isEnabled() is False
    tab.fit_kind.setCurrentText("Polynomial")
    _app.processEvents()
    assert tab.fit_order.isEnabled() is True
    assert tab.fit_expression.isEnabled() is False


# --- Data editing wiring ---

def test_add_computed_column_updates_table_and_combos(tab_with_data):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    ds = tab._datasets[0]
    before = ds.column_count

    tab.new_column_name.setText("gpus_per_node")
    tab.new_column_expr.setText("Total GPUs / Node")
    tab._add_computed_column()
    _app.processEvents()

    assert ds.column_count == before + 1
    assert "gpus_per_node" in ds.columns
    assert tab.data_table.columnCount() == ds.column_count
    assert tab.x_column.count() == ds.column_count


def test_add_computed_column_reports_bad_formula(tab_with_data, monkeypatch):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    warned = {}
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: warned.setdefault("called", True)))
    tab.new_column_name.setText("bad")
    tab.new_column_expr.setText("NoSuchColumn * 2")
    tab._add_computed_column()
    assert warned.get("called") is True


def test_remove_column_updates_configs_and_bounds(tab_with_data):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    ds = tab._datasets[0]
    last = ds.column_count - 1
    tab._configs[0].x = last
    tab.remove_column_choice.setCurrentIndex(last)
    tab._remove_column()
    _app.processEvents()
    assert ds.column_count == last  # one fewer column
    assert tab._configs[0].x < ds.column_count


def test_add_and_remove_row(tab_with_data):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    ds = tab._datasets[0]
    n = ds.row_count

    tab._add_row()
    _app.processEvents()
    assert ds.row_count == n + 1

    tab.data_table.selectRow(0)
    tab._remove_selected_rows()
    _app.processEvents()
    assert ds.row_count == n


def test_remove_rows_with_no_selection_warns_instead_of_crashing(tab_with_data, monkeypatch):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    tab.data_table.clearSelection()
    warned = {}
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: warned.setdefault("called", True)))
    tab._remove_selected_rows()
    assert warned.get("called") is True


def test_sort_by_column_reorders_underlying_data(tab_with_data):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    ds = tab._datasets[0]
    tab.sort_column_choice.setCurrentIndex(1)  # Total GPUs
    tab.sort_descending.setChecked(True)
    tab._sort_by_column()
    _app.processEvents()
    values = ds.column_values(1)
    assert list(values) == sorted(values, reverse=True)


# --- Multi-column plotting + change annotations ---

def test_extra_y_columns_list_populated_and_selectable(tab_with_data):
    tab = tab_with_data
    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    ds = tab._datasets[0]
    assert tab.extra_y_columns.count() == ds.column_count

    tab.extra_y_columns.item(2).setSelected(True)
    tab._extra_y_columns_changed()
    _app.processEvents()
    assert tab._configs[0].extra_y == [2]


def test_multi_column_plot_renders_extra_series(tmp_path):
    p = tmp_path / "prices.csv"
    p.write_text("year,price,salary\n2016,100,10\n2020,150,12\n2024,200,15\n", encoding="utf-8")
    tab = DataPlotterTab()
    tab._load_paths([str(p)])
    deadline = time.time() + 5
    while not tab._datasets and time.time() < deadline:
        _app.processEvents(); time.sleep(0.01)

    tab.dataset_list.setCurrentRow(0)
    _app.processEvents()
    tab.extra_y_columns.item(2).setSelected(True)  # "salary"
    tab.preset.setCurrentText("Line / Scatter")
    _app.processEvents()

    ax = tab.canvas.figure.axes[0]
    assert len(ax.lines) == 2
    labels = {line.get_label() for line in ax.lines}
    assert labels == {"price", "salary"}


def test_extra_y_columns_disabled_outside_line_scatter(tab_with_data):
    tab = tab_with_data
    tab.preset.setCurrentText("Histogram")
    _app.processEvents()
    assert tab.extra_y_columns.isEnabled() is False
    tab.preset.setCurrentText("Line / Scatter")
    _app.processEvents()
    assert tab.extra_y_columns.isEnabled() is True


def test_annotate_changes_checkbox_wired(tmp_path):
    p = tmp_path / "trend.csv"
    p.write_text("x,y\n0,10\n1,20\n2,40\n", encoding="utf-8")
    tab = DataPlotterTab()
    tab._load_paths([str(p)])
    deadline = time.time() + 5
    while not tab._datasets and time.time() < deadline:
        _app.processEvents(); time.sleep(0.01)

    tab.preset.setCurrentText("Line / Scatter")
    tab.annotate_changes.setChecked(True)
    _app.processEvents()

    ax = tab.canvas.figure.axes[0]
    assert len(ax.texts) >= 1
    assert "%" in ax.texts[0].get_text()
