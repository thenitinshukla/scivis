from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RenderSeries:
    x: np.ndarray
    y: np.ndarray
    label: str
    color: str
    line_style: str = "-"
    marker: str = "None"
    line_width: float = 1.8
    marker_size: float = 4.0
    enabled: bool = True


class DataPlotRenderer:
    """Matplotlib renderer isolated from Qt widgets."""

    PALETTES = {
        "Scientific": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"],
        "Viridis": ["#440154", "#482878", "#3E4989", "#31688E", "#26828E", "#35B779", "#6CCE59", "#FDE725"],
        "Tableau": ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC"],
        "Grayscale": ["#111111", "#333333", "#555555", "#777777", "#999999", "#BBBBBB", "#DDDDDD", "#000000"],
    }
    DEFAULT_COLORS = PALETTES["Scientific"]

    LEGEND_LOCATIONS = {
        "Best": "best",
        "Upper right": "upper right",
        "Upper left": "upper left",
        "Lower left": "lower left",
        "Lower right": "lower right",
        "Outside right": "center left",
        "None": None,
    }

    @classmethod
    def _place_legend(cls, ax, legend_loc="Best", **kwargs):
        """Draw a legend at `legend_loc` (a key of LEGEND_LOCATIONS, or a raw
        Matplotlib loc string) and make it draggable so the user can move it
        with the mouse afterward regardless of where it was first placed.
        Passing "None" (or None) removes/skips the legend entirely.
        """
        loc = cls.LEGEND_LOCATIONS.get(legend_loc, legend_loc)
        if loc is None:
            leg = ax.get_legend()
            if leg is not None:
                leg.remove()
            return None
        if loc == "center left":
            # "Outside right": anchor to the right of the axes rather than
            # overlapping the data, the usual escape hatch for busy plots.
            legend = ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0.0, **kwargs)
        else:
            legend = ax.legend(loc=loc, **kwargs)
        if legend is not None:
            legend.set_draggable(True)
        return legend

    def render_histogram(self, ax, series, *, bins=30, normalization="Count", xlabel="Value", ylabel="Count", legend=True, legend_loc="Best"):
        ax.clear()
        density = normalization == "Density"
        probability = normalization == "Probability"
        for item in series:
            values = np.asarray(item.y)
            values = values[np.isfinite(values)]
            if values.size == 0:
                continue
            weights = np.full(values.size, 1.0 / values.size) if probability else None
            ax.hist(values, bins=bins, density=density, weights=weights, alpha=0.45, label=item.label,
                    color=item.color, edgecolor=item.color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Probability" if probability else ylabel)
        if legend and any(s.enabled for s in series):
            self._place_legend(ax, legend_loc)
        ax.grid(True, alpha=0.25)
        return ax

    def render_xy(self, ax, series, *, plot_type="Line", xlabel="X", ylabel="Y", title="", legend=True,
                  xscale="linear", yscale="linear", grid=True, legend_loc="Best"):
        ax.clear()
        for item in series:
            if not item.enabled:
                continue
            kwargs = dict(color=item.color, linewidth=item.line_width, markersize=item.marker_size)
            if plot_type in {"Line", "Line + Scatter"}:
                ax.plot(item.x, item.y, linestyle=item.line_style, label=item.label, **kwargs)
            if plot_type in {"Scatter", "Line + Scatter"}:
                ax.scatter(item.x, item.y, marker=self._marker(item.marker), color=item.color,
                           s=max(4.0, item.marker_size ** 2),
                           label=None if plot_type == "Line + Scatter" else item.label)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        if legend and any(s.enabled for s in series):
            self._place_legend(ax, legend_loc)
        ax.grid(grid, alpha=0.25)
        return ax


    def render_cdf(self, ax, series, *, xlabel="Value", ylabel="Cumulative probability", legend=True, legend_loc="Best"):
        ax.clear()
        for item in series:
            values = np.asarray(item.y, dtype=float)
            values = np.sort(values[np.isfinite(values)])
            if values.size == 0:
                continue
            prob = np.arange(1, values.size + 1, dtype=float) / values.size
            ax.step(values, prob, where="post", color=item.color, linewidth=item.line_width, label=item.label)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if legend and any(s.enabled for s in series):
            self._place_legend(ax, legend_loc)
        ax.grid(True, alpha=0.25)
        return ax

    def render_bar(self, ax, series, *, xlabel="", ylabel="Value", title="", legend=True):
        ax.clear()
        enabled = [s for s in series if s.enabled]
        if not enabled:
            return ax
        # Bars are intended for compact scientific summaries. For each dataset
        # the final finite value is shown, preserving the dataset labels.
        labels, values, colors = [], [], []
        for item in enabled:
            vals = np.asarray(item.y, dtype=float)
            vals = vals[np.isfinite(vals)]
            if vals.size:
                labels.append(item.label)
                values.append(float(vals[-1]))
                colors.append(item.color)
        if values:
            positions = np.arange(len(values))
            ax.bar(positions, values, color=colors, alpha=0.85)
            ax.set_xticks(positions, labels, rotation=30, ha="right")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.25)
        return ax

    def render_boxplot(self, ax, series, *, xlabel="", ylabel="Value", title="", showfliers=True):
        ax.clear()
        data, labels, colors = [], [], []
        for item in series:
            values = np.asarray(item.y, dtype=float)
            values = values[np.isfinite(values)]
            if values.size:
                data.append(values)
                labels.append(item.label)
                colors.append(item.color)
        if data:
            bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=showfliers)
            for patch, color in zip(bp["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.35)
                patch.set_edgecolor(color)
            for median, color in zip(bp["medians"], colors):
                median.set_color(color)
                median.set_linewidth(1.6)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.25)
        return ax

    def render_violin(self, ax, series, *, xlabel="", ylabel="Value", title="", showextrema=True):
        ax.clear()
        data, labels = [], []
        for item in series:
            values = np.asarray(item.y, dtype=float)
            values = values[np.isfinite(values)]
            if values.size:
                data.append(values)
                labels.append(item.label)
        if data:
            parts = ax.violinplot(data, showextrema=showextrema, showmeans=True)
            for body in parts["bodies"]:
                body.set_alpha(0.35)
            ax.set_xticks(np.arange(1, len(labels) + 1), labels, rotation=30, ha="right")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.25)
        return ax

    def render_mean_errorbar(self, ax, series, *, xlabel="X", ylabel="Mean Y", title="Mean \u00b1 1\u03c3", xscale="linear", yscale="linear", legend_loc="Best"):
        ax.clear()
        for item in series:
            x = np.asarray(item.x, dtype=float)
            y = np.asarray(item.y, dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)
            x, y = x[mask], y[mask]
            if not x.size:
                continue
            unique = np.unique(x)
            means, stds = [], []
            for value in unique:
                sample = y[x == value]
                means.append(np.mean(sample))
                stds.append(np.std(sample, ddof=1) if sample.size > 1 else 0.0)
            order = np.argsort(unique)
            unique = unique[order]
            means = np.asarray(means)[order]
            stds = np.asarray(stds)[order]
            ax.errorbar(unique, means, yerr=stds, fmt="o-", color=item.color,
                        linewidth=item.line_width, markersize=item.marker_size, label=item.label,
                        capsize=3)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        self._place_legend(ax, legend_loc)
        ax.grid(True, alpha=0.25)
        return ax

    def render_hexbin(self, ax, series, *, xlabel="X", ylabel="Y", title="Density", gridsize=35):
        ax.clear()
        drawn = False
        for item in series:
            x, y = np.asarray(item.x, dtype=float), np.asarray(item.y, dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)
            if np.count_nonzero(mask) < 3:
                continue
            ax.hexbin(x[mask], y[mask], gridsize=gridsize, mincnt=1, alpha=0.75,
                      edgecolors="none")
            drawn = True
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.15)
        return ax

    def render_correlation_heatmap(self, ax, dataset, *, title="Correlation matrix"):
        ax.clear()
        values = np.asarray(dataset.values, dtype=float)
        valid_cols = []
        for i, name in enumerate(dataset.columns):
            col = values[:, i]
            if np.count_nonzero(np.isfinite(col)) >= 2 and np.nanstd(col) > 0:
                valid_cols.append(i)
        if not valid_cols:
            ax.text(0.5, 0.5, "No variable with finite variance", ha="center", va="center")
            return ax
        clean = values[:, valid_cols]
        corr = np.corrcoef(np.nan_to_num(clean, nan=np.nanmean(clean, axis=0)), rowvar=False)
        image = ax.imshow(corr, vmin=-1, vmax=1, aspect="auto")
        labels = [dataset.columns[i] for i in valid_cols]
        ax.set_xticks(np.arange(len(labels)), labels, rotation=45, ha="right")
        ax.set_yticks(np.arange(len(labels)), labels)
        ax.set_title(title)
        for r in range(corr.shape[0]):
            for c in range(corr.shape[1]):
                if np.isfinite(corr[r, c]):
                    ax.text(c, r, f"{corr[r,c]:.2f}", ha="center", va="center", fontsize=8)
        try:
            ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")
        except Exception:
            pass
        return ax

    @staticmethod
    def _dual_resource_ticks(all_gpus):
        """Compute log2-spaced GPU tick positions/labels and their matching
        node labels (GPU / 4) for the paper's dual resource-axis layout."""
        lo = int(np.floor(np.log2(min(all_gpus))))
        hi = int(np.ceil(np.log2(max(all_gpus))))
        ticks = np.power(2.0, np.arange(lo, hi + 1, dtype=int))
        gpu_labels = [f"{int(v):g}" for v in ticks]
        node_labels = [f"{int(v / 4):g}" if (v / 4).is_integer() else f"{v / 4:g}" for v in ticks]
        xlo, xhi = ticks[0] / 1.25, ticks[-1] * 1.15
        return ticks, gpu_labels, node_labels, xlo, xhi

    def _apply_dual_resource_axes(self, ax_top, ax_bottom, all_gpus):
        """Shared GPU(top)/Node(bottom) dual resource-axis presentation.

        Both the strong- and weak-scaling paper figures share this exact
        axis treatment (log2 ticks, GPU labels pinned to the top spine,
        Node labels on the bottom panel's x-axis) -- factored out here so
        the two renderers can't drift apart and a future third scaling
        figure gets it for free.
        """
        ticks, gpu_labels, node_labels, xlo, xhi = self._dual_resource_ticks(all_gpus)
        ax_top.set_xscale("log", base=2)
        ax_bottom.set_xscale("log", base=2)
        ax_top.set_xlim(xlo, xhi)
        ax_bottom.set_xlim(xlo, xhi)
        ax_top.set_xticks(ticks)
        ax_top.set_xticklabels(gpu_labels)
        ax_top.tick_params(axis="x", which="both", labeltop=True, labelbottom=False, top=True, bottom=False, pad=3)
        ax_top.xaxis.set_label_position("top")
        ax_top.set_xlabel("GPUs", labelpad=2)
        ax_bottom.set_xticks(ticks)
        ax_bottom.set_xticklabels(node_labels)
        ax_bottom.set_xlabel("Nodes")
        ax_top.grid(True, which="major", linestyle=":", linewidth=0.6, alpha=0.35)
        ax_bottom.grid(True, which="major", linestyle=":", linewidth=0.6, alpha=0.35)
        return ticks

    def render_paper_strong_scaling(self, ax_speed, ax_eff, datasets, *, legend_loc="Lower left"):
        """Render a two-panel strong-scaling figure matching the cited paper layout.

        ``datasets`` contains tuples ``(gpus, speedup, efficiency, config)``.
        GPUs are used as the shared numerical x coordinate. The lower panel
        shows node labels (GPU/4) while the upper panel shows GPU labels at the
        top, reproducing the paper's dual resource-axis presentation.
        """
        ax_speed.clear()
        ax_eff.clear()

        all_gpus = []
        for x, speedup, efficiency, cfg in datasets:
            mask = np.isfinite(x) & np.isfinite(speedup) & np.isfinite(efficiency) & (x > 0) & (speedup > 0)
            x = np.asarray(x)[mask]
            speedup = np.asarray(speedup)[mask]
            efficiency = np.asarray(efficiency)[mask] * 100.0
            if x.size == 0:
                continue
            all_gpus.extend(x.tolist())
            order = np.argsort(x)
            x, speedup, efficiency = x[order], speedup[order], efficiency[order]
            label = cfg.label
            color = cfg.color
            ax_speed.plot(x, speedup, marker="o", linewidth=1.45, markersize=3.6,
                           color=color, label=label)
            ax_eff.plot(x, efficiency, marker="o", linewidth=1.45, markersize=3.6,
                        color=color, label=label)

            # Ideal strong scaling is speedup = P/P0, beginning at the
            # baseline resource count for each problem size.
            p0 = float(x[0])
            ideal = x / p0
            ax_speed.plot(x, ideal, linestyle="-", linewidth=0.9, color="black",
                          zorder=0, label="_nolegend_")

        if not all_gpus:
            return ax_speed, ax_eff

        self._apply_dual_resource_axes(ax_speed, ax_eff, all_gpus)
        ax_speed.set_yscale("log")
        ax_speed.set_ylabel("Speedup")
        ax_speed.set_ylim(0.85, max(2.5, max(all_gpus) / min(all_gpus) * 1.25))

        ax_eff.set_ylabel("Efficiency")
        ax_eff.set_ylim(0, 110)
        ax_eff.set_yticks([0, 25, 50, 75, 100])

        ax_speed.legend_.remove() if ax_speed.legend_ is not None else None
        self._place_legend(ax_eff, legend_loc, frameon=True, fontsize=7.5)
        return ax_speed, ax_eff

    def render_paper_weak_scaling(self, ax_runtime, ax_eff, datasets, *, legend_loc="Lower left"):
        """Render a two-panel weak-scaling figure using the same dual
        GPU/Node resource-axis presentation as ``render_paper_strong_scaling``.

        ``datasets`` contains tuples ``(gpus, normalized_runtime, efficiency,
        config)`` as produced by ``scaling.weak_scaling``. Perfect weak
        scaling keeps runtime constant as resource count and problem size
        grow together, so the ideal reference here is a flat line at
        normalized runtime = 1, rather than the diagonal ideal-speedup line
        strong scaling uses.
        """
        ax_runtime.clear()
        ax_eff.clear()

        all_gpus: list[float] = []
        all_runtime: list[float] = [1.0]  # seed with the ideal value so it's always in view
        for x, runtime, efficiency, cfg in datasets:
            mask = np.isfinite(x) & np.isfinite(runtime) & np.isfinite(efficiency) & (x > 0) & (runtime > 0)
            x = np.asarray(x)[mask]
            runtime = np.asarray(runtime)[mask]
            efficiency = np.asarray(efficiency)[mask] * 100.0
            if x.size == 0:
                continue
            all_gpus.extend(x.tolist())
            all_runtime.extend(runtime.tolist())
            order = np.argsort(x)
            x, runtime, efficiency = x[order], runtime[order], efficiency[order]
            ax_runtime.plot(x, runtime, marker="o", linewidth=1.45, markersize=3.6,
                            color=cfg.color, label=cfg.label)
            ax_eff.plot(x, efficiency, marker="o", linewidth=1.45, markersize=3.6,
                        color=cfg.color, label=cfg.label)

        if not all_gpus:
            return ax_runtime, ax_eff

        self._apply_dual_resource_axes(ax_runtime, ax_eff, all_gpus)

        ax_runtime.axhline(1.0, linestyle="-", linewidth=0.9, color="black", zorder=0, label="_nolegend_")
        spread = max(all_runtime) - min(all_runtime)
        pad = max(0.15, spread * 0.25)
        ax_runtime.set_ylim(min(all_runtime) - pad, max(all_runtime) + pad)
        ax_runtime.set_ylabel("Normalized runtime")

        ax_eff.set_ylabel("Efficiency")
        ax_eff.set_ylim(0, 110)
        ax_eff.set_yticks([0, 25, 50, 75, 100])

        ax_runtime.legend_.remove() if ax_runtime.legend_ is not None else None
        self._place_legend(ax_eff, legend_loc, frameon=True, fontsize=7.5)
        return ax_runtime, ax_eff

    def render_paper_scaling_single(self, ax, datasets, *, kind="strong", legend_loc="Best"):
        """Single-panel variant of the strong/weak scaling figures: both
        metrics share one plot via a secondary y-axis (``ax.twinx()``)
        instead of two stacked panels. Same dual GPU/Node resource axis
        (Node labels on the bottom, GPU labels on a secondary top axis),
        just folded into one panel for a more compact figure.

        ``kind`` selects which metric pair `datasets` holds: "strong" for
        ``(gpus, speedup, efficiency, config)`` tuples, "weak" for
        ``(gpus, normalized_runtime, efficiency, config)`` tuples.
        """
        ax.clear()
        ax_eff = ax.twinx()

        all_gpus: list[float] = []
        all_primary: list[float] = [1.0]
        primary_label = "Speedup" if kind == "strong" else "Normalized runtime"
        handles = []
        for x, primary, efficiency, cfg in datasets:
            mask = np.isfinite(x) & np.isfinite(primary) & np.isfinite(efficiency) & (x > 0) & (primary > 0)
            x = np.asarray(x)[mask]
            primary = np.asarray(primary)[mask]
            efficiency = np.asarray(efficiency)[mask] * 100.0
            if x.size == 0:
                continue
            all_gpus.extend(x.tolist())
            all_primary.extend(primary.tolist())
            order = np.argsort(x)
            x, primary, efficiency = x[order], primary[order], efficiency[order]
            (line,) = ax.plot(x, primary, marker="o", linewidth=1.6, markersize=4.0,
                              color=cfg.color, label=cfg.label)
            handles.append(line)
            ax_eff.plot(x, efficiency, marker="s", linewidth=1.1, markersize=3.2,
                       color=cfg.color, linestyle="--", alpha=0.6, label="_nolegend_")

            if kind == "strong":
                p0 = float(x[0])
                ax.plot(x, x / p0, linestyle="-", linewidth=0.8, color="black", zorder=0, label="_nolegend_")

        if not all_gpus:
            ax_eff.remove()
            return ax

        ticks, gpu_labels, node_labels, xlo, xhi = self._dual_resource_ticks(all_gpus)
        ax.set_xscale("log", base=2)
        ax.set_xlim(xlo, xhi)
        ax.set_xticks(ticks)
        ax.set_xticklabels(node_labels)
        ax.set_xlabel("Nodes")
        top_axis = ax.secondary_xaxis("top")
        top_axis.set_xticks(ticks)
        top_axis.set_xticklabels(gpu_labels)
        top_axis.set_xlabel("GPUs", labelpad=2)
        top_axis.tick_params(direction="out", length=3.5, width=0.7)

        if kind == "strong":
            ax.set_yscale("log")
            ax.set_ylim(0.85, max(2.5, max(all_gpus) / min(all_gpus) * 1.25))
        else:
            ax.axhline(1.0, linestyle="-", linewidth=0.9, color="black", zorder=0, label="_nolegend_")
            spread = max(all_primary) - min(all_primary)
            pad = max(0.15, spread * 0.25)
            ax.set_ylim(min(all_primary) - pad, max(all_primary) + pad)
        ax.set_ylabel(primary_label)

        ax_eff.set_ylabel("Efficiency (dashed, right axis)")
        ax_eff.set_ylim(0, 110)
        ax_eff.set_yticks([0, 25, 50, 75, 100])

        ax.grid(True, which="major", linestyle=":", linewidth=0.6, alpha=0.35)
        if handles:
            self._place_legend(ax, legend_loc, handles=handles, fontsize=7.5)
        return ax

    @staticmethod
    def _format_delta(v: float) -> str:
        magnitude = abs(v)
        if magnitude >= 100:
            return f"{v:,.0f}"
        if magnitude >= 1:
            return f"{v:,.2f}"
        return f"{v:.3g}"

    def annotate_changes(self, ax, series):
        """Draw a first->last-value change callout (arrow + text showing
        the absolute and percent change) for every series, plus light
        reference lines at each series' starting value -- the "how much
        did this grow" annotation style common in general-purpose trend
        charts (e.g. a price-vs-salary-over-time comparison). Series with
        fewer than 2 finite points are skipped silently.
        """
        seen_x = set()
        for i, item in enumerate(series):
            x = np.asarray(item.x, dtype=float)
            y = np.asarray(item.y, dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)
            x, y = x[mask], y[mask]
            if x.size < 2:
                continue
            order = np.argsort(x)
            x, y = x[order], y[order]
            x0, y0, x1, y1 = x[0], y[0], x[-1], y[-1]
            delta = y1 - y0
            pct = (delta / y0 * 100.0) if y0 != 0 else float("nan")
            sign = "+" if delta >= 0 else "\u2212"
            pct_text = f"  ({sign}{abs(pct):.0f}%)" if np.isfinite(pct) else ""
            label = item.label or f"series {i + 1}"

            # Dotted horizontal baseline at this series' own starting value,
            # in its own color; dashed vertical lines (shared across series
            # when they start/end at the same X, e.g. columns of one file)
            # marking the start/end of the range being compared.
            ax.axhline(y0, linestyle=":", linewidth=1.0, color=item.color, alpha=0.5, zorder=0)
            for edge_x in (round(float(x0), 9), round(float(x1), 9)):
                if edge_x not in seen_x:
                    ax.axvline(edge_x, linestyle="--", linewidth=1.0, color="#3a86ff", alpha=0.35, zorder=0)
                    seen_x.add(edge_x)

            offset = (-90, 24 + 18 * (i % 3)) if i % 2 == 0 else (-90, -34 - 18 * (i % 3))
            ax.annotate(
                f"{label} change, {x0:g}\u2013{x1:g}:\n{sign}{self._format_delta(abs(delta))}{pct_text}",
                xy=(x1, y1), xycoords="data", xytext=offset, textcoords="offset points",
                fontsize=8.5, color="#222222",
                arrowprops=dict(arrowstyle="->", color="#222222", linewidth=0.9, shrinkA=2, shrinkB=6),
            )
        return ax

    @staticmethod
    def apply_paper_style(ax):
        """Apply restrained publication defaults without changing data styling."""
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(direction="out", length=3.5, width=0.7)
        ax.grid(True, alpha=0.20, linewidth=0.6)
        return ax

    @staticmethod
    def _marker(marker: str) -> str:
        return {"None": "", "Circle": "o", "Square": "s", "Triangle": "^", "Diamond": "D", "Cross": "x"}.get(marker, marker)
