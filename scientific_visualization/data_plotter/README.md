# Data Plotter architecture

The Data Plotter is intentionally split into small layers:

- `parser.py`: CSV/TXT parsing, delimiter and header detection. Includes a
  vectorized fast path for well-formed rectangular files, with automatic
  fallback to a fully general per-cell parser for ragged/missing data.
- `batch.py`: parallel batch loading for multiple CSV/TXT files.
- `model.py`: data tables and per-dataset plot configuration.
- `transform.py`: reusable X/Y transformations.
- `comparison.py`: single-series comparison presets such as normalization,
  speedup, and efficiency.
- `scaling.py`: strong- and weak-scaling column inference and metrics.
- `fitting.py`: user-selectable curve fitting (linear, polynomial,
  exponential, power law, logarithmic, custom) for overlaying a fitted
  curve on the Line/Scatter figure mode.
- `expressions.py`: a restricted-namespace expression evaluator shared by
  computed columns (`model.DatasetTable.add_computed_column`) and custom
  curve fits -- no `eval` of arbitrary Python, just column names and a
  fixed set of NumPy math functions.
- `renderer.py`: Matplotlib-only rendering primitives (one function per
  chart type: line/scatter, histogram, CDF, bar, box, violin, hexbin,
  correlation heatmap, mean±σ errorbar, paper strong-scaling) with no Qt
  dependencies.
- `figure_modes.py`: the Qt-free dispatcher that turns a figure-mode name
  plus a set of datasets/configs into a rendered figure by combining the
  pieces above. This is the layer to extend when adding a new figure mode
  -- it can be unit-tested without starting Qt.
- `gui/data_plotter_tab.py`: Qt controls and user interaction. Its job is
  limited to collecting widget values into a `FigureOptions` and calling
  `figure_modes.render_figure`; it does not contain any plotting logic.

This separation is important for performance and maintainability. Parsing and
numerical operations remain independent of the GUI and can therefore be
tested without starting Qt. Matplotlib and NumPy already execute their core
numerical loops in compiled code, so a C++ rewrite should only be considered
after profiling identifies a custom numerical kernel as the bottleneck.

## Available figure modes

All of the following are selectable from the "Figure mode" dropdown in the
Data Plotter tab (see `figure_modes.FIGURE_MODES`):

- **Line / Scatter** -- raw X vs Y, with a Line / Scatter / Line + Scatter style toggle.
- **Paper Strong Scaling** -- two-panel speedup + efficiency figure with dual GPU/node axes and an ideal-scaling reference line.
- **Paper Weak Scaling** -- two-panel workload-normalized runtime + efficiency figure; requires a per-dataset relative workload factor (problem size cannot be inferred from a filename).
- **Normalize Y to first / Strong scaling: speedup / Strong scaling: efficiency** -- single-panel comparison presets from `comparison.py`.
- **Histogram / Empirical CDF / Bar summary / Box plot / Violin plot** -- distribution views of the Y column across datasets.
- **Mean ± 1σ errorbar** -- mean and standard deviation of Y at each distinct X value.
- **Hexbin density** -- 2D point density, useful for large point clouds.
- **Correlation heatmap** -- Pearson correlation matrix across all numeric columns of the currently selected dataset.

## Scientific paper plotting presets

The Data Plotter accepts multiple CSV/TXT files as one experiment. Common aligned whitespace headers such as `Node    Total GPUs      Simulation time` are parsed without splitting multi-word column names.

Strong-scaling figures use the smallest positive resource count in each file as the baseline. Weak-scaling figures require an explicit relative workload factor for each file, set via the "Workload factor (selected)" control, because problem size should not be inferred from filenames.

Scaling column detection recognizes common aliases such as `Total GPUs`, `GPUs`, `Nodes`, `Processors`, `Runtime`, `Simulation time`, `Wall time`, and `Elapsed time`. Any figure mode can also use an explicit X/Y column choice from the "X column" / "Y column" dropdowns instead of the auto-detected columns.

## Interactive plotting controls

- **No auto-plot on load**: loading files never renders a figure by itself. The canvas shows a placeholder until you pick a figure mode, column, style, or click "Plot \u25b6". This avoids surprising renders (and repeated resize/redraw churn) while you're still choosing what to look at.
- **Panels: Single / Double** (paper scaling modes only): "Double" is the original two stacked panels (metric on top, efficiency on bottom). "Single" combines both into one panel using a secondary y-axis for efficiency, with the same dual GPU-top/Node-bottom resource axis.
- **Legend position**: choose a starting corner (or "Outside right", or "None" to hide it) from the "Legend position" dropdown. Independent of that setting, every legend is draggable -- click and drag it anywhere on the plot with the mouse.
- **On-screen size is fixed by design**: the interactive canvas is never resized by a figure-mode change. A `set_size_inches(..., forward=True)` call on the live Qt-embedded figure previously fought the tab's own layout system and produced corrupted/ghosted renders when switching in or out of a paper scaling mode. A fixed publication aspect ratio (e.g. a narrow two-panel portrait figure) is still available -- set it via the Export panel's Width/Height/DPI fields, which only affect the exported file, not the on-screen canvas.

## Curve fitting

The "Curve fit" box (Line / Scatter mode only) fits a curve to each enabled dataset's own X/Y column choice and overlays it as a dashed line in that dataset's color:

- **Linear**, **Polynomial** (any degree), **Exponential** (`y = a\u00b7exp(b\u00b7x)`), **Power law** (`y = a\u00b7x^b`), **Logarithmic** (`y = a\u00b7ln(x) + b`) -- all solved by ordinary least squares (linearizing the nonlinear ones via logs), so none of these need SciPy.
- **Custom**: an arbitrary formula in `x` and free parameters, e.g. `a*sin(b*x)+c`. This needs SciPy's nonlinear least squares (`scipy.optimize.curve_fit`); the app reports a clear message rather than a raw ImportError if SciPy isn't installed.
- The fitted equation and R\u00b2 for every dataset appear in the status area below the plot.
- See `data_plotter/fitting.py` for the implementation and `data_plotter/expressions.py` for the restricted-namespace expression evaluator custom fits (and computed columns, below) both rely on -- no `eval` of arbitrary Python, no builtins, no attribute/subscript access.

## Editing data

The "Edit data" box operates on the currently selected dataset's in-memory table (never the source file on disk):

- **Add row** / **Remove selected rows** (select rows in the preview table first).
- **Add computed column**: give it a name and a formula referencing existing column names verbatim (spaces and all), e.g. `Total GPUs / Node` or `log(Simulation time)`. Supported functions: the usual trig/exp/log/sqrt/abs/round family (see `expressions.SAFE_FUNCTIONS`).
- **Remove column** and **Sort by column** (ascending or descending; NaNs always sort last).

Editing a dataset that's already plotted with an X/Y column choice past the end of the new column count clamps that choice back into range rather than erroring.

## General-purpose data analysis: multiple series from one file

Real-world CSVs are usually one file with several measurement columns (e.g. `year, house_price, salary`), not one file per series. The "Additional Y columns (same file)" multi-select list (Line / Scatter mode) plots any number of extra columns from the *same* dataset as their own lines against the same X column, alongside the primary Y column -- no need to split the file or duplicate it under different configs.

Combined with **"Annotate first \u2192 last change"** (a checkbox in the same box), each series gets a callout showing its absolute and percent change from its first to last finite data point, plus light dashed/dotted reference lines at the start and end -- the common "how much did this grow" trend-chart annotation seen in data journalism and business reporting. Together these two features let a single CSV reproduce a chart like "house prices vs. salary over time, annotated with % change" without any manual annotation work.
