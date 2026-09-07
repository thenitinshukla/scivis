import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scientific_visualization.data_plotter.renderer import DataPlotRenderer, RenderSeries

def test_renderer_supports_xy_and_histogram():
    renderer = DataPlotRenderer()
    fig, ax = plt.subplots()
    series = [RenderSeries(np.arange(5), np.arange(5) ** 2, "A", "#0072B2")]
    renderer.render_xy(ax, series, plot_type="Line + Scatter")
    assert ax.get_xlabel() == "X"
    renderer.render_histogram(ax, series, bins=5)
    assert len(ax.patches) > 0
    plt.close(fig)

def test_renderer_supports_scientific_distribution_and_diagnostics():
    renderer = DataPlotRenderer()
    fig, ax = plt.subplots()
    rng = np.random.default_rng(7)
    x = np.repeat(np.arange(3), 5)
    y = rng.normal(size=15)
    series = [RenderSeries(x, y, "A", "#0072B2")]
    renderer.render_boxplot(ax, series)
    assert len(ax.lines) > 0
    renderer.render_violin(ax, series)
    assert len(ax.collections) > 0
    renderer.render_mean_errorbar(ax, series)
    assert len(ax.lines) > 0
    renderer.render_hexbin(ax, series)
    assert len(ax.collections) > 0
    plt.close(fig)


def test_renderer_correlation_heatmap():
    from scientific_visualization.data_plotter.model import DatasetTable
    renderer = DataPlotRenderer()
    fig, ax = plt.subplots()
    ds = DatasetTable("sample.txt", ["x", "y", "z"], np.array([[1,2,3],[2,4,6],[3,6,9]], dtype=float), " ", True)
    renderer.render_correlation_heatmap(ax, ds)
    assert len(ax.images) == 1
    plt.close(fig)


def _dataset_plot_config(**overrides):
    from scientific_visualization.data_plotter.model import DatasetPlotConfig
    return DatasetPlotConfig(label=overrides.pop("label", "run"), color=overrides.pop("color", "#0072B2"), **overrides)


def test_paper_strong_and_weak_scaling_share_dual_resource_axes():
    """render_paper_weak_scaling must reproduce the exact GPU-top/Node-bottom
    dual axis layout of render_paper_strong_scaling, not a generic XY plot."""
    renderer = DataPlotRenderer()
    gpus = np.array([1.0, 2.0, 4.0, 8.0])

    fig_strong, (s_top, s_bottom) = plt.subplots(2, 1)
    speedup = np.array([1.0, 1.9, 3.6, 6.8])
    efficiency = speedup / gpus
    renderer.render_paper_strong_scaling(s_top, s_bottom, [(gpus, speedup, efficiency, _dataset_plot_config())])

    fig_weak, (w_top, w_bottom) = plt.subplots(2, 1)
    normalized_runtime = np.array([1.0, 1.05, 1.1, 1.2])
    weak_efficiency = 1.0 / normalized_runtime
    renderer.render_paper_weak_scaling(w_top, w_bottom, [(gpus, normalized_runtime, weak_efficiency, _dataset_plot_config())])

    for strong_ax, weak_ax, expected_xlabel in ((s_top, w_top, "GPUs"), (s_bottom, w_bottom, "Nodes")):
        assert strong_ax.get_xscale() == weak_ax.get_xscale() == "log"
        assert strong_ax.get_xlabel() == weak_ax.get_xlabel() == expected_xlabel
        np.testing.assert_allclose(strong_ax.get_xticks(), weak_ax.get_xticks())
        assert strong_ax.get_xlim() == weak_ax.get_xlim()

    assert w_top.xaxis.get_label_position() == "top"
    assert list(w_bottom.get_yticks()) == list(s_bottom.get_yticks()) == [0, 25, 50, 75, 100]
    assert w_bottom.get_ylim() == s_bottom.get_ylim() == (0, 110)

    # Weak scaling's ideal reference is a flat line at 1.0 (not the diagonal
    # ideal-speedup line strong scaling draws).
    ideal = [ln for ln in w_top.lines if ln.get_label() == "_nolegend_"]
    assert len(ideal) == 1
    np.testing.assert_allclose(ideal[0].get_ydata(), 1.0)

    plt.close(fig_strong)
    plt.close(fig_weak)


def test_paper_weak_scaling_ylim_keeps_ideal_line_in_view():
    renderer = DataPlotRenderer()
    fig, (top, bottom) = plt.subplots(2, 1)
    gpus = np.array([1.0, 2.0, 4.0])
    # Runtime that drifts far from 1.0 -- the ideal line must still be visible.
    normalized_runtime = np.array([1.0, 1.4, 1.9])
    efficiency = 1.0 / normalized_runtime
    renderer.render_paper_weak_scaling(top, bottom, [(gpus, normalized_runtime, efficiency, _dataset_plot_config())])
    lo, hi = top.get_ylim()
    assert lo <= 1.0 <= hi
    assert lo <= min(normalized_runtime)
    assert hi >= max(normalized_runtime)
    plt.close(fig)


def test_paper_weak_scaling_empty_input_does_not_raise():
    renderer = DataPlotRenderer()
    fig, (top, bottom) = plt.subplots(2, 1)
    renderer.render_paper_weak_scaling(top, bottom, [])
    plt.close(fig)
