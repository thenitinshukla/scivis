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
