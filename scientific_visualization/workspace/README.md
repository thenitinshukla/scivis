# Data Workspace

A general-purpose data science workspace: Import -> Preview -> Profile ->
Clean -> Transform -> Analyze -> Visualize, built on pandas. This is a
different, complementary tool to `data_plotter/`: the Data Plotter is a
purely-numeric charting tool (CSV/TXT with float columns) built for
scientific/scaling figures; the Data Workspace handles arbitrary
real-world tabular data (mixed types, messy values, multiple formats) and
hands off to the Data Plotter's richer rendering once the data is numeric
and ready to chart.

## Layers

- `io_formats.py` -- multi-format import (CSV/TSV/TXT/JSON/Excel/Parquet)
  into a plain `pandas.DataFrame`. Delimited-text parsing reuses
  `data_plotter.parser`'s delimiter/header sniffing rather than
  duplicating it.
- `types.py` -- smart column-type detection by inspecting values, not
  just dtype (numeric/boolean/datetime/categorical/identifier/currency/
  percentage/geographic/text), plus `suggest_conversion` for proposing a
  concrete pandas dtype change (e.g. a date stored as text).
- `profiling.py` -- per-column and whole-dataset profiling (missing
  values, duplicates, cardinality, summary statistics, IQR-based outlier
  counts).
- `cleaning.py` -- the pipeline model (`PipelineStep`, `apply_pipeline`)
  and cleaning operations (remove duplicates, fill/drop missing, rename,
  change dtype, trim/standardize text, remove empty/constant columns,
  handle outliers, parse dates, extract date components, split/combine
  columns). Every operation is a plain `(df, **params) -> df` function
  registered by name into `cleaning.OPERATIONS`.
- `transforms.py` -- registers into the same `OPERATIONS` dict: filter,
  sort, select/drop columns, calculated columns, group/aggregate,
  pivot/unpivot, normalize/standardize, encode categorical, binning.
- `expressions_pandas.py` -- the restricted-namespace expression evaluator
  calculated columns use (same safety model as
  `data_plotter.expressions`: no `eval` of arbitrary Python, no builtins,
  a fixed set of NumPy math functions), adapted to operate on a
  DataFrame's Series directly.
- `recommend.py` -- chart-type suggestions from detected column types,
  either for a specific column pair or scanning the whole dataset.
- `session.py` -- `WorkspaceSession`, the object the GUI tab is built
  around: holds the untouched `original` DataFrame and a `pipeline` of
  steps; `current` is always *recomputed* by replaying the pipeline on
  `original`, which is what makes undo/reorder/toggle simple, safe
  operations rather than a bespoke history stack. `to_numeric_dataset()`
  is the bridge to `data_plotter.model.DatasetTable` for handing numeric
  columns off to the Data Plotter's rendering.
- `gui/workspace_tab.py` -- the Qt tab. The Clean and Transform sub-tabs
  share one generic, spec-driven form (`_OperationForm` + the
  `CLEAN_OPS`/`TRANSFORM_OPS` dicts) rather than one hand-written form per
  operation; adding a new operation to the UI means adding one entry to a
  spec dict, not writing new widget-wiring code.

## Why pandas, and why a separate `future.infer_string` fix

This package is pandas-based rather than reimplementing multi-format IO,
profiling, and general transforms on top of NumPy -- there's no benefit to
avoiding pandas here the way `data_plotter` avoids extra dependencies for
its narrower, purely-numeric use case.

One pandas-version pitfall worth knowing about if you extend this code:
pandas >= 3.0 defaults to inferring its new PyArrow-backed `"str"` dtype
for any string data, *even after* an explicit `.astype(object)` cast. That
dtype's `.str.*` accessor dispatches to PyArrow's RE2 regex engine, which
rejects patterns Python's `re` accepts (e.g. `\uXXXX` escapes) and has
other subtly different behavior. `workspace/__init__.py` turns this off
process-wide (`pd.set_option("future.infer_string", False)`) so every
module in this package gets predictable, classic Python-`re` semantics;
`types.to_object_str` is the accompanying helper for safely converting a
Series to plain Python strings (preserving missing values, rather than
stringifying them to `"nan"`) when you need to run string/regex ops.

## What's intentionally out of scope for now

- SQL/database sources: the request mentions "where applicable"; nothing
  is wired up yet since it needs a connection-string/credentials UI this
  first pass didn't build. `session.load_dataframe(name, df)` accepts any
  already-in-memory DataFrame, so a SQL connector can plug in there
  without changing anything else.
- The Visualize step currently recommends chart types and hands numeric
  columns to the Data Plotter for actual rendering, rather than having its
  own full charting engine for mixed-type data (e.g. a native pie chart
  from a categorical column). The recommendation logic (`recommend.py`)
  is already type-aware and ready for a native renderer to be added later.
- The Clean/Transform UI exposes the most commonly needed parameters for
  each operation (e.g. one aggregation function applied to several
  aggregate columns in `group_aggregate`, rather than a different function
  per column); every operation's full parameter set is still reachable
  programmatically via `session.add_step(op, params)` for anything the
  curated form doesn't expose.
