import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from scientific_visualization.data_plotter.figure_modes import (
    FIGURE_MODES, FigureOptions, render_figure,
)
from scientific_visualization.data_plotter.model import DatasetPlotConfig, DatasetTable
from scientific_visualization.data_plotter.renderer import DataPlotRenderer


def make_dataset(name, columns, values):
    return DatasetTable(path=name, columns=columns, values=np.asarray(values, dtype=float),
                        delimiter=",", has_header=True)


@pytest.fixture
def two_scaling_datasets():
    # Two "experiments" with a resource-count column and a runtime column,
    # shaped so strong scaling gives a clean speedup/efficiency curve.
    gpus = np.array([1, 2, 4, 8], dtype=float)
    runtime_a = 100.0 / gpus
    runtime_b = 100.0 / gpus * 1.2
    ds_a = make_dataset("a.csv", ["Total GPUs", "Simulation time"], np.column_stack([gpus, runtime_a]))
    ds_b = make_dataset("b.csv", ["Total GPUs", "Simulation time"], np.column_stack([gpus, runtime_b]))
    cfg_a = DatasetPlotConfig(x=0, y=1, label="a", color="#111111", workload_factor=1.0)
    cfg_b = DatasetPlotConfig(x=0, y=1, label="b", color="#222222", workload_factor=2.0)
    return [ds_a, ds_b], [cfg_a, cfg_b]


@pytest.fixture
def renderer():
    return DataPlotRenderer()


@pytest.fixture
def fig():
    figure = plt.figure()
    yield figure
    plt.close(figure)


def test_every_declared_mode_is_handled_without_raising(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    for mode in FIGURE_MODES:
        fig.clear()
        # Should never raise for ordinary data -- only return a message.
        render_figure(fig, renderer, mode, datasets, configs, FigureOptions())


def test_line_scatter_plots_all_enabled_series(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    err = render_figure(fig, renderer, "Line / Scatter", datasets, configs, FigureOptions())
    assert err is None
    ax = fig.axes[0]
    assert len(ax.lines) == 2  # one line per enabled dataset


def test_disabling_all_datasets_reports_message(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    for cfg in configs:
        cfg.enabled = False
    err = render_figure(fig, renderer, "Line / Scatter", datasets, configs, FigureOptions())
    assert err is not None


def test_paper_strong_scaling_computes_speedup(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    err = render_figure(fig, renderer, "Paper Strong Scaling", datasets, configs, FigureOptions())
    assert err is None
    assert len(fig.axes) == 2


def test_paper_weak_scaling_uses_workload_factor(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    err = render_figure(fig, renderer, "Paper Weak Scaling", datasets, configs, FigureOptions())
    assert err is None
    assert len(fig.axes) == 2
    top_ax = fig.axes[0]
    # One line per enabled dataset plus the ideal-weak-scaling reference line.
    assert len(top_ax.lines) == 3


def test_paper_weak_scaling_matches_strong_scaling_dual_axis_layout(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    render_figure(fig, renderer, "Paper Weak Scaling", datasets, configs, FigureOptions())
    top_ax, bottom_ax = fig.axes
    # Same GPU-on-top / Node-on-bottom dual resource-axis presentation as
    # Paper Strong Scaling: log2 x-axis, GPU labels pinned to the top edge
    # of the top panel, Node labels on the bottom panel.
    assert top_ax.get_xscale() == "log"
    assert bottom_ax.get_xscale() == "log"
    assert top_ax.get_xlabel() == "GPUs"
    assert bottom_ax.get_xlabel() == "Nodes"
    assert top_ax.xaxis.get_label_position() == "top"
    # The ideal weak-scaling reference is a flat line at normalized runtime = 1.
    ideal_lines = [ln for ln in top_ax.lines if ln.get_label() == "_nolegend_"]
    assert len(ideal_lines) == 1
    y = ideal_lines[0].get_ydata()
    assert np.allclose(y, 1.0)
    # Efficiency panel uses the same fixed 0-110 / 0-25-50-75-100 scale as
    # the strong-scaling efficiency panel.
    assert bottom_ax.get_ylim()[1] == pytest.approx(110)
    assert list(bottom_ax.get_yticks()) == [0, 25, 50, 75, 100]


def test_paper_weak_scaling_rejects_zero_workload_factor(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    configs[0].workload_factor = 0.0
    configs[1].enabled = False
    err = render_figure(fig, renderer, "Paper Weak Scaling", datasets, configs, FigureOptions())
    assert err is not None
    assert "workload factor" in err.lower()


def test_single_panel_transform_normalize_to_first(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    err = render_figure(fig, renderer, "Normalize Y to first", datasets, configs, FigureOptions())
    assert err is None
    ax = fig.axes[0]
    # The first point of every normalized series should be 1.0.
    for line in ax.lines:
        y = line.get_ydata()
        if len(y):
            assert y[0] == pytest.approx(1.0)


def test_correlation_heatmap_uses_selected_dataset(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    err = render_figure(fig, renderer, "Correlation heatmap", datasets, configs,
                        FigureOptions(selected_dataset_index=1))
    assert err is None
    assert len(fig.axes) >= 1


def test_correlation_heatmap_out_of_range_index_reports_message(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    err = render_figure(fig, renderer, "Correlation heatmap", datasets, configs,
                        FigureOptions(selected_dataset_index=99))
    assert err is not None


def test_histogram_respects_x_y_column_override(fig, renderer, two_scaling_datasets):
    datasets, configs = two_scaling_datasets
    # Force plotting column 0 (GPUs) instead of each config's own y column.
    err = render_figure(fig, renderer, "Histogram", datasets, configs,
                        FigureOptions(x_index=0, y_index=0, bins=4))
    assert err is None


def test_multi_column_line_scatter_from_one_dataset(fig, renderer):
    """The general-purpose case: one CSV with several measurement columns
    (e.g. year/house_price/salary) plotted as separate lines without
    splitting into multiple files."""
    ds = make_dataset("prices.csv", ["year", "price", "salary"],
                      [[2016, 100, 10], [2017, 120, 11], [2018, 150, 12]])
    cfg = DatasetPlotConfig(x=0, y=1, label="prices.csv", color="#1f77b4", extra_y=[2])
    err = render_figure(fig, DataPlotRenderer(), "Line / Scatter", [ds], [cfg], FigureOptions())
    assert err is None
    ax = fig.axes[0]
    assert len(ax.lines) == 2
    # Both series should be labeled by their own column name, not a mix of
    # filename (primary) and column name (extra) in the same legend.
    labels = {line.get_label() for line in ax.lines}
    assert labels == {"price", "salary"}
    assert ax.get_ylabel() == "Value"
    assert ax.get_xlabel() == "year"


def test_extra_y_column_out_of_range_is_ignored(fig, renderer):
    ds = make_dataset("a.csv", ["x", "y"], [[1, 2], [3, 4]])
    cfg = DatasetPlotConfig(x=0, y=1, label="a", extra_y=[99])
    err = render_figure(fig, renderer, "Line / Scatter", [ds], [cfg], FigureOptions())
    assert err is None
    assert len(fig.axes[0].lines) == 1


def test_annotate_changes_draws_callouts_and_reference_lines(fig, renderer):
    ds = make_dataset("a.csv", ["year", "price"], [[2016, 100], [2020, 150], [2024, 200]])
    cfg = DatasetPlotConfig(x=0, y=1, label="price", color="#1f77b4")
    err = render_figure(fig, renderer, "Line / Scatter", [ds], [cfg], FigureOptions(annotate_changes=True))
    assert err is None
    ax = fig.axes[0]
    assert len(ax.texts) == 1
    assert "+100" in ax.texts[0].get_text()
    assert "100%" in ax.texts[0].get_text()
    # Baseline dotted horizontal line + two dashed vertical lines (start/end).
    assert len(ax.lines) >= 3


def test_annotate_changes_handles_decreasing_series(renderer):
    fig = plt.figure()
    ds = make_dataset("a.csv", ["x", "y"], [[0, 100], [1, 50]])
    cfg = DatasetPlotConfig(x=0, y=1, label="y")
    series = [type("S", (), {})()]  # placeholder not used; call renderer directly
    from scientific_visualization.data_plotter.renderer import RenderSeries
    rs = RenderSeries(x=np.array([0.0, 1.0]), y=np.array([100.0, 50.0]), label="y", color="#111111",
                      line_style="-", marker="None", line_width=1.5, marker_size=4.0, enabled=True)
    ax = fig.add_subplot(1, 1, 1)
    renderer.annotate_changes(ax, [rs])
    assert "\u2212" in ax.texts[0].get_text() or "-50" in ax.texts[0].get_text()
    plt.close(fig)


def test_annotate_changes_skips_series_with_fewer_than_two_points(renderer):
    from scientific_visualization.data_plotter.renderer import RenderSeries
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    rs = RenderSeries(x=np.array([1.0]), y=np.array([1.0]), label="y", color="#111111",
                      line_style="-", marker="None", line_width=1.5, marker_size=4.0, enabled=True)
    renderer.annotate_changes(ax, [rs])
    assert len(ax.texts) == 0
    plt.close(fig)


def test_unknown_mode_raises():
    fig = plt.figure()
    try:
        with pytest.raises(ValueError):
            render_figure(fig, DataPlotRenderer(), "Not a real mode", [], [], FigureOptions())
    finally:
        plt.close(fig)
