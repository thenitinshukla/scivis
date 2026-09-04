# Implementation Guide

This guide explains how to extend the Scientific Simulation Platform without coupling scientific logic to the Qt interface.

The key rule is:

> Implement reusable scientific behavior first, then expose it through Qt.

For the Data Plotter, the preferred architecture is:

```text
Input files
   ↓
parser.py
   ↓
model.py
   ↓
transform.py
   ↓
renderer.py
   ↓
data_plotter_tab.py
```

The first four layers should be usable in tests without creating a `QApplication`.

## 1. Understand the existing application

The project already provides several reusable conventions.

### GUI base

`scientific_visualization/gui/base_tab.py`

`BaseTab` provides:

- the scrollable control panel
- splitter-based control/view layout
- panel placement
- file-dialog helpers
- common theme handling
- typography propagation
- a `PlotCanvas` Matplotlib view by default

A new plotting tab should normally inherit from `BaseTab`.

### Plot canvas

`scientific_visualization/gui/plot_canvas.py`

`PlotCanvas` provides:

- embedded Matplotlib
- Qt navigation toolbar
- theme-aware figure handling
- high-quality figure export

Avoid creating a second Matplotlib canvas implementation unless a feature genuinely requires a different backend.

### Styling

`scientific_visualization/style.py`

Use the shared style and theme system instead of introducing a new application-wide palette.

### Export

`scientific_visualization/export/image.py`

Use `export_figure()` when a feature only needs standard Matplotlib figure export.

## 2. Data Plotter module layout

The Data Plotter currently contains:

```text
scientific_visualization/data_plotter/
├── __init__.py
├── model.py
├── parser.py
├── renderer.py
└── transform.py
```

The GUI is:

```text
scientific_visualization/gui/data_plotter_tab.py
```

### `model.py`

`DatasetTable` represents a loaded CSV/TXT table.

It owns:

- source path
- column names
- numeric values
- detected delimiter
- header status
- comment count
- skipped-row count

The model provides inspection helpers such as row/column counts and basic column statistics.

Keep this class independent of PyQt.

### `parser.py`

`parse_text_file()` is responsible for converting CSV/TXT files into a `ParseResult`.

Supported delimiter modes are represented by the `Delimiter` enum.

Parsing rules should remain here rather than in the Qt tab.

When adding support for a new textual format:

1. Extend the parser.
2. Keep its public result shape stable.
3. Add parser tests.
4. Only then add or modify GUI controls.

### `transform.py`

Transformations operate on copied NumPy arrays.

The important invariant is:

```text
source file → parsed values → copied arrays → transformed values
```

The source table must not be changed by a plot transformation.

To add a transformation:

1. Add an explicit configuration field to `TransformPipeline`.
2. Apply it to the copied array.
3. Validate invalid combinations.
4. Add a test proving both the numerical result and source immutability.

### `renderer.py`

The renderer is intentionally Qt-independent.

Methods should accept an existing Matplotlib `Axes` and plain Python/NumPy data.

For a new plot type, prefer:

```python
def render_my_plot(self, ax, series, *, ...):
    ...
    return ax
```

Do not access widgets from the renderer.

## 3. Add a new plot type

Suppose a future feature requires a stem plot.

### Step 1: Renderer

Add a method to `DataPlotRenderer`:

```python
def render_stem(self, ax, series, *, xlabel="X", ylabel="Y", legend=True):
    ax.clear()
    for item in series:
        if not item.enabled:
            continue
        markerline, stemlines, baseline = ax.stem(
            item.x,
            item.y,
            label=item.label,
        )
        markerline.set_color(item.color)
        stemlines.set_color(item.color)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if legend:
        ax.legend()
    return ax
```

The exact Matplotlib implementation can differ. The architectural point is that the renderer knows nothing about Qt.

### Step 2: GUI option

Add `"Stem"` to the plot type combo in `DataPlotterTab`.

Then dispatch:

```python
if plot_type == "Stem":
    self.renderer.render_stem(...)
```

Keep widget-specific concerns inside the tab.

### Step 3: Test the renderer

Add a Matplotlib Agg test.

Verify at least:

- axes labels
- presence of artists
- multiple-series behavior
- disabled-series behavior

## 4. Add a new scientific transformation

For example, adding a Y offset is already represented in `TransformPipeline`.

A future robust pattern is:

```python
@dataclass
class TransformPipeline:
    ...
    y_offset: float = 0.0
```

and:

```python
yy = yy + p.y_offset
```

Tests should establish:

```python
input_y = original.copy()
output_y = transform(input_y)

assert np.array_equal(input_y, original)
assert np.allclose(output_y, expected)
```

Avoid mutating a `DatasetTable.values` array directly.

## 5. Add per-dataset configuration

`DataPlotterTab` stores one small configuration dictionary per loaded dataset.

For larger features, this should be migrated gradually to a typed dataclass, for example:

```python
@dataclass
class SeriesConfig:
    x_column: int = 0
    y_column: int = 1
    label: str = ""
    color: str = "#0072B2"
    enabled: bool = True
    line_style: str = "-"
    marker: str = "None"
    line_width: float = 1.8
    marker_size: float = 4.0
```

A typed configuration object is preferred when the number of configurable fields becomes large because it is easier to validate and serialize.

Do not put such configuration directly into the parser model. File data and presentation settings are different concerns.

## 6. Add figure formatting

The later formatting phase should be implemented in a dedicated configuration object rather than adding dozens of independent attributes to the Qt tab.

A suitable direction is:

```python
@dataclass
class FigureStyle:
    font_family: str = "DejaVu Sans"
    font_size: float = 10.5
    axis_label_size: float = 10.5
    tick_label_size: float = 9.5
    legend_font_size: float = 9.5
    line_width: float = 1.8
    grid: bool = False
    xscale: str = "linear"
    yscale: str = "linear"
```

Then have the renderer consume the style.

This makes future session serialization straightforward.

## 7. Add color selection

Colors should be attached to the per-series configuration.

The shared `scientific_visualization.style.LINE_PALETTES` should be reused for default palettes.

For custom colors, the Qt layer can use the existing `BaseTab.add_color_picker_button()` helper.

The renderer should receive the resulting color value and should not open dialogs itself.

## 8. Add axis limits

Axis limits belong in plot configuration, not in the parser.

A future configuration might contain:

```python
x_min: float | None = None
x_max: float | None = None
y_min: float | None = None
y_max: float | None = None
```

At render time:

```python
if config.x_min is not None or config.x_max is not None:
    ax.set_xlim(config.x_min, config.x_max)
```

Keep `None` as the autoscale value.

## 9. Add error bars

Error bars should be introduced first as a renderer capability.

A good series model would eventually distinguish:

```text
x
y
xerr_lower
xerr_upper
yerr_lower
yerr_upper
```

The parser should only provide columns. The plotting configuration should determine which columns are interpreted as uncertainties.

The renderer can then map those arrays onto:

```python
ax.errorbar(...)
```

This separation lets the same parser support ordinary XY plots and error-bar plots.

## 10. Add filtering

Filtering should be a data-processing operation between parsing and rendering:

```text
Parser
  ↓
DatasetTable
  ↓
Filter
  ↓
Transform
  ↓
Renderer
```

Do not place numerical filtering code inside `DataPlotterTab`.

For large datasets, filtering/downsampling should happen before data reaches Matplotlib.

## 11. Large-file and background processing

The current Phase 1 implementation keeps parsing synchronous to keep the code simple.

Before adding expensive operations such as:

- very large CSV loading
- millions of points
- expensive downsampling
- batch statistics
- large-file histogram calculation

move those operations into the existing Qt worker pattern in:

```text
scientific_visualization/gui/workers.py
```

The recommended sequence is:

```text
GUI
 ↓
worker request
 ↓
background parser/processor
 ↓
Qt signal with result or error
 ↓
GUI updates model
 ↓
renderer redraw
```

Never access Qt widgets directly from a worker thread.

The worker should return plain Python/NumPy objects.

## 12. Add session save/restore

The future session feature should serialize configuration, not duplicate source files.

A session should store:

- file paths
- parser/delimiter choices
- selected columns
- transformations
- plot mode
- labels
- colors
- axes
- limits
- figure dimensions
- subplot configuration

The numerical source data should generally remain outside the project file.

On restore:

```text
Load project
  ↓
Resolve paths
  ↓
Report missing files
  ↓
Parse existing files
  ↓
Restore configuration
  ↓
Render
```

A JSON-based schema is a reasonable starting point because it is human-readable and Git-friendly.

## 13. Add subplots

Subplots should be introduced at the renderer/configuration level before adding complicated GUI controls.

A future figure model could contain:

```python
@dataclass
class FigureConfig:
    rows: int = 1
    columns: int = 1
    subplots: list[PlotConfig] = field(default_factory=list)
```

The renderer can then build:

```python
figure, axes = plt.subplots(
    figure_config.rows,
    figure_config.columns,
    ...
)
```

Each subplot should own its own plot configuration while sharing the common figure style.

## 14. GUI rules

The Data Plotter UI should remain simple.

The first visible controls should answer only:

```text
What file?
Which X?
Which Y?
Which plot?
```

Advanced options can be grouped later:

```text
Data
Axes
Style
Transform
Legend
Annotations
Export
```

Avoid adding every future feature to the main form.

## 15. Reuse existing application conventions

Before creating a new helper, search the project for an existing implementation.

Examples:

```bash
grep -R "QFileDialog" scientific_visualization/gui
grep -R "export_figure" scientific_visualization
grep -R "LINE_PALETTES" scientific_visualization
grep -R "BaseTab" scientific_visualization/gui
```

Prefer adapting an existing utility over creating another near-duplicate.

## 16. Testing strategy

Every non-trivial data feature should have a unit test.

### Parser tests

Cover:

- comma
- tab
- semicolon
- whitespace
- automatic delimiter detection
- header
- no header
- comments
- missing values
- invalid values
- inconsistent rows
- empty files
- unsupported extensions

### Transformation tests

Cover:

- scaling
- offsets
- normalization
- mathematical operations
- non-finite handling
- source-array immutability

### Renderer tests

Use:

```python
import matplotlib
matplotlib.use("Agg")
```

Then inspect artists/axes rather than relying on screenshots.

### GUI tests

Use the project's existing PyQt test conventions and cover:

- one loaded file
- multiple files
- dataset visibility
- changing X/Y
- switching plot type
- reload
- removal
- export path handling
- malformed-file error handling

## 17. Change sequence for new features

Use this development order:

```text
1. Write the data/model API
2. Implement the numerical operation
3. Add unit tests
4. Implement renderer support
5. Add GUI controls
6. Add GUI-level behavior
7. Run focused tests
8. Run full test suite
9. Update README.md
10. Update this implement_guide.md when the extension pattern changes
```

This order keeps the codebase testable and makes feature work reviewable.

## 18. Definition of done

A feature is ready to merge when:

- the existing application still starts
- the new functionality has no unnecessary Qt coupling
- normal and invalid inputs are handled
- source data is not accidentally modified
- focused tests pass
- the full test suite passes
- the code follows existing project structure
- user-facing behavior is documented
- extension points are documented when future developers need them

## 19. Common anti-patterns to avoid

### Do not parse files inside a widget callback

Bad:

```python
def on_open_clicked(self):
    # 300 lines of parsing, validation and plotting
```

Prefer:

```text
Qt event
  → parser
  → model
  → renderer
```

### Do not mutate the source data for display operations

Bad:

```python
dataset.values *= 1000
```

Prefer:

```python
x = dataset.values[:, x_index].copy()
x *= 1000
```

### Do not make renderers open Qt dialogs

Bad:

```python
renderer.export_dialog(...)
```

Prefer:

```text
Qt chooses path
Qt configures export
export helper saves figure
```

### Do not put application state into global module variables

Use explicit configuration objects or instance state where possible.

### Do not introduce a second plotting backend without a concrete requirement

The existing application already uses Matplotlib as its primary 2D renderer. Reuse it unless a feature requires another backend.

## 20. Recommended next implementation

The most useful next increment is the Phase 2 scientific formatting layer:

```text
FigureStyle
SeriesStyle
AxisStyle
PlotConfig
```

Once those configuration objects exist, the later requirements such as line styles, markers, custom colors, limits, minor ticks, publication presets, templates, and session persistence can be added without restructuring the parser or renderer.


## 5. Performance guidance

Performance-sensitive work should be classified before moving code into C++. The preferred order is:

1. Eliminate repeated I/O and repeated allocation.
2. Reuse existing renderer objects and bounded caches.
3. Use vectorized NumPy/SciPy operations, which already execute in compiled native code.
4. Move a kernel to the C++/OpenMP extension only when profiling shows that the Python layer itself is the remaining bottleneck.

For interactive viewers, avoid synchronous `canvas.draw()` calls in response to many controls. Prefer `draw_idle()` so several UI changes can be coalesced into one paint operation.

For HDF5 frame navigation, use `GridFile.info()` for metadata-only selection and `LazyGridSeries` for bounded data caching. Do not read the full field merely to populate a file list.

## 6. Add directional analysis

Reusable analysis operations belong in `scientific_visualization/analysis/derived.py` or a dedicated analysis module. The GUI should only choose the operation and its parameters.

The directional-average API accepts `x`, `y`, `z`, and `(x,y,z)` forms. A complete 3D average produces a scalar per frame and is therefore suitable for temporal-series accumulation. Keep the original arrays unchanged.

## 7. Session persistence

Session files use `scientific_visualization/session.py`. Serialize plain dictionaries, lists, and scalar values. Do not serialize Qt widget objects or Python class instances. Store paths rather than embedding large simulation arrays.

When restoring a session, validate paths, restore the selected frame, then restore view state such as axis limits or the PyVista camera. Missing source files should produce a clear user-facing error instead of a traceback.

## 8. Adding a new 3D interaction

Camera interactions belong in `scientific_visualization/visualization/three_d/pyvista_renderer.py` rather than directly manipulating PyVista from multiple UI callbacks. This keeps the camera coordinate convention in one place. The current `move_camera_screen()` method translates both the camera and focal point so the apparent image position changes without changing the view direction.

## 9. Testing new features

Test domain logic without Qt whenever possible. Current regression coverage includes:

- directional-average parsing and values
- XML session serialization
- 3D lineout indexing
- Data Plotter parsing and transformations
- existing fast 3D and backend behavior

GUI tests should be run in an environment containing the project's declared PyQt5/PyVista dependencies.
