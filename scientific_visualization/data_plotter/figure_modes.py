"""Figure-mode dispatch for the Data Plotter.

Every figure the Data Plotter tab can draw -- a raw XY plot, a histogram,
a strong/weak-scaling comparison, a correlation heatmap, and so on -- is
described here as a small, pure function of (datasets, configs, options)
that fills in a Matplotlib ``Figure``. None of this module imports PyQt5,
so new figure modes can be written and unit-tested without a GUI event
loop, and ``gui/data_plotter_tab.py`` only needs to know how to collect
widget values and call :func:`render_figure`.

Previously this dispatch lived entirely inside the Qt tab as a single
hardcoded code path for one figure mode ("Paper Strong Scaling"). Several
other renderer/scaling functions (`weak_scaling`, `transform_for_preset`,
`render_hexbin`, `render_correlation_heatmap`, `render_boxplot`,
`render_violin`, `render_mean_errorbar`, ...) were fully implemented and
tested but never reachable from the UI. Adding a mode here plus one entry
in `FIGURE_MODES` is now enough to expose it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .comparison import transform_for_preset
from .model import DatasetPlotConfig, DatasetTable
from .renderer import DataPlotRenderer, RenderSeries
from .scaling import strong_scaling, weak_scaling

# Names shown in the "Figure mode" dropdown, in display order.
SINGLE_PANEL_TRANSFORMS = ("Normalize Y to first", "Strong scaling: speedup", "Strong scaling: efficiency")
DISTRIBUTION_MODES = ("Histogram", "Empirical CDF", "Bar summary", "Box plot", "Violin plot")

FIGURE_MODES = (
    "Line / Scatter",
    "Paper Strong Scaling",
    "Paper Weak Scaling",
    *SINGLE_PANEL_TRANSFORMS,
    *DISTRIBUTION_MODES,
    "Mean \u00b1 1\u03c3 errorbar",
    "Hexbin density",
    "Correlation heatmap",
)

# Modes that plot a single selected dataset rather than every enabled one.
SINGLE_DATASET_MODES = ("Correlation heatmap",)


@dataclass
class FigureOptions:
    """Everything the GUI can vary about how a figure mode is drawn.

    Kept as one plain dataclass (rather than a long parameter list) so
    `render_figure`'s signature stays stable as new modes need new knobs.
    """
    x_index: int | None = None
    y_index: int | None = None
    plot_type: str = "Line"
    bins: int = 30
    histogram_normalization: str = "Count"
    selected_dataset_index: int = 0
    xscale: str = "linear"
    yscale: str = "linear"
    legend: bool = True
    legend_loc: str = "Best"
    panels: str = "Double"
    """"Double" (two stacked panels) or "Single" (one panel, both metrics
    sharing a secondary y-axis) -- only consulted by the paper scaling modes."""
    fit_enabled: bool = False
    fit_kind: str = "Linear"
    fit_order: int = 2
    fit_expression: str = ""
    annotate_changes: bool = False
    """Line/Scatter only: draw a first->last value change callout (with
    percent change) plus light baseline reference lines for every series --
    the "how much did this grow" annotation style common in general-purpose
    trend charts (e.g. a price-vs-salary-over-time comparison)."""


def _columns_for(ds: DatasetTable, cfg: DatasetPlotConfig, options: FigureOptions) -> tuple[int, int]:
    x = options.x_index if options.x_index is not None else cfg.x
    y = options.y_index if options.y_index is not None else cfg.y
    return x, y


def _series_for(
    datasets: Sequence[DatasetTable],
    configs: Sequence[DatasetPlotConfig],
    options: FigureOptions,
    transform: Callable[[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]] | None = None,
    include_extra_y: bool = False,
) -> list[RenderSeries]:
    """Build one RenderSeries per (dataset, Y column) to plot.

    Normally that's one series per enabled dataset (its own X/Y column
    choice). When `include_extra_y` is set (Line/Scatter mode), each
    dataset's `cfg.extra_y` columns are *also* plotted, each as its own
    series against the same X column -- this is what lets a single CSV
    with several measurement columns (e.g. "year, house_price, salary")
    be charted as multiple lines without splitting it into separate files.
    """
    series = []
    palette = DataPlotRenderer.DEFAULT_COLORS
    single_dataset = sum(1 for cfg in configs if cfg.enabled) <= 1
    for ds, cfg in zip(datasets, configs):
        if not cfg.enabled:
            continue
        xi, yi = _columns_for(ds, cfg, options)
        if not (0 <= xi < ds.column_count):
            continue
        y_specs = [(yi, cfg.color, cfg.label)]
        if include_extra_y:
            for k, extra_idx in enumerate(cfg.extra_y):
                if extra_idx == yi or not (0 <= extra_idx < ds.column_count):
                    continue
                color = palette[(k + 1) % len(palette)]
                label = ds.columns[extra_idx] if single_dataset else f"{cfg.label}: {ds.columns[extra_idx]}"
                y_specs.append((extra_idx, color, label))
            if len(y_specs) > 1 and single_dataset and 0 <= yi < ds.column_count:
                # Multi-column mode is active for this (single) dataset --
                # use the primary column's own name too, to match how the
                # extra columns are labeled, rather than mixing a filename
                # label with column-name labels in the same legend.
                y_specs[0] = (yi, cfg.color, ds.columns[yi])

        x_full = ds.column_values(xi)
        for y_idx, color, label in y_specs:
            if not (0 <= y_idx < ds.column_count):
                continue
            x, y = x_full, ds.column_values(y_idx)
            if transform is not None:
                try:
                    x, y = transform(x, y)
                except ValueError:
                    continue
            series.append(RenderSeries(
                x=x, y=y, label=label, color=color, line_style=cfg.line_style,
                marker=cfg.marker, line_width=cfg.line_width, marker_size=cfg.marker_size,
                enabled=cfg.enabled,
            ))
    return series


def _axis_labels(datasets, configs, options: FigureOptions, include_extra_y: bool = False) -> tuple[str, str]:
    """Best-effort X/Y axis labels from the actual column names being
    plotted, instead of the generic "X"/"Y" defaults -- falls back to a
    generic label only when datasets disagree on which column is which
    (e.g. comparing several files with different X columns selected)."""
    x_names, y_names = set(), set()
    for ds, cfg in zip(datasets, configs):
        if not cfg.enabled:
            continue
        xi, yi = _columns_for(ds, cfg, options)
        if 0 <= xi < ds.column_count:
            x_names.add(ds.columns[xi])
        if 0 <= yi < ds.column_count:
            y_names.add(ds.columns[yi])
        if include_extra_y:
            for extra_idx in cfg.extra_y:
                if 0 <= extra_idx < ds.column_count:
                    y_names.add(ds.columns[extra_idx])
    xlabel = next(iter(x_names)) if len(x_names) == 1 else "X"
    ylabel = next(iter(y_names)) if len(y_names) == 1 else ("Value" if y_names else "Y")
    return xlabel, ylabel


def _render_paper_scaling(
    fig, renderer: DataPlotRenderer, kind: str,
    datasets: Sequence[DatasetTable], configs: Sequence[DatasetPlotConfig], options: FigureOptions,
) -> str | None:
    """Shared layout for strong- and weak-scaling comparisons, as either two
    stacked panels or one combined panel (see ``FigureOptions.panels``).

    Deliberately does not resize `fig`: the interactive canvas's on-screen
    size is owned by the Qt layout it sits in, and forcing a different
    physical size here (a prior version called
    ``fig.set_size_inches(..., forward=True)``) fights that layout on the
    next repaint and produces corrupted/ghosted renders. A fixed publication
    aspect ratio is still available -- just via the Export panel's width/
    height/DPI fields at save time, which is the only place figure size
    should be dictated in inches.

    Returns an error message (e.g. from a bad workload factor) or None.
    """
    result = []
    error = None
    for ds, cfg in zip(datasets, configs):
        if not cfg.enabled:
            continue
        xi, yi = _columns_for(ds, cfg, options)
        if not (0 <= xi < ds.column_count) or not (0 <= yi < ds.column_count):
            continue
        x0, y0 = ds.column_values(xi), ds.column_values(yi)
        try:
            if kind == "strong":
                x, top = strong_scaling(x0, y0, metric="Speedup")
                _, bottom = strong_scaling(x0, y0, metric="Efficiency")
            else:
                x, top = weak_scaling(x0, y0, cfg.workload_factor, metric="Normalized runtime")
                _, bottom = weak_scaling(x0, y0, cfg.workload_factor, metric="Efficiency")
        except ValueError as exc:
            error = str(exc)
            continue
        if x.size:
            result.append((x, top, bottom, cfg))

    if not result:
        return error or "No valid positive resource/runtime data were found."

    if options.panels == "Single":
        ax = fig.add_subplot(1, 1, 1)
        renderer.render_paper_scaling_single(ax, result, kind=kind, legend_loc=options.legend_loc)
        renderer.apply_paper_style(ax)
        fig.subplots_adjust(left=0.15, right=0.85, top=0.90, bottom=0.16)
        return None

    ax_top = fig.add_subplot(2, 1, 1)
    ax_bottom = fig.add_subplot(2, 1, 2)
    if kind == "strong":
        renderer.render_paper_strong_scaling(ax_top, ax_bottom, result, legend_loc=options.legend_loc)
    else:
        renderer.render_paper_weak_scaling(ax_top, ax_bottom, result, legend_loc=options.legend_loc)

    renderer.apply_paper_style(ax_top)
    renderer.apply_paper_style(ax_bottom)
    fig.subplots_adjust(left=0.17, right=0.97, top=0.90, bottom=0.14, hspace=0.10)
    return None


def _overlay_fits(ax, series: list[RenderSeries], options: FigureOptions) -> str | None:
    """Fit `options.fit_kind` to each enabled series and draw it as a dashed
    line in the same color. Returns an HTML-ish (``<br>``-joined) summary of
    every fit's equation and R^2 -- plus any per-series fit errors -- meant
    to be shown directly in the tab's stats/status label, or None if fitting
    is off or produced nothing to report.
    """
    from .fitting import fit_curve

    summaries, errors = [], []
    for item in series:
        if not item.enabled:
            continue
        try:
            result = fit_curve(item.x, item.y, options.fit_kind, order=options.fit_order,
                               custom_expression=options.fit_expression)
        except ValueError as exc:
            errors.append(f"{item.label or 'series'}: {exc}")
            continue
        ax.plot(result.x_fit, result.y_fit, linestyle="--", linewidth=1.3, color=item.color,
               alpha=0.85, label=f"{item.label} fit" if item.label else "fit")
        summaries.append(f"{item.label or 'series'}: {result.equation} (R\u00b2={result.r_squared:.4f})")

    if summaries and options.legend:
        # Re-draw the legend so the newly added fit lines get entries too.
        DataPlotRenderer._place_legend(ax, options.legend_loc)
    if not summaries and not errors:
        return None
    return "<br>".join(summaries + errors)


def render_figure(
    fig, renderer: DataPlotRenderer, mode: str,
    datasets: Sequence[DatasetTable], configs: Sequence[DatasetPlotConfig],
    options: FigureOptions | None = None,
) -> str | None:
    """Render `mode` into `fig` for the given datasets/configs.

    Returns an error/status message to surface to the user (e.g. "no data"),
    or None on success. Never raises for ordinary data problems -- only
    programmer errors (an unknown `mode`) propagate.
    """
    options = options or FigureOptions()
    fig.clear()

    if mode == "Correlation heatmap":
        if not (0 <= options.selected_dataset_index < len(datasets)):
            return "Select a dataset to inspect its correlation matrix."
        ax = fig.add_subplot(1, 1, 1)
        renderer.render_correlation_heatmap(ax, datasets[options.selected_dataset_index])
        return None

    if mode in ("Paper Strong Scaling", "Paper Weak Scaling"):
        return _render_paper_scaling(
            fig, renderer, "strong" if mode == "Paper Strong Scaling" else "weak",
            datasets, configs, options,
        )

    ax = fig.add_subplot(1, 1, 1)
    fit_message = None

    if mode == "Line / Scatter":
        series = _series_for(datasets, configs, options, include_extra_y=True)
        xlabel, ylabel = _axis_labels(datasets, configs, options, include_extra_y=True)
        renderer.render_xy(ax, series, plot_type=options.plot_type, xlabel=xlabel, ylabel=ylabel,
                            xscale=options.xscale, yscale=options.yscale, legend=options.legend,
                            legend_loc=options.legend_loc)
        if options.annotate_changes:
            renderer.annotate_changes(ax, series)
        if options.fit_enabled:
            fit_message = _overlay_fits(ax, series, options)
    elif mode in SINGLE_PANEL_TRANSFORMS:
        series = _series_for(datasets, configs, options, transform=lambda x, y: transform_for_preset(x, y, mode))
        xlabel, _ = _axis_labels(datasets, configs, options)
        renderer.render_xy(ax, series, plot_type=options.plot_type, xlabel=xlabel, ylabel=mode,
                            xscale=options.xscale, yscale=options.yscale, legend=options.legend,
                            legend_loc=options.legend_loc)
    elif mode == "Histogram":
        series = _series_for(datasets, configs, options)
        renderer.render_histogram(ax, series, bins=options.bins, normalization=options.histogram_normalization,
                                   legend_loc=options.legend_loc)
    elif mode == "Empirical CDF":
        series = _series_for(datasets, configs, options)
        renderer.render_cdf(ax, series, legend_loc=options.legend_loc)
    elif mode == "Bar summary":
        series = _series_for(datasets, configs, options)
        renderer.render_bar(ax, series)
    elif mode == "Box plot":
        series = _series_for(datasets, configs, options)
        renderer.render_boxplot(ax, series)
    elif mode == "Violin plot":
        series = _series_for(datasets, configs, options)
        renderer.render_violin(ax, series)
    elif mode == "Mean \u00b1 1\u03c3 errorbar":
        series = _series_for(datasets, configs, options)
        renderer.render_mean_errorbar(ax, series, xscale=options.xscale, yscale=options.yscale,
                                       legend_loc=options.legend_loc)
    elif mode == "Hexbin density":
        series = _series_for(datasets, configs, options)
        renderer.render_hexbin(ax, series)
    else:
        raise ValueError(f"Unknown figure mode: {mode!r}")

    if not any(cfg.enabled for cfg in configs):
        return "Enable at least one dataset to plot it."
    return fit_message
