# Scientific Simulation Platform - Source Code Bundle

This file contains the editable source/configuration files from the project. Binary artifacts such as compiled `.so` and HDF5 sample binaries are intentionally excluded.


---

## `BUGFIX.md`

```md
# Folder/File Apply Bug Fix

Fixed the 2D Grid tab error that occurred after selecting a folder, selecting a file, and clicking **Apply selection**.

The metadata-only `GridFile.info()` path intentionally leaves `GridFile.data` as `None`. The lineout control setup was incorrectly accessing `self.grid.data.shape` before the field was lazily loaded. It now uses `self.grid.shape`, which is available from metadata and does not force a data load.

This preserves the lazy-loading design: selecting a file updates controls from metadata, and the actual field array is loaded only when the selected view is rendered.
```

---

## `BUGFIX_AI_GRIDFILE.md`

```md
# AI/GridFile signal-contract fix

The AI tab previously assumed that every `dataset_changed` signal carried the shared `Dataset` model and called `dataset.summary()` unconditionally. The grid tab could emit a metadata-only `GridFile`, which caused:

`AttributeError: 'GridFile' object has no attribute 'summary'`

The GUI contract is now normalized so the grid tab emits the shared `Dataset` when field data are available. A defensive compatibility path in the AI tab also accepts legacy `GridFile` objects without eagerly loading field data. Frame analysis explicitly converts the legacy wrapper only when data are loaded.

Validation: 20 passed, 2 skipped.
```

---

## `BUGFIX_FEATURES.md`

```md
# GUI and analysis fixes in this release

## Fields / Grid
- Added functional contour overlay controls with independent contour color map and optional contour color limits.
- Contour artists are managed using the modern Matplotlib ContourSet API, avoiding the removed `collections` attribute.
- Existing field color limits continue to control the image separately.

## 3D Viewer
- Added richer colormap choices, reverse colormap, symmetric limits, manual color limits, and opacity.
- Added explicit trackball interaction and an on-screen interaction hint.
- Camera is no longer reset when using `Add to scene`, so navigation is preserved.
- Open file and folder workflows retain an Apply selection step.

## Panel placement
- Shared tabs now allow the control panel to be placed Left, Right, Top, or Bottom.
- The splitter remains draggable so the control area can be resized interactively.

## Analysis & Modeling
- Feature and target data can be selected from a folder.
- All files can be selected or cleared with one click.
- Apply-selection buttons make the active file set explicit.
- Multi-file feature sampling is combined into one ML feature set.
- Supervised targets are sampled with the same per-file sample indices to preserve feature/target alignment.

## AI Analysis
- Series analysis now shows three plots: temporal evolution, temporal power spectrum when available, and first-to-last field change summary.
```

---

## `IMPLEMENTATION_PLAN.md`

```md
# Implementation Inspection and Prioritized Roadmap

## 1. Repository inspection

The current project already has a modular structure around a shared `Dataset` abstraction:

- `core/`: dataset, coordinates, rendering configuration
- `io/`: generic HDF5, Simulation grid/particle/track readers, lazy frame loading
- `analysis/`: lineouts, statistics, derived quantities, expressions, time series, spectral analysis, AI analysis
- `physics/`: coordinate-aware vector calculus
- `ml/`: feature extraction, classical ML, neural models, autoencoders, surrogate and active-learning foundations
- `uncertainty/`: ensemble and residual-based uncertainty utilities
- `simulation/`: external simulation process runner
- `visualization/`: 1D/2D/3D and optional GPU/VisPy rendering
- `export/`: image, animation, and OpenCV movie export
- `gui/`: Qt presentation layer
- `workflow.py`: workflow state/orchestration

### Entry point

`run_visualizer.py` imports `scientific_visualization.app:main`.

### GUI

The application uses PyQt5. Matplotlib is embedded for the main 2D/1D plotting workflow. PyVista is used for 3D rendering where available. VisPy is an optional GPU-backed 2D viewer.

### Data loading

The Simulation reader uses `GridFile`, `ParticleFile`, and `TracksFile`, all of which are exposed through `SimulationReader`. `LazyGridSeries` provides metadata-first frame discovery and small-cache frame loading.

### Existing tests

The repository contains architecture, I/O, analysis, visualization, ML, 3D, animation, spectral, and performance-backend tests.

## 2. Current feature status

| Capability | Status | Notes |
|---|---|---|
| Shared scientific Dataset | Implemented | Core abstraction used by analysis and visualization |
| Simulation HDF5 grid reader | Implemented | Includes axis metadata and physical coordinates |
| Simulation particles/tracks | Implemented | Separate readers |
| Lazy HDF5 frame loading | Implemented | Metadata-first, bounded frame cache |
| 1D/2D visualization | Implemented | Matplotlib backend |
| 2D-to-3D | Implemented | Plane, surface, extrusion |
| 3D rendering foundation | Implemented | PyVista backend |
| Optional GPU 2D rendering | Implemented | VisPy backend |
| Lineouts | Implemented | Coordinate/index based |
| Physics-aware gradients/divergence/curl/Laplacian | Implemented | Uses physical coordinate spacing |
| Safe derived expressions | Implemented | Restricted AST evaluator |
| Time-series reduction | Implemented | Frame-series reductions |
| FFT / k-spectrum / k-omega | Implemented | Uniform-coordinate validation is required |
| PCA / clustering / anomaly detection | Implemented | scikit-learn based |
| Classical regression | Implemented | Regression, gradient boosting |
| Neural-network regression | Implemented | MLP |
| Autoencoder | Implemented | Reconstruction/anomaly foundation |
| Uncertainty quantification | Implemented | Ensemble/residual foundations |
| Surrogate model | Foundation | Needs stronger workflow integration |
| Active learning | Foundation | Needs simulation-loop integration |
| Simulation runner | Foundation | External subprocess handoff |
| Model registry | Missing/partial | Needs persistent versioned model metadata/artifacts |
| POD | Missing | Planned Phase 3 |
| DMD | Missing | Planned Phase 3 |
| Parameter exploration UI | Missing/partial | Planned Phase 4 |
| Full closed-loop retraining | Missing/partial | Planned Phase 5 |

## 3. Phase plan

### Phase 1: Data integrity and performance foundation

Completed.

- Robust HDF5 scalar metadata handling
- Explicit malformed-file errors
- Metadata-first lazy loading
- Persistent renderer objects
- Bounded frame caching
- Regression tests
- Documentation of architecture and roadmap

### Phase 2: Physics and scientific analysis

Next priority.

- Complete vector-field component model (`E`, `B`, derived vectors)
- Expand physical differential operators to 1D/2D/3D cases
- Unit propagation and dimensional-consistency checks
- Safe derived-quantity provenance graph
- Spatial and temporal reduction validation
- Spectral analysis refinements

### Phase 3: Reduced-order modeling

- POD / SVD modes
- DMD and optimized DMD where appropriate
- Mode visualization and reconstruction
- Reduced-order feature generation
- Error metrics against original fields

### Phase 4: ML platform and model registry

- Unified training datasets
- Feature/target provenance
- Persistent model registry
- Hyperparameter configuration
- Cross-validation and experiment tracking
- Calibration and uncertainty evaluation
- Surrogate model comparison

### Phase 5: Active learning and simulation loop

- Parameter-space definition
- Candidate generation
- Acquisition functions
- Uncertainty-aware recommendation
- Simulation parameter-file generation
- Job execution/monitoring interface
- Automatic ingestion of completed runs
- Retraining and experiment history

### Phase 6: Integrated scientific workspace

The GUI should present one coherent workflow rather than independent feature tabs:

Simulation -> HDF5 -> Dataset -> Exploration -> Physics/Analysis -> Features -> ML -> Validation -> UQ -> Surrogate -> Active Learning -> Simulation Runner -> New Data -> Retrain

Every stage must remain accessible through reusable Python APIs independent of Qt.
```

---

## `PERFORMANCE_NOTES.md`

```md
# Performance Assessment

The main interactive slowdown was not a lack of C++ for ordinary plotting. The dominant avoidable costs were in the Qt/rendering path:

1. **Synchronous Matplotlib redraws**: `GridTab.refresh_plot()` called `canvas.draw()` after many control changes. This forced immediate rasterization on every UI event. It is now `draw_idle()`, allowing Qt/Matplotlib to coalesce repeated changes.
2. **Full-array temporary allocation for color limits**: `_plot_2d()` used `data[np.isfinite(data)]` even when only minimum and maximum values were required. That creates a second large array. The common no-clipping path now uses `np.nanmin()`/`np.nanmax()` directly.
3. **Repeated frame loading**: the Fields / Grid path already had `LazyGridSeries`, but the 3D tab loaded each selected HDF5 file directly. The 3D tab now uses a bounded `LazyGridSeries` cache for multi-frame navigation.
4. **3D rebuild cost**: the renderer already caches VTK grids and contains safeguards against expensive smoothing and normal computation. The new camera movement controls translate the camera/focal point directly and therefore do not rebuild the scene just to move the image.

## Why C++ was not used for these particular fixes

NumPy reductions and Matplotlib/VTK rendering already execute their heavy loops in compiled native code. Replacing `np.mean`, `np.nanmin`, or plotting calls with a C++ extension would introduce data-conversion and extension-call overhead while duplicating functionality that is already optimized.

The repository's existing C++/OpenMP backend remains appropriate for compute-heavy physics kernels such as gradients, divergence, Laplacian, curl, and particle-field sampling. New C++ kernels should be added only after profiling demonstrates that one of those computational kernels is the bottleneck.

## Microbenchmark

On a 2048 x 2048 float64 NumPy array in the current environment, replacing the temporary finite-value array with `np.nanmin`/`np.nanmax` reduced the local extrema operation from about 33.6 ms median in the allocation-based path to about 6.6 ms median in the direct reduction path, roughly a 5x improvement in this benchmark. Exact timings depend strongly on hardware and NumPy build, so this benchmark is intended as a regression check rather than a hardware claim.
```

---

## `README.md`

```md
# Scientific Simulation Platform

A modular Python/PyQt5 desktop application for scientific simulation visualization, data inspection, analysis, machine learning workflows, and publication-oriented plotting.

The project is organized so that scientific data operations can be reused independently of the Qt interface. The application currently supports simulation HDF5 workflows, 1D/2D/3D visualization, analysis tools, optional accelerated backends, and a new Phase 1 **Data Plotter** for quickly turning CSV/TXT numerical data into figures.

## Project status

The codebase is under active development. The current implementation includes the Phase 1 Data Plotter MVP described in the product request:

- CSV and TXT loading, including multiple files
- automatic delimiter detection with comma, tab, space, and semicolon options
- comment lines beginning with `#`
- header detection and generated column names when no header exists
- numeric columns with invalid/missing values represented as `NaN`
- clear parser errors for unsupported, empty, or malformed files
- drag-and-drop of CSV/TXT files into the Data Plotter
- per-dataset visibility and editable legend labels
- independent X/Y column selection for each loaded dataset
- line, scatter, line + scatter, and histogram plotting
- count, probability, and density histogram normalization
- linear and logarithmic X/Y axes
- editable X/Y axis labels
- Matplotlib zoom, pan, reset-view, and autoscale toolbar
- PNG, SVG, and PDF export with configurable DPI and figure dimensions
- basic data inspection
- reusable parser, data model, renderer, and transformation modules
- tests for parsing, transformations, and rendering

The current implementation also includes the recent performance and simulation-view improvements described below. The architecture remains incremental so further analysis tools can be added without rewriting the rendering stack.

## Architecture

The application uses PyQt5 for the desktop interface and Matplotlib for the main 1D/2D plotting workflow. PyVista is used for optional 3D rendering, and VisPy is an optional GPU-backed 2D viewer.

The main layers are:

```text
scientific_visualization/
├── core/                 # Shared Dataset and coordinate abstractions
├── io/                   # HDF5, simulation, particle and track readers
├── analysis/             # Statistics, lineouts, spectra, expressions, ROIs, etc.
├── physics/              # Coordinate-aware differential operators and backends
├── ml/                   # Feature extraction, models, surrogate/active-learning APIs
├── uncertainty/          # Uncertainty utilities
├── simulation/           # External simulation process runner
├── visualization/        # Reusable 1D/2D/3D/GPU renderers
├── export/               # Figure, data, animation and movie export
├── data_plotter/         # Reusable CSV/TXT plotting primitives
└── gui/                  # PyQt5 presentation layer
```

The Data Plotter specifically follows:

```text
CSV/TXT file
    ↓
data_plotter.parser
    ↓
DatasetTable
    ↓
optional TransformPipeline
    ↓
DataPlotRenderer
    ↓
PlotCanvas / DataPlotterTab
```

This keeps file parsing and numerical processing independent of Qt, which makes the functionality easier to test and extend.

## Repository layout

```text
scientific_simulation_platform/
├── run_visualizer.py
├── requirements.txt
├── pyproject.toml
├── scientific_visualization/
│   ├── core/
│   ├── io/
│   ├── analysis/
│   ├── physics/
│   ├── ml/
│   ├── uncertainty/
│   ├── simulation/
│   ├── visualization/
│   ├── export/
│   ├── data_plotter/
│   └── gui/
└── tests/
```

## Installation

Python 3.10+ is recommended.

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the main dependencies:

```bash
pip install -r requirements.txt
```

The package also contains optional components. PyVista/PyVistaQt provide the 3D viewer, scikit-learn provides the machine-learning features, OpenCV and imageio provide optional movie/export functionality, and VisPy enables the optional GPU 2D viewer.

For editable development installation:

```bash
pip install -e .
```

## Running the application

From the repository root:

```bash
python run_visualizer.py
```

The application entry point is `scientific_visualization.app:main`.

## Data Plotter

Open the **Data Plotter** tab from the main application.

The intended basic workflow is:

```text
Open Data Plotter
    ↓
Select one or more CSV/TXT files
    ↓
Check the detected columns
    ↓
Select X and Y
    ↓
Choose Line / Scatter / Line + Scatter
    ↓
Adjust axis labels or log scales
    ↓
Export PNG, SVG, or PDF
```

Files can also be dragged into the Data Plotter.

### Supported text formats

Typical CSV:

```text
Time,Energy
0.0,1.2
1.0,1.5
2.0,1.9
```

Typical whitespace-delimited TXT:

```text
0.0  1.2
1.0  1.5
2.0  1.9
```

Comments beginning with `#` are ignored:

```text
# simulation output
# columns: time energy
Time,Energy
0.0,1.2
1.0,1.5
```

Automatic detection can identify common comma, tab, semicolon, and whitespace-separated files. The selected delimiter can be changed and the dataset reloaded.

### Headers

A textual first row followed by numeric rows is treated as a header when the shape is consistent. When no header is detected, columns are named:

```text
Column 1
Column 2
Column 3
...
```

### Missing or invalid values

A field that cannot be converted to a numeric value is represented internally as `NaN`. The plotting layer filters non-finite points before drawing standard XY series, preventing malformed individual values from crashing the plot.

Rows with an incompatible number of fields are skipped and counted. A file with no usable numeric rows produces a clear `ValueError` and the GUI reports the error instead of crashing.

## Plot types

### XY plots

The Phase 1 plotter provides:

- Line
- Scatter
- Line + Scatter

Each loaded dataset has its own X and Y column selection. Dataset visibility can be enabled or disabled without removing the dataset.

### Histograms

The histogram mode uses the selected Y column as the distribution. The available normalizations are:

- Count
- Probability
- Density

Multiple loaded datasets can be displayed together with semi-transparent bars.

## Figure export

Figures can be exported as:

- PNG
- SVG
- PDF

For raster output, the DPI can be set explicitly. The export panel also allows figure dimensions to be specified in centimetres.

The renderer uses Matplotlib for vector output, so SVG and PDF can preserve vector graphics.

## Existing simulation visualization

The original application remains available alongside the Data Plotter.

### Fields / Grid

The simulation grid workflow provides HDF5 loading, frame navigation, 2D maps, lineouts, time-series reduction, ROI measurements, colorbar controls, smoothing, annotations, movie export and 3D handoff.

### 3D Viewer

The 3D workflow uses PyVista when installed and supports volume rendering, isosurfaces, clipping, camera presets, screenshots and 2D-to-3D visualization.

### Analysis and modeling

The repository includes analysis and ML infrastructure for statistics, lineouts, expressions, spectral analysis, feature extraction, classical models, neural models, uncertainty foundations, surrogate models and active-learning foundations.


## Simulation performance and interactive viewing

The simulation viewer uses lazy metadata access and a bounded frame cache. Navigating between nearby time steps therefore reuses recently loaded frames instead of reopening the same HDF5 data repeatedly. The plotting path also uses deferred Matplotlib redraws and avoids allocating a finite-value copy when only simple extrema are required.

The project already contains an optional native C++/OpenMP backend for computational kernels in `scientific_visualization/physics/`. NumPy remains the reference path. C++ is used where the operation is computationally intensive enough to justify the array conversion and extension-call overhead. Simple reductions such as `mean` are already implemented in optimized NumPy code and are intentionally not duplicated in C++.

### 3D view controls

The 3D Viewer now provides explicit left/right/up/down camera translation buttons in addition to rotation, zoom, pan, and camera presets. Previous/next frame controls use the same lazy series model as the Fields / Grid tab.

### XML sessions

Both the Fields / Grid and 3D Viewer tabs can save and restore an `.xml` session. Sessions store source paths, selected frame, plot/view settings, analysis settings, and the 3D camera position/focal point/up vector where applicable. Source data are not embedded in the XML file.

### Directional averaging

The Fields / Grid time-series mode supports:

```text
average,dir=x
average,dir=y
average,dir=z
average,dir=(x,y,z)
```

For the `(x,y,z)` form, the field is averaged over all three spatial axes for every compatible frame. The resulting scalar time series can be displayed directly in the plot and exported as CSV. The implementation uses vectorized NumPy reductions rather than a Python loop over individual grid cells.

### Example data

Example numerical text data are included under [`examples/data`](examples/data):

```text
examples/data/
├── 2d/
│   ├── sample_2d_field.txt
│   ├── sample_xy.csv
│   └── sample_with_comments_and_missing.txt
└── 3d/
    └── sample_3d_field.txt
```

These examples are intentionally small so they can be used for quick testing, parser demonstrations, and documentation screenshots.

## Performance design

The existing simulation workflow uses metadata-first HDF5 loading and a small in-memory frame cache. Rendering objects are reused where possible rather than reconstructing entire Matplotlib figures for every update.

Long-running tasks such as movie export and ML training are designed to run outside the main Qt event loop.

The Data Plotter Phase 1 parser is deliberately separated from the GUI so that background parsing can be added without changing the parser API. Large-file background processing is part of the planned next performance refinement for this module.

## Testing

Run all tests:

```bash
pytest -q
```

Run only Data Plotter tests:

```bash
pytest -q tests/test_data_plotter_parser.py \
          tests/test_data_plotter_transform.py \
          tests/test_data_plotter_renderer.py
```

Compile-check the Python package:

```bash
python -m compileall scientific_visualization
```

The Data Plotter tests cover delimiter/header handling, comments, invalid values, empty-file errors, transformation immutability, normalization, and XY/histogram rendering.

## Development principles

The project favors small domain modules over large GUI classes.

For new functionality:

1. Put file-format and numerical logic in a reusable non-Qt module.
2. Keep Qt widgets responsible for presentation and user interaction.
3. Pass explicit data/configuration objects between layers.
4. Avoid modifying source data unless an API explicitly documents mutation.
5. Reuse existing `BaseTab`, `PlotCanvas`, `style`, and export helpers.
6. Add unit tests around data-processing behavior.
7. Keep serialization-friendly configuration objects for features that will later support session save/restore.
8. Prefer incremental phases over one large UI rewrite.

See [`implement_guide.md`](implement_guide.md) for the extension workflow.

## Adding a new plot type

A plot type should normally be implemented first in `scientific_visualization/data_plotter/renderer.py`, using a renderer method that accepts plain data and an existing Matplotlib `Axes`.

The Qt layer should then add only the controls and connect those controls to the renderer.

For example:

```python
renderer.render_xy(
    ax,
    series,
    plot_type="Line",
    xlabel="Time (ps)",
    ylabel="Energy (eV)",
)
```

A new plot mode should not require moving parsing logic into the GUI.

## Roadmap

### Phase 1: Data Plotter MVP

Implemented:

- CSV/TXT loading
- multiple datasets
- delimiter/header detection
- X/Y selection
- line/scatter/line + scatter
- histogram
- visibility and labels
- linear/log axes
- basic inspection
- PNG/SVG/PDF export
- tests

### Phase 2: Scientific figure formatting

Planned:

- font family and size controls
- axis/tick/legend typography
- line width and style controls
- marker controls
- individual dataset color editing
- axis limits
- minor ticks
- grid controls
- publication template
- paper-oriented figure sizes
- DPI presets

### Phase 3: Data processing

Planned:

- scale and offset operations
- normalization
- subtraction from first value
- mathematical transforms
- filtering
- downsampling
- difference plots
- ratio plots
- error bars

### Phase 4: Paper figure tools

Planned:

- text and arrow annotations
- reference lines
- shaded regions
- subplots
- shared axes
- saved templates
- plotting sessions
- copy-to-clipboard support

The application should remain useful after every phase, with a stable build and test suite after each increment.

## Git workflow

A normal Git workflow is:

```bash
git init
git add .
git commit -m "Initial scientific visualization platform"
```

Then create a remote repository and push:

```bash
git branch -M main
git remote add origin <your-repository-url>
git push -u origin main
```

Do not commit virtual environments, build output, IDE metadata, or generated large simulation data. The repository already contains a `.gitignore`; review it before the first push.

## License

No license has been inferred or added by this implementation. Add the license file that matches the project's intended distribution terms before publishing a public repository.
```

---

## `conftest.py`

```py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
```

---

## `examples/data/2d/sample_2d_field.txt`

```txt
# Example 2D scientific data: x y field
# Columns: x, y, field
-2.000000 -1.500000 0.0019304541
-1.900000 -1.500000 0.0028512437
-1.800000 -1.500000 0.0041278442
-1.700000 -1.500000 0.0058576897
-1.600000 -1.500000 0.0081478597
-1.500000 -1.500000 0.0111089965
-1.400000 -1.500000 0.0148463683
-1.300000 -1.500000 0.0194482147
-1.200000 -1.500000 0.0249720020
-1.100000 -1.500000 0.0314297620
-1.000000 -1.500000 0.0387742078
-0.900000 -1.500000 0.0468876952
-0.800000 -1.500000 0.0555762126
-0.700000 -1.500000 0.0645703469
-0.600000 -1.500000 0.0735345438
-0.500000 -1.500000 0.0820849986
-0.400000 -1.500000 0.0898152946
-0.300000 -1.500000 0.0963276382
-0.200000 -1.500000 0.1012664619
-0.100000 -1.500000 0.1043504848
0.000000 -1.500000 0.1053992246
0.100000 -1.500000 0.1043504848
0.200000 -1.500000 0.1012664619
0.300000 -1.500000 0.0963276382
0.400000 -1.500000 0.0898152946
0.500000 -1.500000 0.0820849986
0.600000 -1.500000 0.0735345438
0.700000 -1.500000 0.0645703469
0.800000 -1.500000 0.0555762126
0.900000 -1.500000 0.0468876952
1.000000 -1.500000 0.0387742078
1.100000 -1.500000 0.0314297620
1.200000 -1.500000 0.0249720020
1.300000 -1.500000 0.0194482147
1.400000 -1.500000 0.0148463683
1.500000 -1.500000 0.0111089965
1.600000 -1.500000 0.0081478597
1.700000 -1.500000 0.0058576897
1.800000 -1.500000 0.0041278442
1.900000 -1.500000 0.0028512437
2.000000 -1.500000 0.0019304541
-2.000000 -1.400000 0.0025799120
-1.900000 -1.400000 0.0038104804
-1.800000 -1.400000 0.0055165644
-1.700000 -1.400000 0.0078283775
-1.600000 -1.400000 0.0108890237
-1.500000 -1.400000 0.0148463683
-1.400000 -1.400000 0.0198410947
-1.300000 -1.400000 0.0259911288
-1.200000 -1.400000 0.0333732700
-1.100000 -1.400000 0.0420035979
-1.000000 -1.400000 0.0518189172
-0.900000 -1.400000 0.0626620047
-0.800000 -1.400000 0.0742735782
-0.700000 -1.400000 0.0862935865
-0.600000 -1.400000 0.0982735856
-0.500000 -1.400000 0.1097006485
-0.400000 -1.400000 0.1200316285
-0.300000 -1.400000 0.1287349036
-0.200000 -1.400000 0.1353352832
-0.100000 -1.400000 0.1394568562
0.000000 -1.400000 0.1408584209
0.100000 -1.400000 0.1394568562
0.200000 -1.400000 0.1353352832
0.300000 -1.400000 0.1287349036
0.400000 -1.400000 0.1200316285
0.500000 -1.400000 0.1097006485
0.600000 -1.400000 0.0982735856
0.700000 -1.400000 0.0862935865
0.800000 -1.400000 0.0742735782
0.900000 -1.400000 0.0626620047
1.000000 -1.400000 0.0518189172
1.100000 -1.400000 0.0420035979
1.200000 -1.400000 0.0333732700
1.300000 -1.400000 0.0259911288
1.400000 -1.400000 0.0198410947
1.500000 -1.400000 0.0148463683
1.600000 -1.400000 0.0108890237
1.700000 -1.400000 0.0078283775
1.800000 -1.400000 0.0055165644
1.900000 -1.400000 0.0038104804
2.000000 -1.400000 0.0025799120
-2.000000 -1.300000 0.0033795930
-1.900000 -1.300000 0.0049915939
-1.800000 -1.300000 0.0072265033
-1.700000 -1.300000 0.0102548963
-1.600000 -1.300000 0.0142642339
-1.500000 -1.300000 0.0194482147
-1.400000 -1.300000 0.0259911288
-1.300000 -1.300000 0.0340474547
-1.200000 -1.300000 0.0437177973
-1.100000 -1.300000 0.0550232201
-1.000000 -1.300000 0.0678809394
-0.900000 -1.300000 0.0820849986
-0.800000 -1.300000 0.0972957471
-0.700000 -1.300000 0.1130415306
-0.600000 -1.300000 0.1287349036
-0.500000 -1.300000 0.1437039498
-0.400000 -1.300000 0.1572371663
-0.300000 -1.300000 0.1686381473
-0.200000 -1.300000 0.1772844100
-0.100000 -1.300000 0.1826835241
0.000000 -1.300000 0.1845195240
0.100000 -1.300000 0.1826835241
0.200000 -1.300000 0.1772844100
0.300000 -1.300000 0.1686381473
0.400000 -1.300000 0.1572371663
0.500000 -1.300000 0.1437039498
0.600000 -1.300000 0.1287349036
0.700000 -1.300000 0.1130415306
0.800000 -1.300000 0.0972957471
0.900000 -1.300000 0.0820849986
1.000000 -1.300000 0.0678809394
1.100000 -1.300000 0.0550232201
1.200000 -1.300000 0.0437177973
1.300000 -1.300000 0.0340474547
1.400000 -1.300000 0.0259911288
1.500000 -1.300000 0.0194482147
1.600000 -1.300000 0.0142642339
1.700000 -1.300000 0.0102548963
1.800000 -1.300000 0.0072265033
1.900000 -1.300000 0.0049915939
2.000000 -1.300000 0.0033795930
-2.000000 -1.200000 0.0043394833
-1.900000 -1.200000 0.0064093334
-1.800000 -1.200000 0.0092790139
-1.700000 -1.200000 0.0131675475
-1.600000 -1.200000 0.0183156389
-1.500000 -1.200000 0.0249720020
-1.400000 -1.200000 0.0333732700
-1.300000 -1.200000 0.0437177973
-1.200000 -1.200000 0.0561347628
-1.100000 -1.200000 0.0706512131
-1.000000 -1.200000 0.0871608515
-0.900000 -1.200000 0.1053992246
-0.800000 -1.200000 0.1249302122
-0.700000 -1.200000 0.1451481985
-0.600000 -1.200000 0.1652988882
-0.500000 -1.200000 0.1845195240
-0.400000 -1.200000 0.2018965180
-0.300000 -1.200000 0.2165356673
-0.200000 -1.200000 0.2276376884
-0.100000 -1.200000 0.2345702881
0.000000 -1.200000 0.2369277587
0.100000 -1.200000 0.2345702881
0.200000 -1.200000 0.2276376884
0.300000 -1.200000 0.2165356673
0.400000 -1.200000 0.2018965180
0.500000 -1.200000 0.1845195240
0.600000 -1.200000 0.1652988882
0.700000 -1.200000 0.1451481985
0.800000 -1.200000 0.1249302122
0.900000 -1.200000 0.1053992246
1.000000 -1.200000 0.0871608515
1.100000 -1.200000 0.0706512131
1.200000 -1.200000 0.0561347628
1.300000 -1.200000 0.0437177973
1.400000 -1.200000 0.0333732700
1.500000 -1.200000 0.0249720020
1.600000 -1.200000 0.0183156389
1.700000 -1.200000 0.0131675475
1.800000 -1.200000 0.0092790139
1.900000 -1.200000 0.0064093334
2.000000 -1.200000 0.0043394833
-2.000000 -1.100000 0.0054616737
-1.900000 -1.100000 0.0080667871
-1.800000 -1.100000 0.0116785670
-1.700000 -1.100000 0.0165726754
-1.600000 -1.100000 0.0230520633
-1.500000 -1.100000 0.0314297620
-1.400000 -1.100000 0.0420035979
-1.300000 -1.100000 0.0550232201
-1.200000 -1.100000 0.0706512131
-1.100000 -1.100000 0.0889216175
-1.000000 -1.100000 0.1097006485
-0.900000 -1.100000 0.1326554651
-0.800000 -1.100000 0.1572371663
-0.700000 -1.100000 0.1826835241
-0.600000 -1.100000 0.2080451824
-0.500000 -1.100000 0.2322362747
-0.400000 -1.100000 0.2541069596
-0.300000 -1.100000 0.2725317930
-0.200000 -1.100000 0.2865047969
-0.100000 -1.100000 0.2952301669
0.000000 -1.100000 0.2981972794
0.100000 -1.100000 0.2952301669
0.200000 -1.100000 0.2865047969
0.300000 -1.100000 0.2725317930
0.400000 -1.100000 0.2541069596
0.500000 -1.100000 0.2322362747
0.600000 -1.100000 0.2080451824
0.700000 -1.100000 0.1826835241
0.800000 -1.100000 0.1572371663
0.900000 -1.100000 0.1326554651
1.000000 -1.100000 0.1097006485
1.100000 -1.100000 0.0889216175
1.200000 -1.100000 0.0706512131
1.300000 -1.100000 0.0550232201
1.400000 -1.100000 0.0420035979
1.500000 -1.100000 0.0314297620
1.600000 -1.100000 0.0230520633
1.700000 -1.100000 0.0165726754
1.800000 -1.100000 0.0116785670
1.900000 -1.100000 0.0080667871
2.000000 -1.100000 0.0054616737
-2.000000 -1.000000 0.0067379470
-1.900000 -1.000000 0.0099518183
-1.800000 -1.000000 0.0144075918
-1.700000 -1.000000 0.0204453460
-1.600000 -1.000000 0.0284388247
-1.500000 -1.000000 0.0387742078
-1.400000 -1.000000 0.0518189172
-1.300000 -1.000000 0.0678809394
-1.200000 -1.000000 0.0871608515
-1.100000 -1.000000 0.1097006485
-1.000000 -1.000000 0.1353352832
-0.900000 -1.000000 0.1636541368
-0.800000 -1.000000 0.1939800423
-0.700000 -1.000000 0.2253726555
-0.600000 -1.000000 0.2566607770
-0.500000 -1.000000 0.2865047969
-0.400000 -1.000000 0.3134861809
-0.300000 -1.000000 0.3362164937
-0.200000 -1.000000 0.3534546820
-0.100000 -1.000000 0.3642189796
0.000000 -1.000000 0.3678794412
0.100000 -1.000000 0.3642189796
0.200000 -1.000000 0.3534546820
0.300000 -1.000000 0.3362164937
0.400000 -1.000000 0.3134861809
0.500000 -1.000000 0.2865047969
0.600000 -1.000000 0.2566607770
0.700000 -1.000000 0.2253726555
0.800000 -1.000000 0.1939800423
0.900000 -1.000000 0.1636541368
1.000000 -1.000000 0.1353352832
1.100000 -1.000000 0.1097006485
1.200000 -1.000000 0.0871608515
1.300000 -1.000000 0.0678809394
1.400000 -1.000000 0.0518189172
1.500000 -1.000000 0.0387742078
1.600000 -1.000000 0.0284388247
1.700000 -1.000000 0.0204453460
1.800000 -1.000000 0.0144075918
1.900000 -1.000000 0.0099518183
2.000000 -1.000000 0.0067379470
-2.000000 -0.900000 0.0081478597
-1.900000 -0.900000 0.0120342323
-1.800000 -0.900000 0.0174223746
-1.700000 -0.900000 0.0247235265
-1.600000 -0.900000 0.0343896373
-1.500000 -0.900000 0.0468876952
-1.400000 -0.900000 0.0626620047
-1.300000 -0.900000 0.0820849986
-1.200000 -0.900000 0.1053992246
-1.100000 -0.900000 0.1326554651
-1.000000 -0.900000 0.1636541368
-0.900000 -0.900000 0.1978986991
-0.800000 -0.900000 0.2345702881
-0.700000 -0.900000 0.2725317930
-0.600000 -0.900000 0.3103669413
-0.500000 -0.900000 0.3464558103
-0.400000 -0.900000 0.3790830381
-0.300000 -0.900000 0.4065696597
-0.200000 -0.900000 0.4274149319
-0.100000 -0.900000 0.4404316545
0.000000 -0.900000 0.4448580662
0.100000 -0.900000 0.4404316545
0.200000 -0.900000 0.4274149319
0.300000 -0.900000 0.4065696597
0.400000 -0.900000 0.3790830381
0.500000 -0.900000 0.3464558103
0.600000 -0.900000 0.3103669413
0.700000 -0.900000 0.2725317930
0.800000 -0.900000 0.2345702881
0.900000 -0.900000 0.1978986991
1.000000 -0.900000 0.1636541368
1.100000 -0.900000 0.1326554651
1.200000 -0.900000 0.1053992246
1.300000 -0.900000 0.0820849986
1.400000 -0.900000 0.0626620047
1.500000 -0.900000 0.0468876952
1.600000 -0.900000 0.0343896373
1.700000 -0.900000 0.0247235265
1.800000 -0.900000 0.0174223746
1.900000 -0.900000 0.0120342323
2.000000 -0.900000 0.0081478597
-2.000000 -0.800000 0.0096576976
-1.900000 -0.800000 0.0142642339
-1.800000 -0.800000 0.0206508252
-1.700000 -0.800000 0.0293049159
-1.600000 -0.800000 0.0407622040
-1.500000 -0.800000 0.0555762126
-1.400000 -0.800000 0.0742735782
-1.300000 -0.800000 0.0972957471
-1.200000 -0.800000 0.1249302122
-1.100000 -0.800000 0.1572371663
-1.000000 -0.800000 0.1939800423
-0.900000 -0.800000 0.2345702881
-0.800000 -0.800000 0.2780373005
-0.700000 -0.800000 0.3230332564
-0.600000 -0.800000 0.3678794412
-0.500000 -0.800000 0.4106557528
-0.400000 -0.800000 0.4493289641
-0.300000 -0.800000 0.4819089901
-0.200000 -0.800000 0.5066169924
-0.100000 -0.800000 0.5220457768
0.000000 -0.800000 0.5272924240
0.100000 -0.800000 0.5220457768
0.200000 -0.800000 0.5066169924
0.300000 -0.800000 0.4819089901
0.400000 -0.800000 0.4493289641
0.500000 -0.800000 0.4106557528
0.600000 -0.800000 0.3678794412
0.700000 -0.800000 0.3230332564
0.800000 -0.800000 0.2780373005
0.900000 -0.800000 0.2345702881
1.000000 -0.800000 0.1939800423
1.100000 -0.800000 0.1572371663
1.200000 -0.800000 0.1249302122
1.300000 -0.800000 0.0972957471
1.400000 -0.800000 0.0742735782
1.500000 -0.800000 0.0555762126
1.600000 -0.800000 0.0407622040
1.700000 -0.800000 0.0293049159
1.800000 -0.800000 0.0206508252
1.900000 -0.800000 0.0142642339
2.000000 -0.800000 0.0096576976
-2.000000 -0.700000 0.0112206438
-1.900000 -0.700000 0.0165726754
-1.800000 -0.700000 0.0239928358
-1.700000 -0.700000 0.0340474547
-1.600000 -0.700000 0.0473589244
-1.500000 -0.700000 0.0645703469
-1.400000 -0.700000 0.0862935865
-1.300000 -0.700000 0.1130415306
-1.200000 -0.700000 0.1451481985
-1.100000 -0.700000 0.1826835241
-1.000000 -0.700000 0.2253726555
-0.900000 -0.700000 0.2725317930
-0.800000 -0.700000 0.3230332564
-0.700000 -0.700000 0.3753110989
-0.600000 -0.700000 0.4274149319
-0.500000 -0.700000 0.4771139155
-0.400000 -0.700000 0.5220457768
-0.300000 -0.700000 0.5598983666
-0.200000 -0.700000 0.5886049697
-0.100000 -0.700000 0.6065306597
0.000000 -0.700000 0.6126263942
0.100000 -0.700000 0.6065306597
0.200000 -0.700000 0.5886049697
0.300000 -0.700000 0.5598983666
0.400000 -0.700000 0.5220457768
0.500000 -0.700000 0.4771139155
0.600000 -0.700000 0.4274149319
0.700000 -0.700000 0.3753110989
0.800000 -0.700000 0.3230332564
0.900000 -0.700000 0.2725317930
1.000000 -0.700000 0.2253726555
1.100000 -0.700000 0.1826835241
1.200000 -0.700000 0.1451481985
1.300000 -0.700000 0.1130415306
1.400000 -0.700000 0.0862935865
1.500000 -0.700000 0.0645703469
1.600000 -0.700000 0.0473589244
1.700000 -0.700000 0.0340474547
1.800000 -0.700000 0.0239928358
1.900000 -0.700000 0.0165726754
2.000000 -0.700000 0.0112206438
-2.000000 -0.600000 0.0127783876
-1.900000 -0.600000 0.0188734331
-1.800000 -0.600000 0.0273237224
-1.700000 -0.600000 0.0387742078
-1.600000 -0.600000 0.0539336873
-1.500000 -0.600000 0.0735345438
-1.400000 -0.600000 0.0982735856
-1.300000 -0.600000 0.1287349036
-1.200000 -0.600000 0.1652988882
-1.100000 -0.600000 0.2080451824
-1.000000 -0.600000 0.2566607770
-0.900000 -0.600000 0.3103669413
-0.800000 -0.600000 0.3678794412
-0.700000 -0.600000 0.4274149319
-0.600000 -0.600000 0.4867522560
-0.500000 -0.600000 0.5433508691
-0.400000 -0.600000 0.5945205480
-0.300000 -0.600000 0.6376281516
-0.200000 -0.600000 0.6703200460
-0.100000 -0.600000 0.6907343306
0.000000 -0.600000 0.6976763261
0.100000 -0.600000 0.6907343306
0.200000 -0.600000 0.6703200460
0.300000 -0.600000 0.6376281516
0.400000 -0.600000 0.5945205480
0.500000 -0.600000 0.5433508691
0.600000 -0.600000 0.4867522560
0.700000 -0.600000 0.4274149319
0.800000 -0.600000 0.3678794412
0.900000 -0.600000 0.3103669413
1.000000 -0.600000 0.2566607770
1.100000 -0.600000 0.2080451824
1.200000 -0.600000 0.1652988882
1.300000 -0.600000 0.1287349036
1.400000 -0.600000 0.0982735856
1.500000 -0.600000 0.0735345438
1.600000 -0.600000 0.0539336873
1.700000 -0.600000 0.0387742078
1.800000 -0.600000 0.0273237224
1.900000 -0.600000 0.0188734331
2.000000 -0.600000 0.0127783876
-2.000000 -0.500000 0.0142642339
-1.900000 -0.500000 0.0210679995
-1.800000 -0.500000 0.0305008722
-1.700000 -0.500000 0.0432827979
-1.600000 -0.500000 0.0602049924
-1.500000 -0.500000 0.0820849986
-1.400000 -0.500000 0.1097006485
-1.300000 -0.500000 0.1437039498
-1.200000 -0.500000 0.1845195240
-1.100000 -0.500000 0.2322362747
-1.000000 -0.500000 0.2865047969
-0.900000 -0.500000 0.3464558103
-0.800000 -0.500000 0.4106557528
-0.700000 -0.500000 0.4771139155
-0.600000 -0.500000 0.5433508691
-0.500000 -0.500000 0.6065306597
-0.400000 -0.500000 0.6636502501
-0.300000 -0.500000 0.7117703228
-0.200000 -0.500000 0.7482635676
-0.100000 -0.500000 0.7710515858
0.000000 -0.500000 0.7788007831
0.100000 -0.500000 0.7710515858
0.200000 -0.500000 0.7482635676
0.300000 -0.500000 0.7117703228
0.400000 -0.500000 0.6636502501
0.500000 -0.500000 0.6065306597
0.600000 -0.500000 0.5433508691
0.700000 -0.500000 0.4771139155
0.800000 -0.500000 0.4106557528
0.900000 -0.500000 0.3464558103
1.000000 -0.500000 0.2865047969
1.100000 -0.500000 0.2322362747
1.200000 -0.500000 0.1845195240
1.300000 -0.500000 0.1437039498
1.400000 -0.500000 0.1097006485
1.500000 -0.500000 0.0820849986
1.600000 -0.500000 0.0602049924
1.700000 -0.500000 0.0432827979
1.800000 -0.500000 0.0305008722
1.900000 -0.500000 0.0210679995
2.000000 -0.500000 0.0142642339
-2.000000 -0.400000 0.0156075579
-1.900000 -0.400000 0.0230520633
-1.800000 -0.400000 0.0333732700
-1.700000 -0.400000 0.0473589244
-1.600000 -0.400000 0.0658747544
-1.500000 -0.400000 0.0898152946
-1.400000 -0.400000 0.1200316285
-1.300000 -0.400000 0.1572371663
-1.200000 -0.400000 0.2018965180
-1.100000 -0.400000 0.2541069596
-1.000000 -0.400000 0.3134861809
-0.900000 -0.400000 0.3790830381
-0.800000 -0.400000 0.4493289641
-0.700000 -0.400000 0.5220457768
-0.600000 -0.400000 0.5945205480
-0.500000 -0.400000 0.6636502501
-0.400000 -0.400000 0.7261490371
-0.300000 -0.400000 0.7788007831
-0.200000 -0.400000 0.8187307531
-0.100000 -0.400000 0.8436648166
0.000000 -0.400000 0.8521437890
0.100000 -0.400000 0.8436648166
0.200000 -0.400000 0.8187307531
0.300000 -0.400000 0.7788007831
0.400000 -0.400000 0.7261490371
0.500000 -0.400000 0.6636502501
0.600000 -0.400000 0.5945205480
0.700000 -0.400000 0.5220457768
0.800000 -0.400000 0.4493289641
0.900000 -0.400000 0.3790830381
1.000000 -0.400000 0.3134861809
1.100000 -0.400000 0.2541069596
1.200000 -0.400000 0.2018965180
1.300000 -0.400000 0.1572371663
1.400000 -0.400000 0.1200316285
1.500000 -0.400000 0.0898152946
1.600000 -0.400000 0.0658747544
1.700000 -0.400000 0.0473589244
1.800000 -0.400000 0.0333732700
1.900000 -0.400000 0.0230520633
2.000000 -0.400000 0.0156075579
-2.000000 -0.300000 0.0167392336
-1.900000 -0.300000 0.0247235265
-1.800000 -0.300000 0.0357931051
-1.700000 -0.300000 0.0507928339
-1.600000 -0.300000 0.0706512131
-1.500000 -0.300000 0.0963276382
-1.400000 -0.300000 0.1287349036
-1.300000 -0.300000 0.1686381473
-1.200000 -0.300000 0.2165356673
-1.100000 -0.300000 0.2725317930
-1.000000 -0.300000 0.3362164937
-0.900000 -0.300000 0.4065696597
-0.800000 -0.300000 0.4819089901
-0.700000 -0.300000 0.5598983666
-0.600000 -0.300000 0.6376281516
-0.500000 -0.300000 0.7117703228
-0.400000 -0.300000 0.7788007831
-0.300000 -0.300000 0.8352702114
-0.200000 -0.300000 0.8780954309
-0.100000 -0.300000 0.9048374180
0.000000 -0.300000 0.9139311853
0.100000 -0.300000 0.9048374180
0.200000 -0.300000 0.8780954309
0.300000 -0.300000 0.8352702114
0.400000 -0.300000 0.7788007831
0.500000 -0.300000 0.7117703228
0.600000 -0.300000 0.6376281516
0.700000 -0.300000 0.5598983666
0.800000 -0.300000 0.4819089901
0.900000 -0.300000 0.4065696597
1.000000 -0.300000 0.3362164937
1.100000 -0.300000 0.2725317930
1.200000 -0.300000 0.2165356673
1.300000 -0.300000 0.1686381473
1.400000 -0.300000 0.1287349036
1.500000 -0.300000 0.0963276382
1.600000 -0.300000 0.0706512131
1.700000 -0.300000 0.0507928339
1.800000 -0.300000 0.0357931051
1.900000 -0.300000 0.0247235265
2.000000 -0.300000 0.0167392336
-2.000000 -0.200000 0.0175974724
-1.900000 -0.200000 0.0259911288
-1.800000 -0.200000 0.0376282568
-1.700000 -0.200000 0.0533970381
-1.600000 -0.200000 0.0742735782
-1.500000 -0.200000 0.1012664619
-1.400000 -0.200000 0.1353352832
-1.300000 -0.200000 0.1772844100
-1.200000 -0.200000 0.2276376884
-1.100000 -0.200000 0.2865047969
-1.000000 -0.200000 0.3534546820
-0.900000 -0.200000 0.4274149319
-0.800000 -0.200000 0.5066169924
-0.700000 -0.200000 0.5886049697
-0.600000 -0.200000 0.6703200460
-0.500000 -0.200000 0.7482635676
-0.400000 -0.200000 0.8187307531
-0.300000 -0.200000 0.8780954309
-0.200000 -0.200000 0.9231163464
-0.100000 -0.200000 0.9512294245
0.000000 -0.200000 0.9607894392
0.100000 -0.200000 0.9512294245
0.200000 -0.200000 0.9231163464
0.300000 -0.200000 0.8780954309
0.400000 -0.200000 0.8187307531
0.500000 -0.200000 0.7482635676
0.600000 -0.200000 0.6703200460
0.700000 -0.200000 0.5886049697
0.800000 -0.200000 0.5066169924
0.900000 -0.200000 0.4274149319
1.000000 -0.200000 0.3534546820
1.100000 -0.200000 0.2865047969
1.200000 -0.200000 0.2276376884
1.300000 -0.200000 0.1772844100
1.400000 -0.200000 0.1353352832
1.500000 -0.200000 0.1012664619
1.600000 -0.200000 0.0742735782
1.700000 -0.200000 0.0533970381
1.800000 -0.200000 0.0376282568
1.900000 -0.200000 0.0259911288
2.000000 -0.200000 0.0175974724
-2.000000 -0.100000 0.0181333952
-1.900000 -0.100000 0.0267826765
-1.800000 -0.100000 0.0387742078
-1.700000 -0.100000 0.0550232201
-1.600000 -0.100000 0.0765355454
-1.500000 -0.100000 0.1043504848
-1.400000 -0.100000 0.1394568562
-1.300000 -0.100000 0.1826835241
-1.200000 -0.100000 0.2345702881
-1.100000 -0.100000 0.2952301669
-1.000000 -0.100000 0.3642189796
-0.900000 -0.100000 0.4404316545
-0.800000 -0.100000 0.5220457768
-0.700000 -0.100000 0.6065306597
-0.600000 -0.100000 0.6907343306
-0.500000 -0.100000 0.7710515858
-0.400000 -0.100000 0.8436648166
-0.300000 -0.100000 0.9048374180
-0.200000 -0.100000 0.9512294245
-0.100000 -0.100000 0.9801986733
0.000000 -0.100000 0.9900498337
0.100000 -0.100000 0.9801986733
0.200000 -0.100000 0.9512294245
0.300000 -0.100000 0.9048374180
0.400000 -0.100000 0.8436648166
0.500000 -0.100000 0.7710515858
0.600000 -0.100000 0.6907343306
0.700000 -0.100000 0.6065306597
0.800000 -0.100000 0.5220457768
0.900000 -0.100000 0.4404316545
1.000000 -0.100000 0.3642189796
1.100000 -0.100000 0.2952301669
1.200000 -0.100000 0.2345702881
1.300000 -0.100000 0.1826835241
1.400000 -0.100000 0.1394568562
1.500000 -0.100000 0.1043504848
1.600000 -0.100000 0.0765355454
1.700000 -0.100000 0.0550232201
1.800000 -0.100000 0.0387742078
1.900000 -0.100000 0.0267826765
2.000000 -0.100000 0.0181333952
-2.000000 0.000000 0.0183156389
-1.900000 0.000000 0.0270518469
-1.800000 0.000000 0.0391638951
-1.700000 0.000000 0.0555762126
-1.600000 0.000000 0.0773047404
-1.500000 0.000000 0.1053992246
-1.400000 0.000000 0.1408584209
-1.300000 0.000000 0.1845195240
-1.200000 0.000000 0.2369277587
-1.100000 0.000000 0.2981972794
-1.000000 0.000000 0.3678794412
-0.900000 0.000000 0.4448580662
-0.800000 0.000000 0.5272924240
-0.700000 0.000000 0.6126263942
-0.600000 0.000000 0.6976763261
-0.500000 0.000000 0.7788007831
-0.400000 0.000000 0.8521437890
-0.300000 0.000000 0.9139311853
-0.200000 0.000000 0.9607894392
-0.100000 0.000000 0.9900498337
0.000000 0.000000 1.0000000000
0.100000 0.000000 0.9900498337
0.200000 0.000000 0.9607894392
0.300000 0.000000 0.9139311853
0.400000 0.000000 0.8521437890
0.500000 0.000000 0.7788007831
0.600000 0.000000 0.6976763261
0.700000 0.000000 0.6126263942
0.800000 0.000000 0.5272924240
0.900000 0.000000 0.4448580662
1.000000 0.000000 0.3678794412
1.100000 0.000000 0.2981972794
1.200000 0.000000 0.2369277587
1.300000 0.000000 0.1845195240
1.400000 0.000000 0.1408584209
1.500000 0.000000 0.1053992246
1.600000 0.000000 0.0773047404
1.700000 0.000000 0.0555762126
1.800000 0.000000 0.0391638951
1.900000 0.000000 0.0270518469
2.000000 0.000000 0.0183156389
-2.000000 0.100000 0.0181333952
-1.900000 0.100000 0.0267826765
-1.800000 0.100000 0.0387742078
-1.700000 0.100000 0.0550232201
-1.600000 0.100000 0.0765355454
-1.500000 0.100000 0.1043504848
-1.400000 0.100000 0.1394568562
-1.300000 0.100000 0.1826835241
-1.200000 0.100000 0.2345702881
-1.100000 0.100000 0.2952301669
-1.000000 0.100000 0.3642189796
-0.900000 0.100000 0.4404316545
-0.800000 0.100000 0.5220457768
-0.700000 0.100000 0.6065306597
-0.600000 0.100000 0.6907343306
-0.500000 0.100000 0.7710515858
-0.400000 0.100000 0.8436648166
-0.300000 0.100000 0.9048374180
-0.200000 0.100000 0.9512294245
-0.100000 0.100000 0.9801986733
0.000000 0.100000 0.9900498337
0.100000 0.100000 0.9801986733
0.200000 0.100000 0.9512294245
0.300000 0.100000 0.9048374180
0.400000 0.100000 0.8436648166
0.500000 0.100000 0.7710515858
0.600000 0.100000 0.6907343306
0.700000 0.100000 0.6065306597
0.800000 0.100000 0.5220457768
0.900000 0.100000 0.4404316545
1.000000 0.100000 0.3642189796
1.100000 0.100000 0.2952301669
1.200000 0.100000 0.2345702881
1.300000 0.100000 0.1826835241
1.400000 0.100000 0.1394568562
1.500000 0.100000 0.1043504848
1.600000 0.100000 0.0765355454
1.700000 0.100000 0.0550232201
1.800000 0.100000 0.0387742078
1.900000 0.100000 0.0267826765
2.000000 0.100000 0.0181333952
-2.000000 0.200000 0.0175974724
-1.900000 0.200000 0.0259911288
-1.800000 0.200000 0.0376282568
-1.700000 0.200000 0.0533970381
-1.600000 0.200000 0.0742735782
-1.500000 0.200000 0.1012664619
-1.400000 0.200000 0.1353352832
-1.300000 0.200000 0.1772844100
-1.200000 0.200000 0.2276376884
-1.100000 0.200000 0.2865047969
-1.000000 0.200000 0.3534546820
-0.900000 0.200000 0.4274149319
-0.800000 0.200000 0.5066169924
-0.700000 0.200000 0.5886049697
-0.600000 0.200000 0.6703200460
-0.500000 0.200000 0.7482635676
-0.400000 0.200000 0.8187307531
-0.300000 0.200000 0.8780954309
-0.200000 0.200000 0.9231163464
-0.100000 0.200000 0.9512294245
0.000000 0.200000 0.9607894392
0.100000 0.200000 0.9512294245
0.200000 0.200000 0.9231163464
0.300000 0.200000 0.8780954309
0.400000 0.200000 0.8187307531
0.500000 0.200000 0.7482635676
0.600000 0.200000 0.6703200460
0.700000 0.200000 0.5886049697
0.800000 0.200000 0.5066169924
0.900000 0.200000 0.4274149319
1.000000 0.200000 0.3534546820
1.100000 0.200000 0.2865047969
1.200000 0.200000 0.2276376884
1.300000 0.200000 0.1772844100
1.400000 0.200000 0.1353352832
1.500000 0.200000 0.1012664619
1.600000 0.200000 0.0742735782
1.700000 0.200000 0.0533970381
1.800000 0.200000 0.0376282568
1.900000 0.200000 0.0259911288
2.000000 0.200000 0.0175974724
-2.000000 0.300000 0.0167392336
-1.900000 0.300000 0.0247235265
-1.800000 0.300000 0.0357931051
-1.700000 0.300000 0.0507928339
-1.600000 0.300000 0.0706512131
-1.500000 0.300000 0.0963276382
-1.400000 0.300000 0.1287349036
-1.300000 0.300000 0.1686381473
-1.200000 0.300000 0.2165356673
-1.100000 0.300000 0.2725317930
-1.000000 0.300000 0.3362164937
-0.900000 0.300000 0.4065696597
-0.800000 0.300000 0.4819089901
-0.700000 0.300000 0.5598983666
-0.600000 0.300000 0.6376281516
-0.500000 0.300000 0.7117703228
-0.400000 0.300000 0.7788007831
-0.300000 0.300000 0.8352702114
-0.200000 0.300000 0.8780954309
-0.100000 0.300000 0.9048374180
0.000000 0.300000 0.9139311853
0.100000 0.300000 0.9048374180
0.200000 0.300000 0.8780954309
0.300000 0.300000 0.8352702114
0.400000 0.300000 0.7788007831
0.500000 0.300000 0.7117703228
0.600000 0.300000 0.6376281516
0.700000 0.300000 0.5598983666
0.800000 0.300000 0.4819089901
0.900000 0.300000 0.4065696597
1.000000 0.300000 0.3362164937
1.100000 0.300000 0.2725317930
1.200000 0.300000 0.2165356673
1.300000 0.300000 0.1686381473
1.400000 0.300000 0.1287349036
1.500000 0.300000 0.0963276382
1.600000 0.300000 0.0706512131
1.700000 0.300000 0.0507928339
1.800000 0.300000 0.0357931051
1.900000 0.300000 0.0247235265
2.000000 0.300000 0.0167392336
-2.000000 0.400000 0.0156075579
-1.900000 0.400000 0.0230520633
-1.800000 0.400000 0.0333732700
-1.700000 0.400000 0.0473589244
-1.600000 0.400000 0.0658747544
-1.500000 0.400000 0.0898152946
-1.400000 0.400000 0.1200316285
-1.300000 0.400000 0.1572371663
-1.200000 0.400000 0.2018965180
-1.100000 0.400000 0.2541069596
-1.000000 0.400000 0.3134861809
-0.900000 0.400000 0.3790830381
-0.800000 0.400000 0.4493289641
-0.700000 0.400000 0.5220457768
-0.600000 0.400000 0.5945205480
-0.500000 0.400000 0.6636502501
-0.400000 0.400000 0.7261490371
-0.300000 0.400000 0.7788007831
-0.200000 0.400000 0.8187307531
-0.100000 0.400000 0.8436648166
0.000000 0.400000 0.8521437890
0.100000 0.400000 0.8436648166
0.200000 0.400000 0.8187307531
0.300000 0.400000 0.7788007831
0.400000 0.400000 0.7261490371
0.500000 0.400000 0.6636502501
0.600000 0.400000 0.5945205480
0.700000 0.400000 0.5220457768
0.800000 0.400000 0.4493289641
0.900000 0.400000 0.3790830381
1.000000 0.400000 0.3134861809
1.100000 0.400000 0.2541069596
1.200000 0.400000 0.2018965180
1.300000 0.400000 0.1572371663
1.400000 0.400000 0.1200316285
1.500000 0.400000 0.0898152946
1.600000 0.400000 0.0658747544
1.700000 0.400000 0.0473589244
1.800000 0.400000 0.0333732700
1.900000 0.400000 0.0230520633
2.000000 0.400000 0.0156075579
-2.000000 0.500000 0.0142642339
-1.900000 0.500000 0.0210679995
-1.800000 0.500000 0.0305008722
-1.700000 0.500000 0.0432827979
-1.600000 0.500000 0.0602049924
-1.500000 0.500000 0.0820849986
-1.400000 0.500000 0.1097006485
-1.300000 0.500000 0.1437039498
-1.200000 0.500000 0.1845195240
-1.100000 0.500000 0.2322362747
-1.000000 0.500000 0.2865047969
-0.900000 0.500000 0.3464558103
-0.800000 0.500000 0.4106557528
-0.700000 0.500000 0.4771139155
-0.600000 0.500000 0.5433508691
-0.500000 0.500000 0.6065306597
-0.400000 0.500000 0.6636502501
-0.300000 0.500000 0.7117703228
-0.200000 0.500000 0.7482635676
-0.100000 0.500000 0.7710515858
0.000000 0.500000 0.7788007831
0.100000 0.500000 0.7710515858
0.200000 0.500000 0.7482635676
0.300000 0.500000 0.7117703228
0.400000 0.500000 0.6636502501
0.500000 0.500000 0.6065306597
0.600000 0.500000 0.5433508691
0.700000 0.500000 0.4771139155
0.800000 0.500000 0.4106557528
0.900000 0.500000 0.3464558103
1.000000 0.500000 0.2865047969
1.100000 0.500000 0.2322362747
1.200000 0.500000 0.1845195240
1.300000 0.500000 0.1437039498
1.400000 0.500000 0.1097006485
1.500000 0.500000 0.0820849986
1.600000 0.500000 0.0602049924
1.700000 0.500000 0.0432827979
1.800000 0.500000 0.0305008722
1.900000 0.500000 0.0210679995
2.000000 0.500000 0.0142642339
-2.000000 0.600000 0.0127783876
-1.900000 0.600000 0.0188734331
-1.800000 0.600000 0.0273237224
-1.700000 0.600000 0.0387742078
-1.600000 0.600000 0.0539336873
-1.500000 0.600000 0.0735345438
-1.400000 0.600000 0.0982735856
-1.300000 0.600000 0.1287349036
-1.200000 0.600000 0.1652988882
-1.100000 0.600000 0.2080451824
-1.000000 0.600000 0.2566607770
-0.900000 0.600000 0.3103669413
-0.800000 0.600000 0.3678794412
-0.700000 0.600000 0.4274149319
-0.600000 0.600000 0.4867522560
-0.500000 0.600000 0.5433508691
-0.400000 0.600000 0.5945205480
-0.300000 0.600000 0.6376281516
-0.200000 0.600000 0.6703200460
-0.100000 0.600000 0.6907343306
0.000000 0.600000 0.6976763261
0.100000 0.600000 0.6907343306
0.200000 0.600000 0.6703200460
0.300000 0.600000 0.6376281516
0.400000 0.600000 0.5945205480
0.500000 0.600000 0.5433508691
0.600000 0.600000 0.4867522560
0.700000 0.600000 0.4274149319
0.800000 0.600000 0.3678794412
0.900000 0.600000 0.3103669413
1.000000 0.600000 0.2566607770
1.100000 0.600000 0.2080451824
1.200000 0.600000 0.1652988882
1.300000 0.600000 0.1287349036
1.400000 0.600000 0.0982735856
1.500000 0.600000 0.0735345438
1.600000 0.600000 0.0539336873
1.700000 0.600000 0.0387742078
1.800000 0.600000 0.0273237224
1.900000 0.600000 0.0188734331
2.000000 0.600000 0.0127783876
-2.000000 0.700000 0.0112206438
-1.900000 0.700000 0.0165726754
-1.800000 0.700000 0.0239928358
-1.700000 0.700000 0.0340474547
-1.600000 0.700000 0.0473589244
-1.500000 0.700000 0.0645703469
-1.400000 0.700000 0.0862935865
-1.300000 0.700000 0.1130415306
-1.200000 0.700000 0.1451481985
-1.100000 0.700000 0.1826835241
-1.000000 0.700000 0.2253726555
-0.900000 0.700000 0.2725317930
-0.800000 0.700000 0.3230332564
-0.700000 0.700000 0.3753110989
-0.600000 0.700000 0.4274149319
-0.500000 0.700000 0.4771139155
-0.400000 0.700000 0.5220457768
-0.300000 0.700000 0.5598983666
-0.200000 0.700000 0.5886049697
-0.100000 0.700000 0.6065306597
0.000000 0.700000 0.6126263942
0.100000 0.700000 0.6065306597
0.200000 0.700000 0.5886049697
0.300000 0.700000 0.5598983666
0.400000 0.700000 0.5220457768
0.500000 0.700000 0.4771139155
0.600000 0.700000 0.4274149319
0.700000 0.700000 0.3753110989
0.800000 0.700000 0.3230332564
0.900000 0.700000 0.2725317930
1.000000 0.700000 0.2253726555
1.100000 0.700000 0.1826835241
1.200000 0.700000 0.1451481985
1.300000 0.700000 0.1130415306
1.400000 0.700000 0.0862935865
1.500000 0.700000 0.0645703469
1.600000 0.700000 0.0473589244
1.700000 0.700000 0.0340474547
1.800000 0.700000 0.0239928358
1.900000 0.700000 0.0165726754
2.000000 0.700000 0.0112206438
-2.000000 0.800000 0.0096576976
-1.900000 0.800000 0.0142642339
-1.800000 0.800000 0.0206508252
-1.700000 0.800000 0.0293049159
-1.600000 0.800000 0.0407622040
-1.500000 0.800000 0.0555762126
-1.400000 0.800000 0.0742735782
-1.300000 0.800000 0.0972957471
-1.200000 0.800000 0.1249302122
-1.100000 0.800000 0.1572371663
-1.000000 0.800000 0.1939800423
-0.900000 0.800000 0.2345702881
-0.800000 0.800000 0.2780373005
-0.700000 0.800000 0.3230332564
-0.600000 0.800000 0.3678794412
-0.500000 0.800000 0.4106557528
-0.400000 0.800000 0.4493289641
-0.300000 0.800000 0.4819089901
-0.200000 0.800000 0.5066169924
-0.100000 0.800000 0.5220457768
0.000000 0.800000 0.5272924240
0.100000 0.800000 0.5220457768
0.200000 0.800000 0.5066169924
0.300000 0.800000 0.4819089901
0.400000 0.800000 0.4493289641
0.500000 0.800000 0.4106557528
0.600000 0.800000 0.3678794412
0.700000 0.800000 0.3230332564
0.800000 0.800000 0.2780373005
0.900000 0.800000 0.2345702881
1.000000 0.800000 0.1939800423
1.100000 0.800000 0.1572371663
1.200000 0.800000 0.1249302122
1.300000 0.800000 0.0972957471
1.400000 0.800000 0.0742735782
1.500000 0.800000 0.0555762126
1.600000 0.800000 0.0407622040
1.700000 0.800000 0.0293049159
1.800000 0.800000 0.0206508252
1.900000 0.800000 0.0142642339
2.000000 0.800000 0.0096576976
-2.000000 0.900000 0.0081478597
-1.900000 0.900000 0.0120342323
-1.800000 0.900000 0.0174223746
-1.700000 0.900000 0.0247235265
-1.600000 0.900000 0.0343896373
-1.500000 0.900000 0.0468876952
-1.400000 0.900000 0.0626620047
-1.300000 0.900000 0.0820849986
-1.200000 0.900000 0.1053992246
-1.100000 0.900000 0.1326554651
-1.000000 0.900000 0.1636541368
-0.900000 0.900000 0.1978986991
-0.800000 0.900000 0.2345702881
-0.700000 0.900000 0.2725317930
-0.600000 0.900000 0.3103669413
-0.500000 0.900000 0.3464558103
-0.400000 0.900000 0.3790830381
-0.300000 0.900000 0.4065696597
-0.200000 0.900000 0.4274149319
-0.100000 0.900000 0.4404316545
0.000000 0.900000 0.4448580662
0.100000 0.900000 0.4404316545
0.200000 0.900000 0.4274149319
0.300000 0.900000 0.4065696597
0.400000 0.900000 0.3790830381
0.500000 0.900000 0.3464558103
0.600000 0.900000 0.3103669413
0.700000 0.900000 0.2725317930
0.800000 0.900000 0.2345702881
0.900000 0.900000 0.1978986991
1.000000 0.900000 0.1636541368
1.100000 0.900000 0.1326554651
1.200000 0.900000 0.1053992246
1.300000 0.900000 0.0820849986
1.400000 0.900000 0.0626620047
1.500000 0.900000 0.0468876952
1.600000 0.900000 0.0343896373
1.700000 0.900000 0.0247235265
1.800000 0.900000 0.0174223746
1.900000 0.900000 0.0120342323
2.000000 0.900000 0.0081478597
-2.000000 1.000000 0.0067379470
-1.900000 1.000000 0.0099518183
-1.800000 1.000000 0.0144075918
-1.700000 1.000000 0.0204453460
-1.600000 1.000000 0.0284388247
-1.500000 1.000000 0.0387742078
-1.400000 1.000000 0.0518189172
-1.300000 1.000000 0.0678809394
-1.200000 1.000000 0.0871608515
-1.100000 1.000000 0.1097006485
-1.000000 1.000000 0.1353352832
-0.900000 1.000000 0.1636541368
-0.800000 1.000000 0.1939800423
-0.700000 1.000000 0.2253726555
-0.600000 1.000000 0.2566607770
-0.500000 1.000000 0.2865047969
-0.400000 1.000000 0.3134861809
-0.300000 1.000000 0.3362164937
-0.200000 1.000000 0.3534546820
-0.100000 1.000000 0.3642189796
0.000000 1.000000 0.3678794412
0.100000 1.000000 0.3642189796
0.200000 1.000000 0.3534546820
0.300000 1.000000 0.3362164937
0.400000 1.000000 0.3134861809
0.500000 1.000000 0.2865047969
0.600000 1.000000 0.2566607770
0.700000 1.000000 0.2253726555
0.800000 1.000000 0.1939800423
0.900000 1.000000 0.1636541368
1.000000 1.000000 0.1353352832
1.100000 1.000000 0.1097006485
1.200000 1.000000 0.0871608515
1.300000 1.000000 0.0678809394
1.400000 1.000000 0.0518189172
1.500000 1.000000 0.0387742078
1.600000 1.000000 0.0284388247
1.700000 1.000000 0.0204453460
1.800000 1.000000 0.0144075918
1.900000 1.000000 0.0099518183
2.000000 1.000000 0.0067379470
-2.000000 1.100000 0.0054616737
-1.900000 1.100000 0.0080667871
-1.800000 1.100000 0.0116785670
-1.700000 1.100000 0.0165726754
-1.600000 1.100000 0.0230520633
-1.500000 1.100000 0.0314297620
-1.400000 1.100000 0.0420035979
-1.300000 1.100000 0.0550232201
-1.200000 1.100000 0.0706512131
-1.100000 1.100000 0.0889216175
-1.000000 1.100000 0.1097006485
-0.900000 1.100000 0.1326554651
-0.800000 1.100000 0.1572371663
-0.700000 1.100000 0.1826835241
-0.600000 1.100000 0.2080451824
-0.500000 1.100000 0.2322362747
-0.400000 1.100000 0.2541069596
-0.300000 1.100000 0.2725317930
-0.200000 1.100000 0.2865047969
-0.100000 1.100000 0.2952301669
0.000000 1.100000 0.2981972794
0.100000 1.100000 0.2952301669
0.200000 1.100000 0.2865047969
0.300000 1.100000 0.2725317930
0.400000 1.100000 0.2541069596
0.500000 1.100000 0.2322362747
0.600000 1.100000 0.2080451824
0.700000 1.100000 0.1826835241
0.800000 1.100000 0.1572371663
0.900000 1.100000 0.1326554651
1.000000 1.100000 0.1097006485
1.100000 1.100000 0.0889216175
1.200000 1.100000 0.0706512131
1.300000 1.100000 0.0550232201
1.400000 1.100000 0.0420035979
1.500000 1.100000 0.0314297620
1.600000 1.100000 0.0230520633
1.700000 1.100000 0.0165726754
1.800000 1.100000 0.0116785670
1.900000 1.100000 0.0080667871
2.000000 1.100000 0.0054616737
-2.000000 1.200000 0.0043394833
-1.900000 1.200000 0.0064093334
-1.800000 1.200000 0.0092790139
-1.700000 1.200000 0.0131675475
-1.600000 1.200000 0.0183156389
-1.500000 1.200000 0.0249720020
-1.400000 1.200000 0.0333732700
-1.300000 1.200000 0.0437177973
-1.200000 1.200000 0.0561347628
-1.100000 1.200000 0.0706512131
-1.000000 1.200000 0.0871608515
-0.900000 1.200000 0.1053992246
-0.800000 1.200000 0.1249302122
-0.700000 1.200000 0.1451481985
-0.600000 1.200000 0.1652988882
-0.500000 1.200000 0.1845195240
-0.400000 1.200000 0.2018965180
-0.300000 1.200000 0.2165356673
-0.200000 1.200000 0.2276376884
-0.100000 1.200000 0.2345702881
0.000000 1.200000 0.2369277587
0.100000 1.200000 0.2345702881
0.200000 1.200000 0.2276376884
0.300000 1.200000 0.2165356673
0.400000 1.200000 0.2018965180
0.500000 1.200000 0.1845195240
0.600000 1.200000 0.1652988882
0.700000 1.200000 0.1451481985
0.800000 1.200000 0.1249302122
0.900000 1.200000 0.1053992246
1.000000 1.200000 0.0871608515
1.100000 1.200000 0.0706512131
1.200000 1.200000 0.0561347628
1.300000 1.200000 0.0437177973
1.400000 1.200000 0.0333732700
1.500000 1.200000 0.0249720020
1.600000 1.200000 0.0183156389
1.700000 1.200000 0.0131675475
1.800000 1.200000 0.0092790139
1.900000 1.200000 0.0064093334
2.000000 1.200000 0.0043394833
-2.000000 1.300000 0.0033795930
-1.900000 1.300000 0.0049915939
-1.800000 1.300000 0.0072265033
-1.700000 1.300000 0.0102548963
-1.600000 1.300000 0.0142642339
-1.500000 1.300000 0.0194482147
-1.400000 1.300000 0.0259911288
-1.300000 1.300000 0.0340474547
-1.200000 1.300000 0.0437177973
-1.100000 1.300000 0.0550232201
-1.000000 1.300000 0.0678809394
-0.900000 1.300000 0.0820849986
-0.800000 1.300000 0.0972957471
-0.700000 1.300000 0.1130415306
-0.600000 1.300000 0.1287349036
-0.500000 1.300000 0.1437039498
-0.400000 1.300000 0.1572371663
-0.300000 1.300000 0.1686381473
-0.200000 1.300000 0.1772844100
-0.100000 1.300000 0.1826835241
0.000000 1.300000 0.1845195240
0.100000 1.300000 0.1826835241
0.200000 1.300000 0.1772844100
0.300000 1.300000 0.1686381473
0.400000 1.300000 0.1572371663
0.500000 1.300000 0.1437039498
0.600000 1.300000 0.1287349036
0.700000 1.300000 0.1130415306
0.800000 1.300000 0.0972957471
0.900000 1.300000 0.0820849986
1.000000 1.300000 0.0678809394
1.100000 1.300000 0.0550232201
1.200000 1.300000 0.0437177973
1.300000 1.300000 0.0340474547
1.400000 1.300000 0.0259911288
1.500000 1.300000 0.0194482147
1.600000 1.300000 0.0142642339
1.700000 1.300000 0.0102548963
1.800000 1.300000 0.0072265033
1.900000 1.300000 0.0049915939
2.000000 1.300000 0.0033795930
-2.000000 1.400000 0.0025799120
-1.900000 1.400000 0.0038104804
-1.800000 1.400000 0.0055165644
-1.700000 1.400000 0.0078283775
-1.600000 1.400000 0.0108890237
-1.500000 1.400000 0.0148463683
-1.400000 1.400000 0.0198410947
-1.300000 1.400000 0.0259911288
-1.200000 1.400000 0.0333732700
-1.100000 1.400000 0.0420035979
-1.000000 1.400000 0.0518189172
-0.900000 1.400000 0.0626620047
-0.800000 1.400000 0.0742735782
-0.700000 1.400000 0.0862935865
-0.600000 1.400000 0.0982735856
-0.500000 1.400000 0.1097006485
-0.400000 1.400000 0.1200316285
-0.300000 1.400000 0.1287349036
-0.200000 1.400000 0.1353352832
-0.100000 1.400000 0.1394568562
0.000000 1.400000 0.1408584209
0.100000 1.400000 0.1394568562
0.200000 1.400000 0.1353352832
0.300000 1.400000 0.1287349036
0.400000 1.400000 0.1200316285
0.500000 1.400000 0.1097006485
0.600000 1.400000 0.0982735856
0.700000 1.400000 0.0862935865
0.800000 1.400000 0.0742735782
0.900000 1.400000 0.0626620047
1.000000 1.400000 0.0518189172
1.100000 1.400000 0.0420035979
1.200000 1.400000 0.0333732700
1.300000 1.400000 0.0259911288
1.400000 1.400000 0.0198410947
1.500000 1.400000 0.0148463683
1.600000 1.400000 0.0108890237
1.700000 1.400000 0.0078283775
1.800000 1.400000 0.0055165644
1.900000 1.400000 0.0038104804
2.000000 1.400000 0.0025799120
-2.000000 1.500000 0.0019304541
-1.900000 1.500000 0.0028512437
-1.800000 1.500000 0.0041278442
-1.700000 1.500000 0.0058576897
-1.600000 1.500000 0.0081478597
-1.500000 1.500000 0.0111089965
-1.400000 1.500000 0.0148463683
-1.300000 1.500000 0.0194482147
-1.200000 1.500000 0.0249720020
-1.100000 1.500000 0.0314297620
-1.000000 1.500000 0.0387742078
-0.900000 1.500000 0.0468876952
-0.800000 1.500000 0.0555762126
-0.700000 1.500000 0.0645703469
-0.600000 1.500000 0.0735345438
-0.500000 1.500000 0.0820849986
-0.400000 1.500000 0.0898152946
-0.300000 1.500000 0.0963276382
-0.200000 1.500000 0.1012664619
-0.100000 1.500000 0.1043504848
0.000000 1.500000 0.1053992246
0.100000 1.500000 0.1043504848
0.200000 1.500000 0.1012664619
0.300000 1.500000 0.0963276382
0.400000 1.500000 0.0898152946
0.500000 1.500000 0.0820849986
0.600000 1.500000 0.0735345438
0.700000 1.500000 0.0645703469
0.800000 1.500000 0.0555762126
0.900000 1.500000 0.0468876952
1.000000 1.500000 0.0387742078
1.100000 1.500000 0.0314297620
1.200000 1.500000 0.0249720020
1.300000 1.500000 0.0194482147
1.400000 1.500000 0.0148463683
1.500000 1.500000 0.0111089965
1.600000 1.500000 0.0081478597
1.700000 1.500000 0.0058576897
1.800000 1.500000 0.0041278442
1.900000 1.500000 0.0028512437
2.000000 1.500000 0.0019304541
```

---

## `examples/data/2d/sample_with_comments_and_missing.txt`

```txt
# comments are ignored
# x y
0 0
1 1
2 nan
3 bad
4 16
```

---

## `examples/data/2d/sample_xy.csv`

```csv
x,time_signal
0.000000000000000000e+00,0.000000000000000000e+00
5.000000000000000278e-02,4.985437740233282511e-02
1.000000000000000056e-01,9.933549540403648070e-02
1.500000000000000222e-01,1.483215389398261919e-01
2.000000000000000111e-01,1.966925379247088101e-01
2.500000000000000000e-01,2.443306579140596124e-01
3.000000000000000444e-01,2.911204839760501706e-01
3.500000000000000333e-01,3.369492971007511106e-01
4.000000000000000222e-01,3.817073424922551306e-01
4.500000000000000111e-01,4.252880891137156838e-01
5.000000000000000000e-01,4.675884798802011910e-01
5.500000000000000444e-01,5.085091719206595862e-01
6.000000000000000888e-01,5.479547663579945604e-01
6.500000000000000222e-01,5.858340270852037124e-01
7.000000000000000666e-01,6.220600880456375048e-01
7.500000000000000000e-01,6.565506485566182659e-01
8.000000000000000444e-01,6.892281562478554946e-01
8.500000000000000888e-01,7.200199772191706593e-01
9.000000000000000222e-01,7.488585530559783709e-01
9.500000000000000666e-01,7.756815443756087669e-01
1.000000000000000000e+00,8.004319606128644793e-01
1.050000000000000044e+00,8.230582757890441137e-01
1.100000000000000089e+00,8.435145300449814476e-01
1.150000000000000133e+00,8.617604167553224448e-01
1.200000000000000178e+00,8.777613550782145113e-01
1.250000000000000000e+00,8.914885478317117196e-01
1.300000000000000044e+00,9.029190246254227281e-01
1.350000000000000089e+00,9.120356702131295901e-01
1.400000000000000133e+00,9.188272380692256158e-01
1.450000000000000178e+00,9.232883492287330407e-01
1.500000000000000000e+00,9.254194764672986073e-01
1.550000000000000044e+00,9.252269139338255011e-01
1.600000000000000089e+00,9.227227323841995510e-01
1.650000000000000133e+00,9.179247201998174122e-01
1.700000000000000178e+00,9.108563104092350926e-01
1.750000000000000000e+00,9.015464939651588461e-01
1.800000000000000044e+00,8.900297195620864299e-01
1.850000000000000089e+00,8.763457803121349476e-01
1.900000000000000133e+00,8.605396876278488261e-01
1.950000000000000178e+00,8.426615326910199544e-01
2.000000000000000000e+00,8.227663359156917045e-01
2.050000000000000266e+00,8.009138848414852907e-01
2.100000000000000089e+00,7.771685609201399725e-01
2.149999999999999911e+00,7.515991556835965870e-01
2.200000000000000178e+00,7.242786768060751612e-01
2.250000000000000000e+00,6.952841445952882005e-01
2.300000000000000266e+00,6.646963794691884697e-01
2.350000000000000089e+00,6.325997809944124972e-01
2.400000000000000355e+00,5.990820990807866897e-01
2.450000000000000178e+00,5.642341979429172927e-01
2.500000000000000000e+00,5.281498134549031942e-01
2.550000000000000266e+00,4.909253045376165692e-01
2.600000000000000089e+00,4.526593992297090474e-01
2.650000000000000355e+00,4.134529361035471084e-01
2.700000000000000178e+00,3.734086016956235654e-01
2.750000000000000000e+00,3.326306646275993262e-01
2.800000000000000266e+00,2.912247070990474640e-01
2.850000000000000089e+00,2.492973544361297422e-01
2.900000000000000355e+00,2.069560033818853562e-01
2.950000000000000178e+00,1.643085498135472000e-01
3.000000000000000000e+00,1.214631165702961535e-01
3.050000000000000266e+00,7.852778207119823217e-02
3.100000000000000089e+00,3.561031039769269740e-02
3.150000000000000355e+00,-7.182116492026378515e-03
3.200000000000000178e+00,-4.974316375803515544e-02
3.250000000000000000e+00,-9.196760523469368898e-02
3.300000000000000266e+00,-1.337515809110385312e-01
3.350000000000000089e+00,-1.749928497123202920e-01
3.400000000000000355e+00,-2.155910369743046784e-01
3.450000000000000178e+00,-2.554478760182428698e-01
3.500000000000000000e+00,-2.944674432521348084e-01
3.550000000000000266e+00,-3.325563862429347650e-01
3.600000000000000089e+00,-3.696241442247012454e-01
3.650000000000000355e+00,-4.055831605292645192e-01
3.700000000000000178e+00,-4.403490864487273337e-01
3.750000000000000000e+00,-4.738409760629919698e-01
3.800000000000000266e+00,-5.059814715904032978e-01
3.850000000000000089e+00,-5.366969788454971635e-01
3.900000000000000355e+00,-5.659178324146463268e-01
3.950000000000000178e+00,-5.935784501880279063e-01
4.000000000000000000e+00,-6.196174769147558825e-01
4.049999999999999822e+00,-6.439779164771096687e-01
4.100000000000000533e+00,-6.666072526095072615e-01
4.150000000000000355e+00,-6.874575578181217894e-01
4.200000000000000178e+00,-7.064855902877517080e-01
4.250000000000000000e+00,-7.236528785936371388e-01
4.299999999999999822e+00,-7.389257940673150671e-01
4.350000000000000533e+00,-7.522756106972108281e-01
4.400000000000000355e+00,-7.636785524764160282e-01
4.450000000000000178e+00,-7.731158281419197031e-01
4.500000000000000000e+00,-7.805736532813422057e-01
4.549999999999999822e+00,-7.860432598149261763e-01
4.600000000000000533e+00,-7.895208928920500746e-01
4.650000000000000355e+00,-7.910077952727891937e-01
4.700000000000000178e+00,-7.905101792959842166e-01
4.750000000000000000e+00,-7.880391865657921935e-01
4.800000000000000711e+00,-7.836108355187371144e-01
4.850000000000000533e+00,-7.772459570627630043e-01
4.900000000000000355e+00,-7.689701185086451618e-01
4.950000000000000178e+00,-7.588135360422880726e-01
5.000000000000000000e+00,-7.468109760138311737e-01
5.050000000000000711e+00,-7.330016453460663772e-01
5.100000000000000533e+00,-7.174290713903567207e-01
5.150000000000000355e+00,-7.001409715829808311e-01
5.200000000000000178e+00,-6.811891132785677927e-01
5.250000000000000000e+00,-6.606291641599545406e-01
5.300000000000000711e+00,-6.385205336453634306e-01
5.350000000000000533e+00,-6.149262057342003152e-01
5.400000000000000355e+00,-5.899125637519668786e-01
5.450000000000000178e+00,-5.635492074727415091e-01
5.500000000000000000e+00,-5.359087631143381047e-01
5.550000000000000711e+00,-5.070666867166052638e-01
5.600000000000000533e+00,-4.771010614273192285e-01
5.650000000000000355e+00,-4.460923892327277041e-01
5.700000000000000178e+00,-4.141233776810270273e-01
5.750000000000000000e+00,-3.812787221568154639e-01
5.800000000000000711e+00,-3.476448842729141231e-01
5.850000000000000533e+00,-3.133098669528276981e-01
5.900000000000000355e+00,-2.783629867825153092e-01
5.950000000000000178e+00,-2.428946442141049766e-01
6.000000000000000000e+00,-2.069960922066239883e-01
6.050000000000000711e+00,-1.707592038898216036e-01
6.100000000000000533e+00,-1.342762398366759702e-01
6.150000000000000355e+00,-9.763961552822467138e-02
6.200000000000000178e+00,-6.094166959098661768e-02
6.250000000000000000e+00,-2.427443338239760467e-02
6.300000000000000711e+00,1.227059750654617420e-02
6.350000000000000533e+00,4.860268926987243443e-02
6.400000000000000355e+00,8.463209287389028557e-02
6.450000000000000178e+00,1.202702634708763263e-01
6.500000000000000000e+00,1.554300757086034546e-01
6.550000000000000711e+00,1.900260344180187688e-01
6.600000000000000533e+00,2.239744801755110259e-01
6.650000000000000355e+00,2.571937892515422375e-01
6.700000000000000178e+00,2.896045674738632059e-01
6.750000000000000000e+00,3.211298375511185688e-01
6.800000000000000711e+00,3.516952194212423777e-01
6.850000000000000533e+00,3.812291032086566611e-01
6.900000000000000355e+00,4.096628143948420342e-01
6.950000000000000178e+00,4.369307708282663127e-01
7.000000000000000000e+00,4.629706312219384334e-01
7.050000000000000711e+00,4.877234348098757333e-01
7.100000000000000533e+00,5.111337318575087663e-01
7.150000000000000355e+00,5.331497047454405447e-01
7.200000000000000178e+00,5.537232793709203627e-01
7.250000000000000000e+00,5.728102266368854112e-01
7.300000000000000711e+00,5.903702538243359443e-01
7.350000000000000533e+00,6.063670856701189882e-01
7.400000000000000355e+00,6.207685349988156798e-01
7.450000000000000178e+00,6.335465627842838954e-01
7.500000000000000000e+00,6.446773275434589667e-01
7.550000000000000711e+00,6.541412239921562399e-01
7.600000000000000533e+00,6.619229109198137007e-01
7.650000000000000355e+00,6.680113282672741626e-01
7.700000000000000178e+00,6.723997034187686461e-01
7.750000000000000000e+00,6.750855467461722714e-01
7.800000000000000711e+00,6.760706364702714355e-01
7.850000000000000533e+00,6.753609929301642723e-01
7.900000000000000355e+00,6.729668423779341380e-01
7.950000000000000178e+00,6.689025704413329443e-01
8.000000000000000000e+00,6.631866654223247393e-01
8.050000000000000711e+00,6.558416516239052863e-01
8.099999999999999645e+00,6.468940129215846602e-01
8.150000000000000355e+00,6.363741068192091399e-01
8.200000000000001066e+00,6.243160692514099219e-01
8.250000000000000000e+00,6.107577104167631887e-01
8.300000000000000711e+00,5.957404019467598122e-01
8.349999999999999645e+00,5.793089557358255259e-01
8.400000000000000355e+00,5.615114947768246045e-01
8.450000000000001066e+00,5.423993163647856663e-01
8.500000000000000000e+00,5.220267480488114398e-01
8.550000000000000711e+00,5.004509967283948813e-01
8.599999999999999645e+00,4.777319913055203537e-01
8.650000000000000355e+00,4.539322193179580189e-01
8.700000000000001066e+00,4.291165579921243922e-01
8.750000000000000000e+00,4.033521001656009131e-01
8.800000000000000711e+00,3.767079755400076224e-01
8.849999999999999645e+00,3.492551677343050942e-01
8.900000000000000355e+00,3.210663276167162183e-01
8.950000000000001066e+00,2.922155834004306896e-01
9.000000000000000000e+00,2.627783479938663458e-01
9.050000000000000711e+00,2.328311241007151311e-01
9.099999999999999645e+00,2.024513075681538821e-01
9.150000000000000355e+00,1.717169894834550958e-01
9.200000000000001066e+00,1.407067575199288101e-01
9.250000000000000000e+00,1.094994970324408290e-01
9.300000000000000711e+00,7.817419240092431110e-02
9.349999999999999645e+00,4.680972911719561563e-02
9.400000000000000355e+00,1.548469710601756318e-02
9.450000000000001066e+00,-1.572280423411855435e-02
9.500000000000000000e+00,-4.673535879180179542e-02
9.550000000000000711e+00,-7.747642383425448753e-02
9.600000000000001421e+00,-1.078705169678034897e-01
9.650000000000000355e+00,-1.378433995156036485e-01
9.700000000000001066e+00,-1.673222558721244591e-01
9.750000000000000000e+00,-1.962358684061641101e-01
9.800000000000000711e+00,-2.245147874974534052e-01
9.850000000000001421e+00,-2.520914963060885139e-01
9.900000000000000355e+00,-2.789005698892503826e-01
9.950000000000001066e+00,-3.048788282956871321e-01
1.000000000000000000e+01,-3.299654832853291531e-01
```

---

## `examples/data/3d/sample_3d_field.txt`

```txt
# Example 3D scalar field: x y z field
# Point-form structured data, suitable for import/inspection
-1.000000 -1.000000 -1.000000 0.2000061442
-0.857143 -1.000000 -1.000000 0.1714463276
-0.714286 -1.000000 -1.000000 0.1429007270
-0.571429 -1.000000 -1.000000 0.1143765805
-0.428571 -1.000000 -1.000000 0.0858751911
-0.285714 -1.000000 -1.000000 0.0573848674
-0.142857 -1.000000 -1.000000 0.0288805944
0.000000 -1.000000 -1.000000 0.0003354626
0.142857 -1.000000 -1.000000 -0.0282622627
0.285714 -1.000000 -1.000000 -0.0569008469
0.428571 -1.000000 -1.000000 -0.0855533803
0.571429 -1.000000 -1.000000 -0.1141948481
0.714286 -1.000000 -1.000000 -0.1428135587
0.857143 -1.000000 -1.000000 -0.1714108152
1.000000 -1.000000 -1.000000 -0.1999938558
-1.000000 -0.833333 -1.000000 0.1666875246
-0.857143 -0.833333 -1.000000 0.1429174203
-0.714286 -0.833333 -1.000000 0.1191955753
-0.571429 -0.833333 -1.000000 0.0955465608
-0.428571 -0.833333 -1.000000 0.0719748008
-0.285714 -0.833333 -1.000000 0.0484406053
-0.142857 -0.833333 -1.000000 0.0248590563
0.000000 -0.833333 -1.000000 0.0011388028
0.142857 -0.833333 -1.000000 -0.0227599913
0.285714 -0.833333 -1.000000 -0.0467974899
0.428571 -0.833333 -1.000000 -0.0708823421
0.571429 -0.833333 -1.000000 -0.0949296296
0.714286 -0.833333 -1.000000 -0.1188996628
0.857143 -0.833333 -1.000000 -0.1427968655
1.000000 -0.833333 -1.000000 -0.1666458088
-1.000000 -0.666667 -1.000000 0.1333900310
-0.857143 -0.666667 -1.000000 0.1144495653
-0.714286 -0.666667 -1.000000 0.0956402820
-0.571429 -0.666667 -1.000000 0.0770289726
-0.428571 -0.666667 -1.000000 0.0586276624
-0.285714 -0.666667 -1.000000 0.0403284635
-0.142857 -0.666667 -1.000000 0.0219005442
0.000000 -0.666667 -1.000000 0.0030955869
0.142857 -0.666667 -1.000000 -0.0161946939
0.285714 -0.666667 -1.000000 -0.0358620127
0.428571 -0.666667 -1.000000 -0.0556580519
0.571429 -0.666667 -1.000000 -0.0753519798
0.714286 -0.666667 -1.000000 -0.0948359085
0.857143 -0.666667 -1.000000 -0.1141218633
1.000000 -0.666667 -1.000000 -0.1332766357
-1.000000 -0.500000 -1.000000 0.1001234098
-0.857143 -0.500000 -1.000000 0.0860709286
-0.714286 -0.500000 -1.000000 0.0723039831
-0.571429 -0.500000 -1.000000 0.0589679536
-0.428571 -0.500000 -1.000000 0.0460890144
-0.285714 -0.500000 -1.000000 0.0334323337
-0.142857 -0.500000 -1.000000 0.0204954766
0.000000 -0.500000 -1.000000 0.0067379470
0.142857 -0.500000 -1.000000 -0.0080759519
0.285714 -0.500000 -1.000000 -0.0237105234
0.428571 -0.500000 -1.000000 -0.0396252713
0.571429 -0.500000 -1.000000 -0.0553177607
0.714286 -0.500000 -1.000000 -0.0705531598
0.857143 -0.500000 -1.000000 -0.0853576428
1.000000 -0.500000 -1.000000 -0.0998765902
-1.000000 -0.333333 -1.000000 0.0668817587
-0.857143 -0.333333 -1.000000 0.0577644533
-0.714286 -0.333333 -1.000000 0.0491448105
-0.571429 -0.333333 -1.000000 0.0412762151
-0.428571 -0.333333 -1.000000 0.0342042866
-0.285714 -0.333333 -1.000000 0.0275197344
-0.142857 -0.333333 -1.000000 0.0203468602
0.000000 -0.333333 -1.000000 0.0117436285
0.142857 -0.333333 -1.000000 0.0012992412
0.285714 -0.333333 -1.000000 -0.0105755037
0.428571 -0.333333 -1.000000 -0.0229385705
0.571429 -0.333333 -1.000000 -0.0349142611
0.714286 -0.333333 -1.000000 -0.0460932848
0.857143 -0.333333 -1.000000 -0.0565212610
1.000000 -0.333333 -1.000000 -0.0664515746
-1.000000 -0.166667 -1.000000 0.0336335185
-0.857143 -0.166667 -1.000000 0.0294389359
-0.714286 -0.166667 -1.000000 0.0259388974
-0.571429 -0.166667 -1.000000 0.0234870301
-0.428571 -0.166667 -1.000000 0.0221470009
-0.285714 -0.166667 -1.000000 0.0213475990
-0.142857 -0.166667 -1.000000 0.0198666888
0.000000 -0.166667 -1.000000 0.0163895538
0.142857 -0.166667 -1.000000 0.0103428792
0.285714 -0.166667 -1.000000 0.0022999799
0.428571 -0.166667 -1.000000 -0.0064244276
0.571429 -0.166667 -1.000000 -0.0146082080
0.714286 -0.166667 -1.000000 -0.0216801502
0.857143 -0.166667 -1.000000 -0.0277039213
1.000000 -0.166667 -1.000000 -0.0330331482
-1.000000 0.000000 -1.000000 0.0003354626
-0.857143 0.000000 -1.000000 0.0009694560
-0.714286 0.000000 -1.000000 0.0023796156
-0.571429 0.000000 -1.000000 0.0049611265
-0.428571 0.000000 -1.000000 0.0087851377
-0.285714 0.000000 -1.000000 0.0132133102
-0.142857 0.000000 -1.000000 0.0168798841
0.000000 0.000000 -1.000000 0.0183156389
0.142857 0.000000 -1.000000 0.0168798841
0.285714 0.000000 -1.000000 0.0132133102
0.428571 0.000000 -1.000000 0.0087851377
0.571429 0.000000 -1.000000 0.0049611265
0.714286 0.000000 -1.000000 0.0023796156
0.857143 0.000000 -1.000000 0.0009694560
1.000000 0.000000 -1.000000 0.0003354626
-1.000000 0.166667 -1.000000 -0.0330331482
-0.857143 0.166667 -1.000000 -0.0277039213
-0.714286 0.166667 -1.000000 -0.0216801502
-0.571429 0.166667 -1.000000 -0.0146082080
-0.428571 0.166667 -1.000000 -0.0064244276
-0.285714 0.166667 -1.000000 0.0022999799
-0.142857 0.166667 -1.000000 0.0103428792
0.000000 0.166667 -1.000000 0.0163895538
0.142857 0.166667 -1.000000 0.0198666888
0.285714 0.166667 -1.000000 0.0213475990
0.428571 0.166667 -1.000000 0.0221470009
0.571429 0.166667 -1.000000 0.0234870301
0.714286 0.166667 -1.000000 0.0259388974
0.857143 0.166667 -1.000000 0.0294389359
1.000000 0.166667 -1.000000 0.0336335185
-1.000000 0.333333 -1.000000 -0.0664515746
-0.857143 0.333333 -1.000000 -0.0565212610
-0.714286 0.333333 -1.000000 -0.0460932848
-0.571429 0.333333 -1.000000 -0.0349142611
-0.428571 0.333333 -1.000000 -0.0229385705
-0.285714 0.333333 -1.000000 -0.0105755037
-0.142857 0.333333 -1.000000 0.0012992412
0.000000 0.333333 -1.000000 0.0117436285
0.142857 0.333333 -1.000000 0.0203468602
0.285714 0.333333 -1.000000 0.0275197344
0.428571 0.333333 -1.000000 0.0342042866
0.571429 0.333333 -1.000000 0.0412762151
0.714286 0.333333 -1.000000 0.0491448105
0.857143 0.333333 -1.000000 0.0577644533
1.000000 0.333333 -1.000000 0.0668817587
-1.000000 0.500000 -1.000000 -0.0998765902
-0.857143 0.500000 -1.000000 -0.0853576428
-0.714286 0.500000 -1.000000 -0.0705531598
-0.571429 0.500000 -1.000000 -0.0553177607
-0.428571 0.500000 -1.000000 -0.0396252713
-0.285714 0.500000 -1.000000 -0.0237105234
-0.142857 0.500000 -1.000000 -0.0080759519
0.000000 0.500000 -1.000000 0.0067379470
0.142857 0.500000 -1.000000 0.0204954766
0.285714 0.500000 -1.000000 0.0334323337
0.428571 0.500000 -1.000000 0.0460890144
0.571429 0.500000 -1.000000 0.0589679536
0.714286 0.500000 -1.000000 0.0723039831
0.857143 0.500000 -1.000000 0.0860709286
1.000000 0.500000 -1.000000 0.1001234098
-1.000000 0.666667 -1.000000 -0.1332766357
-0.857143 0.666667 -1.000000 -0.1141218633
-0.714286 0.666667 -1.000000 -0.0948359085
-0.571429 0.666667 -1.000000 -0.0753519798
-0.428571 0.666667 -1.000000 -0.0556580519
-0.285714 0.666667 -1.000000 -0.0358620127
-0.142857 0.666667 -1.000000 -0.0161946939
0.000000 0.666667 -1.000000 0.0030955869
0.142857 0.666667 -1.000000 0.0219005442
0.285714 0.666667 -1.000000 0.0403284635
0.428571 0.666667 -1.000000 0.0586276624
0.571429 0.666667 -1.000000 0.0770289726
0.714286 0.666667 -1.000000 0.0956402820
0.857143 0.666667 -1.000000 0.1144495653
1.000000 0.666667 -1.000000 0.1333900310
-1.000000 0.833333 -1.000000 -0.1666458088
-0.857143 0.833333 -1.000000 -0.1427968655
-0.714286 0.833333 -1.000000 -0.1188996628
-0.571429 0.833333 -1.000000 -0.0949296296
-0.428571 0.833333 -1.000000 -0.0708823421
-0.285714 0.833333 -1.000000 -0.0467974899
-0.142857 0.833333 -1.000000 -0.0227599913
0.000000 0.833333 -1.000000 0.0011388028
0.142857 0.833333 -1.000000 0.0248590563
0.285714 0.833333 -1.000000 0.0484406053
0.428571 0.833333 -1.000000 0.0719748008
0.571429 0.833333 -1.000000 0.0955465608
0.714286 0.833333 -1.000000 0.1191955753
0.857143 0.833333 -1.000000 0.1429174203
1.000000 0.833333 -1.000000 0.1666875246
-1.000000 1.000000 -1.000000 -0.1999938558
-0.857143 1.000000 -1.000000 -0.1714108152
-0.714286 1.000000 -1.000000 -0.1428135587
-0.571429 1.000000 -1.000000 -0.1141948481
-0.428571 1.000000 -1.000000 -0.0855533803
-0.285714 1.000000 -1.000000 -0.0569008469
-0.142857 1.000000 -1.000000 -0.0282622627
0.000000 1.000000 -1.000000 0.0003354626
0.142857 1.000000 -1.000000 0.0288805944
0.285714 1.000000 -1.000000 0.0573848674
0.428571 1.000000 -1.000000 0.0858751911
0.571429 1.000000 -1.000000 0.1143765805
0.714286 1.000000 -1.000000 0.1429007270
0.857143 1.000000 -1.000000 0.1714463276
1.000000 1.000000 -1.000000 0.2000061442
-1.000000 -1.000000 -0.800000 0.2000259329
-0.857143 -1.000000 -0.800000 0.1715035150
-0.714286 -1.000000 -0.800000 0.1430410984
-0.571429 -1.000000 -0.800000 0.1146692329
-0.428571 -1.000000 -0.800000 0.0863934185
-0.285714 -1.000000 -0.800000 0.0581643087
-0.142857 -1.000000 -0.800000 0.0298763236
0.000000 -1.000000 -0.800000 0.0014158857
0.142857 -1.000000 -0.800000 -0.0272665335
0.285714 -1.000000 -0.800000 -0.0561214056
0.428571 -1.000000 -0.800000 -0.0850351529
0.571429 -1.000000 -0.800000 -0.1139021957
0.714286 -1.000000 -0.800000 -0.1426731873
0.857143 -1.000000 -0.800000 -0.1713536279
1.000000 -1.000000 -0.800000 -0.1999740671
-1.000000 -0.833333 -0.800000 0.1667547015
-0.857143 -0.833333 -0.800000 0.1431115554
-0.714286 -0.833333 -0.800000 0.1196720973
-0.571429 -0.833333 -0.800000 0.0965400347
-0.428571 -0.833333 -0.800000 0.0737340393
-0.285714 -0.833333 -0.800000 0.0510865928
-0.142857 -0.833333 -0.800000 0.0282392813
0.000000 -0.833333 -0.800000 0.0048065401
0.142857 -0.833333 -0.800000 -0.0193797663
0.285714 -0.833333 -0.800000 -0.0441515025
0.428571 -0.833333 -0.800000 -0.0691231036
0.571429 -0.833333 -0.800000 -0.0939361558
0.714286 -0.833333 -0.800000 -0.1184231408
0.857143 -0.833333 -0.800000 -0.1426027303
1.000000 -0.833333 -0.800000 -0.1665786318
-1.000000 -0.666667 -0.800000 0.1335726369
-0.857143 -0.666667 -0.800000 0.1149772794
-0.714286 -0.666667 -0.800000 0.0969356030
-0.571429 -0.666667 -0.800000 0.0797295146
-0.428571 -0.666667 -0.800000 0.0634097685
-0.285714 -0.666667 -0.800000 0.0475210030
-0.142857 -0.666667 -0.800000 0.0310889484
0.000000 -0.666667 -0.800000 0.0130655305
0.142857 -0.666667 -0.800000 -0.0070062897
0.285714 -0.666667 -0.800000 -0.0286694732
0.428571 -0.666667 -0.800000 -0.0508759458
0.571429 -0.666667 -0.800000 -0.0726514378
0.714286 -0.666667 -0.800000 -0.0935405874
0.857143 -0.666667 -0.800000 -0.1135941492
1.000000 -0.666667 -0.800000 -0.1330940298
-1.000000 -0.500000 -0.800000 0.1005208752
-0.857143 -0.500000 -0.800000 0.0872195670
-0.714286 -0.500000 -0.800000 0.0751234177
-0.571429 -0.500000 -0.800000 0.0648460341
-0.428571 -0.500000 -0.800000 0.0564978897
-0.285714 -0.500000 -0.800000 0.0490878306
-0.142857 -0.500000 -0.800000 0.0404952323
0.000000 -0.500000 -0.800000 0.0284388247
0.142857 -0.500000 -0.800000 0.0119238037
0.285714 -0.500000 -0.800000 -0.0080550265
0.428571 -0.500000 -0.800000 -0.0292163961
0.571429 -0.500000 -0.800000 -0.0494396802
0.714286 -0.500000 -0.800000 -0.0677337251
0.857143 -0.500000 -0.800000 -0.0842090044
1.000000 -0.500000 -0.800000 -0.0994791248
-1.000000 -0.333333 -0.800000 0.0675745048
-0.857143 -0.333333 -0.800000 0.0597664254
-0.714286 -0.333333 -0.800000 0.0540588285
-0.571429 -0.333333 -0.800000 0.0515211745
-0.428571 -0.333333 -0.800000 0.0523460089
-0.285714 -0.333333 -0.800000 0.0548058408
-0.142857 -0.333333 -0.800000 0.0552046142
0.000000 -0.333333 -0.800000 0.0495662835
0.142857 -0.333333 -0.800000 0.0361569952
0.285714 -0.333333 -0.800000 0.0167106027
0.428571 -0.333333 -0.800000 -0.0047968482
0.571429 -0.333333 -0.800000 -0.0246693017
0.714286 -0.333333 -0.800000 -0.0411792668
0.857143 -0.333333 -0.800000 -0.0545192889
1.000000 -0.333333 -0.800000 -0.0657588285
-1.000000 -0.166667 -0.800000 0.0346003235
-0.857143 -0.166667 -0.800000 0.0322329130
-0.714286 -0.166667 -0.800000 0.0327969620
-0.571429 -0.166667 -0.800000 0.0377850227
-0.428571 -0.166667 -0.800000 0.0474658140
-0.285714 -0.166667 -0.800000 0.0594284281
-0.142857 -0.166667 -0.800000 0.0685146034
0.000000 -0.166667 -0.800000 0.0691753211
0.142857 -0.166667 -0.800000 0.0589907939
0.285714 -0.166667 -0.800000 0.0403808091
0.428571 -0.166667 -0.800000 0.0188943854
0.571429 -0.166667 -0.800000 -0.0003102154
0.714286 -0.166667 -0.800000 -0.0148220857
0.857143 -0.166667 -0.800000 -0.0249099441
1.000000 -0.166667 -0.800000 -0.0320663431
-1.000000 0.000000 -0.800000 0.0014158857
-0.857143 0.000000 -0.800000 0.0040917787
-0.714286 0.000000 -0.800000 0.0100436335
-0.571429 0.000000 -0.800000 0.0209394058
-0.428571 0.000000 -0.800000 0.0370793941
-0.285714 0.000000 -0.800000 0.0557693629
-0.142857 0.000000 -0.800000 0.0712448564
0.000000 0.000000 -0.800000 0.0773047404
0.142857 0.000000 -0.800000 0.0712448564
0.285714 0.000000 -0.800000 0.0557693629
0.428571 0.000000 -0.800000 0.0370793941
0.571429 0.000000 -0.800000 0.0209394058
0.714286 0.000000 -0.800000 0.0100436335
0.857143 0.000000 -0.800000 0.0040917787
1.000000 0.000000 -0.800000 0.0014158857
-1.000000 0.166667 -0.800000 -0.0320663431
-0.857143 0.166667 -0.800000 -0.0249099441
-0.714286 0.166667 -0.800000 -0.0148220857
-0.571429 0.166667 -0.800000 -0.0003102154
-0.428571 0.166667 -0.800000 0.0188943854
-0.285714 0.166667 -0.800000 0.0403808091
-0.142857 0.166667 -0.800000 0.0589907939
0.000000 0.166667 -0.800000 0.0691753211
0.142857 0.166667 -0.800000 0.0685146034
0.285714 0.166667 -0.800000 0.0594284281
0.428571 0.166667 -0.800000 0.0474658140
0.571429 0.166667 -0.800000 0.0377850227
0.714286 0.166667 -0.800000 0.0327969620
0.857143 0.166667 -0.800000 0.0322329130
1.000000 0.166667 -0.800000 0.0346003235
-1.000000 0.333333 -0.800000 -0.0657588285
-0.857143 0.333333 -0.800000 -0.0545192889
-0.714286 0.333333 -0.800000 -0.0411792668
-0.571429 0.333333 -0.800000 -0.0246693017
-0.428571 0.333333 -0.800000 -0.0047968482
-0.285714 0.333333 -0.800000 0.0167106027
-0.142857 0.333333 -0.800000 0.0361569952
0.000000 0.333333 -0.800000 0.0495662835
0.142857 0.333333 -0.800000 0.0552046142
0.285714 0.333333 -0.800000 0.0548058408
0.428571 0.333333 -0.800000 0.0523460089
0.571429 0.333333 -0.800000 0.0515211745
0.714286 0.333333 -0.800000 0.0540588285
0.857143 0.333333 -0.800000 0.0597664254
1.000000 0.333333 -0.800000 0.0675745048
-1.000000 0.500000 -0.800000 -0.0994791248
-0.857143 0.500000 -0.800000 -0.0842090044
-0.714286 0.500000 -0.800000 -0.0677337251
-0.571429 0.500000 -0.800000 -0.0494396802
-0.428571 0.500000 -0.800000 -0.0292163961
-0.285714 0.500000 -0.800000 -0.0080550265
-0.142857 0.500000 -0.800000 0.0119238037
0.000000 0.500000 -0.800000 0.0284388247
0.142857 0.500000 -0.800000 0.0404952323
0.285714 0.500000 -0.800000 0.0490878306
0.428571 0.500000 -0.800000 0.0564978897
0.571429 0.500000 -0.800000 0.0648460341
0.714286 0.500000 -0.800000 0.0751234177
0.857143 0.500000 -0.800000 0.0872195670
1.000000 0.500000 -0.800000 0.1005208752
-1.000000 0.666667 -0.800000 -0.1330940298
-0.857143 0.666667 -0.800000 -0.1135941492
-0.714286 0.666667 -0.800000 -0.0935405874
-0.571429 0.666667 -0.800000 -0.0726514378
-0.428571 0.666667 -0.800000 -0.0508759458
-0.285714 0.666667 -0.800000 -0.0286694732
-0.142857 0.666667 -0.800000 -0.0070062897
0.000000 0.666667 -0.800000 0.0130655305
0.142857 0.666667 -0.800000 0.0310889484
0.285714 0.666667 -0.800000 0.0475210030
0.428571 0.666667 -0.800000 0.0634097685
0.571429 0.666667 -0.800000 0.0797295146
0.714286 0.666667 -0.800000 0.0969356030
0.857143 0.666667 -0.800000 0.1149772794
1.000000 0.666667 -0.800000 0.1335726369
-1.000000 0.833333 -0.800000 -0.1665786318
-0.857143 0.833333 -0.800000 -0.1426027303
-0.714286 0.833333 -0.800000 -0.1184231408
-0.571429 0.833333 -0.800000 -0.0939361558
-0.428571 0.833333 -0.800000 -0.0691231036
-0.285714 0.833333 -0.800000 -0.0441515025
-0.142857 0.833333 -0.800000 -0.0193797663
0.000000 0.833333 -0.800000 0.0048065401
0.142857 0.833333 -0.800000 0.0282392813
0.285714 0.833333 -0.800000 0.0510865928
0.428571 0.833333 -0.800000 0.0737340393
0.571429 0.833333 -0.800000 0.0965400347
0.714286 0.833333 -0.800000 0.1196720973
0.857143 0.833333 -0.800000 0.1431115554
1.000000 0.833333 -0.800000 0.1667547015
-1.000000 1.000000 -0.800000 -0.1999740671
-0.857143 1.000000 -0.800000 -0.1713536279
-0.714286 1.000000 -0.800000 -0.1426731873
-0.571429 1.000000 -0.800000 -0.1139021957
-0.428571 1.000000 -0.800000 -0.0850351529
-0.285714 1.000000 -0.800000 -0.0561214056
-0.142857 1.000000 -0.800000 -0.0272665335
0.000000 1.000000 -0.800000 0.0014158857
0.142857 1.000000 -0.800000 0.0298763236
0.285714 1.000000 -0.800000 0.0581643087
0.428571 1.000000 -0.800000 0.0863934185
0.571429 1.000000 -0.800000 0.1146692329
0.714286 1.000000 -0.800000 0.1430410984
0.857143 1.000000 -0.800000 0.1715035150
1.000000 1.000000 -0.800000 0.2000259329
-1.000000 -1.000000 -0.600000 0.2000794804
-0.857143 -1.000000 -0.600000 0.1716582625
-0.714286 -1.000000 -0.600000 0.1434209398
-0.571429 -1.000000 -0.600000 0.1154611429
-0.428571 -1.000000 -0.600000 0.0877957287
-0.285714 -1.000000 -0.600000 0.0602734571
-0.142857 -1.000000 -0.600000 0.0325707417
0.000000 -1.000000 -0.600000 0.0043394833
0.142857 -1.000000 -0.600000 -0.0245721155
0.285714 -1.000000 -0.600000 -0.0540122572
0.428571 -1.000000 -0.600000 -0.0836328427
0.571429 -1.000000 -0.600000 -0.1131102857
0.714286 -1.000000 -0.600000 -0.1422933459
0.857143 -1.000000 -0.600000 -0.1711988804
1.000000 -1.000000 -0.600000 -0.1999205196
-1.000000 -0.833333 -0.600000 0.1669364807
-0.857143 -0.833333 -0.600000 0.1436368803
-0.714286 -0.833333 -0.600000 0.1209615537
-0.571429 -0.833333 -0.600000 0.0992283499
-0.428571 -0.833333 -0.600000 0.0784944942
-0.285714 -0.833333 -0.600000 0.0582465679
-0.142857 -0.833333 -0.600000 0.0373860848
0.000000 -0.833333 -0.600000 0.0147313445
0.142857 -0.833333 -0.600000 -0.0102329628
0.285714 -0.833333 -0.600000 -0.0369915273
0.428571 -0.833333 -0.600000 -0.0643626486
0.571429 -0.833333 -0.600000 -0.0912478406
0.714286 -0.833333 -0.600000 -0.1171336843
0.857143 -0.833333 -0.600000 -0.1420774054
1.000000 -0.833333 -0.600000 -0.1663968527
-1.000000 -0.666667 -0.600000 0.1340667638
-0.857143 -0.666667 -0.600000 0.1164052604
-0.714286 -0.666667 -0.600000 0.1004407092
-0.571429 -0.666667 -0.600000 0.0870371129
-0.428571 -0.666667 -0.600000 0.0763500267
-0.285714 -0.666667 -0.600000 0.0669838333
-0.142857 -0.666667 -0.600000 0.0559525380
0.000000 -0.666667 -0.600000 0.0400439460
0.142857 -0.666667 -0.600000 0.0178572999
0.285714 -0.666667 -0.600000 -0.0092066429
0.428571 -0.666667 -0.600000 -0.0379356876
0.571429 -0.666667 -0.600000 -0.0653438395
0.714286 -0.666667 -0.600000 -0.0900354813
0.857143 -0.666667 -0.600000 -0.1121661681
1.000000 -0.666667 -0.600000 -0.1325999029
-1.000000 -0.500000 -0.600000 0.1015964067
-0.857143 -0.500000 -0.600000 0.0903277533
-0.714286 -0.500000 -0.600000 0.0827527366
-0.571429 -0.500000 -0.600000 0.0807519713
-0.428571 -0.500000 -0.600000 0.0846640430
-0.285714 -0.500000 -0.600000 0.0914512097
-0.142857 -0.500000 -0.600000 0.0946140656
0.000000 -0.500000 -0.600000 0.0871608515
0.142857 -0.500000 -0.600000 0.0660426370
0.285714 -0.500000 -0.600000 0.0343083525
0.428571 -0.500000 -0.600000 -0.0010502427
0.571429 -0.500000 -0.600000 -0.0335337430
0.714286 -0.500000 -0.600000 -0.0601044063
0.857143 -0.500000 -0.600000 -0.0811008181
1.000000 -0.500000 -0.600000 -0.0984035933
-1.000000 -0.333333 -0.600000 0.0694490582
-0.857143 -0.333333 -0.600000 0.0651837114
-0.714286 -0.333333 -0.600000 0.0673560370
-0.571429 -0.333333 -0.600000 0.0792437756
-0.428571 -0.333333 -0.600000 0.1014370511
-0.285714 -0.333333 -0.600000 0.1286413553
-0.142857 -0.333333 -0.600000 0.1495288159
0.000000 -0.333333 -0.600000 0.1519134323
0.142857 -0.333333 -0.600000 0.1304811968
0.285714 -0.333333 -0.600000 0.0905461172
0.428571 -0.333333 -0.600000 0.0442941939
0.571429 -0.333333 -0.600000 0.0030532994
0.714286 -0.333333 -0.600000 -0.0278820583
0.857143 -0.333333 -0.600000 -0.0491020029
1.000000 -0.333333 -0.600000 -0.0638842751
-1.000000 -0.166667 -0.600000 0.0372164736
-0.857143 -0.166667 -0.600000 0.0397933446
-0.714286 -0.166667 -0.600000 0.0513547114
-0.571429 -0.166667 -0.600000 0.0764750292
-0.428571 -0.166667 -0.600000 0.1159778824
-0.285714 -0.166667 -0.600000 0.1624741896
-0.142857 -0.166667 -0.600000 0.2001546312
0.000000 -0.166667 -0.600000 0.2120122737
0.142857 -0.166667 -0.600000 0.1906308216
0.285714 -0.166667 -0.600000 0.1434265706
0.428571 -0.166667 -0.600000 0.0874064538
0.571429 -0.166667 -0.600000 0.0383797911
0.714286 -0.166667 -0.600000 0.0037356638
0.857143 -0.166667 -0.600000 -0.0173495125
1.000000 -0.166667 -0.600000 -0.0294501931
-1.000000 0.000000 -0.600000 0.0043394833
-0.857143 0.000000 -0.600000 0.0125407052
-0.714286 0.000000 -0.600000 0.0307822724
-0.571429 0.000000 -0.600000 0.0641762260
-0.428571 0.000000 -0.600000 0.1136429370
-0.285714 0.000000 -0.600000 0.1709249663
-0.142857 0.000000 -0.600000 0.2183550977
0.000000 0.000000 -0.600000 0.2369277587
0.142857 0.000000 -0.600000 0.2183550977
0.285714 0.000000 -0.600000 0.1709249663
0.428571 0.000000 -0.600000 0.1136429370
0.571429 0.000000 -0.600000 0.0641762260
0.714286 0.000000 -0.600000 0.0307822724
0.857143 0.000000 -0.600000 0.0125407052
1.000000 0.000000 -0.600000 0.0043394833
-1.000000 0.166667 -0.600000 -0.0294501931
-0.857143 0.166667 -0.600000 -0.0173495125
-0.714286 0.166667 -0.600000 0.0037356638
-0.571429 0.166667 -0.600000 0.0383797911
-0.428571 0.166667 -0.600000 0.0874064538
-0.285714 0.166667 -0.600000 0.1434265706
-0.142857 0.166667 -0.600000 0.1906308216
0.000000 0.166667 -0.600000 0.2120122737
0.142857 0.166667 -0.600000 0.2001546312
0.285714 0.166667 -0.600000 0.1624741896
0.428571 0.166667 -0.600000 0.1159778824
0.571429 0.166667 -0.600000 0.0764750292
0.714286 0.166667 -0.600000 0.0513547114
0.857143 0.166667 -0.600000 0.0397933446
1.000000 0.166667 -0.600000 0.0372164736
-1.000000 0.333333 -0.600000 -0.0638842751
-0.857143 0.333333 -0.600000 -0.0491020029
-0.714286 0.333333 -0.600000 -0.0278820583
-0.571429 0.333333 -0.600000 0.0030532994
-0.428571 0.333333 -0.600000 0.0442941939
-0.285714 0.333333 -0.600000 0.0905461172
-0.142857 0.333333 -0.600000 0.1304811968
0.000000 0.333333 -0.600000 0.1519134323
0.142857 0.333333 -0.600000 0.1495288159
0.285714 0.333333 -0.600000 0.1286413553
0.428571 0.333333 -0.600000 0.1014370511
0.571429 0.333333 -0.600000 0.0792437756
0.714286 0.333333 -0.600000 0.0673560370
0.857143 0.333333 -0.600000 0.0651837114
1.000000 0.333333 -0.600000 0.0694490582
-1.000000 0.500000 -0.600000 -0.0984035933
-0.857143 0.500000 -0.600000 -0.0811008181
-0.714286 0.500000 -0.600000 -0.0601044063
-0.571429 0.500000 -0.600000 -0.0335337430
-0.428571 0.500000 -0.600000 -0.0010502427
-0.285714 0.500000 -0.600000 0.0343083525
-0.142857 0.500000 -0.600000 0.0660426370
0.000000 0.500000 -0.600000 0.0871608515
0.142857 0.500000 -0.600000 0.0946140656
0.285714 0.500000 -0.600000 0.0914512097
0.428571 0.500000 -0.600000 0.0846640430
0.571429 0.500000 -0.600000 0.0807519713
0.714286 0.500000 -0.600000 0.0827527366
0.857143 0.500000 -0.600000 0.0903277533
1.000000 0.500000 -0.600000 0.1015964067
-1.000000 0.666667 -0.600000 -0.1325999029
-0.857143 0.666667 -0.600000 -0.1121661681
-0.714286 0.666667 -0.600000 -0.0900354813
-0.571429 0.666667 -0.600000 -0.0653438395
-0.428571 0.666667 -0.600000 -0.0379356876
-0.285714 0.666667 -0.600000 -0.0092066429
-0.142857 0.666667 -0.600000 0.0178572999
0.000000 0.666667 -0.600000 0.0400439460
0.142857 0.666667 -0.600000 0.0559525380
0.285714 0.666667 -0.600000 0.0669838333
0.428571 0.666667 -0.600000 0.0763500267
0.571429 0.666667 -0.600000 0.0870371129
0.714286 0.666667 -0.600000 0.1004407092
0.857143 0.666667 -0.600000 0.1164052604
1.000000 0.666667 -0.600000 0.1340667638
-1.000000 0.833333 -0.600000 -0.1663968527
-0.857143 0.833333 -0.600000 -0.1420774054
-0.714286 0.833333 -0.600000 -0.1171336843
-0.571429 0.833333 -0.600000 -0.0912478406
-0.428571 0.833333 -0.600000 -0.0643626486
-0.285714 0.833333 -0.600000 -0.0369915273
-0.142857 0.833333 -0.600000 -0.0102329628
0.000000 0.833333 -0.600000 0.0147313445
0.142857 0.833333 -0.600000 0.0373860848
0.285714 0.833333 -0.600000 0.0582465679
0.428571 0.833333 -0.600000 0.0784944942
0.571429 0.833333 -0.600000 0.0992283499
0.714286 0.833333 -0.600000 0.1209615537
0.857143 0.833333 -0.600000 0.1436368803
1.000000 0.833333 -0.600000 0.1669364807
-1.000000 1.000000 -0.600000 -0.1999205196
-0.857143 1.000000 -0.600000 -0.1711988804
-0.714286 1.000000 -0.600000 -0.1422933459
-0.571429 1.000000 -0.600000 -0.1131102857
-0.428571 1.000000 -0.600000 -0.0836328427
-0.285714 1.000000 -0.600000 -0.0540122572
-0.142857 1.000000 -0.600000 -0.0245721155
0.000000 1.000000 -0.600000 0.0043394833
0.142857 1.000000 -0.600000 0.0325707417
0.285714 1.000000 -0.600000 0.0602734571
0.428571 1.000000 -0.600000 0.0877957287
0.571429 1.000000 -0.600000 0.1154611429
0.714286 1.000000 -0.600000 0.1434209398
0.857143 1.000000 -0.600000 0.1716582625
1.000000 1.000000 -0.600000 0.2000794804
-1.000000 -1.000000 -0.400000 0.2001768869
-0.857143 -1.000000 -0.400000 0.1719397582
-0.714286 -1.000000 -0.400000 0.1441118961
-0.571429 -1.000000 -0.400000 0.1169016787
-0.428571 -1.000000 -0.400000 0.0903466223
-0.285714 -1.000000 -0.400000 0.0641101355
-0.142857 -1.000000 -0.400000 0.0374720636
0.000000 -1.000000 -0.400000 0.0096576976
0.142857 -1.000000 -0.400000 -0.0196707935
0.285714 -1.000000 -0.400000 -0.0501755788
0.428571 -1.000000 -0.400000 -0.0810819491
0.571429 -1.000000 -0.400000 -0.1116697499
0.714286 -1.000000 -0.400000 -0.1416023896
0.857143 -1.000000 -0.400000 -0.1709173846
1.000000 -1.000000 -0.400000 -0.1998231131
-1.000000 -0.833333 -0.400000 0.1672671487
-0.857143 -0.833333 -0.400000 0.1445924805
-0.714286 -0.833333 -0.400000 0.1233071591
-0.571429 -0.833333 -0.400000 0.1041185703
-0.428571 -0.833333 -0.400000 0.0871540718
-0.285714 -0.833333 -0.400000 0.0712710290
-0.142857 -0.833333 -0.400000 0.0540247159
0.000000 -0.833333 -0.400000 0.0327852101
0.142857 -0.833333 -0.400000 0.0064056683
0.285714 -0.833333 -0.400000 -0.0239670663
0.428571 -0.833333 -0.400000 -0.0557030710
0.571429 -0.833333 -0.400000 -0.0863576202
0.714286 -0.833333 -0.400000 -0.1147880790
0.857143 -0.833333 -0.400000 -0.1411218052
1.000000 -0.833333 -0.400000 -0.1660661846
-1.000000 -0.666667 -0.400000 0.1349656128
-0.857143 -0.666667 -0.400000 0.1190028510
-0.714286 -0.666667 -0.400000 0.1068167254
-0.571429 -0.666667 -0.400000 0.1003301101
-0.428571 -0.666667 -0.400000 0.0998891991
-0.285714 -0.666667 -0.400000 0.1023879892
-0.142857 -0.666667 -0.400000 0.1011810267
0.000000 -0.666667 -0.400000 0.0891194408
0.142857 -0.666667 -0.400000 0.0630857886
0.285714 -0.666667 -0.400000 0.0261975130
0.428571 -0.666667 -0.400000 -0.0143965152
0.571429 -0.666667 -0.400000 -0.0520508422
0.714286 -0.666667 -0.400000 -0.0836594650
0.857143 -0.666667 -0.400000 -0.1095685776
1.000000 -0.666667 -0.400000 -0.1317010538
-1.000000 -0.500000 -0.400000 0.1035528684
-0.857143 -0.500000 -0.400000 0.0959817467
-0.714286 -0.500000 -0.400000 0.0966309645
-0.571429 -0.500000 -0.400000 0.1096859070
-0.428571 -0.500000 -0.400000 0.1359001102
-0.285714 -0.500000 -0.400000 0.1685129550
-0.142857 -0.500000 -0.400000 0.1930597478
0.000000 -0.500000 -0.400000 0.1939800423
0.142857 -0.500000 -0.400000 0.1644883193
0.285714 -0.500000 -0.400000 0.1113700978
0.428571 -0.500000 -0.400000 0.0501858245
0.571429 -0.500000 -0.400000 -0.0045998073
0.714286 -0.500000 -0.400000 -0.0462261784
0.857143 -0.500000 -0.400000 -0.0754468247
1.000000 -0.500000 -0.400000 -0.0964471316
-1.000000 -0.333333 -0.400000 0.0728589930
-0.857143 -0.333333 -0.400000 0.0750381073
-0.714286 -0.333333 -0.400000 0.0915445253
-0.571429 -0.333333 -0.400000 0.1296729924
-0.428571 -0.333333 -0.400000 0.1907368537
-0.285714 -0.333333 -0.400000 0.2629529647
-0.142857 -0.333333 -0.400000 0.3211106813
0.000000 -0.333333 -0.400000 0.3380895613
0.142857 -0.333333 -0.400000 0.3020630623
0.285714 -0.333333 -0.400000 0.2248577266
0.428571 -0.333333 -0.400000 0.1335939966
0.571429 -0.333333 -0.400000 0.0534825162
0.714286 -0.333333 -0.400000 -0.0036935700
0.857143 -0.333333 -0.400000 -0.0392476070
1.000000 -0.333333 -0.400000 -0.0604743404
-1.000000 -0.166667 -0.400000 0.0419754209
-0.857143 -0.166667 -0.400000 0.0535462621
-0.714286 -0.166667 -0.400000 0.0851124662
-0.571429 -0.166667 -0.400000 0.1468546709
-0.428571 -0.166667 -0.400000 0.2406057965
-0.285714 -0.166667 -0.400000 0.3499211404
-0.142857 -0.166667 -0.400000 0.4396164145
0.000000 -0.166667 -0.400000 0.4718419925
0.142857 -0.166667 -0.400000 0.4300926050
0.285714 -0.166667 -0.400000 0.3308735214
0.428571 -0.166667 -0.400000 0.2120343679
0.571429 -0.166667 -0.400000 0.1087594328
0.714286 -0.166667 -0.400000 0.0374934186
0.857143 -0.166667 -0.400000 -0.0035965951
1.000000 -0.166667 -0.400000 -0.0246912458
-1.000000 0.000000 -0.400000 0.0096576976
-0.857143 0.000000 -0.400000 0.0279098527
-0.714286 0.000000 -0.400000 0.0685072071
-0.571429 0.000000 -0.400000 0.1428268175
-0.428571 0.000000 -0.400000 0.2529170075
-0.285714 0.000000 -0.400000 0.3804005082
-0.142857 0.000000 -0.400000 0.4859582068
0.000000 0.000000 -0.400000 0.5272924240
0.142857 0.000000 -0.400000 0.4859582068
0.285714 0.000000 -0.400000 0.3804005082
0.428571 0.000000 -0.400000 0.2529170075
0.571429 0.000000 -0.400000 0.1428268175
0.714286 0.000000 -0.400000 0.0685072071
0.857143 0.000000 -0.400000 0.0279098527
1.000000 0.000000 -0.400000 0.0096576976
-1.000000 0.166667 -0.400000 -0.0246912458
-0.857143 0.166667 -0.400000 -0.0035965951
-0.714286 0.166667 -0.400000 0.0374934186
-0.571429 0.166667 -0.400000 0.1087594328
-0.428571 0.166667 -0.400000 0.2120343679
-0.285714 0.166667 -0.400000 0.3308735214
-0.142857 0.166667 -0.400000 0.4300926050
0.000000 0.166667 -0.400000 0.4718419925
0.142857 0.166667 -0.400000 0.4396164145
0.285714 0.166667 -0.400000 0.3499211404
0.428571 0.166667 -0.400000 0.2406057965
0.571429 0.166667 -0.400000 0.1468546709
0.714286 0.166667 -0.400000 0.0851124662
0.857143 0.166667 -0.400000 0.0535462621
1.000000 0.166667 -0.400000 0.0419754209
-1.000000 0.333333 -0.400000 -0.0604743404
-0.857143 0.333333 -0.400000 -0.0392476070
-0.714286 0.333333 -0.400000 -0.0036935700
-0.571429 0.333333 -0.400000 0.0534825162
-0.428571 0.333333 -0.400000 0.1335939966
-0.285714 0.333333 -0.400000 0.2248577266
-0.142857 0.333333 -0.400000 0.3020630623
0.000000 0.333333 -0.400000 0.3380895613
0.142857 0.333333 -0.400000 0.3211106813
0.285714 0.333333 -0.400000 0.2629529647
0.428571 0.333333 -0.400000 0.1907368537
0.571429 0.333333 -0.400000 0.1296729924
0.714286 0.333333 -0.400000 0.0915445253
0.857143 0.333333 -0.400000 0.0750381073
1.000000 0.333333 -0.400000 0.0728589930
-1.000000 0.500000 -0.400000 -0.0964471316
-0.857143 0.500000 -0.400000 -0.0754468247
-0.714286 0.500000 -0.400000 -0.0462261784
-0.571429 0.500000 -0.400000 -0.0045998073
-0.428571 0.500000 -0.400000 0.0501858245
-0.285714 0.500000 -0.400000 0.1113700978
-0.142857 0.500000 -0.400000 0.1644883193
0.000000 0.500000 -0.400000 0.1939800423
0.142857 0.500000 -0.400000 0.1930597478
0.285714 0.500000 -0.400000 0.1685129550
0.428571 0.500000 -0.400000 0.1359001102
0.571429 0.500000 -0.400000 0.1096859070
0.714286 0.500000 -0.400000 0.0966309645
0.857143 0.500000 -0.400000 0.0959817467
1.000000 0.500000 -0.400000 0.1035528684
-1.000000 0.666667 -0.400000 -0.1317010538
-0.857143 0.666667 -0.400000 -0.1095685776
-0.714286 0.666667 -0.400000 -0.0836594650
-0.571429 0.666667 -0.400000 -0.0520508422
-0.428571 0.666667 -0.400000 -0.0143965152
-0.285714 0.666667 -0.400000 0.0261975130
-0.142857 0.666667 -0.400000 0.0630857886
0.000000 0.666667 -0.400000 0.0891194408
0.142857 0.666667 -0.400000 0.1011810267
0.285714 0.666667 -0.400000 0.1023879892
0.428571 0.666667 -0.400000 0.0998891991
0.571429 0.666667 -0.400000 0.1003301101
0.714286 0.666667 -0.400000 0.1068167254
0.857143 0.666667 -0.400000 0.1190028510
1.000000 0.666667 -0.400000 0.1349656128
-1.000000 0.833333 -0.400000 -0.1660661846
-0.857143 0.833333 -0.400000 -0.1411218052
-0.714286 0.833333 -0.400000 -0.1147880790
-0.571429 0.833333 -0.400000 -0.0863576202
-0.428571 0.833333 -0.400000 -0.0557030710
-0.285714 0.833333 -0.400000 -0.0239670663
-0.142857 0.833333 -0.400000 0.0064056683
0.000000 0.833333 -0.400000 0.0327852101
0.142857 0.833333 -0.400000 0.0540247159
0.285714 0.833333 -0.400000 0.0712710290
0.428571 0.833333 -0.400000 0.0871540718
0.571429 0.833333 -0.400000 0.1041185703
0.714286 0.833333 -0.400000 0.1233071591
0.857143 0.833333 -0.400000 0.1445924805
1.000000 0.833333 -0.400000 0.1672671487
-1.000000 1.000000 -0.400000 -0.1998231131
-0.857143 1.000000 -0.400000 -0.1709173846
-0.714286 1.000000 -0.400000 -0.1416023896
-0.571429 1.000000 -0.400000 -0.1116697499
-0.428571 1.000000 -0.400000 -0.0810819491
-0.285714 1.000000 -0.400000 -0.0501755788
-0.142857 1.000000 -0.400000 -0.0196707935
0.000000 1.000000 -0.400000 0.0096576976
0.142857 1.000000 -0.400000 0.0374720636
0.285714 1.000000 -0.400000 0.0641101355
0.428571 1.000000 -0.400000 0.0903466223
0.571429 1.000000 -0.400000 0.1169016787
0.714286 1.000000 -0.400000 0.1441118961
0.857143 1.000000 -0.400000 0.1719397582
1.000000 1.000000 -0.400000 0.2001768869
-1.000000 -1.000000 -0.200000 0.2002858624
-0.857143 -1.000000 -0.200000 0.1722546873
-0.714286 -1.000000 -0.200000 0.1448849175
-0.571429 -1.000000 -0.200000 0.1185133074
-0.428571 -1.000000 -0.200000 0.0932004863
-0.285714 -1.000000 -0.200000 0.0684024973
-0.142857 -1.000000 -0.200000 0.0429555170
0.000000 -1.000000 -0.200000 0.0156075579
0.142857 -1.000000 -0.200000 -0.0141873401
0.285714 -1.000000 -0.200000 -0.0458832170
0.428571 -1.000000 -0.200000 -0.0782280851
0.571429 -1.000000 -0.200000 -0.1100581212
0.714286 -1.000000 -0.200000 -0.1408293682
0.857143 -1.000000 -0.200000 -0.1706024556
1.000000 -1.000000 -0.200000 -0.1997141376
-1.000000 -0.833333 -0.200000 0.1676370904
-0.857143 -0.833333 -0.200000 0.1456615776
-0.714286 -0.833333 -0.200000 0.1259313526
-0.571429 -0.833333 -0.200000 0.1095896036
-0.428571 -0.833333 -0.200000 0.0968421501
-0.285714 -0.833333 -0.200000 0.0858424092
-0.142857 -0.833333 -0.200000 0.0726395223
0.000000 -0.833333 -0.200000 0.0529833388
0.142857 -0.833333 -0.200000 0.0250204747
0.285714 -0.833333 -0.200000 -0.0093956860
0.428571 -0.833333 -0.200000 -0.0460149928
0.571429 -0.833333 -0.200000 -0.0808865868
0.714286 -0.833333 -0.200000 -0.1121638855
0.857143 -0.833333 -0.200000 -0.1400527081
1.000000 -0.833333 -0.200000 -0.1656962430
-1.000000 -0.666667 -0.200000 0.1359712184
-0.857143 -0.666667 -0.200000 0.1219089582
-0.714286 -0.666667 -0.200000 0.1139500231
-0.571429 -0.666667 -0.200000 0.1152019207
-0.428571 -0.666667 -0.200000 0.1262241262
-0.285714 -0.666667 -0.200000 0.1419971074
-0.142857 -0.666667 -0.200000 0.1517813168
0.000000 -0.666667 -0.200000 0.1440236470
0.142857 -0.666667 -0.200000 0.1136860787
0.285714 -0.666667 -0.200000 0.0658066312
0.428571 -0.666667 -0.200000 0.0119384119
0.571429 -0.666667 -0.200000 -0.0371790317
0.714286 -0.666667 -0.200000 -0.0765261674
0.857143 -0.666667 -0.200000 -0.1066624704
1.000000 -0.666667 -0.200000 -0.1306954482
-1.000000 -0.500000 -0.200000 0.1057416997
-0.857143 -0.500000 -0.200000 0.1023072666
-0.714286 -0.500000 -0.200000 0.1121575137
-0.571429 -0.500000 -0.200000 0.1420563350
-0.428571 -0.500000 -0.200000 0.1932215008
-0.285714 -0.500000 -0.200000 0.2547273472
-0.142857 -0.500000 -0.200000 0.3031978537
0.000000 -0.500000 -0.200000 0.3134861809
0.142857 -0.500000 -0.200000 0.2746264251
0.285714 -0.500000 -0.200000 0.1975844900
0.428571 -0.500000 -0.200000 0.1075072151
0.571429 -0.500000 -0.200000 0.0277706207
0.714286 -0.500000 -0.200000 -0.0306996291
0.857143 -0.500000 -0.200000 -0.0691213048
1.000000 -0.500000 -0.200000 -0.0942583003
-1.000000 -0.333333 -0.200000 0.0766739267
-0.857143 -0.333333 -0.200000 0.0860629129
-0.714286 -0.333333 -0.200000 0.1186058876
-0.571429 -0.333333 -0.200000 0.1860917027
-0.428571 -0.333333 -0.200000 0.2906428210
-0.285714 -0.333333 -0.200000 0.4132168047
-0.142857 -0.333333 -0.200000 0.5130713771
0.000000 -0.333333 -0.200000 0.5463778856
0.142857 -0.333333 -0.200000 0.4940237580
0.285714 -0.333333 -0.200000 0.3751215666
0.428571 -0.333333 -0.200000 0.2334999639
0.571429 -0.333333 -0.200000 0.1099012265
0.714286 -0.333333 -0.200000 0.0233677924
0.857143 -0.333333 -0.200000 -0.0282228014
1.000000 -0.333333 -0.200000 -0.0566594066
-1.000000 -0.166667 -0.200000 0.0472995898
-0.857143 -0.166667 -0.200000 0.0689326177
-0.714286 -0.166667 -0.200000 0.1228796398
-0.571429 -0.166667 -0.200000 0.2255933239
-0.428571 -0.166667 -0.200000 0.3800358059
-0.285714 -0.166667 -0.200000 0.5596312226
-0.142857 -0.166667 -0.200000 0.7075191467
0.000000 -0.166667 -0.200000 0.7625317659
0.142857 -0.166667 -0.200000 0.6979953371
0.285714 -0.166667 -0.200000 0.5405836035
0.428571 -0.166667 -0.200000 0.3514643773
0.571429 -0.166667 -0.200000 0.1874980858
0.714286 -0.166667 -0.200000 0.0752605921
0.857143 -0.166667 -0.200000 0.0117897605
1.000000 -0.166667 -0.200000 -0.0193670769
-1.000000 0.000000 -0.200000 0.0156075579
-0.857143 0.000000 -0.200000 0.0451043985
-0.714286 0.000000 -0.200000 0.1107127437
-0.571429 0.000000 -0.200000 0.2308187637
-0.428571 0.000000 -0.200000 0.4087327017
-0.285714 0.000000 -0.200000 0.6147555239
-0.142857 0.000000 -0.200000 0.7853446185
0.000000 0.000000 -0.200000 0.8521437890
0.142857 0.000000 -0.200000 0.7853446185
0.285714 0.000000 -0.200000 0.6147555239
0.428571 0.000000 -0.200000 0.4087327017
0.571429 0.000000 -0.200000 0.2308187637
0.714286 0.000000 -0.200000 0.1107127437
0.857143 0.000000 -0.200000 0.0451043985
1.000000 0.000000 -0.200000 0.0156075579
-1.000000 0.166667 -0.200000 -0.0193670769
-0.857143 0.166667 -0.200000 0.0117897605
-0.714286 0.166667 -0.200000 0.0752605921
-0.571429 0.166667 -0.200000 0.1874980858
-0.428571 0.166667 -0.200000 0.3514643773
-0.285714 0.166667 -0.200000 0.5405836035
-0.142857 0.166667 -0.200000 0.6979953371
0.000000 0.166667 -0.200000 0.7625317659
0.142857 0.166667 -0.200000 0.7075191467
0.285714 0.166667 -0.200000 0.5596312226
0.428571 0.166667 -0.200000 0.3800358059
0.571429 0.166667 -0.200000 0.2255933239
0.714286 0.166667 -0.200000 0.1228796398
0.857143 0.166667 -0.200000 0.0689326177
1.000000 0.166667 -0.200000 0.0472995898
-1.000000 0.333333 -0.200000 -0.0566594066
-0.857143 0.333333 -0.200000 -0.0282228014
-0.714286 0.333333 -0.200000 0.0233677924
-0.571429 0.333333 -0.200000 0.1099012265
-0.428571 0.333333 -0.200000 0.2334999639
-0.285714 0.333333 -0.200000 0.3751215666
-0.142857 0.333333 -0.200000 0.4940237580
0.000000 0.333333 -0.200000 0.5463778856
0.142857 0.333333 -0.200000 0.5130713771
0.285714 0.333333 -0.200000 0.4132168047
0.428571 0.333333 -0.200000 0.2906428210
0.571429 0.333333 -0.200000 0.1860917027
0.714286 0.333333 -0.200000 0.1186058876
0.857143 0.333333 -0.200000 0.0860629129
1.000000 0.333333 -0.200000 0.0766739267
-1.000000 0.500000 -0.200000 -0.0942583003
-0.857143 0.500000 -0.200000 -0.0691213048
-0.714286 0.500000 -0.200000 -0.0306996291
-0.571429 0.500000 -0.200000 0.0277706207
-0.428571 0.500000 -0.200000 0.1075072151
-0.285714 0.500000 -0.200000 0.1975844900
-0.142857 0.500000 -0.200000 0.2746264251
0.000000 0.500000 -0.200000 0.3134861809
0.142857 0.500000 -0.200000 0.3031978537
0.285714 0.500000 -0.200000 0.2547273472
0.428571 0.500000 -0.200000 0.1932215008
0.571429 0.500000 -0.200000 0.1420563350
0.714286 0.500000 -0.200000 0.1121575137
0.857143 0.500000 -0.200000 0.1023072666
1.000000 0.500000 -0.200000 0.1057416997
-1.000000 0.666667 -0.200000 -0.1306954482
-0.857143 0.666667 -0.200000 -0.1066624704
-0.714286 0.666667 -0.200000 -0.0765261674
-0.571429 0.666667 -0.200000 -0.0371790317
-0.428571 0.666667 -0.200000 0.0119384119
-0.285714 0.666667 -0.200000 0.0658066312
-0.142857 0.666667 -0.200000 0.1136860787
0.000000 0.666667 -0.200000 0.1440236470
0.142857 0.666667 -0.200000 0.1517813168
0.285714 0.666667 -0.200000 0.1419971074
0.428571 0.666667 -0.200000 0.1262241262
0.571429 0.666667 -0.200000 0.1152019207
0.714286 0.666667 -0.200000 0.1139500231
0.857143 0.666667 -0.200000 0.1219089582
1.000000 0.666667 -0.200000 0.1359712184
-1.000000 0.833333 -0.200000 -0.1656962430
-0.857143 0.833333 -0.200000 -0.1400527081
-0.714286 0.833333 -0.200000 -0.1121638855
-0.571429 0.833333 -0.200000 -0.0808865868
-0.428571 0.833333 -0.200000 -0.0460149928
-0.285714 0.833333 -0.200000 -0.0093956860
-0.142857 0.833333 -0.200000 0.0250204747
0.000000 0.833333 -0.200000 0.0529833388
0.142857 0.833333 -0.200000 0.0726395223
0.285714 0.833333 -0.200000 0.0858424092
0.428571 0.833333 -0.200000 0.0968421501
0.571429 0.833333 -0.200000 0.1095896036
0.714286 0.833333 -0.200000 0.1259313526
0.857143 0.833333 -0.200000 0.1456615776
1.000000 0.833333 -0.200000 0.1676370904
-1.000000 1.000000 -0.200000 -0.1997141376
-0.857143 1.000000 -0.200000 -0.1706024556
-0.714286 1.000000 -0.200000 -0.1408293682
-0.571429 1.000000 -0.200000 -0.1100581212
-0.428571 1.000000 -0.200000 -0.0782280851
-0.285714 1.000000 -0.200000 -0.0458832170
-0.142857 1.000000 -0.200000 -0.0141873401
0.000000 1.000000 -0.200000 0.0156075579
0.142857 1.000000 -0.200000 0.0429555170
0.285714 1.000000 -0.200000 0.0684024973
0.428571 1.000000 -0.200000 0.0932004863
0.571429 1.000000 -0.200000 0.1185133074
0.714286 1.000000 -0.200000 0.1448849175
0.857143 1.000000 -0.200000 0.1722546873
1.000000 1.000000 -0.200000 0.2002858624
-1.000000 -1.000000 0.000000 0.2003354626
-0.857143 -1.000000 0.000000 0.1723980274
-0.714286 -1.000000 0.000000 0.1452367584
-0.571429 -1.000000 0.000000 0.1192468408
-0.428571 -1.000000 0.000000 0.0944994235
-0.285714 -1.000000 0.000000 0.0703561673
-0.142857 -1.000000 0.000000 0.0454513127
0.000000 -1.000000 0.000000 0.0183156389
0.142857 -1.000000 0.000000 -0.0116915444
0.285714 -1.000000 0.000000 -0.0439295470
0.428571 -1.000000 0.000000 -0.0769291480
0.571429 -1.000000 0.000000 -0.1093245878
0.714286 -1.000000 0.000000 -0.1404775273
0.857143 -1.000000 0.000000 -0.1704591155
1.000000 -1.000000 0.000000 -0.1996645374
-1.000000 -0.833333 0.000000 0.1678054694
-0.857143 -0.833333 0.000000 0.1461481775
-0.714286 -0.833333 0.000000 0.1271257552
-0.571429 -0.833333 0.000000 0.1120797464
-0.428571 -0.833333 0.000000 0.1012516822
-0.285714 -0.833333 0.000000 0.0924745780
-0.142857 -0.833333 0.000000 0.0811120579
0.000000 -0.833333 0.000000 0.0621765240
0.142857 -0.833333 0.000000 0.0334930103
0.285714 -0.833333 0.000000 -0.0027635173
0.428571 -0.833333 0.000000 -0.0416054606
0.571429 -0.833333 0.000000 -0.0783964441
0.714286 -0.833333 0.000000 -0.1109694829
0.857143 -0.833333 0.000000 -0.1395661082
1.000000 -0.833333 0.000000 -0.1655278639
-1.000000 -0.666667 0.000000 0.1364289202
-0.857143 -0.666667 0.000000 0.1232316739
-0.714286 -0.666667 0.000000 0.1171967460
-0.571429 -0.666667 0.000000 0.1219708304
-0.428571 -0.666667 0.000000 0.1382104773
-0.285714 -0.666667 0.000000 0.1600252112
-0.142857 -0.666667 0.000000 0.1748120563
0.000000 -0.666667 0.000000 0.1690133154
0.142857 -0.666667 0.000000 0.1367168182
0.285714 -0.666667 0.000000 0.0838347350
0.428571 -0.666667 0.000000 0.0239247631
0.571429 -0.666667 0.000000 -0.0304101220
0.714286 -0.666667 0.000000 -0.0732794445
0.857143 -0.666667 0.000000 -0.1053397547
1.000000 -0.666667 0.000000 -0.1302377465
-1.000000 -0.500000 0.000000 0.1067379470
-0.857143 -0.500000 0.000000 0.1051863292
-0.714286 -0.500000 0.000000 0.1192244280
-0.571429 -0.500000 0.000000 0.1567897465
-0.428571 -0.500000 0.000000 0.2193113515
-0.285714 -0.500000 0.000000 0.2939678576
-0.142857 -0.500000 0.000000 0.3533272506
0.000000 -0.500000 0.000000 0.3678794412
0.142857 -0.500000 0.000000 0.3247558220
0.285714 -0.500000 0.000000 0.2368250005
0.428571 -0.500000 0.000000 0.1335970658
0.571429 -0.500000 0.000000 0.0425040322
0.714286 -0.500000 0.000000 -0.0236327149
0.857143 -0.500000 0.000000 -0.0662422422
1.000000 -0.500000 0.000000 -0.0932620530
-1.000000 -0.333333 0.000000 0.0784102951
-0.857143 -0.333333 0.000000 0.0910808569
-0.714286 -0.333333 0.000000 0.1309228761
-0.571429 -0.333333 0.000000 0.2117706982
-0.428571 -0.333333 0.000000 0.3361150566
-0.285714 -0.333333 0.000000 0.4816094434
-0.142857 -0.333333 0.000000 0.6004423541
0.000000 -0.333333 0.000000 0.6411803884
0.142857 -0.333333 0.000000 0.5813947351
0.285714 -0.333333 0.000000 0.4435142053
0.428571 -0.333333 0.000000 0.2789721995
0.571429 -0.333333 0.000000 0.1355802220
0.714286 -0.333333 0.000000 0.0356847808
0.857143 -0.333333 0.000000 -0.0232048574
1.000000 -0.333333 0.000000 -0.0549230382
-1.000000 -0.166667 0.000000 0.0497228871
-0.857143 -0.166667 0.000000 0.0759357228
-0.714286 -0.166667 0.000000 0.1400693819
-0.571429 -0.166667 0.000000 0.2614312490
-0.428571 -0.166667 0.000000 0.4434974228
-0.285714 -0.166667 0.000000 0.6550808390
-0.142857 -0.166667 0.000000 0.8294551678
0.000000 -0.166667 0.000000 0.8948393168
0.142857 -0.166667 0.000000 0.8199313583
0.285714 -0.166667 0.000000 0.6360332199
0.428571 -0.166667 0.000000 0.4149259943
0.571429 -0.166667 0.000000 0.2233360109
0.714286 -0.166667 0.000000 0.0924503342
0.857143 -0.166667 0.000000 0.0187928656
1.000000 -0.166667 0.000000 -0.0169437795
-1.000000 0.000000 0.000000 0.0183156389
-0.857143 0.000000 0.000000 0.0529305019
-0.714286 0.000000 0.000000 0.1299226083
-0.571429 0.000000 0.000000 0.2708683285
-0.428571 0.000000 0.000000 0.4796522688
-0.285714 0.000000 0.000000 0.7214222904
-0.142857 0.000000 0.000000 0.9216104473
0.000000 0.000000 0.000000 1.0000000000
0.142857 0.000000 0.000000 0.9216104473
0.285714 0.000000 0.000000 0.7214222904
0.428571 0.000000 0.000000 0.4796522688
0.571429 0.000000 0.000000 0.2708683285
0.714286 0.000000 0.000000 0.1299226083
0.857143 0.000000 0.000000 0.0529305019
1.000000 0.000000 0.000000 0.0183156389
-1.000000 0.166667 0.000000 -0.0169437795
-0.857143 0.166667 0.000000 0.0187928656
-0.714286 0.166667 0.000000 0.0924503342
-0.571429 0.166667 0.000000 0.2233360109
-0.428571 0.166667 0.000000 0.4149259943
-0.285714 0.166667 0.000000 0.6360332199
-0.142857 0.166667 0.000000 0.8199313583
0.000000 0.166667 0.000000 0.8948393168
0.142857 0.166667 0.000000 0.8294551678
0.285714 0.166667 0.000000 0.6550808390
0.428571 0.166667 0.000000 0.4434974228
0.571429 0.166667 0.000000 0.2614312490
0.714286 0.166667 0.000000 0.1400693819
0.857143 0.166667 0.000000 0.0759357228
1.000000 0.166667 0.000000 0.0497228871
-1.000000 0.333333 0.000000 -0.0549230382
-0.857143 0.333333 0.000000 -0.0232048574
-0.714286 0.333333 0.000000 0.0356847808
-0.571429 0.333333 0.000000 0.1355802220
-0.428571 0.333333 0.000000 0.2789721995
-0.285714 0.333333 0.000000 0.4435142053
-0.142857 0.333333 0.000000 0.5813947351
0.000000 0.333333 0.000000 0.6411803884
0.142857 0.333333 0.000000 0.6004423541
0.285714 0.333333 0.000000 0.4816094434
0.428571 0.333333 0.000000 0.3361150566
0.571429 0.333333 0.000000 0.2117706982
0.714286 0.333333 0.000000 0.1309228761
0.857143 0.333333 0.000000 0.0910808569
1.000000 0.333333 0.000000 0.0784102951
-1.000000 0.500000 0.000000 -0.0932620530
-0.857143 0.500000 0.000000 -0.0662422422
-0.714286 0.500000 0.000000 -0.0236327149
-0.571429 0.500000 0.000000 0.0425040322
-0.428571 0.500000 0.000000 0.1335970658
-0.285714 0.500000 0.000000 0.2368250005
-0.142857 0.500000 0.000000 0.3247558220
0.000000 0.500000 0.000000 0.3678794412
0.142857 0.500000 0.000000 0.3533272506
0.285714 0.500000 0.000000 0.2939678576
0.428571 0.500000 0.000000 0.2193113515
0.571429 0.500000 0.000000 0.1567897465
0.714286 0.500000 0.000000 0.1192244280
0.857143 0.500000 0.000000 0.1051863292
1.000000 0.500000 0.000000 0.1067379470
-1.000000 0.666667 0.000000 -0.1302377465
-0.857143 0.666667 0.000000 -0.1053397547
-0.714286 0.666667 0.000000 -0.0732794445
-0.571429 0.666667 0.000000 -0.0304101220
-0.428571 0.666667 0.000000 0.0239247631
-0.285714 0.666667 0.000000 0.0838347350
-0.142857 0.666667 0.000000 0.1367168182
0.000000 0.666667 0.000000 0.1690133154
0.142857 0.666667 0.000000 0.1748120563
0.285714 0.666667 0.000000 0.1600252112
0.428571 0.666667 0.000000 0.1382104773
0.571429 0.666667 0.000000 0.1219708304
0.714286 0.666667 0.000000 0.1171967460
0.857143 0.666667 0.000000 0.1232316739
1.000000 0.666667 0.000000 0.1364289202
-1.000000 0.833333 0.000000 -0.1655278639
-0.857143 0.833333 0.000000 -0.1395661082
-0.714286 0.833333 0.000000 -0.1109694829
-0.571429 0.833333 0.000000 -0.0783964441
-0.428571 0.833333 0.000000 -0.0416054606
-0.285714 0.833333 0.000000 -0.0027635173
-0.142857 0.833333 0.000000 0.0334930103
0.000000 0.833333 0.000000 0.0621765240
0.142857 0.833333 0.000000 0.0811120579
0.285714 0.833333 0.000000 0.0924745780
0.428571 0.833333 0.000000 0.1012516822
0.571429 0.833333 0.000000 0.1120797464
0.714286 0.833333 0.000000 0.1271257552
0.857143 0.833333 0.000000 0.1461481775
1.000000 0.833333 0.000000 0.1678054694
-1.000000 1.000000 0.000000 -0.1996645374
-0.857143 1.000000 0.000000 -0.1704591155
-0.714286 1.000000 0.000000 -0.1404775273
-0.571429 1.000000 0.000000 -0.1093245878
-0.428571 1.000000 0.000000 -0.0769291480
-0.285714 1.000000 0.000000 -0.0439295470
-0.142857 1.000000 0.000000 -0.0116915444
0.000000 1.000000 0.000000 0.0183156389
0.142857 1.000000 0.000000 0.0454513127
0.285714 1.000000 0.000000 0.0703561673
0.428571 1.000000 0.000000 0.0944994235
0.571429 1.000000 0.000000 0.1192468408
0.714286 1.000000 0.000000 0.1452367584
0.857143 1.000000 0.000000 0.1723980274
1.000000 1.000000 0.000000 0.2003354626
-1.000000 -1.000000 0.200000 0.2002858624
-0.857143 -1.000000 0.200000 0.1722546873
-0.714286 -1.000000 0.200000 0.1448849175
-0.571429 -1.000000 0.200000 0.1185133074
-0.428571 -1.000000 0.200000 0.0932004863
-0.285714 -1.000000 0.200000 0.0684024973
-0.142857 -1.000000 0.200000 0.0429555170
0.000000 -1.000000 0.200000 0.0156075579
0.142857 -1.000000 0.200000 -0.0141873401
0.285714 -1.000000 0.200000 -0.0458832170
0.428571 -1.000000 0.200000 -0.0782280851
0.571429 -1.000000 0.200000 -0.1100581212
0.714286 -1.000000 0.200000 -0.1408293682
0.857143 -1.000000 0.200000 -0.1706024556
1.000000 -1.000000 0.200000 -0.1997141376
-1.000000 -0.833333 0.200000 0.1676370904
-0.857143 -0.833333 0.200000 0.1456615776
-0.714286 -0.833333 0.200000 0.1259313526
-0.571429 -0.833333 0.200000 0.1095896036
-0.428571 -0.833333 0.200000 0.0968421501
-0.285714 -0.833333 0.200000 0.0858424092
-0.142857 -0.833333 0.200000 0.0726395223
0.000000 -0.833333 0.200000 0.0529833388
0.142857 -0.833333 0.200000 0.0250204747
0.285714 -0.833333 0.200000 -0.0093956860
0.428571 -0.833333 0.200000 -0.0460149928
0.571429 -0.833333 0.200000 -0.0808865868
0.714286 -0.833333 0.200000 -0.1121638855
0.857143 -0.833333 0.200000 -0.1400527081
1.000000 -0.833333 0.200000 -0.1656962430
-1.000000 -0.666667 0.200000 0.1359712184
-0.857143 -0.666667 0.200000 0.1219089582
-0.714286 -0.666667 0.200000 0.1139500231
-0.571429 -0.666667 0.200000 0.1152019207
-0.428571 -0.666667 0.200000 0.1262241262
-0.285714 -0.666667 0.200000 0.1419971074
-0.142857 -0.666667 0.200000 0.1517813168
0.000000 -0.666667 0.200000 0.1440236470
0.142857 -0.666667 0.200000 0.1136860787
0.285714 -0.666667 0.200000 0.0658066312
0.428571 -0.666667 0.200000 0.0119384119
0.571429 -0.666667 0.200000 -0.0371790317
0.714286 -0.666667 0.200000 -0.0765261674
0.857143 -0.666667 0.200000 -0.1066624704
1.000000 -0.666667 0.200000 -0.1306954482
-1.000000 -0.500000 0.200000 0.1057416997
-0.857143 -0.500000 0.200000 0.1023072666
-0.714286 -0.500000 0.200000 0.1121575137
-0.571429 -0.500000 0.200000 0.1420563350
-0.428571 -0.500000 0.200000 0.1932215008
-0.285714 -0.500000 0.200000 0.2547273472
-0.142857 -0.500000 0.200000 0.3031978537
0.000000 -0.500000 0.200000 0.3134861809
0.142857 -0.500000 0.200000 0.2746264251
0.285714 -0.500000 0.200000 0.1975844900
0.428571 -0.500000 0.200000 0.1075072151
0.571429 -0.500000 0.200000 0.0277706207
0.714286 -0.500000 0.200000 -0.0306996291
0.857143 -0.500000 0.200000 -0.0691213048
1.000000 -0.500000 0.200000 -0.0942583003
-1.000000 -0.333333 0.200000 0.0766739267
-0.857143 -0.333333 0.200000 0.0860629129
-0.714286 -0.333333 0.200000 0.1186058876
-0.571429 -0.333333 0.200000 0.1860917027
-0.428571 -0.333333 0.200000 0.2906428210
-0.285714 -0.333333 0.200000 0.4132168047
-0.142857 -0.333333 0.200000 0.5130713771
0.000000 -0.333333 0.200000 0.5463778856
0.142857 -0.333333 0.200000 0.4940237580
0.285714 -0.333333 0.200000 0.3751215666
0.428571 -0.333333 0.200000 0.2334999639
0.571429 -0.333333 0.200000 0.1099012265
0.714286 -0.333333 0.200000 0.0233677924
0.857143 -0.333333 0.200000 -0.0282228014
1.000000 -0.333333 0.200000 -0.0566594066
-1.000000 -0.166667 0.200000 0.0472995898
-0.857143 -0.166667 0.200000 0.0689326177
-0.714286 -0.166667 0.200000 0.1228796398
-0.571429 -0.166667 0.200000 0.2255933239
-0.428571 -0.166667 0.200000 0.3800358059
-0.285714 -0.166667 0.200000 0.5596312226
-0.142857 -0.166667 0.200000 0.7075191467
0.000000 -0.166667 0.200000 0.7625317659
0.142857 -0.166667 0.200000 0.6979953371
0.285714 -0.166667 0.200000 0.5405836035
0.428571 -0.166667 0.200000 0.3514643773
0.571429 -0.166667 0.200000 0.1874980858
0.714286 -0.166667 0.200000 0.0752605921
0.857143 -0.166667 0.200000 0.0117897605
1.000000 -0.166667 0.200000 -0.0193670769
-1.000000 0.000000 0.200000 0.0156075579
-0.857143 0.000000 0.200000 0.0451043985
-0.714286 0.000000 0.200000 0.1107127437
-0.571429 0.000000 0.200000 0.2308187637
-0.428571 0.000000 0.200000 0.4087327017
-0.285714 0.000000 0.200000 0.6147555239
-0.142857 0.000000 0.200000 0.7853446185
0.000000 0.000000 0.200000 0.8521437890
0.142857 0.000000 0.200000 0.7853446185
0.285714 0.000000 0.200000 0.6147555239
0.428571 0.000000 0.200000 0.4087327017
0.571429 0.000000 0.200000 0.2308187637
0.714286 0.000000 0.200000 0.1107127437
0.857143 0.000000 0.200000 0.0451043985
1.000000 0.000000 0.200000 0.0156075579
-1.000000 0.166667 0.200000 -0.0193670769
-0.857143 0.166667 0.200000 0.0117897605
-0.714286 0.166667 0.200000 0.0752605921
-0.571429 0.166667 0.200000 0.1874980858
-0.428571 0.166667 0.200000 0.3514643773
-0.285714 0.166667 0.200000 0.5405836035
-0.142857 0.166667 0.200000 0.6979953371
0.000000 0.166667 0.200000 0.7625317659
0.142857 0.166667 0.200000 0.7075191467
0.285714 0.166667 0.200000 0.5596312226
0.428571 0.166667 0.200000 0.3800358059
0.571429 0.166667 0.200000 0.2255933239
0.714286 0.166667 0.200000 0.1228796398
0.857143 0.166667 0.200000 0.0689326177
1.000000 0.166667 0.200000 0.0472995898
-1.000000 0.333333 0.200000 -0.0566594066
-0.857143 0.333333 0.200000 -0.0282228014
-0.714286 0.333333 0.200000 0.0233677924
-0.571429 0.333333 0.200000 0.1099012265
-0.428571 0.333333 0.200000 0.2334999639
-0.285714 0.333333 0.200000 0.3751215666
-0.142857 0.333333 0.200000 0.4940237580
0.000000 0.333333 0.200000 0.5463778856
0.142857 0.333333 0.200000 0.5130713771
0.285714 0.333333 0.200000 0.4132168047
0.428571 0.333333 0.200000 0.2906428210
0.571429 0.333333 0.200000 0.1860917027
0.714286 0.333333 0.200000 0.1186058876
0.857143 0.333333 0.200000 0.0860629129
1.000000 0.333333 0.200000 0.0766739267
-1.000000 0.500000 0.200000 -0.0942583003
-0.857143 0.500000 0.200000 -0.0691213048
-0.714286 0.500000 0.200000 -0.0306996291
-0.571429 0.500000 0.200000 0.0277706207
-0.428571 0.500000 0.200000 0.1075072151
-0.285714 0.500000 0.200000 0.1975844900
-0.142857 0.500000 0.200000 0.2746264251
0.000000 0.500000 0.200000 0.3134861809
0.142857 0.500000 0.200000 0.3031978537
0.285714 0.500000 0.200000 0.2547273472
0.428571 0.500000 0.200000 0.1932215008
0.571429 0.500000 0.200000 0.1420563350
0.714286 0.500000 0.200000 0.1121575137
0.857143 0.500000 0.200000 0.1023072666
1.000000 0.500000 0.200000 0.1057416997
-1.000000 0.666667 0.200000 -0.1306954482
-0.857143 0.666667 0.200000 -0.1066624704
-0.714286 0.666667 0.200000 -0.0765261674
-0.571429 0.666667 0.200000 -0.0371790317
-0.428571 0.666667 0.200000 0.0119384119
-0.285714 0.666667 0.200000 0.0658066312
-0.142857 0.666667 0.200000 0.1136860787
0.000000 0.666667 0.200000 0.1440236470
0.142857 0.666667 0.200000 0.1517813168
0.285714 0.666667 0.200000 0.1419971074
0.428571 0.666667 0.200000 0.1262241262
0.571429 0.666667 0.200000 0.1152019207
0.714286 0.666667 0.200000 0.1139500231
0.857143 0.666667 0.200000 0.1219089582
1.000000 0.666667 0.200000 0.1359712184
-1.000000 0.833333 0.200000 -0.1656962430
-0.857143 0.833333 0.200000 -0.1400527081
-0.714286 0.833333 0.200000 -0.1121638855
-0.571429 0.833333 0.200000 -0.0808865868
-0.428571 0.833333 0.200000 -0.0460149928
-0.285714 0.833333 0.200000 -0.0093956860
-0.142857 0.833333 0.200000 0.0250204747
0.000000 0.833333 0.200000 0.0529833388
0.142857 0.833333 0.200000 0.0726395223
0.285714 0.833333 0.200000 0.0858424092
0.428571 0.833333 0.200000 0.0968421501
0.571429 0.833333 0.200000 0.1095896036
0.714286 0.833333 0.200000 0.1259313526
0.857143 0.833333 0.200000 0.1456615776
1.000000 0.833333 0.200000 0.1676370904
-1.000000 1.000000 0.200000 -0.1997141376
-0.857143 1.000000 0.200000 -0.1706024556
-0.714286 1.000000 0.200000 -0.1408293682
-0.571429 1.000000 0.200000 -0.1100581212
-0.428571 1.000000 0.200000 -0.0782280851
-0.285714 1.000000 0.200000 -0.0458832170
-0.142857 1.000000 0.200000 -0.0141873401
0.000000 1.000000 0.200000 0.0156075579
0.142857 1.000000 0.200000 0.0429555170
0.285714 1.000000 0.200000 0.0684024973
0.428571 1.000000 0.200000 0.0932004863
0.571429 1.000000 0.200000 0.1185133074
0.714286 1.000000 0.200000 0.1448849175
0.857143 1.000000 0.200000 0.1722546873
1.000000 1.000000 0.200000 0.2002858624
-1.000000 -1.000000 0.400000 0.2001768869
-0.857143 -1.000000 0.400000 0.1719397582
-0.714286 -1.000000 0.400000 0.1441118961
-0.571429 -1.000000 0.400000 0.1169016787
-0.428571 -1.000000 0.400000 0.0903466223
-0.285714 -1.000000 0.400000 0.0641101355
-0.142857 -1.000000 0.400000 0.0374720636
0.000000 -1.000000 0.400000 0.0096576976
0.142857 -1.000000 0.400000 -0.0196707935
0.285714 -1.000000 0.400000 -0.0501755788
0.428571 -1.000000 0.400000 -0.0810819491
0.571429 -1.000000 0.400000 -0.1116697499
0.714286 -1.000000 0.400000 -0.1416023896
0.857143 -1.000000 0.400000 -0.1709173846
1.000000 -1.000000 0.400000 -0.1998231131
-1.000000 -0.833333 0.400000 0.1672671487
-0.857143 -0.833333 0.400000 0.1445924805
-0.714286 -0.833333 0.400000 0.1233071591
-0.571429 -0.833333 0.400000 0.1041185703
-0.428571 -0.833333 0.400000 0.0871540718
-0.285714 -0.833333 0.400000 0.0712710290
-0.142857 -0.833333 0.400000 0.0540247159
0.000000 -0.833333 0.400000 0.0327852101
0.142857 -0.833333 0.400000 0.0064056683
0.285714 -0.833333 0.400000 -0.0239670663
0.428571 -0.833333 0.400000 -0.0557030710
0.571429 -0.833333 0.400000 -0.0863576202
0.714286 -0.833333 0.400000 -0.1147880790
0.857143 -0.833333 0.400000 -0.1411218052
1.000000 -0.833333 0.400000 -0.1660661846
-1.000000 -0.666667 0.400000 0.1349656128
-0.857143 -0.666667 0.400000 0.1190028510
-0.714286 -0.666667 0.400000 0.1068167254
-0.571429 -0.666667 0.400000 0.1003301101
-0.428571 -0.666667 0.400000 0.0998891991
-0.285714 -0.666667 0.400000 0.1023879892
-0.142857 -0.666667 0.400000 0.1011810267
0.000000 -0.666667 0.400000 0.0891194408
0.142857 -0.666667 0.400000 0.0630857886
0.285714 -0.666667 0.400000 0.0261975130
0.428571 -0.666667 0.400000 -0.0143965152
0.571429 -0.666667 0.400000 -0.0520508422
0.714286 -0.666667 0.400000 -0.0836594650
0.857143 -0.666667 0.400000 -0.1095685776
1.000000 -0.666667 0.400000 -0.1317010538
-1.000000 -0.500000 0.400000 0.1035528684
-0.857143 -0.500000 0.400000 0.0959817467
-0.714286 -0.500000 0.400000 0.0966309645
-0.571429 -0.500000 0.400000 0.1096859070
-0.428571 -0.500000 0.400000 0.1359001102
-0.285714 -0.500000 0.400000 0.1685129550
-0.142857 -0.500000 0.400000 0.1930597478
0.000000 -0.500000 0.400000 0.1939800423
0.142857 -0.500000 0.400000 0.1644883193
0.285714 -0.500000 0.400000 0.1113700978
0.428571 -0.500000 0.400000 0.0501858245
0.571429 -0.500000 0.400000 -0.0045998073
0.714286 -0.500000 0.400000 -0.0462261784
0.857143 -0.500000 0.400000 -0.0754468247
1.000000 -0.500000 0.400000 -0.0964471316
-1.000000 -0.333333 0.400000 0.0728589930
-0.857143 -0.333333 0.400000 0.0750381073
-0.714286 -0.333333 0.400000 0.0915445253
-0.571429 -0.333333 0.400000 0.1296729924
-0.428571 -0.333333 0.400000 0.1907368537
-0.285714 -0.333333 0.400000 0.2629529647
-0.142857 -0.333333 0.400000 0.3211106813
0.000000 -0.333333 0.400000 0.3380895613
0.142857 -0.333333 0.400000 0.3020630623
0.285714 -0.333333 0.400000 0.2248577266
0.428571 -0.333333 0.400000 0.1335939966
0.571429 -0.333333 0.400000 0.0534825162
0.714286 -0.333333 0.400000 -0.0036935700
0.857143 -0.333333 0.400000 -0.0392476070
1.000000 -0.333333 0.400000 -0.0604743404
-1.000000 -0.166667 0.400000 0.0419754209
-0.857143 -0.166667 0.400000 0.0535462621
-0.714286 -0.166667 0.400000 0.0851124662
-0.571429 -0.166667 0.400000 0.1468546709
-0.428571 -0.166667 0.400000 0.2406057965
-0.285714 -0.166667 0.400000 0.3499211404
-0.142857 -0.166667 0.400000 0.4396164145
0.000000 -0.166667 0.400000 0.4718419925
0.142857 -0.166667 0.400000 0.4300926050
0.285714 -0.166667 0.400000 0.3308735214
0.428571 -0.166667 0.400000 0.2120343679
0.571429 -0.166667 0.400000 0.1087594328
0.714286 -0.166667 0.400000 0.0374934186
0.857143 -0.166667 0.400000 -0.0035965951
1.000000 -0.166667 0.400000 -0.0246912458
-1.000000 0.000000 0.400000 0.0096576976
-0.857143 0.000000 0.400000 0.0279098527
-0.714286 0.000000 0.400000 0.0685072071
-0.571429 0.000000 0.400000 0.1428268175
-0.428571 0.000000 0.400000 0.2529170075
-0.285714 0.000000 0.400000 0.3804005082
-0.142857 0.000000 0.400000 0.4859582068
0.000000 0.000000 0.400000 0.5272924240
0.142857 0.000000 0.400000 0.4859582068
0.285714 0.000000 0.400000 0.3804005082
0.428571 0.000000 0.400000 0.2529170075
0.571429 0.000000 0.400000 0.1428268175
0.714286 0.000000 0.400000 0.0685072071
0.857143 0.000000 0.400000 0.0279098527
1.000000 0.000000 0.400000 0.0096576976
-1.000000 0.166667 0.400000 -0.0246912458
-0.857143 0.166667 0.400000 -0.0035965951
-0.714286 0.166667 0.400000 0.0374934186
-0.571429 0.166667 0.400000 0.1087594328
-0.428571 0.166667 0.400000 0.2120343679
-0.285714 0.166667 0.400000 0.3308735214
-0.142857 0.166667 0.400000 0.4300926050
0.000000 0.166667 0.400000 0.4718419925
0.142857 0.166667 0.400000 0.4396164145
0.285714 0.166667 0.400000 0.3499211404
0.428571 0.166667 0.400000 0.2406057965
0.571429 0.166667 0.400000 0.1468546709
0.714286 0.166667 0.400000 0.0851124662
0.857143 0.166667 0.400000 0.0535462621
1.000000 0.166667 0.400000 0.0419754209
-1.000000 0.333333 0.400000 -0.0604743404
-0.857143 0.333333 0.400000 -0.0392476070
-0.714286 0.333333 0.400000 -0.0036935700
-0.571429 0.333333 0.400000 0.0534825162
-0.428571 0.333333 0.400000 0.1335939966
-0.285714 0.333333 0.400000 0.2248577266
-0.142857 0.333333 0.400000 0.3020630623
0.000000 0.333333 0.400000 0.3380895613
0.142857 0.333333 0.400000 0.3211106813
0.285714 0.333333 0.400000 0.2629529647
0.428571 0.333333 0.400000 0.1907368537
0.571429 0.333333 0.400000 0.1296729924
0.714286 0.333333 0.400000 0.0915445253
0.857143 0.333333 0.400000 0.0750381073
1.000000 0.333333 0.400000 0.0728589930
-1.000000 0.500000 0.400000 -0.0964471316
-0.857143 0.500000 0.400000 -0.0754468247
-0.714286 0.500000 0.400000 -0.0462261784
-0.571429 0.500000 0.400000 -0.0045998073
-0.428571 0.500000 0.400000 0.0501858245
-0.285714 0.500000 0.400000 0.1113700978
-0.142857 0.500000 0.400000 0.1644883193
0.000000 0.500000 0.400000 0.1939800423
0.142857 0.500000 0.400000 0.1930597478
0.285714 0.500000 0.400000 0.1685129550
0.428571 0.500000 0.400000 0.1359001102
0.571429 0.500000 0.400000 0.1096859070
0.714286 0.500000 0.400000 0.0966309645
0.857143 0.500000 0.400000 0.0959817467
1.000000 0.500000 0.400000 0.1035528684
-1.000000 0.666667 0.400000 -0.1317010538
-0.857143 0.666667 0.400000 -0.1095685776
-0.714286 0.666667 0.400000 -0.0836594650
-0.571429 0.666667 0.400000 -0.0520508422
-0.428571 0.666667 0.400000 -0.0143965152
-0.285714 0.666667 0.400000 0.0261975130
-0.142857 0.666667 0.400000 0.0630857886
0.000000 0.666667 0.400000 0.0891194408
0.142857 0.666667 0.400000 0.1011810267
0.285714 0.666667 0.400000 0.1023879892
0.428571 0.666667 0.400000 0.0998891991
0.571429 0.666667 0.400000 0.1003301101
0.714286 0.666667 0.400000 0.1068167254
0.857143 0.666667 0.400000 0.1190028510
1.000000 0.666667 0.400000 0.1349656128
-1.000000 0.833333 0.400000 -0.1660661846
-0.857143 0.833333 0.400000 -0.1411218052
-0.714286 0.833333 0.400000 -0.1147880790
-0.571429 0.833333 0.400000 -0.0863576202
-0.428571 0.833333 0.400000 -0.0557030710
-0.285714 0.833333 0.400000 -0.0239670663
-0.142857 0.833333 0.400000 0.0064056683
0.000000 0.833333 0.400000 0.0327852101
0.142857 0.833333 0.400000 0.0540247159
0.285714 0.833333 0.400000 0.0712710290
0.428571 0.833333 0.400000 0.0871540718
0.571429 0.833333 0.400000 0.1041185703
0.714286 0.833333 0.400000 0.1233071591
0.857143 0.833333 0.400000 0.1445924805
1.000000 0.833333 0.400000 0.1672671487
-1.000000 1.000000 0.400000 -0.1998231131
-0.857143 1.000000 0.400000 -0.1709173846
-0.714286 1.000000 0.400000 -0.1416023896
-0.571429 1.000000 0.400000 -0.1116697499
-0.428571 1.000000 0.400000 -0.0810819491
-0.285714 1.000000 0.400000 -0.0501755788
-0.142857 1.000000 0.400000 -0.0196707935
0.000000 1.000000 0.400000 0.0096576976
0.142857 1.000000 0.400000 0.0374720636
0.285714 1.000000 0.400000 0.0641101355
0.428571 1.000000 0.400000 0.0903466223
0.571429 1.000000 0.400000 0.1169016787
0.714286 1.000000 0.400000 0.1441118961
0.857143 1.000000 0.400000 0.1719397582
1.000000 1.000000 0.400000 0.2001768869
-1.000000 -1.000000 0.600000 0.2000794804
-0.857143 -1.000000 0.600000 0.1716582625
-0.714286 -1.000000 0.600000 0.1434209398
-0.571429 -1.000000 0.600000 0.1154611429
-0.428571 -1.000000 0.600000 0.0877957287
-0.285714 -1.000000 0.600000 0.0602734571
-0.142857 -1.000000 0.600000 0.0325707417
0.000000 -1.000000 0.600000 0.0043394833
0.142857 -1.000000 0.600000 -0.0245721155
0.285714 -1.000000 0.600000 -0.0540122572
0.428571 -1.000000 0.600000 -0.0836328427
0.571429 -1.000000 0.600000 -0.1131102857
0.714286 -1.000000 0.600000 -0.1422933459
0.857143 -1.000000 0.600000 -0.1711988804
1.000000 -1.000000 0.600000 -0.1999205196
-1.000000 -0.833333 0.600000 0.1669364807
-0.857143 -0.833333 0.600000 0.1436368803
-0.714286 -0.833333 0.600000 0.1209615537
-0.571429 -0.833333 0.600000 0.0992283499
-0.428571 -0.833333 0.600000 0.0784944942
-0.285714 -0.833333 0.600000 0.0582465679
-0.142857 -0.833333 0.600000 0.0373860848
0.000000 -0.833333 0.600000 0.0147313445
0.142857 -0.833333 0.600000 -0.0102329628
0.285714 -0.833333 0.600000 -0.0369915273
0.428571 -0.833333 0.600000 -0.0643626486
0.571429 -0.833333 0.600000 -0.0912478406
0.714286 -0.833333 0.600000 -0.1171336843
0.857143 -0.833333 0.600000 -0.1420774054
1.000000 -0.833333 0.600000 -0.1663968527
-1.000000 -0.666667 0.600000 0.1340667638
-0.857143 -0.666667 0.600000 0.1164052604
-0.714286 -0.666667 0.600000 0.1004407092
-0.571429 -0.666667 0.600000 0.0870371129
-0.428571 -0.666667 0.600000 0.0763500267
-0.285714 -0.666667 0.600000 0.0669838333
-0.142857 -0.666667 0.600000 0.0559525380
0.000000 -0.666667 0.600000 0.0400439460
0.142857 -0.666667 0.600000 0.0178572999
0.285714 -0.666667 0.600000 -0.0092066429
0.428571 -0.666667 0.600000 -0.0379356876
0.571429 -0.666667 0.600000 -0.0653438395
0.714286 -0.666667 0.600000 -0.0900354813
0.857143 -0.666667 0.600000 -0.1121661681
1.000000 -0.666667 0.600000 -0.1325999029
-1.000000 -0.500000 0.600000 0.1015964067
-0.857143 -0.500000 0.600000 0.0903277533
-0.714286 -0.500000 0.600000 0.0827527366
-0.571429 -0.500000 0.600000 0.0807519713
-0.428571 -0.500000 0.600000 0.0846640430
-0.285714 -0.500000 0.600000 0.0914512097
-0.142857 -0.500000 0.600000 0.0946140656
0.000000 -0.500000 0.600000 0.0871608515
0.142857 -0.500000 0.600000 0.0660426370
0.285714 -0.500000 0.600000 0.0343083525
0.428571 -0.500000 0.600000 -0.0010502427
0.571429 -0.500000 0.600000 -0.0335337430
0.714286 -0.500000 0.600000 -0.0601044063
0.857143 -0.500000 0.600000 -0.0811008181
1.000000 -0.500000 0.600000 -0.0984035933
-1.000000 -0.333333 0.600000 0.0694490582
-0.857143 -0.333333 0.600000 0.0651837114
-0.714286 -0.333333 0.600000 0.0673560370
-0.571429 -0.333333 0.600000 0.0792437756
-0.428571 -0.333333 0.600000 0.1014370511
-0.285714 -0.333333 0.600000 0.1286413553
-0.142857 -0.333333 0.600000 0.1495288159
0.000000 -0.333333 0.600000 0.1519134323
0.142857 -0.333333 0.600000 0.1304811968
0.285714 -0.333333 0.600000 0.0905461172
0.428571 -0.333333 0.600000 0.0442941939
0.571429 -0.333333 0.600000 0.0030532994
0.714286 -0.333333 0.600000 -0.0278820583
0.857143 -0.333333 0.600000 -0.0491020029
1.000000 -0.333333 0.600000 -0.0638842751
-1.000000 -0.166667 0.600000 0.0372164736
-0.857143 -0.166667 0.600000 0.0397933446
-0.714286 -0.166667 0.600000 0.0513547114
-0.571429 -0.166667 0.600000 0.0764750292
-0.428571 -0.166667 0.600000 0.1159778824
-0.285714 -0.166667 0.600000 0.1624741896
-0.142857 -0.166667 0.600000 0.2001546312
0.000000 -0.166667 0.600000 0.2120122737
0.142857 -0.166667 0.600000 0.1906308216
0.285714 -0.166667 0.600000 0.1434265706
0.428571 -0.166667 0.600000 0.0874064538
0.571429 -0.166667 0.600000 0.0383797911
0.714286 -0.166667 0.600000 0.0037356638
0.857143 -0.166667 0.600000 -0.0173495125
1.000000 -0.166667 0.600000 -0.0294501931
-1.000000 0.000000 0.600000 0.0043394833
-0.857143 0.000000 0.600000 0.0125407052
-0.714286 0.000000 0.600000 0.0307822724
-0.571429 0.000000 0.600000 0.0641762260
-0.428571 0.000000 0.600000 0.1136429370
-0.285714 0.000000 0.600000 0.1709249663
-0.142857 0.000000 0.600000 0.2183550977
0.000000 0.000000 0.600000 0.2369277587
0.142857 0.000000 0.600000 0.2183550977
0.285714 0.000000 0.600000 0.1709249663
0.428571 0.000000 0.600000 0.1136429370
0.571429 0.000000 0.600000 0.0641762260
0.714286 0.000000 0.600000 0.0307822724
0.857143 0.000000 0.600000 0.0125407052
1.000000 0.000000 0.600000 0.0043394833
-1.000000 0.166667 0.600000 -0.0294501931
-0.857143 0.166667 0.600000 -0.0173495125
-0.714286 0.166667 0.600000 0.0037356638
-0.571429 0.166667 0.600000 0.0383797911
-0.428571 0.166667 0.600000 0.0874064538
-0.285714 0.166667 0.600000 0.1434265706
-0.142857 0.166667 0.600000 0.1906308216
0.000000 0.166667 0.600000 0.2120122737
0.142857 0.166667 0.600000 0.2001546312
0.285714 0.166667 0.600000 0.1624741896
0.428571 0.166667 0.600000 0.1159778824
0.571429 0.166667 0.600000 0.0764750292
0.714286 0.166667 0.600000 0.0513547114
0.857143 0.166667 0.600000 0.0397933446
1.000000 0.166667 0.600000 0.0372164736
-1.000000 0.333333 0.600000 -0.0638842751
-0.857143 0.333333 0.600000 -0.0491020029
-0.714286 0.333333 0.600000 -0.0278820583
-0.571429 0.333333 0.600000 0.0030532994
-0.428571 0.333333 0.600000 0.0442941939
-0.285714 0.333333 0.600000 0.0905461172
-0.142857 0.333333 0.600000 0.1304811968
0.000000 0.333333 0.600000 0.1519134323
0.142857 0.333333 0.600000 0.1495288159
0.285714 0.333333 0.600000 0.1286413553
0.428571 0.333333 0.600000 0.1014370511
0.571429 0.333333 0.600000 0.0792437756
0.714286 0.333333 0.600000 0.0673560370
0.857143 0.333333 0.600000 0.0651837114
1.000000 0.333333 0.600000 0.0694490582
-1.000000 0.500000 0.600000 -0.0984035933
-0.857143 0.500000 0.600000 -0.0811008181
-0.714286 0.500000 0.600000 -0.0601044063
-0.571429 0.500000 0.600000 -0.0335337430
-0.428571 0.500000 0.600000 -0.0010502427
-0.285714 0.500000 0.600000 0.0343083525
-0.142857 0.500000 0.600000 0.0660426370
0.000000 0.500000 0.600000 0.0871608515
0.142857 0.500000 0.600000 0.0946140656
0.285714 0.500000 0.600000 0.0914512097
0.428571 0.500000 0.600000 0.0846640430
0.571429 0.500000 0.600000 0.0807519713
0.714286 0.500000 0.600000 0.0827527366
0.857143 0.500000 0.600000 0.0903277533
1.000000 0.500000 0.600000 0.1015964067
-1.000000 0.666667 0.600000 -0.1325999029
-0.857143 0.666667 0.600000 -0.1121661681
-0.714286 0.666667 0.600000 -0.0900354813
-0.571429 0.666667 0.600000 -0.0653438395
-0.428571 0.666667 0.600000 -0.0379356876
-0.285714 0.666667 0.600000 -0.0092066429
-0.142857 0.666667 0.600000 0.0178572999
0.000000 0.666667 0.600000 0.0400439460
0.142857 0.666667 0.600000 0.0559525380
0.285714 0.666667 0.600000 0.0669838333
0.428571 0.666667 0.600000 0.0763500267
0.571429 0.666667 0.600000 0.0870371129
0.714286 0.666667 0.600000 0.1004407092
0.857143 0.666667 0.600000 0.1164052604
1.000000 0.666667 0.600000 0.1340667638
-1.000000 0.833333 0.600000 -0.1663968527
-0.857143 0.833333 0.600000 -0.1420774054
-0.714286 0.833333 0.600000 -0.1171336843
-0.571429 0.833333 0.600000 -0.0912478406
-0.428571 0.833333 0.600000 -0.0643626486
-0.285714 0.833333 0.600000 -0.0369915273
-0.142857 0.833333 0.600000 -0.0102329628
0.000000 0.833333 0.600000 0.0147313445
0.142857 0.833333 0.600000 0.0373860848
0.285714 0.833333 0.600000 0.0582465679
0.428571 0.833333 0.600000 0.0784944942
0.571429 0.833333 0.600000 0.0992283499
0.714286 0.833333 0.600000 0.1209615537
0.857143 0.833333 0.600000 0.1436368803
1.000000 0.833333 0.600000 0.1669364807
-1.000000 1.000000 0.600000 -0.1999205196
-0.857143 1.000000 0.600000 -0.1711988804
-0.714286 1.000000 0.600000 -0.1422933459
-0.571429 1.000000 0.600000 -0.1131102857
-0.428571 1.000000 0.600000 -0.0836328427
-0.285714 1.000000 0.600000 -0.0540122572
-0.142857 1.000000 0.600000 -0.0245721155
0.000000 1.000000 0.600000 0.0043394833
0.142857 1.000000 0.600000 0.0325707417
0.285714 1.000000 0.600000 0.0602734571
0.428571 1.000000 0.600000 0.0877957287
0.571429 1.000000 0.600000 0.1154611429
0.714286 1.000000 0.600000 0.1434209398
0.857143 1.000000 0.600000 0.1716582625
1.000000 1.000000 0.600000 0.2000794804
-1.000000 -1.000000 0.800000 0.2000259329
-0.857143 -1.000000 0.800000 0.1715035150
-0.714286 -1.000000 0.800000 0.1430410984
-0.571429 -1.000000 0.800000 0.1146692329
-0.428571 -1.000000 0.800000 0.0863934185
-0.285714 -1.000000 0.800000 0.0581643087
-0.142857 -1.000000 0.800000 0.0298763236
0.000000 -1.000000 0.800000 0.0014158857
0.142857 -1.000000 0.800000 -0.0272665335
0.285714 -1.000000 0.800000 -0.0561214056
0.428571 -1.000000 0.800000 -0.0850351529
0.571429 -1.000000 0.800000 -0.1139021957
0.714286 -1.000000 0.800000 -0.1426731873
0.857143 -1.000000 0.800000 -0.1713536279
1.000000 -1.000000 0.800000 -0.1999740671
-1.000000 -0.833333 0.800000 0.1667547015
-0.857143 -0.833333 0.800000 0.1431115554
-0.714286 -0.833333 0.800000 0.1196720973
-0.571429 -0.833333 0.800000 0.0965400347
-0.428571 -0.833333 0.800000 0.0737340393
-0.285714 -0.833333 0.800000 0.0510865928
-0.142857 -0.833333 0.800000 0.0282392813
0.000000 -0.833333 0.800000 0.0048065401
0.142857 -0.833333 0.800000 -0.0193797663
0.285714 -0.833333 0.800000 -0.0441515025
0.428571 -0.833333 0.800000 -0.0691231036
0.571429 -0.833333 0.800000 -0.0939361558
0.714286 -0.833333 0.800000 -0.1184231408
0.857143 -0.833333 0.800000 -0.1426027303
1.000000 -0.833333 0.800000 -0.1665786318
-1.000000 -0.666667 0.800000 0.1335726369
-0.857143 -0.666667 0.800000 0.1149772794
-0.714286 -0.666667 0.800000 0.0969356030
-0.571429 -0.666667 0.800000 0.0797295146
-0.428571 -0.666667 0.800000 0.0634097685
-0.285714 -0.666667 0.800000 0.0475210030
-0.142857 -0.666667 0.800000 0.0310889484
0.000000 -0.666667 0.800000 0.0130655305
0.142857 -0.666667 0.800000 -0.0070062897
0.285714 -0.666667 0.800000 -0.0286694732
0.428571 -0.666667 0.800000 -0.0508759458
0.571429 -0.666667 0.800000 -0.0726514378
0.714286 -0.666667 0.800000 -0.0935405874
0.857143 -0.666667 0.800000 -0.1135941492
1.000000 -0.666667 0.800000 -0.1330940298
-1.000000 -0.500000 0.800000 0.1005208752
-0.857143 -0.500000 0.800000 0.0872195670
-0.714286 -0.500000 0.800000 0.0751234177
-0.571429 -0.500000 0.800000 0.0648460341
-0.428571 -0.500000 0.800000 0.0564978897
-0.285714 -0.500000 0.800000 0.0490878306
-0.142857 -0.500000 0.800000 0.0404952323
0.000000 -0.500000 0.800000 0.0284388247
0.142857 -0.500000 0.800000 0.0119238037
0.285714 -0.500000 0.800000 -0.0080550265
0.428571 -0.500000 0.800000 -0.0292163961
0.571429 -0.500000 0.800000 -0.0494396802
0.714286 -0.500000 0.800000 -0.0677337251
0.857143 -0.500000 0.800000 -0.0842090044
1.000000 -0.500000 0.800000 -0.0994791248
-1.000000 -0.333333 0.800000 0.0675745048
-0.857143 -0.333333 0.800000 0.0597664254
-0.714286 -0.333333 0.800000 0.0540588285
-0.571429 -0.333333 0.800000 0.0515211745
-0.428571 -0.333333 0.800000 0.0523460089
-0.285714 -0.333333 0.800000 0.0548058408
-0.142857 -0.333333 0.800000 0.0552046142
0.000000 -0.333333 0.800000 0.0495662835
0.142857 -0.333333 0.800000 0.0361569952
0.285714 -0.333333 0.800000 0.0167106027
0.428571 -0.333333 0.800000 -0.0047968482
0.571429 -0.333333 0.800000 -0.0246693017
0.714286 -0.333333 0.800000 -0.0411792668
0.857143 -0.333333 0.800000 -0.0545192889
1.000000 -0.333333 0.800000 -0.0657588285
-1.000000 -0.166667 0.800000 0.0346003235
-0.857143 -0.166667 0.800000 0.0322329130
-0.714286 -0.166667 0.800000 0.0327969620
-0.571429 -0.166667 0.800000 0.0377850227
-0.428571 -0.166667 0.800000 0.0474658140
-0.285714 -0.166667 0.800000 0.0594284281
-0.142857 -0.166667 0.800000 0.0685146034
0.000000 -0.166667 0.800000 0.0691753211
0.142857 -0.166667 0.800000 0.0589907939
0.285714 -0.166667 0.800000 0.0403808091
0.428571 -0.166667 0.800000 0.0188943854
0.571429 -0.166667 0.800000 -0.0003102154
0.714286 -0.166667 0.800000 -0.0148220857
0.857143 -0.166667 0.800000 -0.0249099441
1.000000 -0.166667 0.800000 -0.0320663431
-1.000000 0.000000 0.800000 0.0014158857
-0.857143 0.000000 0.800000 0.0040917787
-0.714286 0.000000 0.800000 0.0100436335
-0.571429 0.000000 0.800000 0.0209394058
-0.428571 0.000000 0.800000 0.0370793941
-0.285714 0.000000 0.800000 0.0557693629
-0.142857 0.000000 0.800000 0.0712448564
0.000000 0.000000 0.800000 0.0773047404
0.142857 0.000000 0.800000 0.0712448564
0.285714 0.000000 0.800000 0.0557693629
0.428571 0.000000 0.800000 0.0370793941
0.571429 0.000000 0.800000 0.0209394058
0.714286 0.000000 0.800000 0.0100436335
0.857143 0.000000 0.800000 0.0040917787
1.000000 0.000000 0.800000 0.0014158857
-1.000000 0.166667 0.800000 -0.0320663431
-0.857143 0.166667 0.800000 -0.0249099441
-0.714286 0.166667 0.800000 -0.0148220857
-0.571429 0.166667 0.800000 -0.0003102154
-0.428571 0.166667 0.800000 0.0188943854
-0.285714 0.166667 0.800000 0.0403808091
-0.142857 0.166667 0.800000 0.0589907939
0.000000 0.166667 0.800000 0.0691753211
0.142857 0.166667 0.800000 0.0685146034
0.285714 0.166667 0.800000 0.0594284281
0.428571 0.166667 0.800000 0.0474658140
0.571429 0.166667 0.800000 0.0377850227
0.714286 0.166667 0.800000 0.0327969620
0.857143 0.166667 0.800000 0.0322329130
1.000000 0.166667 0.800000 0.0346003235
-1.000000 0.333333 0.800000 -0.0657588285
-0.857143 0.333333 0.800000 -0.0545192889
-0.714286 0.333333 0.800000 -0.0411792668
-0.571429 0.333333 0.800000 -0.0246693017
-0.428571 0.333333 0.800000 -0.0047968482
-0.285714 0.333333 0.800000 0.0167106027
-0.142857 0.333333 0.800000 0.0361569952
0.000000 0.333333 0.800000 0.0495662835
0.142857 0.333333 0.800000 0.0552046142
0.285714 0.333333 0.800000 0.0548058408
0.428571 0.333333 0.800000 0.0523460089
0.571429 0.333333 0.800000 0.0515211745
0.714286 0.333333 0.800000 0.0540588285
0.857143 0.333333 0.800000 0.0597664254
1.000000 0.333333 0.800000 0.0675745048
-1.000000 0.500000 0.800000 -0.0994791248
-0.857143 0.500000 0.800000 -0.0842090044
-0.714286 0.500000 0.800000 -0.0677337251
-0.571429 0.500000 0.800000 -0.0494396802
-0.428571 0.500000 0.800000 -0.0292163961
-0.285714 0.500000 0.800000 -0.0080550265
-0.142857 0.500000 0.800000 0.0119238037
0.000000 0.500000 0.800000 0.0284388247
0.142857 0.500000 0.800000 0.0404952323
0.285714 0.500000 0.800000 0.0490878306
0.428571 0.500000 0.800000 0.0564978897
0.571429 0.500000 0.800000 0.0648460341
0.714286 0.500000 0.800000 0.0751234177
0.857143 0.500000 0.800000 0.0872195670
1.000000 0.500000 0.800000 0.1005208752
-1.000000 0.666667 0.800000 -0.1330940298
-0.857143 0.666667 0.800000 -0.1135941492
-0.714286 0.666667 0.800000 -0.0935405874
-0.571429 0.666667 0.800000 -0.0726514378
-0.428571 0.666667 0.800000 -0.0508759458
-0.285714 0.666667 0.800000 -0.0286694732
-0.142857 0.666667 0.800000 -0.0070062897
0.000000 0.666667 0.800000 0.0130655305
0.142857 0.666667 0.800000 0.0310889484
0.285714 0.666667 0.800000 0.0475210030
0.428571 0.666667 0.800000 0.0634097685
0.571429 0.666667 0.800000 0.0797295146
0.714286 0.666667 0.800000 0.0969356030
0.857143 0.666667 0.800000 0.1149772794
1.000000 0.666667 0.800000 0.1335726369
-1.000000 0.833333 0.800000 -0.1665786318
-0.857143 0.833333 0.800000 -0.1426027303
-0.714286 0.833333 0.800000 -0.1184231408
-0.571429 0.833333 0.800000 -0.0939361558
-0.428571 0.833333 0.800000 -0.0691231036
-0.285714 0.833333 0.800000 -0.0441515025
-0.142857 0.833333 0.800000 -0.0193797663
0.000000 0.833333 0.800000 0.0048065401
0.142857 0.833333 0.800000 0.0282392813
0.285714 0.833333 0.800000 0.0510865928
0.428571 0.833333 0.800000 0.0737340393
0.571429 0.833333 0.800000 0.0965400347
0.714286 0.833333 0.800000 0.1196720973
0.857143 0.833333 0.800000 0.1431115554
1.000000 0.833333 0.800000 0.1667547015
-1.000000 1.000000 0.800000 -0.1999740671
-0.857143 1.000000 0.800000 -0.1713536279
-0.714286 1.000000 0.800000 -0.1426731873
-0.571429 1.000000 0.800000 -0.1139021957
-0.428571 1.000000 0.800000 -0.0850351529
-0.285714 1.000000 0.800000 -0.0561214056
-0.142857 1.000000 0.800000 -0.0272665335
0.000000 1.000000 0.800000 0.0014158857
0.142857 1.000000 0.800000 0.0298763236
0.285714 1.000000 0.800000 0.0581643087
0.428571 1.000000 0.800000 0.0863934185
0.571429 1.000000 0.800000 0.1146692329
0.714286 1.000000 0.800000 0.1430410984
0.857143 1.000000 0.800000 0.1715035150
1.000000 1.000000 0.800000 0.2000259329
-1.000000 -1.000000 1.000000 0.2000061442
-0.857143 -1.000000 1.000000 0.1714463276
-0.714286 -1.000000 1.000000 0.1429007270
-0.571429 -1.000000 1.000000 0.1143765805
-0.428571 -1.000000 1.000000 0.0858751911
-0.285714 -1.000000 1.000000 0.0573848674
-0.142857 -1.000000 1.000000 0.0288805944
0.000000 -1.000000 1.000000 0.0003354626
0.142857 -1.000000 1.000000 -0.0282622627
0.285714 -1.000000 1.000000 -0.0569008469
0.428571 -1.000000 1.000000 -0.0855533803
0.571429 -1.000000 1.000000 -0.1141948481
0.714286 -1.000000 1.000000 -0.1428135587
0.857143 -1.000000 1.000000 -0.1714108152
1.000000 -1.000000 1.000000 -0.1999938558
-1.000000 -0.833333 1.000000 0.1666875246
-0.857143 -0.833333 1.000000 0.1429174203
-0.714286 -0.833333 1.000000 0.1191955753
-0.571429 -0.833333 1.000000 0.0955465608
-0.428571 -0.833333 1.000000 0.0719748008
-0.285714 -0.833333 1.000000 0.0484406053
-0.142857 -0.833333 1.000000 0.0248590563
0.000000 -0.833333 1.000000 0.0011388028
0.142857 -0.833333 1.000000 -0.0227599913
0.285714 -0.833333 1.000000 -0.0467974899
0.428571 -0.833333 1.000000 -0.0708823421
0.571429 -0.833333 1.000000 -0.0949296296
0.714286 -0.833333 1.000000 -0.1188996628
0.857143 -0.833333 1.000000 -0.1427968655
1.000000 -0.833333 1.000000 -0.1666458088
-1.000000 -0.666667 1.000000 0.1333900310
-0.857143 -0.666667 1.000000 0.1144495653
-0.714286 -0.666667 1.000000 0.0956402820
-0.571429 -0.666667 1.000000 0.0770289726
-0.428571 -0.666667 1.000000 0.0586276624
-0.285714 -0.666667 1.000000 0.0403284635
-0.142857 -0.666667 1.000000 0.0219005442
0.000000 -0.666667 1.000000 0.0030955869
0.142857 -0.666667 1.000000 -0.0161946939
0.285714 -0.666667 1.000000 -0.0358620127
0.428571 -0.666667 1.000000 -0.0556580519
0.571429 -0.666667 1.000000 -0.0753519798
0.714286 -0.666667 1.000000 -0.0948359085
0.857143 -0.666667 1.000000 -0.1141218633
1.000000 -0.666667 1.000000 -0.1332766357
-1.000000 -0.500000 1.000000 0.1001234098
-0.857143 -0.500000 1.000000 0.0860709286
-0.714286 -0.500000 1.000000 0.0723039831
-0.571429 -0.500000 1.000000 0.0589679536
-0.428571 -0.500000 1.000000 0.0460890144
-0.285714 -0.500000 1.000000 0.0334323337
-0.142857 -0.500000 1.000000 0.0204954766
0.000000 -0.500000 1.000000 0.0067379470
0.142857 -0.500000 1.000000 -0.0080759519
0.285714 -0.500000 1.000000 -0.0237105234
0.428571 -0.500000 1.000000 -0.0396252713
0.571429 -0.500000 1.000000 -0.0553177607
0.714286 -0.500000 1.000000 -0.0705531598
0.857143 -0.500000 1.000000 -0.0853576428
1.000000 -0.500000 1.000000 -0.0998765902
-1.000000 -0.333333 1.000000 0.0668817587
-0.857143 -0.333333 1.000000 0.0577644533
-0.714286 -0.333333 1.000000 0.0491448105
-0.571429 -0.333333 1.000000 0.0412762151
-0.428571 -0.333333 1.000000 0.0342042866
-0.285714 -0.333333 1.000000 0.0275197344
-0.142857 -0.333333 1.000000 0.0203468602
0.000000 -0.333333 1.000000 0.0117436285
0.142857 -0.333333 1.000000 0.0012992412
0.285714 -0.333333 1.000000 -0.0105755037
0.428571 -0.333333 1.000000 -0.0229385705
0.571429 -0.333333 1.000000 -0.0349142611
0.714286 -0.333333 1.000000 -0.0460932848
0.857143 -0.333333 1.000000 -0.0565212610
1.000000 -0.333333 1.000000 -0.0664515746
-1.000000 -0.166667 1.000000 0.0336335185
-0.857143 -0.166667 1.000000 0.0294389359
-0.714286 -0.166667 1.000000 0.0259388974
-0.571429 -0.166667 1.000000 0.0234870301
-0.428571 -0.166667 1.000000 0.0221470009
-0.285714 -0.166667 1.000000 0.0213475990
-0.142857 -0.166667 1.000000 0.0198666888
0.000000 -0.166667 1.000000 0.0163895538
0.142857 -0.166667 1.000000 0.0103428792
0.285714 -0.166667 1.000000 0.0022999799
0.428571 -0.166667 1.000000 -0.0064244276
0.571429 -0.166667 1.000000 -0.0146082080
0.714286 -0.166667 1.000000 -0.0216801502
0.857143 -0.166667 1.000000 -0.0277039213
1.000000 -0.166667 1.000000 -0.0330331482
-1.000000 0.000000 1.000000 0.0003354626
-0.857143 0.000000 1.000000 0.0009694560
-0.714286 0.000000 1.000000 0.0023796156
-0.571429 0.000000 1.000000 0.0049611265
-0.428571 0.000000 1.000000 0.0087851377
-0.285714 0.000000 1.000000 0.0132133102
-0.142857 0.000000 1.000000 0.0168798841
0.000000 0.000000 1.000000 0.0183156389
0.142857 0.000000 1.000000 0.0168798841
0.285714 0.000000 1.000000 0.0132133102
0.428571 0.000000 1.000000 0.0087851377
0.571429 0.000000 1.000000 0.0049611265
0.714286 0.000000 1.000000 0.0023796156
0.857143 0.000000 1.000000 0.0009694560
1.000000 0.000000 1.000000 0.0003354626
-1.000000 0.166667 1.000000 -0.0330331482
-0.857143 0.166667 1.000000 -0.0277039213
-0.714286 0.166667 1.000000 -0.0216801502
-0.571429 0.166667 1.000000 -0.0146082080
-0.428571 0.166667 1.000000 -0.0064244276
-0.285714 0.166667 1.000000 0.0022999799
-0.142857 0.166667 1.000000 0.0103428792
0.000000 0.166667 1.000000 0.0163895538
0.142857 0.166667 1.000000 0.0198666888
0.285714 0.166667 1.000000 0.0213475990
0.428571 0.166667 1.000000 0.0221470009
0.571429 0.166667 1.000000 0.0234870301
0.714286 0.166667 1.000000 0.0259388974
0.857143 0.166667 1.000000 0.0294389359
1.000000 0.166667 1.000000 0.0336335185
-1.000000 0.333333 1.000000 -0.0664515746
-0.857143 0.333333 1.000000 -0.0565212610
-0.714286 0.333333 1.000000 -0.0460932848
-0.571429 0.333333 1.000000 -0.0349142611
-0.428571 0.333333 1.000000 -0.0229385705
-0.285714 0.333333 1.000000 -0.0105755037
-0.142857 0.333333 1.000000 0.0012992412
0.000000 0.333333 1.000000 0.0117436285
0.142857 0.333333 1.000000 0.0203468602
0.285714 0.333333 1.000000 0.0275197344
0.428571 0.333333 1.000000 0.0342042866
0.571429 0.333333 1.000000 0.0412762151
0.714286 0.333333 1.000000 0.0491448105
0.857143 0.333333 1.000000 0.0577644533
1.000000 0.333333 1.000000 0.0668817587
-1.000000 0.500000 1.000000 -0.0998765902
-0.857143 0.500000 1.000000 -0.0853576428
-0.714286 0.500000 1.000000 -0.0705531598
-0.571429 0.500000 1.000000 -0.0553177607
-0.428571 0.500000 1.000000 -0.0396252713
-0.285714 0.500000 1.000000 -0.0237105234
-0.142857 0.500000 1.000000 -0.0080759519
0.000000 0.500000 1.000000 0.0067379470
0.142857 0.500000 1.000000 0.0204954766
0.285714 0.500000 1.000000 0.0334323337
0.428571 0.500000 1.000000 0.0460890144
0.571429 0.500000 1.000000 0.0589679536
0.714286 0.500000 1.000000 0.0723039831
0.857143 0.500000 1.000000 0.0860709286
1.000000 0.500000 1.000000 0.1001234098
-1.000000 0.666667 1.000000 -0.1332766357
-0.857143 0.666667 1.000000 -0.1141218633
-0.714286 0.666667 1.000000 -0.0948359085
-0.571429 0.666667 1.000000 -0.0753519798
-0.428571 0.666667 1.000000 -0.0556580519
-0.285714 0.666667 1.000000 -0.0358620127
-0.142857 0.666667 1.000000 -0.0161946939
0.000000 0.666667 1.000000 0.0030955869
0.142857 0.666667 1.000000 0.0219005442
0.285714 0.666667 1.000000 0.0403284635
0.428571 0.666667 1.000000 0.0586276624
0.571429 0.666667 1.000000 0.0770289726
0.714286 0.666667 1.000000 0.0956402820
0.857143 0.666667 1.000000 0.1144495653
1.000000 0.666667 1.000000 0.1333900310
-1.000000 0.833333 1.000000 -0.1666458088
-0.857143 0.833333 1.000000 -0.1427968655
-0.714286 0.833333 1.000000 -0.1188996628
-0.571429 0.833333 1.000000 -0.0949296296
-0.428571 0.833333 1.000000 -0.0708823421
-0.285714 0.833333 1.000000 -0.0467974899
-0.142857 0.833333 1.000000 -0.0227599913
0.000000 0.833333 1.000000 0.0011388028
0.142857 0.833333 1.000000 0.0248590563
0.285714 0.833333 1.000000 0.0484406053
0.428571 0.833333 1.000000 0.0719748008
0.571429 0.833333 1.000000 0.0955465608
0.714286 0.833333 1.000000 0.1191955753
0.857143 0.833333 1.000000 0.1429174203
1.000000 0.833333 1.000000 0.1666875246
-1.000000 1.000000 1.000000 -0.1999938558
-0.857143 1.000000 1.000000 -0.1714108152
-0.714286 1.000000 1.000000 -0.1428135587
-0.571429 1.000000 1.000000 -0.1141948481
-0.428571 1.000000 1.000000 -0.0855533803
-0.285714 1.000000 1.000000 -0.0569008469
-0.142857 1.000000 1.000000 -0.0282622627
0.000000 1.000000 1.000000 0.0003354626
0.142857 1.000000 1.000000 0.0288805944
0.285714 1.000000 1.000000 0.0573848674
0.428571 1.000000 1.000000 0.0858751911
0.571429 1.000000 1.000000 0.1143765805
0.714286 1.000000 1.000000 0.1429007270
0.857143 1.000000 1.000000 0.1714463276
1.000000 1.000000 1.000000 0.2000061442
```

---

## `implement_guide.md`

```md
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
```

---

## `native/CMakeLists.txt`

```txt
cmake_minimum_required(VERSION 3.21)
project(ScientificSimulationNative LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)
find_package(Qt6 REQUIRED COMPONENTS Widgets OpenGLWidgets)
find_package(OpenMP QUIET)

add_library(scientific_core STATIC src/scientific_core.cpp)
target_include_directories(scientific_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_compile_options(scientific_core PRIVATE -O3 -march=native -ffast-math)
if(OpenMP_CXX_FOUND)
  target_link_libraries(scientific_core PUBLIC OpenMP::OpenMP_CXX)
endif()

add_executable(scientific_simulation_native src/main.cpp src/MainWindow.cpp src/MainWindow.h src/Fast3DView.cpp src/Fast3DView.h)
target_link_libraries(scientific_simulation_native PRIVATE scientific_core Qt6::Widgets Qt6::OpenGLWidgets)
target_compile_options(scientific_simulation_native PRIVATE -O3 -march=native -ffast-math)
if(OpenMP_CXX_FOUND)
  target_link_libraries(scientific_simulation_native PRIVATE OpenMP::OpenMP_CXX)
endif()
install(TARGETS scientific_simulation_native RUNTIME DESTINATION bin)
```

---

## `native/README.md`

```md
# Native C++20 + Qt6 high-performance path

This directory is the native rendering/core path. It is deliberately separate from the Python scientific workflow so the application can be migrated incrementally without changing HDF5 semantics.

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/scientific_simulation_native
```

The build uses Qt6 Widgets + OpenGLWidgets, C++20, `-O3`, `-march=native`, optional OpenMP, and a static native core. The intended production integration is HDF5 -> zero-copy/typed field buffers -> VTK/PyVista or native OpenGL GPU buffers -> Qt, with long operations kept off the GUI thread.
```

---

## `native/build.sh`

```sh
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel "${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"
echo "Native Qt executable: $PWD/build/scientific_simulation_native"
```

---

## `native/src/Fast3DView.cpp`

```cpp
#include "Fast3DView.h"
#include <QOpenGLFunctions>
void Fast3DView::initializeGL(){ initializeOpenGLFunctions(); glClearColor(0.04f,0.05f,0.07f,1.0f); }
void Fast3DView::resizeGL(int w,int h){ glViewport(0,0,w,h); }
void Fast3DView::paintGL(){ glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT); }
```

---

## `native/src/Fast3DView.h`

```h
#pragma once
#include <QOpenGLWidget>
#include <QOpenGLFunctions>
class Fast3DView : public QOpenGLWidget, protected QOpenGLFunctions {
    Q_OBJECT
public:
    explicit Fast3DView(QWidget* p=nullptr):QOpenGLWidget(p){}
protected:
    void initializeGL() override;
    void resizeGL(int w,int h) override;
    void paintGL() override;
};
```

---

## `native/src/MainWindow.cpp`

```cpp
#include "MainWindow.h"
#include "Fast3DView.h"
#include <QTabWidget>
#include <QLabel>
MainWindow::MainWindow(){
    setWindowTitle("Scientific Simulation Platform - Native Qt Renderer"); resize(1440,900);
    auto* tabs=new QTabWidget(this); setCentralWidget(tabs);
    tabs->addTab(new Fast3DView(this),"GPU 3D");
    tabs->addTab(new QLabel("Native Qt/OpenGL data pipeline. Connect this view to HDF5/VTK backends in the production C++ build."),"Architecture");
}
```

---

## `native/src/MainWindow.h`

```h
#pragma once
#include <QMainWindow>
class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    MainWindow();
};
```

---

## `native/src/main.cpp`

```cpp
#include "MainWindow.h"
#include <QApplication>
int main(int argc,char** argv){ QApplication app(argc,argv); MainWindow w; w.show(); return app.exec(); }
```

---

## `native/src/native_physics.cpp`

```cpp
// Optional, OpenMP-parallelized C++ backend for the physics differential
// operators (gradient/divergence/curl/laplacian) and particle-field
// trilinear sampling.
//
// Design constraints this file must satisfy (see project docs):
//   * The Python application must work perfectly without this extension
//     being compiled at all -- see scientific_visualization/physics/native_backend.py
//     for the pure-NumPy fallback that mirrors every function here.
//   * Every formula here must exactly match the pre-existing NumPy
//     implementation in scientific_visualization/physics/engine.py (which is
//     built on np.gradient) for *uniform* grid spacing, so switching backends
//     never silently changes a scientific result. Non-uniform coordinate
//     spacing is intentionally NOT supported here -- the Python layer must
//     check CoordinateAxis.is_uniform before calling into this module and
//     fall back to np.gradient (which does support non-uniform spacing)
//     otherwise.
//
// Why this helps performance:
//   * np.gradient() re-derives edge handling and validates its inputs in
//     Python/C on every call, and divergence()/laplacian() in engine.py sum
//     several full-size temporary NumPy arrays (one per axis / per pass).
//     The kernels below fuse those passes into a single set of tight loops
//     over contiguous memory, parallelized across the outer (non-derivative)
//     axes with OpenMP so they scale with the number of CPU cores available
//     at runtime (see omp_get_max_threads()/omp_set_num_threads() below).

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <stdexcept>
#include <algorithm>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

using Array = py::array_t<double, py::array::c_style | py::array::forcecast>;

namespace {

// Decompose shape/strides (in elements) for a C-contiguous array.
struct Layout {
    std::vector<ssize_t> shape;
    std::vector<ssize_t> strides_elems; // per-dimension stride, in elements
    ssize_t total = 1;
    int ndim = 0;

    explicit Layout(const py::buffer_info& buf) {
        ndim = buf.ndim;
        shape.assign(buf.shape.begin(), buf.shape.end());
        strides_elems.resize(ndim);
        ssize_t acc = 1;
        for (int d = ndim - 1; d >= 0; --d) {
            strides_elems[d] = acc;
            acc *= shape[d];
        }
        total = acc;
    }
};

// One-dimensional finite-difference derivative along `axis` of an N-D
// C-contiguous array, using the same formulas as numpy.gradient for
// *uniform* spacing `h`:
//   interior:  (f[i+1] - f[i-1]) / (2h)                         (2nd order)
//   edge_order 2 boundary: 3-point one-sided formula             (2nd order)
//   edge_order 1 boundary (or n == 2): simple forward/backward   (1st order)
//
// `accumulate` selects whether results are written (`false`) or added
// in-place (`true`) into `out` -- the latter is what lets divergence()
// and laplacian() fuse multiple axis-passes without allocating a fresh
// full-size temporary array for every axis.
void gradient_pass(const double* in, double* out, const Layout& layout,
                    int axis, double h, int edge_order, bool accumulate) {
    if (axis < 0 || axis >= layout.ndim)
        throw std::invalid_argument("axis out of range");
    const ssize_t n = layout.shape[axis];
    if (n < 2)
        throw std::invalid_argument("need at least 2 points along the differentiated axis");
    const ssize_t axis_stride = layout.strides_elems[axis];
    const ssize_t outer_size = layout.total / n;

    std::vector<ssize_t> other_shape, other_stride;
    other_shape.reserve(layout.ndim - 1);
    other_stride.reserve(layout.ndim - 1);
    for (int d = 0; d < layout.ndim; ++d) {
        if (d != axis) {
            other_shape.push_back(layout.shape[d]);
            other_stride.push_back(layout.strides_elems[d]);
        }
    }
    const int n_other = static_cast<int>(other_shape.size());
    const bool two_point = (n == 2);
    const bool second_order_edges = (edge_order >= 2) && !two_point;

    #pragma omp parallel for schedule(static)
    for (ssize_t o = 0; o < outer_size; ++o) {
        ssize_t rem = o, base = 0;
        for (int d = n_other - 1; d >= 0; --d) {
            const ssize_t s = other_shape[d];
            const ssize_t idx = rem % s;
            rem /= s;
            base += idx * other_stride[d];
        }
        const double* col_in = in + base;
        double* col_out = out + base;

        if (two_point) {
            const double d0 = (col_in[axis_stride] - col_in[0]) / h;
            if (accumulate) { col_out[0] += d0; col_out[axis_stride] += d0; }
            else { col_out[0] = d0; col_out[axis_stride] = d0; }
            continue;
        }

        for (ssize_t i = 1; i < n - 1; ++i) {
            const double val = (col_in[(i + 1) * axis_stride] - col_in[(i - 1) * axis_stride]) / (2.0 * h);
            if (accumulate) col_out[i * axis_stride] += val;
            else col_out[i * axis_stride] = val;
        }

        double left, right;
        if (second_order_edges) {
            left  = (-3.0 * col_in[0] + 4.0 * col_in[axis_stride] - col_in[2 * axis_stride]) / (2.0 * h);
            right = (3.0 * col_in[(n - 1) * axis_stride] - 4.0 * col_in[(n - 2) * axis_stride] + col_in[(n - 3) * axis_stride]) / (2.0 * h);
        } else {
            left  = (col_in[axis_stride] - col_in[0]) / h;
            right = (col_in[(n - 1) * axis_stride] - col_in[(n - 2) * axis_stride]) / h;
        }
        if (accumulate) { col_out[0] += left; col_out[(n - 1) * axis_stride] += right; }
        else { col_out[0] = left; col_out[(n - 1) * axis_stride] = right; }
    }
}

} // namespace

// ---------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------

Array gradient_uniform(Array input, double h, int axis, int edge_order) {
    auto buf = input.request();
    Layout layout(buf);
    Array result(layout.shape);
    auto out_buf = result.request();
    std::fill(static_cast<double*>(out_buf.ptr), static_cast<double*>(out_buf.ptr) + layout.total, 0.0);
    gradient_pass(static_cast<const double*>(buf.ptr), static_cast<double*>(out_buf.ptr),
                  layout, axis, h, edge_order, /*accumulate=*/false);
    return result;
}

Array divergence_uniform(std::vector<Array> components, std::vector<double> spacings, int edge_order) {
    if (components.empty())
        throw std::invalid_argument("divergence_uniform requires at least one component");
    if (components.size() != spacings.size())
        throw std::invalid_argument("components and spacings must have the same length");

    auto buf0 = components[0].request();
    Layout layout(buf0);
    if (static_cast<int>(components.size()) != layout.ndim)
        throw std::invalid_argument("number of components must equal the array dimensionality");

    Array result(layout.shape);
    auto out_buf = result.request();
    double* out = static_cast<double*>(out_buf.ptr);
    std::fill(out, out + layout.total, 0.0);

    for (int axis = 0; axis < layout.ndim; ++axis) {
        auto buf = components[axis].request();
        Layout comp_layout(buf);
        if (comp_layout.shape != layout.shape)
            throw std::invalid_argument("all components must share the same shape");
        gradient_pass(static_cast<const double*>(buf.ptr), out, layout, axis,
                      spacings[axis], edge_order, /*accumulate=*/true);
    }
    return result;
}

Array laplacian_uniform(Array input, std::vector<double> spacings, int edge_order) {
    auto buf = input.request();
    Layout layout(buf);
    if (static_cast<int>(spacings.size()) != layout.ndim)
        throw std::invalid_argument("spacings must have one entry per dimension");

    Array result(layout.shape);
    auto out_buf = result.request();
    double* out = static_cast<double*>(out_buf.ptr);
    std::fill(out, out + layout.total, 0.0);

    // Matches physics.engine.PhysicsEngine.laplacian(): apply the first
    // derivative, then differentiate that result again along the same axis
    // (a wider, still-second-order stencil), summed over every axis.
    std::vector<double> scratch(layout.total);
    for (int axis = 0; axis < layout.ndim; ++axis) {
        std::fill(scratch.begin(), scratch.end(), 0.0);
        gradient_pass(static_cast<const double*>(buf.ptr), scratch.data(), layout, axis,
                      spacings[axis], edge_order, /*accumulate=*/false);
        gradient_pass(scratch.data(), out, layout, axis,
                      spacings[axis], edge_order, /*accumulate=*/true);
    }
    return result;
}

py::tuple curl_uniform_3d(Array c1, Array c2, Array c3, double h1, double h2, double h3, int edge_order) {
    auto buf1 = c1.request();
    Layout layout(buf1);
    if (layout.ndim != 3)
        throw std::invalid_argument("curl_uniform_3d requires 3D arrays");
    auto buf2 = c2.request();
    auto buf3 = c3.request();
    Layout layout2(buf2), layout3(buf3);
    if (layout2.shape != layout.shape || layout3.shape != layout.shape)
        throw std::invalid_argument("all three components must share the same shape");

    const double* d1 = static_cast<const double*>(buf1.ptr);
    const double* d2 = static_cast<const double*>(buf2.ptr);
    const double* d3 = static_cast<const double*>(buf3.ptr);

    // out_a = d(c3)/dx2 - d(c2)/dx3
    // out_b = d(c1)/dx3 - d(c3)/dx1
    // out_c = d(c2)/dx1 - d(c1)/dx2
    std::vector<double> d3_dx2(layout.total), d2_dx3(layout.total);
    std::vector<double> d1_dx3(layout.total), d3_dx1(layout.total);
    std::vector<double> d2_dx1(layout.total), d1_dx2(layout.total);

    gradient_pass(d3, d3_dx2.data(), layout, 1, h2, edge_order, false);
    gradient_pass(d2, d2_dx3.data(), layout, 2, h3, edge_order, false);
    gradient_pass(d1, d1_dx3.data(), layout, 2, h3, edge_order, false);
    gradient_pass(d3, d3_dx1.data(), layout, 0, h1, edge_order, false);
    gradient_pass(d2, d2_dx1.data(), layout, 0, h1, edge_order, false);
    gradient_pass(d1, d1_dx2.data(), layout, 1, h2, edge_order, false);

    Array out_a(layout.shape), out_b(layout.shape), out_c(layout.shape);
    double* pa = static_cast<double*>(out_a.request().ptr);
    double* pb = static_cast<double*>(out_b.request().ptr);
    double* pc = static_cast<double*>(out_c.request().ptr);

    #pragma omp parallel for schedule(static)
    for (ssize_t i = 0; i < layout.total; ++i) {
        pa[i] = d3_dx2[i] - d2_dx3[i];
        pb[i] = d1_dx3[i] - d3_dx1[i];
        pc[i] = d2_dx1[i] - d1_dx2[i];
    }
    return py::make_tuple(out_a, out_b, out_c);
}

// Trilinear sampling of a scalar 3D field at arbitrary physical points,
// parallelized across the (typically large and independent) set of
// sample points -- the natural use case being "sample E(x(t), y(t), z(t))
// along a particle trajectory" for many particles/timesteps at once.
// Points outside the grid are clamped to the boundary (matching how
// lineouts/interpolation already behave elsewhere in this codebase)
// rather than raising, since a slightly-out-of-bounds particle position
// due to floating point error is expected, not exceptional.
py::array_t<double> sample_field_trilinear(
    Array field,
    std::array<double, 3> origin,
    std::array<double, 3> spacing,
    Array points // (N, 3)
) {
    auto fbuf = field.request();
    if (fbuf.ndim != 3)
        throw std::invalid_argument("sample_field_trilinear requires a 3D field");
    const ssize_t n0 = fbuf.shape[0], n1 = fbuf.shape[1], n2 = fbuf.shape[2];
    const ssize_t s0 = n1 * n2, s1 = n2, s2 = 1;
    const double* f = static_cast<const double*>(fbuf.ptr);

    auto pbuf = points.request();
    if (pbuf.ndim != 2 || pbuf.shape[1] != 3)
        throw std::invalid_argument("points must have shape (N, 3)");
    const ssize_t npts = pbuf.shape[0];
    const double* pts = static_cast<const double*>(pbuf.ptr);

    for (double h : spacing)
        if (h == 0.0) throw std::invalid_argument("grid spacing must be non-zero");

    auto result = py::array_t<double>(npts);
    double* out = static_cast<double*>(result.request().ptr);

    #pragma omp parallel for schedule(static)
    for (ssize_t k = 0; k < npts; ++k) {
        double gx = (pts[k * 3 + 0] - origin[0]) / spacing[0];
        double gy = (pts[k * 3 + 1] - origin[1]) / spacing[1];
        double gz = (pts[k * 3 + 2] - origin[2]) / spacing[2];

        gx = std::min(std::max(gx, 0.0), static_cast<double>(n0 - 1));
        gy = std::min(std::max(gy, 0.0), static_cast<double>(n1 - 1));
        gz = std::min(std::max(gz, 0.0), static_cast<double>(n2 - 1));

        ssize_t i0 = static_cast<ssize_t>(std::floor(gx));
        ssize_t j0 = static_cast<ssize_t>(std::floor(gy));
        ssize_t k0 = static_cast<ssize_t>(std::floor(gz));
        ssize_t i1 = std::min(i0 + 1, n0 - 1);
        ssize_t j1 = std::min(j0 + 1, n1 - 1);
        ssize_t k1 = std::min(k0 + 1, n2 - 1);

        const double tx = gx - i0, ty = gy - j0, tz = gz - k0;

        auto at = [&](ssize_t i, ssize_t j, ssize_t kk) { return f[i * s0 + j * s1 + kk * s2]; };

        const double c00 = at(i0, j0, k0) * (1 - tx) + at(i1, j0, k0) * tx;
        const double c01 = at(i0, j0, k1) * (1 - tx) + at(i1, j0, k1) * tx;
        const double c10 = at(i0, j1, k0) * (1 - tx) + at(i1, j1, k0) * tx;
        const double c11 = at(i0, j1, k1) * (1 - tx) + at(i1, j1, k1) * tx;
        const double c0 = c00 * (1 - ty) + c10 * ty;
        const double c1 = c01 * (1 - ty) + c11 * ty;
        out[k] = c0 * (1 - tz) + c1 * tz;
    }
    return result;
}

int omp_max_threads() {
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}

bool openmp_enabled() {
#ifdef _OPENMP
    return true;
#else
    return false;
#endif
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Optional OpenMP-parallelized C++ kernels for uniform-grid physics "
              "operators and particle-field trilinear sampling. Pure-NumPy "
              "fallbacks with identical numerics live in "
              "scientific_visualization.physics.native_backend and are used "
              "automatically whenever this extension is not compiled.";
    m.def("gradient_uniform", &gradient_uniform, py::arg("data"), py::arg("h"), py::arg("axis"), py::arg("edge_order") = 2);
    m.def("divergence_uniform", &divergence_uniform, py::arg("components"), py::arg("spacings"), py::arg("edge_order") = 2);
    m.def("laplacian_uniform", &laplacian_uniform, py::arg("data"), py::arg("spacings"), py::arg("edge_order") = 2);
    m.def("curl_uniform_3d", &curl_uniform_3d, py::arg("c1"), py::arg("c2"), py::arg("c3"),
          py::arg("h1"), py::arg("h2"), py::arg("h3"), py::arg("edge_order") = 2);
    m.def("sample_field_trilinear", &sample_field_trilinear, py::arg("field"), py::arg("origin"),
          py::arg("spacing"), py::arg("points"));
    m.def("omp_max_threads", &omp_max_threads);
    m.def("openmp_enabled", &openmp_enabled);
}
```

---

## `native/src/scientific_core.cpp`

```cpp
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

extern "C" void smooth_field(const float* in, float* out, std::size_t n, int radius) {
    if (!in || !out || n == 0) return;
    if (radius <= 0) { std::copy(in, in+n, out); return; }
#pragma omp parallel for if(n > 4096)
    for (long long i=0; i<static_cast<long long>(n); ++i) {
        const std::size_t lo = (i < radius) ? 0 : static_cast<std::size_t>(i-radius);
        const std::size_t hi = std::min<std::size_t>(n-1, static_cast<std::size_t>(i+radius));
        double s=0.0; for (std::size_t j=lo;j<=hi;++j) s += in[j];
        out[i]=static_cast<float>(s/static_cast<double>(hi-lo+1));
    }
}
```

---

## `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "scientific-simulation-platform"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
performance = ["opencv-python>=4.8", "vispy>=0.14"]

[tool.setuptools.packages.find]
include = ["scientific_visualization*"]
```

---

## `requirements.txt`

```txt
PyQt5>=5.15
h5py>=3.8
numpy>=1.23
matplotlib>=3.6
scipy>=1.9   # optional but recommended: enables Gaussian/moving-average smoothing
PyVista>=0.43  # optional runtime dependency for 3D rendering
PyVistaQt>=0.11  # optional Qt integration for the 3D viewer
# Optional machine-learning features
scikit-learn>=1.3
Pillow>=9.5
# Optional bundled ffmpeg support for MP4 animation export
imageio>=2.31
imageio-ffmpeg>=0.4.9

# Optional fast movie encoding / image processing
opencv-python>=4.8
# Optional GPU-backed interactive 2D rendering
vispy>=0.14
```

---

## `run_visualizer.py`

```py
#!/usr/bin/env python3
"""Launch the Scientific Visualization (Python) desktop application."""
from scientific_visualization.app import main

if __name__ == "__main__":
    main()
```

---

## `scientific_visualization/__init__.py`

```py

```

---

## `scientific_visualization/analysis/__init__.py`

```py
from .lineout import LineoutAnalyzer
from .statistics import statistics
from .derived import DerivedQuantityEngine
from .smoothing import smooth_1d, smooth_2d
from .time_series import TimeSeriesAnalyzer, reduce_grid_series
from .expression import SafeExpressionEngine
from .ai import AIAnalysisEngine
from .series import SimulationSeries
from .spectral import SpectrumResult, fft_1d, fft_nd, power_spectrum_1d, wavenumber_spectrum, temporal_spectrum, k_omega
from .roi import RegionOfInterest, roi_statistics, roi_time_series, export_roi_results

__all__ = ["LineoutAnalyzer", "statistics", "DerivedQuantityEngine", "smooth_1d", "smooth_2d", "TimeSeriesAnalyzer", "reduce_grid_series", "SafeExpressionEngine", "AIAnalysisEngine", "SimulationSeries", "SpectrumResult", "fft_1d", "fft_nd", "power_spectrum_1d", "wavenumber_spectrum", "temporal_spectrum", "k_omega", "RegionOfInterest", "roi_statistics", "roi_time_series", "export_roi_results"]

from .derived import DerivedQuantityEngine, parse_average_direction, format_average_direction
```

---

## `scientific_visualization/analysis/ai.py`

```py
from __future__ import annotations

import numpy as np

from ..core.data import Dataset
from .statistics import statistics
from .series import SimulationSeries


class AIAnalysisEngine:
    """Deterministic scientific-analysis service for one frame or an entire simulation series."""

    def analyze(self, dataset: Dataset) -> dict:
        data = np.asarray(dataset.data)
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            raise ValueError("The selected dataset contains no finite numerical values.")
        stats = statistics(data)
        return {
            "scope": "frame",
            "n_frames": 1,
            "summary": self._summary(dataset, finite, stats),
            "statistics": stats,
            "physics": self._physics_suggestions(dataset),
            "recommendations": self._recommendations(dataset, finite),
        }

    def analyze_series(self, files=None, quantity=None, folder=None, reduction="mean", max_frames=None) -> dict:
        if folder:
            series = SimulationSeries.from_folder(folder, quantity=quantity)
        elif files:
            series = SimulationSeries(files, quantity=quantity)
        else:
            raise ValueError("Provide a simulation folder or a list of HDF5 files")
        frames = series.discover()
        if max_frames and len(frames) > max_frames:
            # Keep the full metadata inventory but sample evenly for expensive statistics.
            ids = np.linspace(0, len(frames) - 1, max_frames, dtype=int)
            sampled = [frames[i] for i in ids]
            sampled_series = SimulationSeries([x[0] for x in sampled], quantity=series.quantity)
            sampled_series._frames = sampled
            analysis_series = sampled_series
        else:
            analysis_series = series

        times, iterations, values = analysis_series.temporal_reduction(reduction)
        finite_values = values[np.isfinite(values)]
        if not finite_values.size:
            raise ValueError("The simulation series contains no finite values for the requested reduction")
        temporal_stats = {
            "frames_discovered": len(frames),
            "frames_analyzed": len(analysis_series.frames),
            "time_start": float(times.min()),
            "time_end": float(times.max()),
            "value_min": float(finite_values.min()),
            "value_max": float(finite_values.max()),
            "value_mean": float(finite_values.mean()),
            "value_rms": float(np.sqrt(np.mean(finite_values ** 2))),
        }
        frequency = None
        if len(times) >= 4:
            try:
                _, _, _, spec = analysis_series.temporal_frequency(reduction)
                power = np.asarray(spec.power).reshape(-1)
                freq = np.asarray(spec.frequencies).reshape(-1)
                idx = int(np.argmax(power[1:]) + 1) if power.size > 1 else 0
                frequency = {"peak_frequency": float(freq[idx]), "peak_power": float(power[idx])}
            except ValueError:
                frequency = {"status": "temporal spacing is not uniform; FFT skipped"}

        first_ds = analysis_series.load(0)
        last_ds = analysis_series.load(len(analysis_series.frames) - 1)
        change = np.asarray(last_ds.data, dtype=float) - np.asarray(first_ds.data, dtype=float)
        finite_change = change[np.isfinite(change)]
        return {
            "scope": "simulation_series",
            "quantity": series.quantity,
            "n_files_discovered": len(series.files),
            "n_frames": len(frames),
            "n_frames_analyzed": len(analysis_series.frames),
            "files": [f[0] for f in frames],
            "times": times,
            "iterations": iterations,
            "reduced_values": values,
            "temporal_statistics": temporal_stats,
            "temporal_frequency": frequency,
            "field_change": {
                "delta_min": float(np.nanmin(finite_change)),
                "delta_max": float(np.nanmax(finite_change)),
                "delta_rms": float(np.sqrt(np.nanmean(finite_change ** 2))),
            },
            "summary": (
                f"{series.quantity}: analyzed {len(analysis_series.frames)} of {len(frames)} discovered frames "
                f"from t={times.min():.6g} to {times.max():.6g}. "
                f"{reduction} over space ranges from {finite_values.min():.6g} to {finite_values.max():.6g}."
            ),
            "recommendations": self._series_recommendations(first_ds, times, values, frequency),
        }

    def _summary(self, ds, finite, stats):
        return (
            f"{ds.name}: {ds.ndim}D {ds.shape}, units={ds.units or 'not specified'}. "
            f"Finite range [{finite.min():.6g}, {finite.max():.6g}], "
            f"mean={stats['mean']:.6g}, RMS={stats['rms']:.6g}."
        )

    def _physics_suggestions(self, ds):
        axes = set(ds.axes)
        suggestions = []
        if ds.ndim >= 1:
            suggestions.append("Inspect coordinate-aware gradients along the available physical axes.")
        if ds.ndim >= 2:
            suggestions.append("Inspect lineouts and spatial averages to identify localized structure.")
        lower = ds.name.lower()
        if lower.startswith(("e", "electric")):
            suggestions.append("If E1/E2/E3 are available, evaluate |E|, E², divergence, and related derived quantities.")
        if lower.startswith(("b", "magnetic")):
            suggestions.append("If B1/B2/B3 are available, evaluate |B|, B², curl, and related derived quantities.")
        if axes:
            suggestions.append("Use physical coordinates for derivatives, integrals, and spectral wavenumbers.")
        return suggestions

    def _series_recommendations(self, ds, times, values, frequency):
        recs = [
            "Use the complete frame inventory for temporal statistics rather than analyzing only the displayed frame.",
            "Compare field evolution against simulation iteration and physical time before training a surrogate model.",
        ]
        if frequency and "peak_frequency" in frequency and frequency["peak_frequency"] > 0:
            recs.append(f"A temporal spectral peak was detected near {frequency['peak_frequency']:.6g} cycles per time unit; inspect its stability across the run.")
        if ds.ndim >= 2:
            recs.append("Run spatial FFT/wavenumber analysis and k-ω analysis when the spatial and temporal coordinates are uniform.")
        if np.ptp(values) > 0:
            recs.append("Use normalized temporal features and coordinate-aware spatial features for ML/surrogate training.")
        return recs

    def _recommendations(self, ds, finite):
        p01, p99 = np.percentile(finite, [1, 99])
        recs = []
        if np.min(finite) <= 0 < np.max(finite):
            recs.append("A diverging colormap or symmetric limits may be appropriate because the field crosses zero.")
        elif p99 / max(abs(p01), 1e-30) > 100:
            recs.append("The dynamic range is large; percentile clipping or logarithmic normalization may improve visualization.")
        if ds.ndim >= 2 and finite.size > 1000:
            recs.append("For ML, start with coordinate-aware features and bounded spatial sampling before training.")
        return recs
```

---

## `scientific_visualization/analysis/derived.py`

```py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import numpy as np

from ..core.data import CoordinateAxis, Dataset


@dataclass(frozen=True)
class Operation:
    name: str
    function: Callable
    description: str = ""


class DerivedQuantityEngine:
    def __init__(self):
        self.operations: dict[str, Operation] = {
            "add": Operation("add", lambda a, b: a + b),
            "subtract": Operation("subtract", lambda a, b: a - b),
            "multiply": Operation("multiply", lambda a, b: a * b),
            "divide": Operation("divide", lambda a, b: np.divide(a, b)),
            "abs": Operation("abs", np.abs),
            "log": Operation("log", np.log),
        }

    def register(self, operation: Operation):
        self.operations[operation.name] = operation

    def binary(self, op: str, a: Dataset, b: Dataset, name=None, units="") -> Dataset:
        if a.shape != b.shape or a.axes != b.axes:
            raise ValueError("Derived operands must have compatible shapes and axes")
        if op not in self.operations or op in {"abs", "log"}:
            raise ValueError(f"'{op}' is not a binary operation")
        return Dataset(name or f"({a.name} {op} {b.name})", self.operations[op].function(a.data, b.data), a.axes, a.coordinates, units or a.units, a.time, a.time_units, {"operation": op}, a.source, a.simulation_metadata, derived_from=(a.name,b.name))

    def unary(self, op: str, a: Dataset, name=None, units="") -> Dataset:
        if op not in {"abs", "log"}:
            raise ValueError(f"'{op}' is not a unary operation")
        if op == "log" and np.any(a.data <= 0):
            raise ValueError("logarithm is only defined for positive values")
        return Dataset(name or f"{op}({a.name})", self.operations[op].function(a.data), a.axes, a.coordinates, units or a.units, a.time, a.time_units, {"operation": op}, a.source, a.simulation_metadata, derived_from=(a.name,))

    def vector_magnitude(self, components: Mapping[str, Dataset], name="|A|") -> Dataset:
        if not components:
            raise ValueError("At least one component is required")
        items = list(components.values())
        base = items[0]
        if any(x.shape != base.shape or x.axes != base.axes for x in items[1:]):
            raise ValueError("Vector components must have compatible shapes and axes")
        data = np.sqrt(sum(np.asarray(x.data) ** 2 for x in items))
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units, {"operation": "vector_magnitude", "components": tuple(components)}, base.source, base.simulation_metadata, derived_from=tuple(components))

    def gradient(self, dataset: Dataset, axis: str | int) -> Dataset:
        ai = dataset.axis_index(axis)
        coord = dataset.coordinates[ai].values
        if coord.size < 2:
            raise ValueError("At least two coordinate points are required for a gradient")
        edge_order = 2 if coord.size > 2 else 1
        data = np.gradient(dataset.data, coord, axis=ai, edge_order=edge_order)
        unit = f"{dataset.units}/{dataset.coordinates[ai].units}" if dataset.units and dataset.coordinates[ai].units else dataset.units
        return Dataset(f"d({dataset.name})/d{dataset.axes[ai]}", data, dataset.axes, dataset.coordinates, unit, dataset.time, dataset.time_units, {"operation": "gradient", "axis": dataset.axes[ai]}, dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    def integrate(self, dataset: Dataset, axis: str | int) -> Dataset:
        ai = dataset.axis_index(axis)
        coord = dataset.coordinates[ai].values
        data = np.trapz(dataset.data, coord, axis=ai)
        new_axes = tuple(x for i, x in enumerate(dataset.axes) if i != ai)
        new_coords = tuple(x for i, x in enumerate(dataset.coordinates) if i != ai)
        return Dataset(f"int {dataset.name} d{dataset.axes[ai]}", data, new_axes, new_coords, dataset.units, dataset.time, dataset.time_units, {"operation": "integral", "axis": dataset.axes[ai]}, dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    def average(self, dataset: Dataset, axis: str | int) -> Dataset:
        ai = dataset.axis_index(axis)
        data = np.mean(dataset.data, axis=ai)
        return Dataset(f"avg({dataset.name})", data, tuple(x for i,x in enumerate(dataset.axes) if i != ai), tuple(x for i,x in enumerate(dataset.coordinates) if i != ai), dataset.units, dataset.time, dataset.time_units, {"operation":"average","axis":dataset.axes[ai]}, dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    def directional_average(self, dataset: Dataset, direction: str, name=None) -> Dataset:
        """Average a field over one or more physical axes.

        ``direction`` accepts ``x``, ``y``, ``z`` or a parenthesized tuple such
        as ``(x,y,z)``. Axes that are not present are rejected explicitly.
        For a 3D ``(x,y,z)`` average the result is a scalar Dataset, which can
        naturally be accumulated across a Simulation frame series.
        """
        axes = parse_average_direction(direction)
        indices = [dataset.axis_index("x" + str(ord(i) - ord("x") + 1)) for i in axes]
        data = np.mean(dataset.data, axis=tuple(indices))
        keep = [i for i in range(dataset.ndim) if i not in set(indices)]
        return Dataset(
            name or f"average,dir={format_average_direction(axes)}({dataset.name})",
            data,
            tuple(dataset.axes[i] for i in keep),
            tuple(dataset.coordinates[i] for i in keep),
            dataset.units, dataset.time, dataset.time_units,
            {**dict(dataset.metadata), "operation": "directional_average", "directions": axes},
            dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,),
        )


def parse_average_direction(direction: str) -> tuple[str, ...]:
    """Parse the supported directional-average syntax."""
    text = str(direction).strip().lower()
    if text.startswith("average,dir="):
        text = text.split("=", 1)[1].strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    parts = tuple(p.strip() for p in text.split(",") if p.strip())
    if not parts:
        raise ValueError("average direction must be x, y, z, or a comma-separated tuple such as (x,y,z)")
    if any(p not in {"x", "y", "z"} for p in parts):
        raise ValueError("average direction entries must be x, y, or z")
    if len(set(parts)) != len(parts):
        raise ValueError("average direction cannot contain duplicate axes")
    return parts


def format_average_direction(direction: tuple[str, ...]) -> str:
    return direction[0] if len(direction) == 1 else "(" + ",".join(direction) + ")"
```

---

## `scientific_visualization/analysis/expression.py`

```py
from __future__ import annotations
import ast
import numpy as np
from ..core.data import Dataset
from .derived import DerivedQuantityEngine
from ..physics import PhysicsEngine

_ALLOWED_BIN = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)

class SafeExpressionEngine:
    """Small AST-based expression evaluator for Dataset arithmetic.

    No unrestricted eval is used. Names resolve only to supplied datasets or approved functions.
    """
    def __init__(self):
        self.derived = DerivedQuantityEngine()
        self.physics = PhysicsEngine()

    def evaluate(self, expression: str, datasets: dict[str, Dataset], name: str|None=None) -> Dataset:
        tree = ast.parse(expression, mode="eval")
        ds = self._eval(tree.body, datasets)
        if not isinstance(ds, Dataset):
            raise ValueError("Expression must produce a Dataset")
        ds.name = name or ds.name
        return ds

    def _eval(self, node, env):
        if isinstance(node, ast.Name):
            if node.id not in env: raise ValueError(f"Unknown quantity '{node.id}'")
            return env[node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value,(int,float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op,_ALLOWED_UNARY):
            a=self._eval(node.operand,env)
            if isinstance(a,Dataset):
                data = a.data if isinstance(node.op,ast.UAdd) else -a.data
                return Dataset(a.name,data,a.axes,a.coordinates,a.units,a.time,a.time_units,{**dict(a.metadata),"expression":True},a.source,a.simulation_metadata,derived_from=(a.name,))
            return +a if isinstance(node.op,ast.UAdd) else -a
        if isinstance(node, ast.BinOp) and isinstance(node.op,_ALLOWED_BIN):
            a,b=self._eval(node.left,env),self._eval(node.right,env)
            return self._binary(a,b,node.op)
        if isinstance(node, ast.Call):
            if not isinstance(node.func,ast.Name): raise ValueError("Only direct function calls are allowed")
            fn=node.func.id
            if fn in {"sqrt","abs","log","log10"} and len(node.args)==1:
                a=self._eval(node.args[0],env)
                if not isinstance(a,Dataset): raise ValueError(f"{fn} requires a Dataset")
                func={"sqrt":np.sqrt,"abs":np.abs,"log":np.log,"log10":np.log10}[fn]
                return Dataset(f"{fn}({a.name})",func(a.data),a.axes,a.coordinates,a.units,a.time,a.time_units,{"expression":fn},a.source,a.simulation_metadata,derived_from=(a.name,))
            if fn in {"magnitude", "div", "curl"}:
                return self._vector_call(node.args,env,operation=fn)
            if fn in {"gradient","integrate","average"} and len(node.args)==2:
                a=self._eval(node.args[0],env); axis=self._literal(node.args[1])
                return getattr(self.derived,fn)(a,axis)
            raise ValueError(f"Function '{fn}' is not permitted")
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    def _vector_call(self,args,env,operation="magnitude"):
        if len(args)!=1 or not isinstance(args[0],ast.Name): raise ValueError("magnitude(E) requires a component prefix name")
        prefix=args[0].id
        comps={k[1:]:v for k,v in env.items() if k.startswith(prefix) and k[len(prefix):] in {"1","2","3"}}
        if not comps: raise ValueError(f"No components found for {prefix}")
        if operation == "magnitude":
            return self.derived.vector_magnitude(comps,name=f"|{prefix}|")
        if operation == "div":
            return self.physics.divergence(comps, name=f"div({prefix})")
        if operation == "curl":
            raise ValueError("curl(B) is available through PhysicsEngine.curl; use a 3-component Dataset mapping in the Python API")

    def _literal(self,node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,int)): return node.value
        if isinstance(node,ast.Name): return node.id
        raise ValueError("Expected an axis literal")

    def _binary(self,a,b,op):
        if isinstance(a,Dataset) and isinstance(b,Dataset):
            if a.shape!=b.shape or a.axes!=b.axes: raise ValueError("Datasets must have compatible shapes and axes")
            data = {ast.Add:a.data+b.data,ast.Sub:a.data-b.data,ast.Mult:a.data*b.data,ast.Div:np.divide(a.data,b.data),ast.Pow:a.data**b.data}[type(op)]
            return Dataset("derived",data,a.axes,a.coordinates,a.units,a.time,a.time_units,{"expression":type(op).__name__},a.source,a.simulation_metadata,derived_from=(a.name,b.name))
        if isinstance(a,Dataset): data={ast.Add:a.data+b,ast.Sub:a.data-b,ast.Mult:a.data*b,ast.Div:np.divide(a.data,b),ast.Pow:a.data**b}[type(op)]; return Dataset(a.name,data,a.axes,a.coordinates,a.units,a.time,a.time_units,{"expression":True},a.source,a.simulation_metadata,derived_from=(a.name,))
        if isinstance(b,Dataset): data={ast.Add:a+b.data,ast.Sub:a-b.data,ast.Mult:a*b.data,ast.Div:np.divide(a,b.data),ast.Pow:a**b.data}[type(op)]; return Dataset(b.name,data,b.axes,b.coordinates,b.units,b.time,b.time_units,{"expression":True},b.source,b.simulation_metadata,derived_from=(b.name,))
        return {ast.Add:a+b,ast.Sub:a-b,ast.Mult:a*b,ast.Div:a/b,ast.Pow:a**b}[type(op)]
```

---

## `scientific_visualization/analysis/lineout.py`

```py
from __future__ import annotations

import numpy as np

from ..core.data import Dataset


class LineoutAnalyzer:
    def lineout(self, dataset: Dataset, axis: str | int = 0, position=None, indices=None):
        if dataset.ndim < 1:
            raise ValueError("Lineouts require at least a 1D dataset")
        axis_i = dataset.axis_index(axis)
        if dataset.ndim == 1:
            return dataset.coordinates[0].values, dataset.data

        selectors = [slice(None)] * dataset.ndim
        if indices is not None:
            if len(indices) != dataset.ndim:
                raise ValueError("indices must have one entry per dataset dimension")
            selectors = list(indices)
        else:
            for i in range(dataset.ndim):
                if i != axis_i:
                    selectors[i] = dataset.shape[i] // 2

        if position is not None:
            fixed = [i for i in range(dataset.ndim) if i != axis_i]
            if len(fixed) != 1:
                raise ValueError("coordinate-based position requires exactly one fixed dimension for ndim > 2")
            fixed_i = fixed[0]
            coords = dataset.coordinates[fixed_i].values
            if not np.isfinite(position) or position < coords.min() or position > coords.max():
                raise ValueError(f"Lineout position {position} is outside [{coords.min()}, {coords.max()}]")
            idx = float(np.interp(position, coords, np.arange(coords.size)))
            i0, i1 = int(np.floor(idx)), min(int(np.floor(idx)) + 1, coords.size - 1)
            w = idx - i0
            s0, s1 = list(selectors), list(selectors)
            s0[fixed_i], s1[fixed_i] = i0, i1
            values = dataset.data[tuple(s0)] * (1 - w) + dataset.data[tuple(s1)] * w
        else:
            values = dataset.data[tuple(selectors)]
        return dataset.coordinates[axis_i].values, np.asarray(values)

    def along_x1(self, dataset, position=None, indices=None):
        return self.lineout(dataset, axis="x1", position=position, indices=indices)

    def along_x2(self, dataset, position=None, indices=None):
        return self.lineout(dataset, axis="x2", position=position, indices=indices)

    def along_x3(self, dataset, position=None, indices=None):
        return self.lineout(dataset, axis="x3", position=position, indices=indices)
```

---

## `scientific_visualization/analysis/roi.py`

```py
"""Region-of-interest (ROI) definitions and statistics.

Pure, GUI-independent logic per this project's architecture rule ("the
GUI must not contain scientific algorithms"): `gui/grid_tab.py` only
handles drawing the ROI shape with the mouse and displaying the results
computed here.

Scope note: this implements rectangle and ellipse ROIs with full
statistics, multiple simultaneous ROIs, JSON export, and time-evolution
across a file series (see `roi_time_series`). Polygon/freehand ROIs are
not implemented -- the shapes here cover the large majority of practical
"measure this region" use cases while keeping the mask math simple and
exactly verifiable; freehand/polygon support would need canvas-based
point collection that belongs in the GUI layer and can build on the same
`RegionOfInterest.mask()`/`roi_statistics()` functions when added.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field, asdict
from typing import Sequence

import numpy as np

from .statistics import statistics

_id_counter = itertools.count(1)


@dataclass
class RegionOfInterest:
    """A rectangle or ellipse region, defined in *physical* coordinates
    (the same units as the dataset's axes), not pixel/array indices --
    this is what makes a ROI meaningful across frames whose array
    resolution can differ but whose physical domain matches.
    """
    shape: str  # "rectangle" or "ellipse"
    x0: float
    y0: float
    x1: float
    y1: float
    label: str = ""
    id: int = field(default_factory=lambda: next(_id_counter))

    def __post_init__(self):
        if self.shape not in ("rectangle", "ellipse"):
            raise ValueError(f"shape must be 'rectangle' or 'ellipse', got {self.shape!r}")
        if self.x0 == self.x1 or self.y0 == self.y1:
            raise ValueError("ROI must have non-zero width and height")
        # Normalize so x0<x1, y0<y1 regardless of drag direction.
        if self.x0 > self.x1:
            self.x0, self.x1 = self.x1, self.x0
        if self.y0 > self.y1:
            self.y0, self.y1 = self.y1, self.y0
        if not self.label:
            self.label = f"ROI {self.id}"

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        """Physical area: exact for a rectangle, pi/4 of the bounding-box
        area for an ellipse."""
        base = self.width * self.height
        return base if self.shape == "rectangle" else base * (np.pi / 4.0)

    def mask(self, x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
        """Boolean mask of shape (len(y_coords), len(x_coords)) -- matching
        this project's `data.shape == (n_axis2, n_axis1)` convention --
        True where a grid point falls inside this ROI."""
        x_coords = np.asarray(x_coords, dtype=float)
        y_coords = np.asarray(y_coords, dtype=float)
        X, Y = np.meshgrid(x_coords, y_coords)  # shape (len(y), len(x))
        if self.shape == "rectangle":
            return (X >= self.x0) & (X <= self.x1) & (Y >= self.y0) & (Y <= self.y1)
        cx, cy = (self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0
        rx, ry = self.width / 2.0, self.height / 2.0
        return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RegionOfInterest":
        d = dict(d)
        d.pop("id", None)  # always assign a fresh id on reconstruction
        return cls(**d)


def roi_statistics(data: np.ndarray, x_coords: np.ndarray, y_coords: np.ndarray, roi: RegionOfInterest) -> dict:
    """Statistics for the portion of `data` (shape (len(y), len(x))) that
    falls inside `roi`, plus physical-coordinate-aware area/integral.

    Raises ValueError if the ROI doesn't overlap the data at all, rather
    than silently returning empty/NaN statistics.
    """
    data = np.asarray(data, dtype=float)
    x_coords = np.asarray(x_coords, dtype=float)
    y_coords = np.asarray(y_coords, dtype=float)
    if data.shape != (y_coords.size, x_coords.size):
        raise ValueError(
            f"data.shape {data.shape} does not match (len(y_coords), len(x_coords)) "
            f"= ({y_coords.size}, {x_coords.size})"
        )
    mask = roi.mask(x_coords, y_coords)
    selected = data[mask]
    finite = selected[np.isfinite(selected)]
    if finite.size == 0:
        raise ValueError(
            f"ROI '{roi.label}' ({roi.shape}, x=[{roi.x0:.6g},{roi.x1:.6g}], "
            f"y=[{roi.y0:.6g},{roi.y1:.6g}]) contains no finite data points -- "
            f"check it overlaps the plotted domain."
        )
    stats = statistics(finite, finite_only=False)
    quantiles = {f"p{p}": float(np.percentile(finite, p)) for p in (5, 25, 50, 75, 95)}

    # Area-weighted integral: each selected grid point contributes
    # value * (per-point physical cell area), approximated from the local
    # coordinate spacing so non-uniform axes are still handled reasonably.
    dx = np.gradient(x_coords) if x_coords.size > 1 else np.ones_like(x_coords)
    dy = np.gradient(y_coords) if y_coords.size > 1 else np.ones_like(y_coords)
    cell_area = np.outer(np.abs(dy), np.abs(dx))  # shape (len(y), len(x)), matches `data`
    integral = float(np.sum(np.where(mask & np.isfinite(data), data * cell_area, 0.0)))
    covered_area = float(np.sum(np.where(mask & np.isfinite(data), cell_area, 0.0)))

    return {
        "roi": roi.to_dict(),
        "n_points": int(finite.size),
        **stats,
        **quantiles,
        "roi_area_nominal": roi.area,
        "roi_area_covered": covered_area,
        "integral": integral,
    }


def roi_time_series(
    files: Sequence[str],
    loader,
    roi: RegionOfInterest,
    progress_callback=None,
) -> list[dict]:
    """Evaluate `roi_statistics` for the same ROI across a series of grid
    files (e.g. every frame of a simulation run), returning one result
    dict per file plus its source path/time/iteration -- the "time
    evolution of ROI statistics" capability. `loader(path)` must return an
    object with `.data`, `.axes[0].values()`, `.axes[1].values()`,
    `.time`, `.time_units`, `.iteration` (i.e. a loaded GridFile).

    Files that fail to load or whose ROI doesn't overlap them are skipped
    with a recorded error rather than aborting the whole series, since a
    single bad/empty frame shouldn't discard every other frame's result.
    """
    results = []
    total = len(files)
    for i, path in enumerate(files, start=1):
        if progress_callback is not None:
            progress_callback(i, total, path)
        try:
            grid = loader(path)
            x = np.asarray(grid.axes[0].values(), dtype=float)
            y = np.asarray(grid.axes[1].values(), dtype=float)
            stats = roi_statistics(grid.data, x, y, roi)
            stats["source_file"] = path
            stats["time"] = float(grid.time)
            stats["time_units"] = grid.time_units
            stats["iteration"] = int(grid.iteration)
        except Exception as exc:
            stats = {"source_file": path, "error": str(exc)}
        results.append(stats)
    return results


def export_roi_results(results, path: str) -> str:
    """Write ROI statistics (a single roi_statistics() dict, or a list from
    roi_time_series()) to a JSON file. Returns the path written."""
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=float)
    return path
```

---

## `scientific_visualization/analysis/series.py`

```py
from __future__ import annotations

from pathlib import Path
import numpy as np

from ..io.grid import GridFile
from .spectral import temporal_spectrum, k_omega


class SimulationSeries:
    """Discover and analyze many Simulation grid frames without treating one frame as the simulation."""
    def __init__(self, files, quantity=None):
        self.files = [str(Path(f)) for f in files]
        self.quantity = quantity
        self._frames = []

    @classmethod
    def from_folder(cls, folder, quantity=None):
        files = sorted(str(p) for p in Path(folder).iterdir() if p.suffix.lower() in {".h5", ".hdf5"})
        if not files:
            raise ValueError(f"No HDF5 files found in '{folder}'")
        return cls(files, quantity=quantity)

    def discover(self):
        frames = []
        for path in self.files:
            try:
                info = GridFile.info(path)
                if self.quantity and info.dataset_name != self.quantity and info.name != self.quantity and info.label != self.quantity:
                    continue
                frames.append((path, info.time, info.iteration, info.dataset_name, info.shape, info.units, info.label))
            except Exception:
                continue
        frames.sort(key=lambda x: (x[1], x[2], x[0]))
        if not frames:
            raise ValueError("No compatible Simulation grid frames were found for the selected quantity")
        self._frames = frames
        if self.quantity is None:
            self.quantity = frames[0][3]
        return frames

    @property
    def frames(self):
        return self._frames or self.discover()

    def load(self, index):
        path = self.frames[index][0]
        return GridFile.load(path).to_dataset()

    def temporal_reduction(self, reduction="mean"):
        times, iterations, values = [], [], []
        for idx, (path, time, iteration, *_rest) in enumerate(self.frames):
            ds = self.load(idx)
            data = np.asarray(ds.data, dtype=float)
            finite = data[np.isfinite(data)]
            if not finite.size:
                value = np.nan
            elif reduction == "mean": value = np.mean(finite)
            elif reduction == "sum": value = np.sum(finite)
            elif reduction == "max": value = np.max(finite)
            elif reduction == "min": value = np.min(finite)
            elif reduction == "rms": value = np.sqrt(np.mean(finite**2))
            else: raise ValueError(f"Unsupported reduction '{reduction}'")
            times.append(time); iterations.append(iteration); values.append(value)
        return np.asarray(times), np.asarray(iterations), np.asarray(values)

    def temporal_frequency(self, reduction="mean"):
        times, iterations, values = self.temporal_reduction(reduction)
        result = temporal_spectrum(values, times)
        return times, iterations, values, result

    def k_omega(self, axis="x1", *, max_frames=None):
        frames = self.frames[:max_frames] if max_frames else self.frames
        stack = np.stack([np.asarray(self.load(i).data, dtype=float) for i in range(len(frames))], axis=0)
        reference = self.load(0)
        spatial_index = reference.axis_index(axis)
        # Dataset data axes are physical order, so stack is (time, x1, x2, ...).
        x = reference.coordinates[spatial_index].values
        times = np.asarray([f[1] for f in frames], dtype=float)
        if stack.ndim > 2:
            other_axes = tuple(i for i in range(1, stack.ndim) if i != spatial_index + 1)
            if other_axes:
                stack = np.mean(stack, axis=other_axes)
            spatial_index = 1
        omega, k, power = k_omega(stack, x, times, spatial_axis=spatial_index, time_axis=0)
        return omega, k, power
```

---

## `scientific_visualization/analysis/smoothing.py`

```py
from __future__ import annotations

from pathlib import Path
import numpy as np
from ..io.simulation.grid import GridFile

try:
    from scipy.ndimage import gaussian_filter, uniform_filter1d
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False


def smooth_1d(y, method="None", window=5):
    y = np.asarray(y)
    if method in (None, "None") or window <= 1:
        return y
    if method == "Moving average":
        if _HAVE_SCIPY: return uniform_filter1d(y, size=int(window), mode="nearest")
        return np.convolve(y, np.ones(int(window))/int(window), mode="same")
    if method == "Gaussian":
        if _HAVE_SCIPY: return gaussian_filter(y, sigma=float(window)/2.0, mode="nearest")
        sigma=max(float(window)/2.0, 1e-6); radius=max(int(3*sigma),1); x=np.arange(-radius,radius+1); k=np.exp(-0.5*(x/sigma)**2); k/=k.sum(); return np.convolve(y,k,mode="same")
    raise ValueError(f"Unknown smoothing method: {method}")


def smooth_2d(data, method="None", window=5):
    data=np.asarray(data)
    if method in (None,"None") or window<=1: return data
    if method == "Moving average":
        if _HAVE_SCIPY: from scipy.ndimage import uniform_filter; return uniform_filter(data,size=int(window),mode="nearest")
        k=np.ones((int(window),int(window)))/(window*window); pad=int(window)//2; p=np.pad(data,pad,mode="edge"); out=np.empty_like(data,dtype=float)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]): out[i,j]=np.sum(p[i:i+window,j:j+window]*k)
        return out
    if method == "Gaussian":
        if _HAVE_SCIPY: return gaussian_filter(data,sigma=float(window)/2.0,mode="nearest")
        return data
    raise ValueError(f"Unknown smoothing method: {method}")


def reduce_grid_series(files, reduction="mean", smoothing=None):
    reducers={"mean":np.mean,"sum":np.sum,"max":np.max,"min":np.min,"rms":lambda a:np.sqrt(np.mean(np.asarray(a)**2)),"integral":lambda a:np.sum(np.asarray(a))}
    if reduction not in reducers: raise ValueError(f"Unknown reduction: {reduction}")
    times=[]; iters=[]; vals=[]; meta={}
    for path in sorted(files):
        g=GridFile.load(path); times.append(g.time); iters.append(g.iteration); vals.append(float(reducers[reduction](g.data))); meta.update(label=g.label or g.name,units=g.units,ndim=g.ndim)
    vals=np.asarray(vals)
    if smoothing: vals=smooth_1d(vals,smoothing.get("method","None"),smoothing.get("window",5))
    return np.asarray(times),np.asarray(iters),vals,meta
```

---

## `scientific_visualization/analysis/spectral.py`

```py
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SpectrumResult:
    frequencies: np.ndarray
    power: np.ndarray
    amplitude: np.ndarray
    axis: str = ""
    units: str = ""


def _uniform_spacing(values, *, name="coordinate", rtol=1e-6, atol=1e-12):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or x.size < 2:
        raise ValueError(f"{name} needs at least two coordinates for spectral analysis")
    d = np.diff(x)
    if not np.all(np.isfinite(d)) or np.any(d == 0):
        raise ValueError(f"{name} contains invalid or repeated coordinates")
    ref = float(np.mean(d))
    if not np.allclose(d, ref, rtol=rtol, atol=atol):
        raise ValueError(f"{name} is non-uniform; FFT requires uniform spacing. Resample explicitly first.")
    return ref


def fft_1d(data, coordinate, axis=-1, *, use_rfft=True):
    spacing = _uniform_spacing(coordinate)
    arr = np.asarray(data)
    if use_rfft:
        spec = np.fft.rfft(arr, axis=axis)
        freq = np.fft.rfftfreq(arr.shape[axis], d=abs(spacing))
    else:
        spec = np.fft.fft(arr, axis=axis)
        freq = np.fft.fftfreq(arr.shape[axis], d=abs(spacing))
    amp = np.abs(spec)
    power = amp ** 2
    return SpectrumResult(freq, power, amp)


def fft_nd(data, coordinates, axes=None, *, use_rfftn=True):
    arr = np.asarray(data)
    if axes is None:
        axes = tuple(range(arr.ndim))
    axes = tuple(axes)
    spacings = [_uniform_spacing(coordinates[i], name=f"axis {i}") for i in axes]
    if use_rfftn:
        spec = np.fft.rfftn(arr, axes=axes)
        freq_axes = [np.fft.fftfreq(arr.shape[i], d=abs(spacings[j])) for j, i in enumerate(axes[:-1])]
        freq_axes.append(np.fft.rfftfreq(arr.shape[axes[-1]], d=abs(spacings[-1])))
    else:
        spec = np.fft.fftn(arr, axes=axes)
        freq_axes = [np.fft.fftfreq(arr.shape[i], d=abs(spacings[j])) for j, i in enumerate(axes)]
    return tuple(freq_axes), np.abs(spec), np.abs(spec) ** 2


def power_spectrum_1d(data, coordinate, axis=-1):
    return fft_1d(data, coordinate, axis=axis)


def wavenumber_spectrum(data, coordinate, axis=-1):
    result = fft_1d(data, coordinate, axis=axis)
    k = 2 * np.pi * result.frequencies
    return SpectrumResult(k, result.power, result.amplitude, axis="k")


def temporal_spectrum(values, times, axis=0):
    return fft_1d(values, times, axis=axis)


def k_omega(values, x, times, spatial_axis=-1, time_axis=0):
    arr = np.asarray(values)
    dt = _uniform_spacing(times, name="time")
    dx = _uniform_spacing(x, name="spatial coordinate")
    if time_axis != 0:
        arr = np.moveaxis(arr, time_axis, 0)
    if spatial_axis != arr.ndim - 1:
        spatial_axis = spatial_axis if spatial_axis >= 0 else arr.ndim + spatial_axis
        arr = np.moveaxis(arr, spatial_axis, -1)
    spec = np.fft.rfft2(arr, axes=(0, arr.ndim - 1))
    omega = 2 * np.pi * np.fft.fftfreq(arr.shape[0], d=abs(dt))
    k = 2 * np.pi * np.fft.rfftfreq(arr.shape[-1], d=abs(dx))
    return omega, k, np.abs(spec) ** 2
```

---

## `scientific_visualization/analysis/statistics.py`

```py
from __future__ import annotations

import numpy as np


def statistics(data, finite_only=True):
    arr = np.asarray(data)
    if finite_only:
        arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("No finite samples available")
    return {"min": float(np.min(arr)), "max": float(np.max(arr)), "mean": float(np.mean(arr)), "std": float(np.std(arr)), "rms": float(np.sqrt(np.mean(arr**2))), "count": int(arr.size)}
```

---

## `scientific_visualization/analysis/time_series.py`

```py
from __future__ import annotations

from pathlib import Path
import numpy as np

from ..io.simulation import SimulationReader


class TimeSeriesAnalyzer:
    def __init__(self, reader=None):
        self.reader = reader or SimulationReader()

    def track_point(self, files, quantity, positions=None):
        times, values = [], []
        for path in files:
            ds = self.reader.load(path, quantity=quantity)
            if ds.ndim == 0:
                value = float(ds.data)
            elif positions is None:
                value = float(np.mean(ds.data))
            else:
                idx = []
                for i, p in enumerate(positions):
                    c = ds.coordinates[i].values
                    idx.append(int(np.argmin(np.abs(c - p))))
                value = float(ds.data[tuple(idx)])
            times.append(ds.time if ds.time is not None else len(times))
            values.append(value)
        return np.asarray(times), np.asarray(values)

    def reduce(self, files, quantity, reduction="mean"):
        times, vals = [], []
        reducers = {"mean": np.mean, "sum": np.sum, "max": np.max, "min": np.min, "rms": lambda a: np.sqrt(np.mean(np.asarray(a)**2))}
        if reduction not in reducers:
            raise ValueError(f"Unsupported reduction '{reduction}'")
        for path in files:
            ds = self.reader.load(path, quantity=quantity)
            times.append(ds.time if ds.time is not None else len(times))
            vals.append(float(reducers[reduction](ds.data)))
        return np.asarray(times), np.asarray(vals)


def reduce_grid_series(files, reduction="mean", smoothing=None, quantity=None):
    """Compatibility wrapper for Simulation grid-field time-series reductions."""
    from ..io.grid import GridFile
    allowed = {"mean", "sum", "integral", "max", "min", "rms"}
    if reduction not in allowed:
        raise ValueError(f"unknown reduction '{reduction}'. Choose from {sorted(allowed)}")
    times, iters, values = [], [], []
    label = units = ""
    selected_name = selected_shape = None
    for fname in files:
        try:
            gf = GridFile.load(fname)
        except Exception:
            continue
        if quantity and gf.dataset_name != quantity and gf.name != quantity and gf.label != quantity:
            continue
        if selected_name is None:
            selected_name, selected_shape = gf.dataset_name, gf.shape
        if gf.dataset_name != selected_name or gf.shape != selected_shape:
            continue
        data = np.asarray(gf.data)
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            value = np.nan
        elif reduction == "mean":
            value = np.mean(finite)
        elif reduction == "sum":
            value = np.sum(finite)
        elif reduction == "integral":
            # Integrate using the actual physical cell-centre coordinates.
            # Do not assume unit or uniform spacing.
            arr = np.asarray(gf.data, dtype=float)
            for physical_axis in range(gf.ndim):
                np_axis = gf.ndim - 1 - physical_axis
                coords = gf.axes[physical_axis].values()
                arr = np.trapezoid(arr, coords, axis=np_axis)
            value = float(arr)
        elif reduction == "max":
            value = np.max(finite)
        elif reduction == "min":
            value = np.min(finite)
        else:
            value = np.sqrt(np.mean(finite ** 2))
        times.append(float(gf.time)); iters.append(int(gf.iteration)); values.append(float(value))
        label, units = gf.label, gf.units
    if not values:
        raise ValueError("No compatible grid frames were found for the selected quantity.")
    order = np.argsort(times)
    times, iters, values = np.asarray(times)[order], np.asarray(iters)[order], np.asarray(values)[order]
    if smoothing and smoothing.get("method") not in (None, "None"):
        from .smoothing import smooth_1d
        values = smooth_1d(values, smoothing["method"], smoothing.get("window", 5))
    return times, iters, values, {"label": label, "units": units, "reduction": reduction, "quantity": selected_name}
```

---

## `scientific_visualization/analysis.py`

```py
"""
Analysis helpers: smoothing and spatial-reduction-over-time, used by the
Fields/Grid tab's advanced options.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

try:
    from scipy.ndimage import gaussian_filter, uniform_filter1d
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False


def smooth_1d(y: np.ndarray, method: str = "None", window: int = 5) -> np.ndarray:
    """Smooth a 1D array. `method` is 'None', 'Moving average', or 'Gaussian'.
    `window` is the moving-average box size (points) or the Gaussian sigma
    (points), respectively."""
    if method in (None, "None") or window <= 1:
        return y
    if method == "Moving average":
        if _HAVE_SCIPY:
            return uniform_filter1d(y, size=int(window), mode="nearest")
        kernel = np.ones(int(window)) / int(window)
        return np.convolve(y, kernel, mode="same")
    if method == "Gaussian":
        if _HAVE_SCIPY:
            return gaussian_filter(y, sigma=float(window) / 2.0, mode="nearest")
        # crude fallback gaussian kernel
        sigma = max(float(window) / 2.0, 1e-6)
        radius = max(int(3 * sigma), 1)
        x = np.arange(-radius, radius + 1)
        kernel = np.exp(-0.5 * (x / sigma) ** 2)
        kernel /= kernel.sum()
        return np.convolve(y, kernel, mode="same")
    return y


def smooth_2d(data: np.ndarray, method: str = "None", window: int = 3) -> np.ndarray:
    """Smooth a 2D array. `method` is 'None', 'Moving average', or 'Gaussian'."""
    if method in (None, "None") or window <= 1:
        return data
    if not _HAVE_SCIPY:
        return data  # 2D smoothing without scipy is skipped rather than done poorly
    if method == "Moving average":
        from scipy.ndimage import uniform_filter
        return uniform_filter(data, size=int(window), mode="nearest")
    if method == "Gaussian":
        return gaussian_filter(data, sigma=float(window) / 2.0, mode="nearest")
    return data


def reduce_grid_series(files: list, reduction: str = "mean", smoothing: Optional[dict] = None,
                       quantity: Optional[str] = None, average_direction: str | None = None):
    """Reduce one compatible grid quantity over space for each time step.

    ``average_direction`` optionally applies the directional-average operation
    before the scalar temporal reduction. The original files are never modified.
    """
    from .io.grid import GridFile
    from .analysis.derived import parse_average_direction

    allowed = {"mean", "sum", "integral", "max", "min", "rms"}
    if reduction not in allowed:
        raise ValueError(f"unknown reduction '{reduction}'. Choose from {sorted(allowed)}")

    direction = parse_average_direction(average_direction) if average_direction else None
    times, iters, values = [], [], []
    label, units, selected_name, selected_shape = "", "", None, None
    errors = []
    for fname in files:
        try:
            gf = GridFile.load(fname)
        except Exception as exc:
            errors.append(f"{fname}: {exc}")
            continue
        if quantity and gf.dataset_name != quantity and gf.name != quantity and gf.label != quantity:
            continue
        if selected_name is None:
            selected_name, selected_shape = gf.dataset_name, gf.shape
        if gf.dataset_name != selected_name or gf.shape != selected_shape:
            continue
        data = np.asarray(gf.data, dtype=float)
        # Convert once to Dataset physical axis ordering, then average over the
        # requested axes. np.mean/max/etc. are already implemented in optimized
        # compiled NumPy loops, so moving these reductions to C++ would add
        # conversion overhead without a meaningful benefit.
        if direction:
            ds = gf.to_dataset()
            axis_indices = tuple(ds.axis_index("x" + str(ord(i) - ord("x") + 1)) for i in direction)
            data = np.mean(ds.data, axis=axis_indices)
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            values.append(np.nan)
        elif reduction == "mean":
            values.append(float(np.mean(finite)))
        elif reduction == "sum":
            values.append(float(np.sum(finite)))
        elif reduction == "integral":
            cell = 1.0
            for ax in gf.axes:
                if ax.n > 1:
                    cell *= abs((ax.max - ax.min) / ax.n)
            values.append(float(np.sum(finite) * cell))
        elif reduction == "max":
            values.append(float(np.max(finite)))
        elif reduction == "min":
            values.append(float(np.min(finite)))
        else:
            values.append(float(np.sqrt(np.mean(finite ** 2))))
        times.append(gf.time)
        iters.append(gf.iteration)
        label, units = gf.label, gf.units

    if not values:
        detail = f" Skipped {len(errors)} unreadable file(s)." if errors else ""
        raise ValueError("No compatible grid frames were found for the selected quantity." + detail)

    order = np.argsort(times)
    times = np.asarray(times)[order]
    iters = np.asarray(iters)[order]
    values = np.asarray(values)[order]
    if smoothing and smoothing.get("method") not in (None, "None"):
        values = smooth_1d(values, smoothing["method"], smoothing.get("window", 5))
    return times, iters, values, {"label": label, "units": units, "reduction": reduction,
                                  "quantity": selected_name, "skipped_files": errors,
                                  "average_direction": direction}
```

---

## `scientific_visualization/app.py`

```py
import sys

from PyQt5.QtWidgets import QApplication

from . import style
from .gui.main_window import MainWindow


def main():
    style.base_rcparams()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```

---

## `scientific_visualization/core/__init__.py`

```py
from .data import CoordinateAxis, Dataset
from .configuration import RenderingConfig

__all__ = ["CoordinateAxis", "Dataset", "RenderingConfig"]
```

---

## `scientific_visualization/core/configuration/__init__.py`

```py
from .rendering import RenderingConfig

__all__ = ["RenderingConfig"]
```

---

## `scientific_visualization/core/configuration/rendering.py`

```py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RenderingConfig:
    colormap: str = "viridis"
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    normalization: str = "linear"
    symmetric_limits: bool = False
    show_colorbar: bool = True
    opacity: float = 1.0
    aspect: str = "auto"
    interpolation: str = "nearest"
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    zlabel: Optional[str] = None
    figure_width: float = 7.0
    figure_height: float = 5.0
    dpi: int = 300
    background: Optional[str] = None
    transparent: bool = False
    font_family: str = "DejaVu Sans"
    font_size: float = 10.0
    bbox_inches: str = "tight"

    # Colorbar/scalar-bar placement (2D Matplotlib view and 3D PyVista view).
    # `colorbar_position` is one of "right", "left", "top", "bottom".
    colorbar_position: str = "right"
    # Draws a visible border (and, in the 3D view, an opaque background) box
    # around the colorbar/scalar bar instead of a borderless overlay.
    colorbar_box: bool = False
    # 3D view only: PyVista supports natively dragging/resizing a scalar bar
    # with the mouse at runtime when this is True.
    colorbar_interactive: bool = True
    colorbar_width: Optional[float] = None
    colorbar_height: Optional[float] = None
    colorbar_label_position: str = "auto"
    colorbar_label_rotation: float = 90.0
    colorbar_label_pad: float = 8.0
    contour_filled: bool = False
    hillshade: bool = False
    antialiasing: bool = True
    lighting: bool = True
    eye_dome_lighting: bool = False
    smooth_shading: bool = True
    show_edges: bool = False
    edge_color: str = "black"
    render_decimation: float = 1.0
    depth_peeling: bool = False
    ssao: bool = False
    stereo: bool = False
    hidden_line_removal: bool = False

    COLORBAR_POSITIONS = ("right", "left", "top", "bottom")

    def validate(self):
        if self.normalization not in {"linear", "log"}:
            raise ValueError("normalization must be 'linear' or 'log'")
        if self.vmin is not None and self.vmax is not None and self.vmin >= self.vmax:
            raise ValueError("vmin must be smaller than vmax")
        if self.normalization == "log":
            for value in (self.vmin, self.vmax):
                if value is not None and value <= 0:
                    raise ValueError("log normalization requires positive vmin/vmax")
        if not 0 < self.opacity <= 1:
            raise ValueError("opacity must be in (0, 1]")
        if self.colorbar_position not in self.COLORBAR_POSITIONS:
            raise ValueError(f"colorbar_position must be one of {self.COLORBAR_POSITIONS}")
        for name, value in (("colorbar_width", self.colorbar_width), ("colorbar_height", self.colorbar_height)):
            if value is not None and not 0 < value <= 1:
                raise ValueError(f"{name} must be in (0, 1] when specified")
        if self.colorbar_label_position not in {"auto", "left", "right", "top", "bottom"}:
            raise ValueError("invalid colorbar_label_position")
        if not -360 <= self.colorbar_label_rotation <= 360:
            raise ValueError("colorbar_label_rotation must be between -360 and 360 degrees")
        if self.colorbar_label_pad < 0:
            raise ValueError("colorbar_label_pad must be non-negative")
        if not 0 < self.render_decimation <= 1:
            raise ValueError("render_decimation must be in (0, 1]")
```

---

## `scientific_visualization/core/coordinates/__init__.py`

```py
from .grid import coordinate_centers, coordinate_edges

__all__ = ["coordinate_centers", "coordinate_edges"]
```

---

## `scientific_visualization/core/coordinates/grid.py`

```py
from __future__ import annotations

import numpy as np


def coordinate_centers(vmin: float, vmax: float, n: int) -> np.ndarray:
    if n <= 0:
        return np.empty(0, dtype=float)
    return np.linspace(float(vmin), float(vmax), int(n), endpoint=False) + (vmax - vmin) / (2 * n)


def coordinate_edges(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    if values.size == 1:
        d = 0.5
        return np.array([values[0] - d, values[0] + d])
    mid = 0.5 * (values[:-1] + values[1:])
    return np.concatenate(([values[0] - (mid[0] - values[0])], mid, [values[-1] + (values[-1] - mid[-1])]))
```

---

## `scientific_visualization/core/data/__init__.py`

```py
from .model import CoordinateAxis, Dataset

__all__ = ["CoordinateAxis", "Dataset"]
```

---

## `scientific_visualization/core/data/model.py`

```py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import numpy as np


@dataclass(frozen=True)
class CoordinateAxis:
    name: str
    values: np.ndarray
    units: str = ""
    label: str = ""

    def __post_init__(self):
        values = np.asarray(self.values)
        if values.ndim != 1:
            raise ValueError(f"Coordinate axis '{self.name}' must be one-dimensional")
        object.__setattr__(self, "values", values)

    @property
    def size(self) -> int:
        return int(self.values.size)

    @property
    def is_uniform(self) -> bool:
        """True if consecutive coordinate values are evenly spaced.

        Physics operators may only use the fast, OpenMP-parallelized native
        backend (which assumes a constant grid spacing `h`) when every axis
        of a Dataset reports `is_uniform`; otherwise they must fall back to
        the `np.gradient`-based implementation, which handles non-uniform
        spacing correctly. See physics/native_backend.py.
        """
        if self.values.size < 3:
            return True
        diffs = np.diff(self.values)
        if diffs.size == 0:
            return True
        scale = max(float(np.max(np.abs(diffs))), 1e-300)
        return bool(np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-9 * scale))

    @property
    def spacing(self) -> float:
        """Grid spacing for a uniform axis. Raises if the axis isn't uniform
        (check `is_uniform` first) or has fewer than 2 points."""
        if self.values.size < 2:
            raise ValueError(f"Coordinate axis '{self.name}' needs at least 2 points to have a spacing")
        if not self.is_uniform:
            raise ValueError(f"Coordinate axis '{self.name}' is not uniformly spaced")
        return float(self.values[1] - self.values[0])


@dataclass
class Dataset:
    """Common scientific dataset abstraction shared by I/O, analysis, and renderers.

    The array is intentionally stored by reference. Renderers and analyses should slice
    or derive views instead of copying the source data unless a copy is required.
    """

    name: str
    data: np.ndarray
    axes: tuple[str, ...]
    coordinates: tuple[CoordinateAxis, ...] = ()
    units: str = ""
    time: Optional[float] = None
    time_units: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    simulation_metadata: Mapping[str, Any] = field(default_factory=dict)
    components: Mapping[str, "Dataset"] = field(default_factory=dict)
    derived_from: tuple[str, ...] = ()

    def __post_init__(self):
        self.data = np.asarray(self.data)
        if self.data.ndim != len(self.axes):
            raise ValueError(f"Dataset '{self.name}' has {self.data.ndim} dimensions but {len(self.axes)} axes")
        if self.coordinates and len(self.coordinates) != self.data.ndim:
            raise ValueError("Number of coordinates must match data dimensionality")
        if self.coordinates:
            for i, coord in enumerate(self.coordinates):
                if coord.size != self.data.shape[i]:
                    # HDF5/Simulation readers may expose numpy dimensions in reverse physical order.
                    # Such datasets should be normalized before constructing Dataset.
                    raise ValueError(f"Coordinate '{coord.name}' length {coord.size} does not match axis {i} size {self.data.shape[i]}")

    @property
    def ndim(self) -> int:
        return self.data.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.data.shape)

    @property
    def is_scalar(self) -> bool:
        return not self.components and self.ndim >= 0

    @property
    def is_vector(self) -> bool:
        return bool(self.components)

    def axis_index(self, axis: str | int) -> int:
        if isinstance(axis, int):
            if not 0 <= axis < self.ndim:
                raise IndexError(axis)
            return axis
        key = axis.lower()
        aliases = {f"x{i+1}": i for i in range(self.ndim)}
        aliases.update({name.lower(): i for i, name in enumerate(self.axes)})
        if key not in aliases:
            raise KeyError(f"Unknown axis '{axis}'")
        return aliases[key]

    def axis(self, axis: str | int) -> CoordinateAxis:
        return self.coordinates[self.axis_index(axis)]

    def summary(self) -> str:
        src = Path(self.source).name if self.source else "in-memory"
        return f"{self.name}: shape={self.shape}, axes={self.axes}, units={self.units!r}, source={src}"
```

---

## `scientific_visualization/core/data/service.py`

```py
from __future__ import annotations

from pathlib import Path



class DataService:
    """GUI-independent application service for browsing and loading scientific data."""

    def __init__(self, reader=None):
        from ...io.simulation import SimulationReader
        self.reader = reader or SimulationReader()

    def discover(self, path: str | Path):
        return self.reader.discover(path)

    def load(self, path: str | Path, quantity: str | None = None):
        return self.reader.load(path, quantity=quantity)

    def generic_discover(self, path: str | Path):
        from ...io.hdf5.generic import discover_hdf5_datasets
        return discover_hdf5_datasets(path)
```

---

## `scientific_visualization/data_plotter/__init__.py`

```py
"""Reusable scientific data plotting primitives and the Phase 1 Qt workflow."""

from .model import DatasetTable
from .parser import Delimiter, ParseResult, parse_text_file
from .renderer import DataPlotRenderer
from .transform import TransformPipeline, apply_transforms

__all__ = [
    "DatasetTable", "Delimiter", "ParseResult", "parse_text_file",
    "DataPlotRenderer", "TransformPipeline", "apply_transforms",
]
```

---

## `scientific_visualization/data_plotter/model.py`

```py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class DatasetTable:
    """In-memory numeric table used by the plotting layer.

    The original file is never modified. ``values`` is owned by this object
    and may therefore be copied/transformed by downstream operations.
    """

    path: str
    columns: list[str]
    values: np.ndarray
    delimiter: str
    has_header: bool
    skipped_comments: int = 0
    skipped_rows: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def row_count(self) -> int:
        return int(self.values.shape[0])

    @property
    def column_count(self) -> int:
        return int(self.values.shape[1])

    def column_values(self, index: int) -> np.ndarray:
        if index < 0 or index >= self.column_count:
            raise IndexError(f"column index {index} is out of range")
        return self.values[:, index]

    def statistics(self, index: int) -> dict[str, float]:
        values = self.column_values(index)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return {"count": 0, "min": np.nan, "max": np.nan, "mean": np.nan, "std": np.nan}
        return {
            "count": int(finite.size),
            "min": float(np.min(finite)),
            "max": float(np.max(finite)),
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite)),
        }

    def copy_values(self) -> np.ndarray:
        return self.values.copy()
```

---

## `scientific_visualization/data_plotter/parser.py`

```py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

import numpy as np


class Delimiter(str, Enum):
    AUTO = "Automatic"
    COMMA = "Comma (,)"
    TAB = "Tab"
    SPACE = "Space"
    SEMICOLON = "Semicolon (;)"

    @property
    def char(self) -> str | None:
        return {
            Delimiter.AUTO: None,
            Delimiter.COMMA: ",",
            Delimiter.TAB: "\t",
            Delimiter.SPACE: None,
            Delimiter.SEMICOLON: ";",
        }[self]


@dataclass
class ParseResult:
    path: str
    columns: list[str]
    values: np.ndarray
    delimiter: str
    has_header: bool
    skipped_comments: int
    skipped_rows: int


def _data_lines(text: str) -> tuple[list[str], int]:
    lines, comments = [], 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments += 1
            continue
        lines.append(line)
    return lines, comments


def _split(line: str, delimiter: str | None) -> list[str]:
    if delimiter == " ":
        return re.split(r"\s+", line.strip())
    if delimiter is None:
        return re.split(r"\s+", line.strip())
    return [part.strip() for part in line.split(delimiter)]


def detect_delimiter(lines: list[str]) -> str:
    candidates = [",", "\t", ";", " "]
    sample = lines[: min(8, len(lines))]
    scores = {}
    for candidate in candidates:
        counts = [len(_split(line, candidate)) for line in sample]
        if counts and min(counts) >= 2 and len(set(counts)) == 1:
            scores[candidate] = (counts[0], -sum(len(x) for x in sample))
    if scores:
        return max(scores, key=scores.get)
    return " "


def _is_numeric_row(parts: list[str]) -> bool:
    try:
        [float(x) for x in parts]
        return True
    except ValueError:
        return False


def parse_text_file(path: str | Path, delimiter: Delimiter = Delimiter.AUTO) -> ParseResult:
    path = Path(path)
    if path.suffix.lower() not in {".csv", ".txt"}:
        raise ValueError(f"Unsupported data file type: {path.suffix or '<none>'}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    except OSError as exc:
        raise ValueError(f"Could not read '{path}': {exc}") from exc

    lines, comments = _data_lines(text)
    if not lines:
        raise ValueError(f"'{path.name}' is empty or contains only comments")

    detected = delimiter.char if delimiter != Delimiter.AUTO else detect_delimiter(lines)
    rows = [_split(line, detected) for line in lines]
    width = max((len(r) for r in rows), default=0)
    if width < 1:
        raise ValueError(f"Could not detect columns in '{path.name}'")

    # A textual first row is treated as a header when the next row is numeric
    # and has the same number of fields. Otherwise generic column names are used.
    has_header = False
    first = rows[0]
    if len(rows) > 1 and not _is_numeric_row(first):
        if len(rows[1]) == len(first) and any(not re.fullmatch(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", x) for x in first):
            has_header = True

    if has_header:
        columns = [x or f"Column {i+1}" for i, x in enumerate(first)]
        data_rows = rows[1:]
    else:
        columns = [f"Column {i+1}" for i in range(width)]
        data_rows = rows

    parsed: list[list[float]] = []
    skipped = 0
    for row in data_rows:
        if len(row) != len(columns):
            skipped += 1
            continue
        try:
            values = [float(x) for x in row]
        except ValueError:
            # Allow missing/invalid entries while keeping the row shape.
            values = []
            for x in row:
                try:
                    values.append(float(x))
                except ValueError:
                    values.append(np.nan)
        parsed.append(values)

    if not parsed:
        raise ValueError(f"No numeric data rows could be read from '{path.name}'")
    array = np.asarray(parsed, dtype=float)
    if array.ndim != 2 or array.shape[1] == 0:
        raise ValueError(f"No numeric columns could be read from '{path.name}'")
    return ParseResult(str(path), columns, array, detected, has_header, comments, skipped)
```

---

## `scientific_visualization/data_plotter/renderer.py`

```py
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

    DEFAULT_COLORS = [
        "#0072B2", "#D55E00", "#009E73", "#CC79A7",
        "#E69F00", "#56B4E9", "#F0E442", "#000000",
    ]

    def render_histogram(
        self,
        ax,
        series: list[RenderSeries],
        *,
        bins: int = 30,
        normalization: str = "Count",
        xlabel: str = "Value",
        ylabel: str = "Count",
        legend: bool = True,
    ):
        ax.clear()
        density = normalization == "Density"
        weights_mode = normalization == "Probability"
        for item in series:
            values = item.y[np.isfinite(item.y)]
            if values.size == 0:
                continue
            weights = np.ones(values.size) / values.size if weights_mode else None
            ax.hist(values, bins=bins, density=density, weights=weights, alpha=0.45,
                    label=item.label, color=item.color, edgecolor=item.color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel if normalization != "Probability" else "Probability")
        if legend and any(s.enabled for s in series):
            ax.legend()
        ax.grid(True, alpha=0.25)
        return ax

    def render_xy(
        self,
        ax,
        series: list[RenderSeries],
        *,
        plot_type: str = "Line",
        xlabel: str = "X",
        ylabel: str = "Y",
        title: str = "",
        legend: bool = True,
        xscale: str = "linear",
        yscale: str = "linear",
    ):
        ax.clear()
        for item in series:
            if not item.enabled:
                continue
            kwargs = dict(label=item.label, color=item.color, linewidth=item.line_width,
                          markersize=item.marker_size)
            if plot_type in {"Line", "Line + Scatter"}:
                ax.plot(item.x, item.y, linestyle=item.line_style, **kwargs)
            if plot_type in {"Scatter", "Line + Scatter"}:
                ax.scatter(item.x, item.y, marker=self._marker(item.marker), color=item.color,
                           s=max(4.0, item.marker_size ** 2), label=None if plot_type == "Line + Scatter" else item.label)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        if legend and any(s.enabled for s in series):
            ax.legend()
        ax.grid(True, alpha=0.25)
        return ax

    @staticmethod
    def _marker(marker: str) -> str:
        return {"None": "", "Circle": "o", "Square": "s", "Triangle": "^",
                "Diamond": "D", "Cross": "x"}.get(marker, marker)
```

---

## `scientific_visualization/data_plotter/transform.py`

```py
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class TransformPipeline:
    """Small, serializable transformation definition for plotted X/Y arrays."""

    x_scale: float = 1.0
    y_scale: float = 1.0
    x_offset: float = 0.0
    y_offset: float = 0.0
    normalize_y: str | None = None  # None, "max", "first"
    subtract_first_y: bool = False
    y_operation: str | None = None  # None, abs, square, sqrt, log
    remove_nonfinite: bool = True
    metadata: dict = field(default_factory=dict)

    def apply(self, x, y) -> tuple[np.ndarray, np.ndarray]:
        return apply_transforms(x, y, self)


def apply_transforms(x, y, pipeline: TransformPipeline | None = None):
    p = pipeline or TransformPipeline()
    xx = np.asarray(x, dtype=float).copy()
    yy = np.asarray(y, dtype=float).copy()

    xx = xx * p.x_scale + p.x_offset
    yy = yy * p.y_scale + p.y_offset

    if p.subtract_first_y and yy.size:
        finite = yy[np.isfinite(yy)]
        if finite.size:
            yy = yy - finite[0]
    if p.normalize_y:
        finite = yy[np.isfinite(yy)]
        if finite.size:
            if p.normalize_y == "max":
                denom = np.max(np.abs(finite))
            elif p.normalize_y == "first":
                denom = finite[0]
            else:
                raise ValueError(f"Unknown Y normalization: {p.normalize_y}")
            if denom == 0:
                raise ValueError("Cannot normalize Y because the normalization value is zero")
            yy = yy / denom

    operations = {
        None: lambda a: a,
        "abs": np.abs,
        "square": np.square,
        "sqrt": lambda a: np.sqrt(a),
        "log": lambda a: np.log(a),
    }
    if p.y_operation not in operations:
        raise ValueError(f"Unknown Y operation: {p.y_operation}")
    yy = operations[p.y_operation](yy)

    if p.remove_nonfinite:
        mask = np.isfinite(xx) & np.isfinite(yy)
        xx, yy = xx[mask], yy[mask]
    return xx, yy
```

---

## `scientific_visualization/export/__init__.py`

```py
from .image import export_figure
from .data import export_dataset

__all__ = ["export_figure", "export_dataset"]
```

---

## `scientific_visualization/export/animation.py`

```py
"""Animation export for time-resolved scientific grid data."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

from matplotlib.animation import FFMpegWriter, PillowWriter
from matplotlib.colors import LogNorm, Normalize
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np


def _configure_ffmpeg() -> bool:
    """Use system ffmpeg or the optional imageio-ffmpeg bundled executable."""
    try:
        writer = FFMpegWriter(fps=1)
        if writer.isAvailable():
            return True
    except Exception:
        pass
    try:
        import matplotlib as mpl
        from imageio_ffmpeg import get_ffmpeg_exe
        mpl.rcParams["animation.ffmpeg_path"] = get_ffmpeg_exe()
        return bool(FFMpegWriter(fps=1).isAvailable())
    except Exception:
        return False


def ffmpeg_available() -> bool:
    return _configure_ffmpeg()


def _normalization(data: np.ndarray, normalization: str, vmin: float | None, vmax: float | None):
    finite = np.asarray(data)[np.isfinite(data)]
    if finite.size == 0:
        raise ValueError("The selected frame contains no finite values.")
    lo = float(np.min(finite)) if vmin is None else float(vmin)
    hi = float(np.max(finite)) if vmax is None else float(vmax)
    if lo == hi:
        pad = max(abs(lo) * 1e-6, 1e-12)
        lo, hi = lo - pad, hi + pad
    elif not lo < hi:
        raise ValueError(f"Invalid movie color range: minimum {lo:g} must be less than maximum {hi:g}.")
    if normalization == "log":
        if lo <= 0 or hi <= 0:
            raise ValueError("Logarithmic normalization requires positive color limits.")
        return LogNorm(vmin=lo, vmax=hi)
    return Normalize(vmin=lo, vmax=hi)


def export_grid_movie(
    files: Iterable[str],
    output_path: str | os.PathLike,
    *,
    frame_start: int = 0,
    frame_end: int | None = None,
    frame_step: int = 1,
    fps: float = 10.0,
    cmap: str = "viridis",
    normalization: str = "linear",
    vmin: float | None = None,
    vmax: float | None = None,
    symmetric: bool = False,
    clip_percentile: float = 0.0,
    aspect: str = "auto",
    interpolation: str = "nearest",
    title_prefix: str = "",
    figsize: tuple[float, float] = (7.0, 5.5),
    dpi: int = 150,
    loader: Callable[[str], object] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
    verbose: bool = True,
) -> int:
    """Render a sequence of 2D grid files to GIF or MP4.

    The source HDF5 files are read one frame at a time. No expanded 3D array
    is created. A fixed color range is recommended for quantitative movies.
    Returns the number of rendered frames.

    If `verbose` (default True), each frame's progress is printed to
    stdout as it is rendered -- useful when running from a terminal,
    since encoding a long movie can otherwise look like the application
    has stalled. `progress_callback(frame_index, total_frames, path)` is
    also invoked per frame, e.g. for a GUI status bar.
    """
    paths = [str(p) for p in files]
    if not paths:
        raise ValueError("No frames were provided for movie export.")
    if frame_step <= 0:
        raise ValueError("Frame step must be positive.")
    if fps <= 0:
        raise ValueError("FPS must be positive.")
    frame_end = len(paths) - 1 if frame_end is None else min(int(frame_end), len(paths) - 1)
    frame_start = max(0, int(frame_start))
    if frame_start > frame_end:
        raise ValueError("Movie start frame must not be after the end frame.")

    if loader is None:
        from ..io.grid import GridFile
        loader = GridFile.load

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    suffix = out.suffix.lower()
    if suffix not in {".gif", ".mp4"}:
        raise ValueError("Movie output must use .gif or .mp4 extension.")

    selected = paths[frame_start : frame_end + 1 : frame_step]
    first = loader(selected[0])
    if getattr(first, "ndim", 0) != 2:
        raise ValueError("Movie export currently supports 2D scalar grid datasets.")

    # Compute a fixed range when the caller does not provide one and requested
    # clipping/symmetry. This scans each selected frame once, without keeping
    # all arrays in memory simultaneously.
    effective_vmin, effective_vmax = vmin, vmax
    if clip_percentile > 0 or symmetric or vmin is None or vmax is None:
        if clip_percentile > 0 or symmetric:
            values = []
            for path in selected:
                g = loader(path)
                arr = np.asarray(g.data)
                finite = arr[np.isfinite(arr)]
                if finite.size:
                    values.append(finite)
            if values:
                finite = np.concatenate(values)
                lo, hi = np.percentile(finite, [clip_percentile, 100.0 - clip_percentile]) if clip_percentile > 0 else (float(finite.min()), float(finite.max()))
                if symmetric and not (vmin is not None or vmax is not None):
                    m = max(abs(float(lo)), abs(float(hi)))
                    lo, hi = -m, m
                effective_vmin = float(lo) if effective_vmin is None else effective_vmin
                effective_vmax = float(hi) if effective_vmax is None else effective_vmax
            else:
                raise ValueError("No finite values were found in the selected movie frames.")

    # Build a bare Agg-backed Figure instead of going through `pyplot`.
    # `pyplot` keeps a global current-figure/backend state that is not safe
    # to touch from a worker thread while the Qt GUI thread may simultaneously
    # be drawing its own embedded Matplotlib canvas; a plain `Figure` +
    # `FigureCanvasAgg` has no such shared state and is safe for background
    # rendering (Pillow/FFMpeg writers only need `fig.canvas.draw()`).
    fig = Figure(figsize=figsize, dpi=dpi)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    first_data = np.asarray(first.data)
    extent = first.extent()
    norm = _normalization(first_data, normalization, effective_vmin, effective_vmax)
    im = ax.imshow(first_data, origin="lower", extent=extent, aspect=aspect, cmap=cmap, norm=norm, interpolation=interpolation)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"{getattr(first, 'label', getattr(first, 'name', 'quantity'))} [{first.units}]" if getattr(first, "units", "") else getattr(first, "label", getattr(first, "name", "quantity")))
    ax.set_xlabel(first.axes[0].label if first.axes else "x1")
    ax.set_ylabel(first.axes[1].label if len(first.axes) > 1 else "x2")

    def draw(path: str):
        grid = loader(path)
        data = np.asarray(grid.data)
        if data.ndim != 2:
            raise ValueError(f"Frame '{path}' is not 2D.")
        if data.shape != first_data.shape:
            raise ValueError(f"Frame '{path}' has shape {data.shape}, expected {first_data.shape}.")
        im.set_data(data)
        im.set_extent(grid.extent())
        title = title_prefix.strip() or f"{getattr(grid, 'label', getattr(grid, 'name', 'quantity'))}"
        im.axes.set_title(f"{title}    t = {getattr(grid, 'time', 0.0):g} {getattr(grid, 'time_units', '')}    (iter {getattr(grid, 'iteration', 0)})")
        return im

    writer = PillowWriter(fps=fps) if suffix == ".gif" else FFMpegWriter(fps=fps, metadata={"title": "Scientific simulation"})
    if suffix == ".mp4" and not _configure_ffmpeg():
        pass  # non-pyplot Figure: no global state to close/leak
        raise RuntimeError("MP4 export requires ffmpeg. Install ffmpeg or use GIF export.")

    total = len(selected)
    if verbose:
        print(f"[movie export] starting: {total} frame(s) -> {out}", flush=True)
    with writer.saving(fig, str(out), dpi=dpi):
        for i, path in enumerate(selected, start=1):
            if verbose:
                print(f"[movie export] frame {i}/{total}: {Path(path).name}", flush=True)
            if progress_callback is not None:
                progress_callback(i, total, path)
            draw(path)
            fig.canvas.draw()
            writer.grab_frame()
    if verbose:
        print(f"[movie export] done: {total} frame(s) written to {out}", flush=True)
    pass  # non-pyplot Figure: no global state to close/leak
    return len(selected)
```

---

## `scientific_visualization/export/data.py`

```py
from __future__ import annotations

from pathlib import Path
import json
import numpy as np

from ..core.data import Dataset


def export_dataset(dataset: Dataset, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".npz":
        np.savez_compressed(path, data=dataset.data, **{f"coord_{i}": c.values for i,c in enumerate(dataset.coordinates)})
        return
    if path.suffix.lower() == ".json":
        payload = {"name": dataset.name, "shape": dataset.shape, "axes": dataset.axes, "units": dataset.units, "time": dataset.time, "source": dataset.source, "metadata": dict(dataset.metadata)}
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return
    raise ValueError("Supported dataset exports are .npz and .json")
```

---

## `scientific_visualization/export/image.py`

```py
from __future__ import annotations

from pathlib import Path


def export_figure(figure, path, *, dpi=300, transparent=False, background=None, bbox_inches="tight"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = dict(dpi=dpi, transparent=transparent, bbox_inches=bbox_inches)
    if background is not None:
        kwargs["facecolor"] = background
    figure.savefig(path, **kwargs)
```

---

## `scientific_visualization/export/opencv_movie.py`

```py
from __future__ import annotations
from pathlib import Path
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except Exception:
    cv2 = None
    OPENCV_AVAILABLE = False


def _limits(arr, vmin=None, vmax=None, symmetric=False, clip_percentile=0.0):
    finite = np.asarray(arr)[np.isfinite(arr)]
    if finite.size == 0:
        raise ValueError('Frame contains no finite values.')
    lo = float(np.min(finite)) if vmin is None else float(vmin)
    hi = float(np.max(finite)) if vmax is None else float(vmax)
    if clip_percentile:
        lo, hi = np.percentile(finite, [clip_percentile, 100 - clip_percentile])
    if symmetric:
        m = max(abs(lo), abs(hi)); lo, hi = -m, m
    if lo == hi:
        pad = max(abs(lo) * 1e-6, 1e-12); lo -= pad; hi += pad
    if lo >= hi:
        raise ValueError(f'Invalid limits: {lo} >= {hi}')
    return float(lo), float(hi)


def export_grid_movie_opencv(files, output_path, *, fps=10, cmap='viridis', vmin=None, vmax=None,
                              symmetric=False, clip_percentile=0.0, frame_start=0, frame_end=None,
                              frame_step=1, title_prefix='', size=None, loader=None,
                              progress_callback=None, verbose=True):
    """Encode scientific 2D field frames directly with OpenCV VideoWriter.

    Rendering uses a Matplotlib colormap lookup to preserve scientific color
    maps, while OpenCV handles image assembly and MP4/AVI encoding.

    If `verbose` (default True), each frame's progress is printed to
    stdout as it is encoded, so running this from a terminal shows which
    frame is currently being processed instead of appearing to hang.
    `progress_callback(frame_index, total_frames, path)` is also invoked
    per frame for GUI use.
    """
    if not OPENCV_AVAILABLE:
        raise RuntimeError('OpenCV is not installed. Install opencv-python.')
    from matplotlib import colormaps
    from ..io.grid import GridFile
    loader = loader or GridFile.load
    paths = [str(p) for p in files]
    if not paths:
        raise ValueError('No frames supplied.')
    end = len(paths) - 1 if frame_end is None else min(int(frame_end), len(paths)-1)
    start = max(0, int(frame_start))
    selected = paths[start:end+1:int(frame_step)]
    if not selected:
        raise ValueError('No frames selected.')
    first = loader(selected[0])
    if first.ndim != 2:
        raise ValueError('OpenCV movie export supports 2D scalar grid fields.')
    lo, hi = _limits(first.data, vmin=vmin, vmax=vmax, symmetric=symmetric, clip_percentile=clip_percentile)
    lut = colormaps.get_cmap(cmap)(np.linspace(0, 1, 256))[:, :3]
    if size is None:
        width = int(first.shape[1] if len(first.shape) > 1 else first.shape[0])
        height = int(first.shape[0] if first.shape else 1)
    else:
        width, height = int(size[0]), int(size[1])
    out = str(Path(output_path))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*('mp4v' if Path(out).suffix.lower() == '.mp4' else 'MJPG'))
    writer = cv2.VideoWriter(out, fourcc, float(fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError('OpenCV could not open the video encoder. Try an .avi output or install a codec-enabled OpenCV build.')
    count = 0
    total = len(selected)
    if verbose:
        print(f"[movie export] starting: {total} frame(s) -> {out}", flush=True)
    try:
        for i, path in enumerate(selected, start=1):
            if verbose:
                print(f"[movie export] frame {i}/{total}: {Path(path).name}", flush=True)
            if progress_callback is not None:
                progress_callback(i, total, path)
            grid = loader(path)
            arr = np.asarray(grid.data, dtype=float)
            if arr.shape != tuple(first.shape):
                raise ValueError(f"Frame '{path}' has shape {arr.shape}, expected {first.shape}.")
            scaled = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
            idx = np.nan_to_num(scaled * 255.0, nan=0.0).astype(np.uint8)
            rgb = (lut[idx] * 255.0).astype(np.uint8)
            frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            if (frame.shape[1], frame.shape[0]) != (width, height):
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            label = title_prefix.strip() or getattr(grid, 'label', getattr(grid, 'name', 'field'))
            text = f'{label}  t={getattr(grid, "time", 0.0):g}  iter={getattr(grid, "iteration", 0)}'
            cv2.putText(frame, text, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame, text, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0,0,0), 1, cv2.LINE_AA)
            writer.write(frame)
            count += 1
    finally:
        writer.release()
    if verbose:
        print(f"[movie export] done: {count} frame(s) written to {out}", flush=True)
    return count
```

---

## `scientific_visualization/gui/__init__.py`

```py

```

---

## `scientific_visualization/gui/ai_tab.py`

```py
from __future__ import annotations

from pathlib import Path
import numpy as np
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox, QFileDialog, QComboBox, QFormLayout, QSpinBox

from ..analysis.ai import AIAnalysisEngine
from ..analysis.series import SimulationSeries
from ..io.simulation import SimulationReader
from .plot_canvas import PlotCanvas


class AITab(QWidget):
    """Simulation-scale scientific analysis. One frame remains available, but series analysis is the primary workflow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reader = SimulationReader()
        self.engine = AIAnalysisEngine()
        self.dataset = None
        self.series_files = []
        root = QVBoxLayout(self)
        row = QHBoxLayout()
        self.open_btn = QPushButton("Open dataset…")
        self.open_series_btn = QPushButton("Open simulation folder…")
        self.analyze_btn = QPushButton("Analyze current frame")
        self.analyze_series_btn = QPushButton("Analyze all frames")
        self.analyze_btn.setEnabled(False); self.analyze_series_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open)
        self.open_series_btn.clicked.connect(self._open_series)
        self.analyze_btn.clicked.connect(self._analyze)
        self.analyze_series_btn.clicked.connect(self._analyze_series)
        for b in (self.open_btn, self.open_series_btn, self.analyze_btn, self.analyze_series_btn): row.addWidget(b)
        row.addStretch(1)
        root.addLayout(row)
        form = QFormLayout()
        self.quantity = QComboBox(); self.quantity.setEditable(True)
        self.max_frames = QSpinBox(); self.max_frames.setRange(1, 1000000); self.max_frames.setValue(1000)
        form.addRow("Quantity:", self.quantity); form.addRow("Max frames to load:", self.max_frames)
        root.addLayout(form)
        self.info = QLabel("No dataset or simulation series selected."); self.info.setWordWrap(True); root.addWidget(self.info)
        self.plot = PlotCanvas(figsize=(7.5, 4.5)); root.addWidget(self.plot, 2)
        self.output = QTextEdit(); self.output.setReadOnly(True); root.addWidget(self.output, 1)

    def set_dataset(self, dataset):
        """Accept either the shared Dataset model or the legacy GridFile wrapper.

        The GUI signal contract is now Dataset, but this compatibility path keeps
        the AI tab safe if an older tab/plugin still sends GridFile metadata.
        Metadata-only GridFile objects are not converted into field arrays here,
        preserving lazy loading.
        """
        if dataset is not None and hasattr(dataset, "to_dataset") and not hasattr(dataset, "summary"):
            # A metadata-only GridFile has no data. Keep a lazy reference and
            # show a lightweight summary; load the Dataset only when analysis runs.
            grid = dataset
            self.dataset = grid
            source = getattr(grid, "filename", None)
            name = getattr(grid, "name", getattr(grid, "dataset_name", "dataset"))
            shape = getattr(grid, "shape", ())
            units = getattr(grid, "units", "")
            self.analyze_btn.setEnabled(source is not None)
            self.info.setText(f"{name}: shape={shape}, units={units or 'not specified'}, source={Path(source).name if source else 'unknown'}")
            self.series_files = [source] if source else []
            self._set_quantity(name)
            self.analyze_series_btn.setEnabled(len(self.series_files) > 1)
            return

        self.dataset = dataset
        self.analyze_btn.setEnabled(dataset is not None)
        self.info.setText(dataset.summary() if dataset is not None else "No dataset selected.")
        if dataset is not None:
            self.series_files = [dataset.source] if dataset.source else []
            self._set_quantity(dataset.name)
            self.analyze_series_btn.setEnabled(len(self.series_files) > 1)

    def set_series(self, files):
        self.series_files = list(files or [])
        self.analyze_series_btn.setEnabled(len(self.series_files) > 1)
        self.info.setText(f"Simulation series: {len(self.series_files)} HDF5 file(s) available for analysis.")

    def _set_quantity(self, name):
        if not name: return
        if self.quantity.findText(name) < 0: self.quantity.addItem(name)
        self.quantity.setCurrentText(name)

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open dataset", "", "HDF5 files (*.h5 *.hdf5);;All files (*)")
        if not path: return
        try:
            self.dataset = self.reader.load(path)
            self.series_files = [path]
            self._set_quantity(self.dataset.name)
            self.analyze_btn.setEnabled(True); self.analyze_series_btn.setEnabled(False)
            self.info.setText(self.dataset.summary()); self.output.clear(); self.plot.clear()
        except Exception as exc:
            QMessageBox.critical(self, "Dataset load failed", str(exc))

    def _open_series(self):
        folder = QFileDialog.getExistingDirectory(self, "Open simulation folder")
        if not folder: return
        try:
            series = SimulationSeries.from_folder(folder, quantity=self.quantity.currentText() or None)
            frames = series.discover()
            self.series_files = [f[0] for f in frames]
            if frames:
                self.dataset = series.load(0)
                self._set_quantity(series.quantity)
            self.analyze_series_btn.setEnabled(len(self.series_files) > 1)
            self.analyze_btn.setEnabled(self.dataset is not None)
            self.info.setText(f"Simulation series: {len(self.series_files)} compatible frames. "
                              f"Quantity: {series.quantity}. t={frames[0][1]:g}…{frames[-1][1]:g}")
            self.output.clear(); self.plot.clear()
        except Exception as exc:
            QMessageBox.critical(self, "Simulation series failed", str(exc))

    def _analyze(self):
        if self.dataset is None: return
        try:
            dataset = self.dataset.to_dataset() if hasattr(self.dataset, "to_dataset") else self.dataset
            if getattr(dataset, "data", None) is None:
                raise ValueError("The selected dataset could not be loaded for analysis.")
            r = self.engine.analyze(dataset)
            lines = ["SCIENTIFIC FRAME ANALYSIS", "", r["summary"], "", "STATISTICS"]
            lines += [f"  {k}: {v}" for k, v in r["statistics"].items()]
            lines += ["", "PHYSICS / NEXT STEPS"] + [f"  • {x}" for x in r["physics"]]
            lines += ["", "RECOMMENDATIONS"] + [f"  • {x}" for x in r["recommendations"]]
            self.output.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.warning(self, "AI analysis failed", str(exc))

    def _analyze_series(self):
        if len(self.series_files) < 2: return
        try:
            q = self.quantity.currentText().strip() or None
            r = self.engine.analyze_series(files=self.series_files, quantity=q, reduction="mean", max_frames=self.max_frames.value())
            lines = ["SIMULATION-SCALE SCIENTIFIC ANALYSIS", "", r["summary"], "",
                     "FILE INVENTORY", f"  discovered: {r['n_files_discovered']}", f"  compatible frames: {r['n_frames']}",
                     f"  analyzed: {r['n_frames_analyzed']}", "", "TEMPORAL STATISTICS"]
            lines += [f"  {k}: {v}" for k, v in r["temporal_statistics"].items()]
            lines += ["", "FIELD CHANGE (first → last)"] + [f"  {k}: {v}" for k, v in r["field_change"].items()]
            if r.get("temporal_frequency"):
                lines += ["", "TEMPORAL SPECTRUM"] + [f"  {k}: {v}" for k, v in r["temporal_frequency"].items()]
            lines += ["", "NEXT ANALYSES"] + [f"  • {x}" for x in r["recommendations"]]
            self.output.setPlainText("\n".join(lines))
            self._plot_series(r)
        except Exception as exc:
            QMessageBox.warning(self, "Series analysis failed", str(exc))

    def _plot_series(self, result):
        self.plot.clear()
        fig = self.plot.figure
        axes = fig.subplots(1, 3)
        t = np.asarray(result["times"], dtype=float)
        y = np.asarray(result["reduced_values"], dtype=float)

        ax = axes[0]
        ax.plot(t, y, "o-", lw=1.4, ms=3)
        ax.set_xlabel("time")
        ax.set_ylabel(f"{result['quantity']} ({result.get('temporal_statistics', {}).get('value_mean', '')})")
        ax.set_title("Temporal evolution")
        ax.grid(alpha=0.2)

        ax = axes[1]
        freq = result.get("temporal_frequency")
        if freq and "peak_frequency" in freq and len(t) >= 4:
            dt = np.diff(t)
            if np.allclose(dt, dt[0], rtol=1e-5, atol=max(abs(dt[0]) * 1e-8, 1e-15)):
                yy = y - np.nanmean(y)
                spectrum = np.abs(np.fft.rfft(np.nan_to_num(yy))) ** 2
                frequencies = np.fft.rfftfreq(len(yy), d=float(dt[0]))
                ax.plot(frequencies, spectrum, lw=1.2)
                ax.axvline(freq["peak_frequency"], ls="--", lw=1.0, label=f"peak={freq['peak_frequency']:.4g}")
                ax.legend()
                ax.set_xlabel("frequency")
                ax.set_ylabel("power")
                ax.set_title("Temporal spectrum")
            else:
                ax.text(0.5, 0.5, "Non-uniform time spacing\nFFT unavailable", ha="center", va="center", transform=ax.transAxes)
                ax.set_title("Temporal spectrum")
        else:
            ax.text(0.5, 0.5, "Not enough frames for FFT", ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Temporal spectrum")

        ax = axes[2]
        change = result.get("field_change", {})
        labels = ["min", "max", "RMS"]
        vals = [change.get("delta_min", 0.0), change.get("delta_max", 0.0), change.get("delta_rms", 0.0)]
        ax.bar(labels, vals)
        ax.axhline(0.0, lw=0.8)
        ax.set_title("First → last frame change")
        ax.set_ylabel("Δ field")

        fig.suptitle(f"{result['quantity']} across {result['n_frames_analyzed']} simulation frames")
        fig.tight_layout()
        self.plot.draw()
```

---

## `scientific_visualization/gui/base_tab.py`

```py
"""
Common scaffolding shared by all tabs (Fields/Grid, Particles, Tracks, and
the 3D viewer), so new tabs/features can be added consistently instead of
each tab re-implementing file dialogs, scroll areas, panel positioning,
and theme handling slightly differently.

Subclasses should:
  1. call `super().__init__(parent)` -- or `super().__init__(parent,
     view_widget=<your own main view widget>)` if the tab's primary view
     isn't a Matplotlib canvas (e.g. a PyVista/QtInteractor 3D viewport;
     see gui/three_d_tab.py)
  2. build their controls into `self.control_layout` (a QVBoxLayout)
  3. call `self.finish_layout()` once at the end of __init__
  4. implement `refresh_plot(self)`

Every subclass gets the same splitter-based layout and the "Panel:
Left/Right/Top/Bottom" placement control for free, so this is the one
place that needs to change to add a layout feature to every tab at once.
"""
from __future__ import annotations

import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog, QFileDialog, QHBoxLayout, QListWidget, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QVBoxLayout, QWidget, QComboBox, QLabel,
)

from .. import style
from .plot_canvas import PlotCanvas


class BaseTab(QWidget):
    #: subclasses may override to restrict the file dialog filter text
    file_filter = "HDF5 files (*.h5 *.hdf5);;All files (*)"

    def __init__(self, parent=None, figsize=(6.5, 5.5), view_widget=None):
        super().__init__(parent)
        self.files = []
        self.theme = "Light"
        self.accent_color = QColor(style.DEFAULT_ACCENT["Light"])

        self._splitter = QSplitter(Qt.Horizontal)

        # Scrollable control panel -- this is what prevents controls from
        # being clipped/hidden when the window or panel is resized smaller
        # than the sum of all the option groups.
        control_container = QWidget()
        self.control_layout = QVBoxLayout(control_container)
        self.control_layout.setContentsMargins(6, 6, 6, 6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(control_container)
        scroll.setMinimumWidth(280)
        scroll.setMaximumWidth(16777215)
        self._splitter.addWidget(scroll)

        # Subclasses whose main view isn't a Matplotlib canvas (e.g. the 3D
        # tab's PyVista/QtInteractor viewport) can supply their own widget
        # here and still get the shared splitter, scrollable panel, and
        # panel-position controls below "for free". `self.canvas` is kept
        # as the attribute name for backward compatibility with tabs that
        # do use PlotCanvas.
        self.canvas = view_widget if view_widget is not None else PlotCanvas(figsize=figsize)
        self._splitter.addWidget(self.canvas)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setHandleWidth(8)
        self._splitter.setCollapsible(0, False)
        self._splitter.setSizes([340, 900])

        # Compact panel-placement control. The splitter remains draggable,
        # and the user can also move the controls to any outer side.
        placement_row = QHBoxLayout()
        placement_row.addWidget(QLabel("Panel:"))
        self._panel_position = QComboBox()
        self._panel_position.addItems(["Left", "Right", "Top", "Bottom"])
        self._panel_position.currentTextChanged.connect(self.set_panel_position)
        placement_row.addWidget(self._panel_position)
        placement_row.addStretch(1)
        self.control_layout.insertLayout(0, placement_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._splitter)


    def set_panel_position(self, position: str):
        """Move the scrollable controls to any side of the plot."""
        if not hasattr(self, "_splitter") or self._splitter.count() < 2:
            return
        panel = self._splitter.widget(0)
        canvas = self._splitter.widget(1)
        orientation = Qt.Horizontal if position in {"Left", "Right"} else Qt.Vertical
        self._splitter.setOrientation(orientation)
        # Reorder widgets using insertWidget while preserving the live widgets.
        self._splitter.insertWidget(0 if position in {"Left", "Top"} else 1, panel)
        self._splitter.insertWidget(1 if position in {"Left", "Top"} else 0, canvas)
        if orientation == Qt.Horizontal:
            self._splitter.setSizes([340, max(500, self.width() - 360)])
        else:
            self._splitter.setSizes([280, max(320, self.height() - 300)])

    def finish_layout(self):
        """Call once after all controls have been added to control_layout."""
        self.control_layout.addStretch(1)

    # -- reusable control-builders -------------------------------------
    def add_open_buttons(self, folder: bool = True, label: str = "file"):
        """Adds Open File… (and optionally Open Folder…) buttons plus a
        QListWidget that lists whichever files are currently loaded.
        Returns the QListWidget so subclasses can connect selection signals."""
        row = QHBoxLayout()
        open_file_btn = QPushButton(f"Open {label.capitalize()}…")
        open_file_btn.clicked.connect(lambda: self._open_file(label))
        row.addWidget(open_file_btn)
        if folder:
            open_folder_btn = QPushButton("Open Folder…")
            open_folder_btn.clicked.connect(lambda: self._open_folder(label))
            row.addWidget(open_folder_btn)
        self.control_layout.addLayout(row)

        file_list = QListWidget()
        self.control_layout.addWidget(file_list, stretch=1)
        self._file_list = file_list
        return file_list

    def add_color_picker_button(self, on_change, label: str = "Line color…"):
        """A button that opens a QColorDialog and calls on_change(QColor)."""
        btn = QPushButton(label)

        def pick():
            color = QColorDialog.getColor(self.accent_color, self, "Choose color")
            if color.isValid():
                self.accent_color = color
                on_change(color)
        btn.clicked.connect(pick)
        return btn

    def accent_hex(self) -> str:
        return self.accent_color.name()

    # -- file dialogs ----------------------------------------------------
    def _open_file(self, label):
        path, _ = QFileDialog.getOpenFileName(self, f"Open Simulation {label}", "", self.file_filter)
        if not path:
            return
        self.files = [path]
        self._file_list.clear()
        self._file_list.addItem(os.path.basename(path))
        self._file_list.setCurrentRow(0)

    def _open_folder(self, label):
        folder = QFileDialog.getExistingDirectory(self, f"Open folder with Simulation {label}s")
        if not folder:
            return
        files = sorted(
            os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith((".h5", ".hdf5"))
        )
        if not files:
            QMessageBox.warning(self, "No files found", "No .h5/.hdf5 files were found in that folder.")
            return
        self.files = files
        self._file_list.clear()
        for f in files:
            self._file_list.addItem(os.path.basename(f))
        self._file_list.setCurrentRow(0)

    # -- theme -------------------------------------------------------
    def set_typography(self, family: str, size: float):
        style.set_font_preferences(family, size)
        self.refresh_plot()

    def set_theme(self, theme_name: str):
        """Called by the main window when the global app theme changes."""
        self.theme = theme_name
        if hasattr(self.canvas, "set_theme"):
            self.canvas.set_theme(theme_name)
        # keep the default accent in sync unless the user picked a custom one
        if self.accent_color.name().lower() in (
            style.DEFAULT_ACCENT["Light"].lower(), style.DEFAULT_ACCENT["Dark"].lower()
        ):
            self.accent_color = QColor(style.DEFAULT_ACCENT[theme_name])
        self.refresh_plot()

    def refresh_plot(self):
        raise NotImplementedError
```

---

## `scientific_visualization/gui/data_plotter_tab.py`

```py
from __future__ import annotations

import os
from pathlib import Path

from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..data_plotter.model import DatasetTable
from ..data_plotter.parser import Delimiter, parse_text_file
from ..data_plotter.renderer import DataPlotRenderer, RenderSeries
from ..data_plotter.transform import TransformPipeline
from ..export.image import export_figure
from .. import style
from .base_tab import BaseTab


class DataPlotterTab(BaseTab):
    """Quick plotting workflow for CSV/TXT scientific data."""

    file_filter = "Data files (*.csv *.txt);;CSV files (*.csv);;Text files (*.txt);;All files (*)"

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(7.0, 5.5))
        self._datasets: list[DatasetTable] = []
        self._configs: list[dict] = []
        self.renderer = DataPlotRenderer()
        self._updating = False

        self._build_controls()
        self._enable_drop()
        self.finish_layout()
        self.refresh_plot()

    def _build_controls(self):
        file_row = QHBoxLayout()
        open_btn = QPushButton("Open CSV/TXT…")
        open_btn.clicked.connect(self.open_files)
        remove_btn = QPushButton("Remove selected")
        remove_btn.clicked.connect(self.remove_selected)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_datasets)
        file_row.addWidget(open_btn); file_row.addWidget(remove_btn); file_row.addWidget(clear_btn)
        self.control_layout.addLayout(file_row)
        self.dataset_list = QListWidget()
        self.dataset_list.itemSelectionChanged.connect(self._select_dataset)
        self.control_layout.addWidget(self.dataset_list, stretch=1)

        self.delimiter = QComboBox()
        self.delimiter.addItems([d.value for d in Delimiter])
        self.delimiter.setCurrentText(Delimiter.AUTO.value)
        reload_btn = QPushButton("Reload selected")
        reload_btn.clicked.connect(self.reload_selected)
        self.control_layout.addWidget(self.delimiter); self.control_layout.addWidget(reload_btn)

        basic = QGroupBox("Quick Plot")
        form = QFormLayout(basic)
        self.x_combo = QComboBox(); self.y_combo = QComboBox()
        self.x_combo.currentIndexChanged.connect(self._column_changed)
        self.y_combo.currentIndexChanged.connect(self._column_changed)
        self.plot_type = QComboBox(); self.plot_type.addItems(["Line", "Scatter", "Line + Scatter", "Histogram"])
        self.plot_type.currentTextChanged.connect(self.refresh_plot)
        self.bins = QSpinBox(); self.bins.setRange(1, 500); self.bins.setValue(30)
        self.normalization = QComboBox(); self.normalization.addItems(["Count", "Probability", "Density"])
        self.hist_label = QLineEdit("Value")
        self.bins.valueChanged.connect(self.refresh_plot); self.normalization.currentTextChanged.connect(self.refresh_plot)
        self.hist_label.editingFinished.connect(self.refresh_plot)
        form.addRow("X:", self.x_combo); form.addRow("Y:", self.y_combo); form.addRow("Plot type:", self.plot_type)
        form.addRow("Histogram bins:", self.bins); form.addRow("Histogram normalization:", self.normalization)
        form.addRow("Histogram X label:", self.hist_label)
        self.control_layout.addWidget(basic)

        axes = QGroupBox("Axes")
        form = QFormLayout(axes)
        self.x_label = QLineEdit("X"); self.y_label = QLineEdit("Y")
        self.x_label.editingFinished.connect(self.refresh_plot); self.y_label.editingFinished.connect(self.refresh_plot)
        self.x_scale = QComboBox(); self.x_scale.addItems(["linear", "log"]); self.x_scale.currentTextChanged.connect(self.refresh_plot)
        self.y_scale = QComboBox(); self.y_scale.addItems(["linear", "log"]); self.y_scale.currentTextChanged.connect(self.refresh_plot)
        form.addRow("X label:", self.x_label); form.addRow("Y label:", self.y_label)
        form.addRow("X scale:", self.x_scale); form.addRow("Y scale:", self.y_scale)
        self.control_layout.addWidget(axes)

        export_box = QGroupBox("Export")
        exp = QFormLayout(export_box)
        self.dpi = QSpinBox(); self.dpi.setRange(72, 1200); self.dpi.setValue(300)
        self.width = QDoubleSpinBox(); self.width.setRange(1.0, 30.0); self.width.setValue(8.0); self.width.setSuffix(" cm")
        self.height = QDoubleSpinBox(); self.height.setRange(1.0, 30.0); self.height.setValue(6.0); self.height.setSuffix(" cm")
        export_btn = QPushButton("Export PNG/SVG/PDF…"); export_btn.clicked.connect(self.export_plot)
        exp.addRow("DPI:", self.dpi); exp.addRow("Width:", self.width); exp.addRow("Height:", self.height); exp.addRow(export_btn)
        self.control_layout.addWidget(export_box)

        inspect = QGroupBox("Data inspection")
        self.stats_label = QLabel("Select a dataset to inspect columns and basic statistics.")
        self.stats_label.setWordWrap(True)
        ins = QVBoxLayout(inspect); ins.addWidget(self.stats_label)
        self.control_layout.addWidget(inspect)

    def _enable_drop(self):
        self.setAcceptDrops(True)
        self.canvas.setAcceptDrops(True)
        self.canvas.installEventFilter(self)
        self.setToolTip("Drop CSV/TXT files anywhere in the Data Plotter.")

    def dragEnterEvent(self, event):
        if self._urls_are_supported(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self._load_paths(paths)
        event.acceptProposedAction()

    def eventFilter(self, obj, event):
        if event.type() == event.DragEnter:
            if self._urls_are_supported(event.mimeData()):
                event.acceptProposedAction(); return True
        elif event.type() == event.Drop:
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            self._load_paths(paths); event.acceptProposedAction(); return True
        return super().eventFilter(obj, event)

    @staticmethod
    def _urls_are_supported(mime: QMimeData):
        return any(u.isLocalFile() and Path(u.toLocalFile()).suffix.lower() in {".csv", ".txt"} for u in mime.urls())

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open data files", "", self.file_filter)
        self._load_paths(paths)

    def _load_paths(self, paths):
        existing = {Path(d.path).resolve() for d in self._datasets}
        errors = []
        for path in paths:
            if Path(path).suffix.lower() not in {".csv", ".txt"}:
                continue
            if Path(path).resolve() in existing:
                continue
            try:
                result = parse_text_file(path, self._selected_delimiter())
            except ValueError as exc:
                errors.append(str(exc)); continue
            ds = DatasetTable(result.path, result.columns, result.values, result.delimiter,
                              result.has_header, result.skipped_comments, result.skipped_rows)
            self._datasets.append(ds)
            self._configs.append(self._default_config(ds, len(self._datasets) - 1))
        self._rebuild_dataset_list()
        if errors:
            QMessageBox.warning(self, "Some files could not be loaded", "\n".join(errors))
        if self._datasets:
            self.dataset_list.setCurrentRow(max(0, self.dataset_list.count() - 1))
            self._refresh_column_choices()
        self.refresh_plot()

    def _selected_delimiter(self):
        try:
            return Delimiter(self.delimiter.currentText())
        except ValueError:
            return Delimiter.AUTO

    def _default_config(self, ds, index=None):
        color = self.renderer.DEFAULT_COLORS[(index or 0) % len(self.renderer.DEFAULT_COLORS)]
        return {"x": 0, "y": min(1, max(0, ds.column_count - 1)), "label": ds.name,
                "color": color, "enabled": True,
                "line_style": "-", "marker": "None", "line_width": 1.8, "marker_size": 4.0}

    def _rebuild_dataset_list(self):
        self.dataset_list.blockSignals(True)
        self.dataset_list.clear()
        for ds, cfg in zip(self._datasets, self._configs):
            item = QListWidgetItem(cfg["label"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if cfg["enabled"] else Qt.Unchecked)
            self.dataset_list.addItem(item)
        self.dataset_list.blockSignals(False)
        for i in range(self.dataset_list.count()):
            self.dataset_list.item(i).itemChanged = getattr(self.dataset_list.item(i), "itemChanged", None)
        self.dataset_list.itemChanged.connect(self._item_changed) if not getattr(self, "_item_changed_connected", False) else None
        self._item_changed_connected = True

    def _item_changed(self, item):
        idx = self.dataset_list.row(item)
        if idx < 0 or idx >= len(self._configs): return
        self._configs[idx]["enabled"] = item.checkState() == Qt.Checked
        self._configs[idx]["label"] = item.text()
        self.refresh_plot()

    def _select_dataset(self):
        idx = self.dataset_list.currentRow()
        if idx < 0 or idx >= len(self._datasets): return
        ds = self._datasets[idx]
        cfg = self._configs[idx]
        self._refresh_column_choices(cfg["x"], cfg["y"])
        self._show_stats(ds)

    def _refresh_column_choices(self, x=0, y=1):
        if not self._datasets: return
        idx = self.dataset_list.currentRow()
        ds = self._datasets[idx if 0 <= idx < len(self._datasets) else 0]
        self._updating = True
        self.x_combo.clear(); self.y_combo.clear()
        self.x_combo.addItems(ds.columns); self.y_combo.addItems(ds.columns)
        self.x_combo.setCurrentIndex(min(max(0, x), ds.column_count - 1))
        self.y_combo.setCurrentIndex(min(max(0, y), ds.column_count - 1))
        self._updating = False

    def _column_changed(self):
        if self._updating:
            return
        self._config_for_current()
        idx = self.dataset_list.currentRow()
        if 0 <= idx < len(self._datasets):
            self._show_stats(self._datasets[idx])
        self.refresh_plot()

    def _show_stats(self, ds: DatasetTable):
        lines = [
            f"<b>{ds.name}</b>",
            f"Rows: {ds.row_count}, columns: {ds.column_count}",
            f"Delimiter: {repr(ds.delimiter)}, header: {'yes' if ds.has_header else 'no'}",
        ]
        for label, combo in (("X", self.x_combo), ("Y", self.y_combo)):
            ci = combo.currentIndex()
            if 0 <= ci < ds.column_count:
                stats = ds.statistics(ci)
                if stats["count"]:
                    lines.append(
                        f"{label} <b>{ds.columns[ci]}</b>: "
                        f"n={stats['count']}, min={stats['min']:.6g}, max={stats['max']:.6g}, "
                        f"mean={stats['mean']:.6g}, std={stats['std']:.6g}"
                    )
        self.stats_label.setText("<br>".join(lines))

    def _config_for_current(self):
        idx = self.dataset_list.currentRow()
        if idx < 0 or idx >= len(self._configs): return None, None
        cfg = self._configs[idx]
        cfg["x"] = self.x_combo.currentIndex(); cfg["y"] = self.y_combo.currentIndex()
        return idx, cfg

    def refresh_plot(self):
        if self._updating or not self._datasets:
            if not self._datasets:
                self.canvas.clear()
            return
        self._config_for_current()
        series = []
        for ds, cfg in zip(self._datasets, self._configs):
            if not cfg["enabled"]: continue
            x = ds.column_values(cfg["x"]); y = ds.column_values(cfg["y"])
            x, y = TransformPipeline().apply(x, y)
            series.append(RenderSeries(x, y, cfg["label"], cfg["color"], cfg["line_style"],
                                       cfg["marker"], cfg["line_width"], cfg["marker_size"], True))
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else self.canvas.figure.add_subplot(111)
        if self.plot_type.currentText() == "Histogram":
            self.renderer.render_histogram(
                ax, series, bins=self.bins.value(), normalization=self.normalization.currentText(),
                xlabel=self.hist_label.text(), ylabel="Value",
            )
        else:
            self.renderer.render_xy(
                ax, series, plot_type=self.plot_type.currentText(),
                xlabel=self.x_label.text(), ylabel=self.y_label.text(),
                xscale=self.x_scale.currentText(), yscale=self.y_scale.currentText(),
            )
        self.canvas.mark_theme_dirty()
        self.canvas.draw()

    def remove_selected(self):
        idx = self.dataset_list.currentRow()
        if idx < 0: return
        self._datasets.pop(idx); self._configs.pop(idx)
        self._rebuild_dataset_list(); self.refresh_plot()

    def clear_datasets(self):
        self._datasets.clear(); self._configs.clear(); self._rebuild_dataset_list(); self.refresh_plot()

    def reload_selected(self):
        idx = self.dataset_list.currentRow()
        if idx < 0: return
        try:
            result = parse_text_file(self._datasets[idx].path, self._selected_delimiter())
        except ValueError as exc:
            QMessageBox.warning(self, "Reload failed", str(exc)); return
        old_cfg = self._configs[idx]
        self._datasets[idx] = DatasetTable(result.path, result.columns, result.values, result.delimiter,
                                           result.has_header, result.skipped_comments, result.skipped_rows)
        old_cfg["x"] = min(old_cfg["x"], self._datasets[idx].column_count - 1)
        old_cfg["y"] = min(old_cfg["y"], self._datasets[idx].column_count - 1)
        self._refresh_column_choices(old_cfg["x"], old_cfg["y"]); self.refresh_plot()

    def export_plot(self):
        if not self._datasets:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export figure", "figure.png",
                                              "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if not path: return
        fig = self.canvas.figure
        fig.set_size_inches(self.width.value() / 2.54, self.height.value() / 2.54)
        export_figure(fig, path, dpi=self.dpi.value(), background=style.THEMES[self.theme]["figure_facecolor"])
```

---

## `scientific_visualization/gui/gpu_viewer.py`

```py
from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
try:
    from ..visualization.gpu.vispy_renderer import VISPY_AVAILABLE, VisPyFieldRenderer
except Exception:
    VISPY_AVAILABLE = False
    VisPyFieldRenderer = None

class GPUViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('GPU 2D Viewer (VisPy)')
        self.resize(900, 700)
        lay = QVBoxLayout(self)
        self._renderer = None
        if not VISPY_AVAILABLE:
            lay.addWidget(QLabel('VisPy is not installed or OpenGL is unavailable. Install vispy and restart the application.'))
        else:
            self._renderer = VisPyFieldRenderer(self)
            lay.addWidget(self._renderer.widget())

    def set_field(self, data, extent, cmap):
        if self._renderer is None:
            return
        self._renderer.set_data(data, extent=extent, cmap=cmap)
```

---

## `scientific_visualization/gui/grid_tab.py`

```py
import numpy as np
from pathlib import Path
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLabel, QRadioButton, QSpinBox, QVBoxLayout, QLineEdit, QHBoxLayout,
    QPushButton, QDialog, QDialogButtonBox, QFileDialog, QMessageBox, QListWidget,
)

from .. import style
from ..rendering_colors import ALL_PALETTES, make_palette
from ..analysis import reduce_grid_series, smooth_1d, smooth_2d
from ..analysis.roi import RegionOfInterest, roi_statistics, roi_time_series, export_roi_results
from ..io.grid import GridFile
from ..session import save_xml_session, load_xml_session, value_as_bool, value_as_float, value_as_int
from ..io.lazy import LazyGridSeries
from .base_tab import BaseTab

# Sentinel shown in the "Palette preset" dropdown meaning "don't use a
# custom palette -- use the plain Colormap group/Colormap dropdowns (and
# their own Reverse checkbox) instead". This is the default, so the
# ordinary matplotlib colormap picker and its reverse toggle work
# out of the box.
USE_LEGACY_CMAP = "(use Colormap dropdown)"


class ColorRangeDialog(QDialog):
    def __init__(self, vmin, vmax, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Colorbar range")
        form = QFormLayout(self)
        self.vmin = QDoubleSpinBox()
        self.vmax = QDoubleSpinBox()
        for w, value in ((self.vmin, vmin), (self.vmax, vmax)):
            w.setRange(-1e300, 1e300)
            w.setDecimals(10)
            w.setValue(float(value))
        form.addRow("Minimum:", self.vmin)
        form.addRow("Maximum:", self.vmax)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class MovieDialog(QDialog):
    def __init__(self, count, current_row=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create movie")
        form = QFormLayout(self)
        self.start = QSpinBox(); self.start.setRange(0, count - 1); self.start.setValue(0)
        self.end = QSpinBox(); self.end.setRange(0, count - 1); self.end.setValue(count - 1)
        self.step = QSpinBox(); self.step.setRange(1, count); self.step.setValue(1)
        self.fps = QDoubleSpinBox(); self.fps.setRange(0.1, 120.0); self.fps.setDecimals(1); self.fps.setValue(10.0)
        self.format = QComboBox(); self.format.addItems(["MP4 (OpenCV)", "MP4 (FFmpeg/Matplotlib)", "GIF"])
        self.output = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        out_row = QHBoxLayout(); out_row.addWidget(self.output); out_row.addWidget(browse)
        form.addRow("Start frame:", self.start)
        form.addRow("End frame:", self.end)
        form.addRow("Frame step:", self.step)
        form.addRow("Frames per second:", self.fps)
        form.addRow("Format:", self.format)
        form.addRow("Output:", out_row)
        note = QLabel("A fixed color range is recommended for quantitative movies. MP4 requires ffmpeg; GIF does not.")
        note.setWordWrap(True); form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self):
        suffix = ".gif" if self.format.currentText() == "GIF" else ".mp4"
        path, _ = QFileDialog.getSaveFileName(self, "Save movie", "simulation_movie" + suffix, f"Movie (*{suffix})")
        if path: self.output.setText(path)

    def values(self):
        return self.output.text().strip(), self.start.value(), self.end.value(), self.step.value(), self.fps.value(), self.format.currentText()


class TextAnnotationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Add plot text")
        form=QFormLayout(self); self.text=QLineEdit(); self.text.setPlaceholderText("Annotation text")
        form.addRow("Text:", self.text)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)

class AnnotationStyleDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent); self.setWindowTitle(title); form=QFormLayout(self)
        self.value=QLineEdit(); form.addRow("Label:", self.value)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)


class GridTab(BaseTab):
    dataset_changed = pyqtSignal(object)
    series_changed = pyqtSignal(object)
    open_in_3d_requested = pyqtSignal(str)
    """View Simulation field/grid files with robust frame navigation and interactive plotting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = None
        self._cbar = None
        self._cbar_user_position = None  # figure-fraction [x0,y0,w,h] after a manual drag, or None
        self._cbar_drag = None
        self._press_info = None
        self._press_connection = self.canvas.canvas.mpl_connect("button_press_event", self._on_canvas_press)
        self._motion_connection = self.canvas.canvas.mpl_connect("motion_notify_event", self._on_canvas_motion)
        self._release_connection = self.canvas.canvas.mpl_connect("button_release_event", self._on_canvas_release)
        self._last_limits = None
        self._default_limits = None
        self._manual_limits_update = False
        self._annotations = []
        self._rectangle_selector = None
        self._annotation_mode = None
        self._arrow_start = None
        self._series = None
        self._gpu_dialog = None
        self._gpu_widget = None
        self._image = None
        self._line_artist = None
        self._contour_artists = []
        self._last_contour_sig = None
        self._annotation_artists = []
        self._active_plot_mode = None
        self._force_full_view = False
        self._time_series_cache = {}
        self._rois = []            # list[RegionOfInterest], persists across frames (physical coords)
        self._roi_mode = None      # "rectangle" | "ellipse" | None while drawing
        self._roi_draft = None     # {"x0","y0","ax"} during an active drag
        self._roi_preview_patch = None
        self._roi_patches = []
        self._last_roi_results = None  # dict or list[dict], for Export
        self._rois = []            # list[RegionOfInterest], persists across frames (physical coords)
        self._roi_mode = None      # "rectangle" | "ellipse" | None, when actively drawing
        self._roi_draft = None     # {"x0":..., "y0":..., "ax":...} during drag
        self._roi_preview_patch = None
        self._roi_patches = []
        self._last_roi_results = None

        self.file_list = self.add_open_buttons(folder=True, label="field file")
        self.file_list.currentRowChanged.connect(self._pending_selection_changed)
        apply_btn = QPushButton("Apply selection")
        apply_btn.clicked.connect(self.apply_selection)
        self.control_layout.addWidget(apply_btn)
        open3d_btn = QPushButton("Open selected frame in 3D…")
        open3d_btn.clicked.connect(self._open_current_in_3d)
        self.control_layout.addWidget(open3d_btn)

        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous frame")
        self.next_btn = QPushButton("Next frame ▶")
        self.prev_btn.clicked.connect(lambda: self._select_relative(-1))
        self.next_btn.clicked.connect(lambda: self._select_relative(1))
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.next_btn)
        movie_btn = QPushButton("🎞 Create movie…")
        movie_btn.clicked.connect(self.open_movie_dialog)
        nav_row.addWidget(movie_btn)
        gpu_btn = QPushButton("GPU 2D viewer")
        gpu_btn.clicked.connect(self.open_gpu_viewer)
        nav_row.addWidget(gpu_btn)
        self.control_layout.addLayout(nav_row)
        zoom_row = QHBoxLayout()
        zoom_btn = QPushButton("Select region and zoom")
        zoom_btn.clicked.connect(self.enable_region_zoom)
        reset_zoom_btn = QPushButton("Reset view")
        reset_zoom_btn.clicked.connect(self.reset_view)
        zoom_row.addWidget(zoom_btn); zoom_row.addWidget(reset_zoom_btn)
        self.control_layout.addLayout(zoom_row)
        ann_row = QHBoxLayout()
        text_btn = QPushButton("Add text")
        text_btn.clicked.connect(self.start_text_annotation)
        arrow_btn = QPushButton("Add arrow")
        arrow_btn.clicked.connect(self.start_arrow_annotation)
        clear_ann_btn = QPushButton("Clear annotations")
        clear_ann_btn.clicked.connect(self.clear_annotations)
        ann_row.addWidget(text_btn); ann_row.addWidget(arrow_btn); ann_row.addWidget(clear_ann_btn)
        self.control_layout.addLayout(ann_row)

        roi_box = QGroupBox("Measurement (ROI)")
        roi_layout = QVBoxLayout(roi_box)
        roi_shape_row = QHBoxLayout()
        roi_shape_row.addWidget(QLabel("Shape:"))
        self.roi_shape = QComboBox(); self.roi_shape.addItems(["Rectangle", "Ellipse"])
        roi_shape_row.addWidget(self.roi_shape)
        draw_roi_btn = QPushButton("Draw ROI"); draw_roi_btn.clicked.connect(self.start_roi_draw)
        roi_shape_row.addWidget(draw_roi_btn)
        roi_layout.addLayout(roi_shape_row)
        self.roi_list = QListWidget(); self.roi_list.setMaximumHeight(90)
        self.roi_list.currentRowChanged.connect(self._on_roi_selected)
        roi_layout.addWidget(self.roi_list)
        roi_btn_row = QHBoxLayout()
        remove_roi_btn = QPushButton("Remove selected"); remove_roi_btn.clicked.connect(self.remove_selected_roi)
        clear_roi_btn = QPushButton("Clear all"); clear_roi_btn.clicked.connect(self.clear_rois)
        roi_btn_row.addWidget(remove_roi_btn); roi_btn_row.addWidget(clear_roi_btn)
        roi_layout.addLayout(roi_btn_row)
        self.roi_stats_label = QLabel("Click 'Draw ROI' then click-drag on the plot to measure a region.")
        self.roi_stats_label.setWordWrap(True)
        roi_layout.addWidget(self.roi_stats_label)
        roi_action_row = QHBoxLayout()
        export_roi_btn = QPushButton("Export stats (JSON)…"); export_roi_btn.clicked.connect(self.export_roi_stats)
        time_evo_btn = QPushButton("Time evolution across frames…"); time_evo_btn.clicked.connect(self.compute_roi_time_evolution)
        roi_action_row.addWidget(export_roi_btn); roi_action_row.addWidget(time_evo_btn)
        roi_layout.addLayout(roi_action_row)
        self.control_layout.addWidget(roi_box)
        self.frame_label = QLabel("Frame: - / -")
        self.control_layout.addWidget(self.frame_label)

        mode_box = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_box)
        self.mode_2d = QRadioButton("2D map")
        self.mode_line_index = QRadioButton("Lineout (grid index)")
        self.mode_line_coord = QRadioButton("Lineout (physical coordinate)")
        self.mode_time_series = QRadioButton("Time series (reduced over space)")
        self.mode_2d.setChecked(True)
        for rb in (self.mode_2d, self.mode_line_index, self.mode_line_coord, self.mode_time_series):
            rb.toggled.connect(self._update_mode_widgets)
            rb.toggled.connect(self.refresh_plot)
            mode_layout.addWidget(rb)
        self.control_layout.addWidget(mode_box)

        self.slice_box = QGroupBox("3D slice (this file has 3 axes)")
        slice_form = QFormLayout(self.slice_box)
        self.slice_axis = QComboBox(); self.slice_axis.addItems(["x1", "x2", "x3"])
        self.slice_axis.currentIndexChanged.connect(self._update_slice_controls)
        self.slice_axis.currentIndexChanged.connect(self.refresh_plot)
        self.slice_index = QSpinBox(); self.slice_index.setMinimum(0)
        self.slice_index.valueChanged.connect(self._update_slice_coord_label)
        self.slice_index.valueChanged.connect(self.refresh_plot)
        self.slice_coord_label = QLabel("")
        slice_form.addRow("Fix axis:", self.slice_axis)
        slice_form.addRow("At grid index:", self.slice_index)
        slice_form.addRow("Physical position:", self.slice_coord_label)
        slice_hint = QLabel("3D data can't be shown directly as an image, so the axis above is "
                             "held fixed at one grid index and the remaining two axes are plotted.")
        slice_hint.setWordWrap(True)
        slice_form.addRow(slice_hint)
        self.slice_box.setVisible(False)
        self.control_layout.addWidget(self.slice_box)

        line_box = QGroupBox("Lineout")
        line_form = QFormLayout(line_box)
        self.lineout_axis = QComboBox(); self.lineout_axis.addItems(["x1", "x2", "x3"]); self.lineout_axis.currentTextChanged.connect(self._update_lineout_controls); self.lineout_axis.currentTextChanged.connect(self.refresh_plot)
        self.lineout_index = QSpinBox(); self.lineout_index.setMinimum(0); self.lineout_index.valueChanged.connect(self.refresh_plot)
        self.lineout_coord = QDoubleSpinBox(); self.lineout_coord.setRange(-1e9, 1e9); self.lineout_coord.setDecimals(6); self.lineout_coord.valueChanged.connect(self.refresh_plot)
        line_form.addRow("Along axis:", self.lineout_axis)
        line_form.addRow("Fixed index:", self.lineout_index)
        line_form.addRow("Fixed coordinate:", self.lineout_coord)
        self.control_layout.addWidget(line_box)

        ts_box = QGroupBox("Time series (needs a folder open)")
        ts_form = QFormLayout(ts_box)
        self.reduction_combo = QComboBox(); self.reduction_combo.addItems(["mean", "sum", "integral", "max", "min", "rms", "directional average"]); self.reduction_combo.currentTextChanged.connect(self.refresh_plot)
        ts_form.addRow("Reduction:", self.reduction_combo)
        self.average_direction = QComboBox(); self.average_direction.addItems(["x", "y", "z", "(x,y,z)"]); self.average_direction.setToolTip("Supports average,dir=x/y/z/(x,y,z)")
        self.average_direction.currentTextChanged.connect(self.refresh_plot)
        ts_form.addRow("Direction:", self.average_direction)
        export_ts = QPushButton("Export time series (CSV)…"); export_ts.clicked.connect(self.export_time_series)
        ts_form.addRow(export_ts)
        self.control_layout.addWidget(ts_box)

        session_box = QGroupBox("Session")
        session_row = QHBoxLayout(session_box)
        save_session = QPushButton("Save .xml…"); save_session.clicked.connect(self.save_session)
        load_session = QPushButton("Restore .xml…"); load_session.clicked.connect(self.load_session)
        session_row.addWidget(save_session); session_row.addWidget(load_session)
        self.control_layout.addWidget(session_box)

        smooth_box = QGroupBox("Smoothing (1D)")
        smooth_form = QFormLayout(smooth_box)
        self.smooth_method = QComboBox(); self.smooth_method.addItems(["None", "Moving average", "Gaussian"]); self.smooth_method.currentTextChanged.connect(self.refresh_plot)
        self.smooth_window = QSpinBox(); self.smooth_window.setRange(1, 200); self.smooth_window.setValue(5); self.smooth_window.valueChanged.connect(self.refresh_plot)
        smooth_form.addRow("Method:", self.smooth_method); smooth_form.addRow("Window / sigma:", self.smooth_window)
        self.control_layout.addWidget(smooth_box)

        map_box = QGroupBox("2D map rendering")
        map_form = QFormLayout(map_box)
        self.cmap_category = QComboBox(); self.cmap_category.addItems(list(style.COLORMAPS.keys())); self.cmap_category.currentTextChanged.connect(self._populate_cmaps)
        self.cmap_combo = QComboBox(); self.cmap_combo.currentTextChanged.connect(self.refresh_plot)
        self._populate_cmaps()
        map_form.addRow("Colormap group:", self.cmap_category); map_form.addRow("Colormap:", self.cmap_combo)
        self.palette_combo = QComboBox(); self.palette_combo.addItem(USE_LEGACY_CMAP); self.palette_combo.addItems(list(ALL_PALETTES.keys())); self.palette_combo.setCurrentText(USE_LEGACY_CMAP); self.palette_combo.currentTextChanged.connect(self.refresh_plot)
        self.mapping_combo = QComboBox(); self.mapping_combo.addItems(["Scalar", "Cyclic phase"]); self.mapping_combo.currentTextChanged.connect(self.refresh_plot)
        self.palette_reverse = QCheckBox("Reverse palette"); self.palette_reverse.stateChanged.connect(self.refresh_plot)
        self.phase_offset = QDoubleSpinBox(); self.phase_offset.setRange(0.0, 1.0); self.phase_offset.setDecimals(3); self.phase_offset.setSingleStep(0.01); self.phase_offset.valueChanged.connect(self.refresh_plot)
        self.gamma_spin = QDoubleSpinBox(); self.gamma_spin.setRange(0.1, 4.0); self.gamma_spin.setDecimals(2); self.gamma_spin.setValue(1.0); self.gamma_spin.setSingleStep(0.1); self.gamma_spin.valueChanged.connect(self.refresh_plot)
        self.contrast_spin = QDoubleSpinBox(); self.contrast_spin.setRange(0.5, 2.5); self.contrast_spin.setDecimals(2); self.contrast_spin.setValue(1.0); self.contrast_spin.setSingleStep(0.1); self.contrast_spin.valueChanged.connect(self.refresh_plot)
        self.black_floor_spin = QDoubleSpinBox(); self.black_floor_spin.setRange(0.0, 0.5); self.black_floor_spin.setDecimals(3); self.black_floor_spin.setValue(0.0); self.black_floor_spin.setSingleStep(0.01); self.black_floor_spin.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Palette preset:", self.palette_combo); map_form.addRow("Mapping:", self.mapping_combo); map_form.addRow("Reverse palette:", self.palette_reverse)
        map_form.addRow("Phase offset:", self.phase_offset); map_form.addRow("Gamma:", self.gamma_spin); map_form.addRow("Contrast:", self.contrast_spin); map_form.addRow("Black floor:", self.black_floor_spin)
        self.palette_note = QLabel("Palette controls affect the rendered field without changing the underlying data."); self.palette_note.setWordWrap(True); map_form.addRow(self.palette_note)
        self.reverse_cmap = QCheckBox("Reverse legacy matplotlib colormap"); self.reverse_cmap.stateChanged.connect(self.refresh_plot); map_form.addRow(self.reverse_cmap)
        self.cbar_position = QComboBox(); self.cbar_position.addItems(["right", "left", "top", "bottom"])
        self.cbar_position.currentTextChanged.connect(self._on_cbar_position_changed)
        map_form.addRow("Colorbar position:", self.cbar_position)
        self.cbar_box = QCheckBox("Colorbar box/outline"); self.cbar_box.setChecked(True)
        self.cbar_box.stateChanged.connect(self.refresh_plot)
        map_form.addRow(self.cbar_box)
        self.cbar_width = QDoubleSpinBox(); self.cbar_width.setRange(0.02, 1.0); self.cbar_width.setDecimals(3); self.cbar_width.setValue(0.10); self.cbar_width.setSingleStep(0.01); self.cbar_width.valueChanged.connect(self.refresh_plot)
        self.cbar_height = QDoubleSpinBox(); self.cbar_height.setRange(0.02, 1.0); self.cbar_height.setDecimals(3); self.cbar_height.setValue(0.80); self.cbar_height.setSingleStep(0.01); self.cbar_height.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar width:", self.cbar_width); map_form.addRow("Colorbar height:", self.cbar_height)
        self.cbar_label_position = QComboBox(); self.cbar_label_position.addItems(["auto", "left", "right", "top", "bottom"]); self.cbar_label_position.currentTextChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar label side:", self.cbar_label_position)
        self.cbar_label_rotation = QDoubleSpinBox(); self.cbar_label_rotation.setRange(-360, 360); self.cbar_label_rotation.setValue(90); self.cbar_label_rotation.setDecimals(1); self.cbar_label_rotation.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar label rotation:", self.cbar_label_rotation)
        self.cbar_label_pad = QDoubleSpinBox(); self.cbar_label_pad.setRange(0, 60); self.cbar_label_pad.setValue(8); self.cbar_label_pad.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Colorbar label spacing:", self.cbar_label_pad)
        cbar_hint = QLabel("Tip: click-drag the colorbar itself to move it anywhere on the figure. "
                            "A plain click (no drag) opens the color-range dialog as before.")
        cbar_hint.setWordWrap(True)
        map_form.addRow(cbar_hint)
        self.symmetric_cbar = QCheckBox("Symmetric color limits"); self.symmetric_cbar.setChecked(True); self.symmetric_cbar.stateChanged.connect(self.refresh_plot); map_form.addRow(self.symmetric_cbar)
        self.clip_percentile = QDoubleSpinBox(); self.clip_percentile.setRange(0, 49); self.clip_percentile.setSuffix(" %"); self.clip_percentile.valueChanged.connect(self.refresh_plot); map_form.addRow("Clip outliers:", self.clip_percentile)
        self.contour_overlay = QCheckBox("Overlay contour lines"); self.contour_overlay.stateChanged.connect(self.refresh_plot); map_form.addRow(self.contour_overlay)
        self.n_contours = QSpinBox(); self.n_contours.setRange(2, 30); self.n_contours.setValue(8); self.n_contours.valueChanged.connect(self.refresh_plot); map_form.addRow("Contour levels:", self.n_contours)
        self.contour_cmap = QComboBox(); self.contour_cmap.addItems(["black", "white", "viridis", "plasma", "turbo", "coolwarm", "RdBu_r"]); self.contour_cmap.currentTextChanged.connect(self.refresh_plot); map_form.addRow("Contour colors:", self.contour_cmap)
        self.contour_limits = QCheckBox("Separate contour color limits"); self.contour_limits.stateChanged.connect(self.refresh_plot); map_form.addRow(self.contour_limits)
        self.contour_vmin = QDoubleSpinBox(); self.contour_vmin.setRange(-1e300, 1e300); self.contour_vmin.setDecimals(10); self.contour_vmin.setValue(-1.0); self.contour_vmin.valueChanged.connect(self.refresh_plot)
        self.contour_vmax = QDoubleSpinBox(); self.contour_vmax.setRange(-1e300, 1e300); self.contour_vmax.setDecimals(10); self.contour_vmax.setValue(1.0); self.contour_vmax.valueChanged.connect(self.refresh_plot)
        map_form.addRow("Contour vmin:", self.contour_vmin); map_form.addRow("Contour vmax:", self.contour_vmax)
        self.interp_combo = QComboBox(); self.interp_combo.addItems(["nearest", "bilinear", "bicubic", "gaussian"]); self.interp_combo.currentTextChanged.connect(self.refresh_plot); map_form.addRow("Shading:", self.interp_combo)
        self.aspect_combo = QComboBox(); self.aspect_combo.addItems(["auto", "equal"]); self.aspect_combo.currentTextChanged.connect(self.refresh_plot); map_form.addRow("Aspect:", self.aspect_combo)
        self.smooth_2d_check = QCheckBox("Apply smoothing to 2D map too"); self.smooth_2d_check.stateChanged.connect(self.refresh_plot); map_form.addRow(self.smooth_2d_check)
        self.control_layout.addWidget(map_box)

        backend_box = QGroupBox("Interactive rendering backend")
        backend_form = QFormLayout(backend_box)
        self.backend_combo = QComboBox(); self.backend_combo.addItems(["Matplotlib (compatible)", "VisPy (GPU, optional)"])
        self.backend_combo.currentTextChanged.connect(self._on_backend_changed)
        backend_form.addRow("Backend:", self.backend_combo)
        backend_note = QLabel("Matplotlib remains the publication-quality default. VisPy is used for GPU-backed interactive 2D fields when installed.")
        backend_note.setWordWrap(True); backend_form.addRow(backend_note)
        self.control_layout.addWidget(backend_box)

        view_box = QGroupBox("View and axes")
        view_form = QFormLayout(view_box)
        self.x_range_check = QCheckBox("Manual x range")
        self.x_range_min = QDoubleSpinBox(); self.x_range_min.setRange(-1e12, 1e12); self.x_range_min.setDecimals(6)
        self.x_range_max = QDoubleSpinBox(); self.x_range_max.setRange(-1e12, 1e12); self.x_range_max.setDecimals(6)
        self.x_range_check.stateChanged.connect(self.refresh_plot); self.x_range_min.valueChanged.connect(self.refresh_plot); self.x_range_max.valueChanged.connect(self.refresh_plot)
        view_form.addRow(self.x_range_check); view_form.addRow("x min:", self.x_range_min); view_form.addRow("x max:", self.x_range_max)
        self.y_range_check = QCheckBox("Manual y range")
        self.y_range_min = QDoubleSpinBox(); self.y_range_min.setRange(-1e12, 1e12); self.y_range_min.setDecimals(6)
        self.y_range_max = QDoubleSpinBox(); self.y_range_max.setRange(-1e12, 1e12); self.y_range_max.setDecimals(6)
        self.y_range_check.stateChanged.connect(self.refresh_plot); self.y_range_min.valueChanged.connect(self.refresh_plot); self.y_range_max.valueChanged.connect(self.refresh_plot)
        view_form.addRow(self.y_range_check); view_form.addRow("y min:", self.y_range_min); view_form.addRow("y max:", self.y_range_max)
        self.title_edit = QLineEdit(); self.title_edit.textChanged.connect(self.refresh_plot); view_form.addRow("Title:", self.title_edit)
        self.tick_format = QComboBox(); self.tick_format.addItems(["Auto", "Scientific", "Plain"]); self.tick_format.currentTextChanged.connect(self.refresh_plot); view_form.addRow("Tick format:", self.tick_format)
        self.fig_width = QDoubleSpinBox(); self.fig_width.setRange(3, 20); self.fig_width.setValue(7); self.fig_width.setSuffix(" in"); self.fig_width.valueChanged.connect(self._resize_figure)
        self.fig_height = QDoubleSpinBox(); self.fig_height.setRange(3, 20); self.fig_height.setValue(5.5); self.fig_height.setSuffix(" in"); self.fig_height.valueChanged.connect(self._resize_figure)
        view_form.addRow("Figure width:", self.fig_width); view_form.addRow("Figure height:", self.fig_height)
        self.control_layout.addWidget(view_box)

        lim_box = QGroupBox("Color normalization")
        lim_form = QFormLayout(lim_box)
        self.norm_combo = QComboBox(); self.norm_combo.addItems(["linear", "log"]); self.norm_combo.currentTextChanged.connect(self.refresh_plot); lim_form.addRow("Normalization:", self.norm_combo)
        self.vmin_check = QCheckBox("Manual minimum"); self.vmin = QDoubleSpinBox(); self.vmin.setRange(-1e300, 1e300); self.vmin.setDecimals(10)
        self.vmax_check = QCheckBox("Manual maximum"); self.vmax = QDoubleSpinBox(); self.vmax.setRange(-1e300, 1e300); self.vmax.setDecimals(10)
        self.vmin_check.stateChanged.connect(self.refresh_plot); self.vmin.valueChanged.connect(self.refresh_plot); self.vmax_check.stateChanged.connect(self.refresh_plot); self.vmax.valueChanged.connect(self.refresh_plot)
        lim_form.addRow(self.vmin_check); lim_form.addRow("vmin:", self.vmin); lim_form.addRow(self.vmax_check); lim_form.addRow("vmax:", self.vmax)
        self.control_layout.addWidget(lim_box)

        color_box = QGroupBox("Line color")
        color_form = QFormLayout(color_box)
        self.color_preview = QLabel(); self.color_preview.setFixedSize(24, 16); self._update_color_preview()
        color_btn = self.add_color_picker_button(self._on_color_picked, "Pick line color…")
        color_form.addRow(self.color_preview, color_btn)
        self.control_layout.addWidget(color_box)

        self.info_label = QLabel("No file loaded"); self.info_label.setWordWrap(True); self.control_layout.addWidget(self.info_label)
        self._update_mode_widgets()
        self.finish_layout()


    def _on_backend_changed(self, name):
        if "VisPy" in name and self.grid is not None:
            self.open_gpu_viewer()

    def open_gpu_viewer(self):
        if self.grid is None:
            QMessageBox.information(self, "GPU viewer", "Open a 2D field first.")
            return
        if self.grid.ndim != 2:
            QMessageBox.information(self, "GPU viewer", "GPU interactive rendering currently supports 2D scalar fields.")
            return
        try:
            from .gpu_viewer import GPUViewerDialog
            if self._gpu_dialog is None:
                self._gpu_dialog = GPUViewerDialog(self)
                self._gpu_dialog.finished.connect(lambda _=0: setattr(self, "_gpu_dialog", None))
            self._ensure_grid_loaded()
            self._gpu_dialog.set_field(self.grid.data, self.grid.extent(), self._cmap_name())
            self._gpu_dialog.show(); self._gpu_dialog.raise_(); self._gpu_dialog.activateWindow()
        except Exception as exc:
            QMessageBox.warning(self, "GPU viewer unavailable", str(exc))

    def open_movie_dialog(self):
        if len(self.files) < 2:
            QMessageBox.information(self, "Movie export", "Open a folder containing at least two time-step files first.")
            return
        if not self.mode_2d.isChecked() or self.grid is None or self.grid.ndim != 2:
            QMessageBox.information(self, "Movie export", "Switch to 2D map mode with a 2D scalar dataset before creating a movie.")
            return
        dlg = MovieDialog(len(self.files), self.file_list.currentRow(), self)
        if dlg.exec_() != QDialog.Accepted:
            return
        output, start, end, step, fps, fmt = dlg.values()
        if not output:
            suffix = ".mp4" if fmt == "MP4" else ".gif"
            output, _ = QFileDialog.getSaveFileName(self, "Save movie", "simulation_movie" + suffix, f"{fmt} (*{suffix})")
            if not output:
                return
        # Capture every widget value up front -- the export itself runs on a
        # worker thread (encoding dozens/hundreds of frames can take a while
        # and used to freeze the whole window), so nothing below this point
        # may touch a Qt widget from the job() closure.
        cmap = self._cmap_name()
        vmin = self.vmin.value() if self.vmin_check.isChecked() else None
        vmax = self.vmax.value() if self.vmax_check.isChecked() else None
        symmetric = self.symmetric_cbar.isChecked()
        clip_percentile = self.clip_percentile.value()
        title_prefix = self.title_edit.text()
        files = list(self.files)
        use_opencv = fmt.startswith("MP4 (OpenCV)")
        normalization = self.norm_combo.currentText()
        aspect = self.aspect_combo.currentText()
        interpolation = self.interp_combo.currentText()
        figsize = (self.fig_width.value(), self.fig_height.value())

        def job():
            if use_opencv:
                from ..export.opencv_movie import export_grid_movie_opencv
                return export_grid_movie_opencv(
                    files, output, frame_start=start, frame_end=end, frame_step=step, fps=fps,
                    cmap=cmap, vmin=vmin, vmax=vmax, symmetric=symmetric,
                    clip_percentile=clip_percentile, title_prefix=title_prefix,
                    loader=GridFile.load,
                )
            from ..export.animation import export_grid_movie
            return export_grid_movie(
                files, output, frame_start=start, frame_end=end, frame_step=step, fps=fps,
                cmap=cmap, normalization=normalization, vmin=vmin, vmax=vmax,
                symmetric=symmetric, clip_percentile=clip_percentile,
                aspect=aspect, interpolation=interpolation,
                title_prefix=title_prefix, figsize=figsize,
                dpi=150,
            )

        from .workers import run_in_background
        run_in_background(
            self, job,
            on_success=lambda n: QMessageBox.information(self, "Movie export complete", f"Rendered {n} frames to:\n{output}"),
            on_error=lambda exc: QMessageBox.critical(self, "Movie export failed", str(exc)),
            label="Exporting movie… this keeps the window responsive.",
        )

    def _populate_cmaps(self):
        current = self.cmap_combo.currentText()
        self.cmap_combo.blockSignals(True); self.cmap_combo.clear()
        self.cmap_combo.addItems(style.COLORMAPS.get(self.cmap_category.currentText(), ["viridis"]))
        if current in [self.cmap_combo.itemText(i) for i in range(self.cmap_combo.count())]: self.cmap_combo.setCurrentText(current)
        self.cmap_combo.blockSignals(False)
        self.refresh_plot()

    def _on_color_picked(self, color): self._update_color_preview(); self.refresh_plot()
    def _update_color_preview(self): self.color_preview.setStyleSheet(f"background:{self.accent_hex()}; border:1px solid #777;")

    def _update_lineout_controls(self):
        """Keep lineout index/coordinate controls tied to the selected physical axis."""
        if self.grid is None or self.grid.ndim < 2:
            return
        along_axis = min(self.lineout_axis.currentIndex(), self.grid.ndim - 1)
        # For an index lineout, the controlled index belongs to the first
        # non-lineout physical axis. For a 2D field this is simply the other axis.
        fixed_axis = 1 - along_axis if self.grid.ndim == 2 else next((i for i in range(self.grid.ndim) if i != along_axis), 0)
        fixed_np_axis = self.grid.ndim - 1 - fixed_axis
        self.lineout_index.blockSignals(True)
        self.lineout_index.setMaximum(max(0, int(self.grid.shape[fixed_np_axis] - 1)))
        self.lineout_index.setValue(min(self.lineout_index.value(), self.lineout_index.maximum()))
        self.lineout_index.blockSignals(False)
        coords = self.grid.axes[fixed_axis].values()
        if coords.size:
            self.lineout_coord.blockSignals(True)
            self.lineout_coord.setRange(float(coords.min()), float(coords.max()))
            if not (coords.min() <= self.lineout_coord.value() <= coords.max()):
                self.lineout_coord.setValue(float(0.5 * (coords.min() + coords.max())))
            self.lineout_coord.blockSignals(False)

    def _update_slice_controls(self):
        """Show/hide and range-limit the 3D-slice controls based on the
        currently loaded file's dimensionality, and pick a sensible default
        slice axis (the axis with the fewest grid points, since that's
        almost always the one a user wants to hold fixed -- e.g. a "thin"
        3D Simulation run with only 2 points along one axis)."""
        if self.grid is None:
            self.slice_box.setVisible(False)
            return
        is_3d = self.grid.ndim == 3
        self.slice_box.setVisible(is_3d)
        if not is_3d:
            return
        if self.slice_axis.property("_auto_selected_for") != id(self.grid):
            smallest_axis = min(range(3), key=lambda i: self.grid.axes[i].n)
            self.slice_axis.blockSignals(True)
            self.slice_axis.setCurrentIndex(smallest_axis)
            self.slice_axis.blockSignals(False)
            self.slice_axis.setProperty("_auto_selected_for", id(self.grid))
        axis = self.grid.axes[self.slice_axis.currentIndex()]
        self.slice_index.blockSignals(True)
        self.slice_index.setMaximum(max(0, axis.n - 1))
        self.slice_index.setValue(min(self.slice_index.value(), self.slice_index.maximum()))
        self.slice_index.blockSignals(False)
        self._update_slice_coord_label()
        # The manual X/Y-range controls must track whichever two axes are
        # actually displayed after slicing, not the original three.
        remaining = [self.grid.axes[i] for i in range(3) if i != self.slice_axis.currentIndex()]
        self.x_range_min.setValue(float(remaining[0].min)); self.x_range_max.setValue(float(remaining[0].max))
        self.y_range_min.setValue(float(remaining[1].min)); self.y_range_max.setValue(float(remaining[1].max))

    def _update_slice_coord_label(self):
        if self.grid is None or self.grid.ndim != 3:
            return
        axis = self.grid.axes[self.slice_axis.currentIndex()]
        idx = min(self.slice_index.value(), axis.n - 1)
        value = float(axis.values()[idx]) if axis.n else 0.0
        self.slice_coord_label.setText(f"{axis.name} = {value:.6g} {axis.units} (index {idx} of {axis.n})")

    def _effective_2d_grid(self):
        """The GridFile that 2D-mode plotting/analysis should actually use:
        the loaded file itself if it's already 2D, or a 2D slice through it
        if it's 3D (see GridFile.slice2d). Centralizing this here means
        `_plot_2d` and friends never need to special-case 3D data."""
        if self.grid is None:
            return None
        if self.grid.ndim == 2:
            return self.grid
        if self.grid.ndim == 3:
            axis = self.slice_axis.currentIndex()
            index = min(self.slice_index.value(), self.grid.axes[axis].n - 1)
            return self.grid.slice2d(axis=axis, index=index)
        raise ValueError(f"2D view requires a 2D or 3D dataset; this file is {self.grid.ndim}D")

    def _update_mode_widgets(self):
        is_2d = self.mode_2d.isChecked(); is_line_index = self.mode_line_index.isChecked(); is_line_coord = self.mode_line_coord.isChecked(); is_ts = self.mode_time_series.isChecked()
        self.lineout_index.setEnabled(is_line_index); self.lineout_coord.setEnabled(is_line_coord); self.lineout_axis.setEnabled(is_line_index or is_line_coord); self.reduction_combo.setEnabled(is_ts); self.average_direction.setEnabled(is_ts and self.reduction_combo.currentText() == "directional average")
        for w in (self.cmap_category, self.cmap_combo, self.palette_combo, self.mapping_combo, self.palette_reverse, self.phase_offset, self.gamma_spin, self.contrast_spin, self.black_floor_spin, self.reverse_cmap, self.symmetric_cbar, self.clip_percentile, self.contour_overlay, self.n_contours, self.cbar_label_position, self.cbar_label_rotation, self.cbar_label_pad, self.contour_cmap, self.contour_limits, self.contour_vmin, self.contour_vmax, self.interp_combo, self.aspect_combo, self.smooth_2d_check, self.norm_combo, self.vmin_check, self.vmin, self.vmax_check, self.vmax): w.setEnabled(is_2d)

    def _open_current_in_3d(self):
        row = self.file_list.currentRow()
        if 0 <= row < len(self.files):
            self.open_in_3d_requested.emit(self.files[row])

    def _pending_selection_changed(self, row):
        if row >= 0 and row < len(self.files):
            self.info_label.setText(f"Selected: {Path(self.files[row]).name}. Click Apply selection to load the frame.")

    def apply_selection(self):
        row = self.file_list.currentRow()
        if 0 <= row < len(self.files):
            self.on_file_selected(row)

    def _select_relative(self, delta):
        count = self.file_list.count()
        if count == 0: return
        row = self.file_list.currentRow()
        if row < 0: row = 0
        new_row = max(0, min(count - 1, row + delta))
        if new_row != row:
            self.file_list.blockSignals(True)
            self.file_list.setCurrentRow(new_row)
            self.file_list.blockSignals(False)
            self.apply_selection()

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.files): return
        try:
            if self._series is None or list(self._series.paths) != list(self.files):
                self._series = LazyGridSeries(self.files)
            cached = self._series._cache.get(row)
            if cached is not None:
                # Already have the full GridFile (data included) from a
                # recent visit -- reuse it directly instead of paying for
                # another HDF5 open just to re-read metadata we already
                # have. This is what makes scrubbing back and forth
                # between recently-visited frames actually fast, not just
                # the later `_ensure_grid_loaded()` data-cache lookup.
                self.grid = cached
            else:
                self.grid = GridFile.info(self.files[row])
        except Exception as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>Error reading file:<br>{exc}</span>"); return
        self._update_lineout_controls()
        self._update_slice_controls()
        if self.grid.ndim != 3:
            # For a 3D file, _update_slice_controls() above already set
            # x_range/y_range to whichever two axes remain after slicing.
            if self.grid.axes:
                ax0 = self.grid.axes[0]; self.x_range_min.setValue(float(ax0.min)); self.x_range_max.setValue(float(ax0.max))
            if len(self.grid.axes) > 1:
                ax1 = self.grid.axes[1]; self.y_range_min.setValue(float(ax1.min)); self.y_range_max.setValue(float(ax1.max))
        # Color limits are intentionally computed lazily on first 2D render.
        self.frame_label.setText(f"Frame: {row + 1} / {len(self.files)}")
        self.prev_btn.setEnabled(row > 0); self.next_btn.setEnabled(row < len(self.files) - 1)
        self.info_label.setText(f"<b>{self.grid.name}</b> ({self.grid.label})<br>units: {self.grid.units}<br>shape: {self.grid.shape}<br>time: {self.grid.time:g} {self.grid.time_units}  iter: {self.grid.iteration}<br>{len(self.files)} file(s) in current folder")
        self._last_limits = None
        self._default_limits = None
        self._force_full_view = True
        # NOTE: deliberately NOT resetting self._active_plot_mode here.
        # refresh_plot() already recomputes `mode` from the current radio
        # button + the new grid's ndim, so a genuine mode change (e.g. a
        # newly selected file collapses from 2D to 1D, or the user
        # switches radio buttons) is still detected and still forces the
        # full ax.cla() + colorbar-rebuild path where it's actually
        # needed. Forcing that reset unconditionally on every frame change
        # -- the single most common interactive action -- meant every
        # "next frame" click paid for a full axes teardown, a brand new
        # colorbar, and a full theme re-application, even for the totally
        # ordinary case of scrubbing through frames of the same quantity
        # with unchanged shape/axes. _plot_2d()'s `needs_new_image` check
        # already handles the case where shape *does* change between
        # files by rebuilding the image (and colorbar) then; there is
        # nothing left for this reset to protect against.
        self._time_series_cache.clear()
        self._deactivate_mouse_tools()
        # Public signal contract: always emit the shared Dataset abstraction.
        # Keep metadata-only GridFile internal to this tab so consumers never
        # accidentally call Dataset-only APIs on a legacy wrapper.
        try:
            self.dataset_changed.emit(self.grid.to_dataset())
        except Exception:
            # A metadata-only frame is valid during folder browsing; loading is
            # deferred until the plot/analysis operation requests the field.
            self.dataset_changed.emit(self.grid)
        self.series_changed.emit(list(self.files))
        self.refresh_plot()

    def _deactivate_mouse_tools(self):
        self._annotation_mode = None
        self._arrow_start = None
        self._roi_mode = None
        self._roi_draft = None
        if self._roi_preview_patch is not None:
            try: self._roi_preview_patch.remove()
            except Exception: pass
            self._roi_preview_patch = None
        try:
            self.canvas.deactivate_navigation()
        except Exception:
            pass
        try:
            if self._rectangle_selector is not None:
                self._rectangle_selector.set_active(False)
                self._rectangle_selector.disconnect_events()
        except Exception:
            pass
        self._rectangle_selector = None
        try:
            self.canvas.deactivate_navigation()
        except Exception:
            pass

    def _ensure_grid_loaded(self):
        if self.grid is None:
            return None
        if getattr(self.grid, "data", None) is None:
            row = max(0, self.file_list.currentRow())
            # Route through the bounded LazyGridSeries cache rather than
            # re-reading the HDF5 file from disk every time: scrubbing
            # back and forth between recently-visited frames (the most
            # common interactive pattern) then hits the cache instead of
            # paying a full read again.
            if self._series is not None and list(self._series.paths) == list(self.files):
                self.grid = self._series.load(row)
            else:
                self.grid = GridFile.load(self.files[row])
            self._update_lineout_controls()
            self._update_slice_controls()
        return self.grid

    def refresh_plot(self):
        if self.grid is None:
            return
        self._ensure_grid_loaded()
        mode = (
            "time_series" if self.mode_time_series.isChecked() else
            "2d" if self.mode_2d.isChecked() and self.grid.ndim >= 2 else
            "line_coord" if self.mode_line_coord.isChecked() and self.grid.ndim >= 2 else
            "line_index"
        )
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else self.canvas.figure.add_subplot(111)
        mode_changed = self._active_plot_mode != mode
        if mode_changed:
            self._clear_plot_artists(ax)
            self._active_plot_mode = mode
            self.canvas.mark_theme_dirty()  # ax.cla() reset styling to matplotlib defaults
        elif self._last_limits is not None and not self.x_range_check.isChecked() and not self.y_range_check.isChecked() and not self._force_full_view:
            self._last_limits = (ax.get_xlim(), ax.get_ylim())

        try:
            if mode == "time_series":
                self._plot_time_series(ax)
            elif mode == "2d":
                self._plot_2d(ax)
            elif mode == "line_coord":
                self._plot_lineout_coord(ax)
            else:
                self._plot_lineout_index(ax)
        except Exception as exc:
            ax.cla()
            self._clear_colorbar()
            self._image = None
            self._line_artist = None
            ax.text(0.5, 0.5, f"Unable to compute this view:\n{exc}", ha="center", va="center", transform=ax.transAxes)
            self.info_label.setText(f"Analysis error: {exc}")

        if self._last_limits and not self.x_range_check.isChecked() and not self.y_range_check.isChecked() and not self._force_full_view:
            try:
                ax.set_xlim(*self._last_limits[0]); ax.set_ylim(*self._last_limits[1])
            except Exception:
                pass
        elif self._force_full_view:
            try:
                if mode == "2d" and self.grid.ndim >= 2:
                    ext = self.grid.extent()
                    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
                else:
                    ax.relim(); ax.autoscale_view()
            except Exception:
                pass
            self._force_full_view = False
        self._draw_annotations(ax)
        self._draw_rois(ax)
        self.canvas.draw_idle()
        self._last_limits = (ax.get_xlim(), ax.get_ylim())

    def _clear_colorbar(self):
        if self._cbar is not None:
            try:
                self._cbar.remove()
            except Exception:
                try: self._cbar.ax.remove()
                except Exception: pass
        self._cbar = None

    def _clear_plot_artists(self, ax):
        self._clear_colorbar()
        for artist in list(getattr(ax, "images", [])):
            try: artist.remove()
            except Exception: pass
        if self._line_artist is not None:
            try: self._line_artist.remove()
            except Exception: pass
        self._line_artist = None
        for c in self._contour_artists:
            try: c.remove()
            except Exception: pass
        self._contour_artists = []
        self._last_contour_sig = None
        for artist in self._annotation_artists:
            try: artist.remove()
            except Exception: pass
        self._annotation_artists = []
        ax.cla()
        self._image = None

    def _resize_figure(self): self.canvas.figure.set_size_inches(self.fig_width.value(), self.fig_height.value(), forward=True); self.refresh_plot()
    def _cmap_name(self):
        name = self.cmap_combo.currentText() or "viridis"
        return name + "_r" if self.reverse_cmap.isChecked() and not name.endswith("_r") else name

    def _plot_2d(self, ax):
        from matplotlib.colors import LogNorm, Normalize
        grid2d = self._effective_2d_grid()
        data = grid2d.data
        if self.smooth_2d_check.isChecked():
            data = smooth_2d(data, self.smooth_method.currentText(), self.smooth_window.value())
        extent = grid2d.extent()
        palette_choice = self.palette_combo.currentText()
        if not palette_choice or palette_choice == USE_LEGACY_CMAP:
            # Plain matplotlib colormap picker (Colormap group/Colormap +
            # its own Reverse checkbox). This is the default path.
            cmap_name = self._cmap_name()
        else:
            # A custom palette preset was explicitly chosen; it has its own
            # independent reverse checkbox ("Reverse palette").
            cmap_name = make_palette(palette_choice, reverse=self.palette_reverse.isChecked(), phase=self.phase_offset.value())
        finite = data[np.isfinite(data)] if self.clip_percentile.value() > 0 else None
        if finite is not None and finite.size == 0:
            raise ValueError("No finite values in selected field")
        if finite is None:
            try:
                vmin, vmax = float(np.nanmin(data)), float(np.nanmax(data))
            except ValueError:
                raise ValueError("No finite values in selected field")
        else:
            vmin, vmax = float(finite.min()), float(finite.max())
        # Visual-only contrast controls. These alter the normalization, not the Dataset.
        pct = self.clip_percentile.value()
        if pct > 0:
            vmin, vmax = np.percentile(finite, [pct, 100 - pct])
        if self.vmin_check.isChecked(): vmin = self.vmin.value()
        if self.vmax_check.isChecked(): vmax = self.vmax.value()
        if self.symmetric_cbar.isChecked() and not (self.vmin_check.isChecked() or self.vmax_check.isChecked()):
            m = max(abs(vmin), abs(vmax)); vmin, vmax = -m, m
        if vmin == vmax:
            delta = max(abs(vmin) * 1e-12, 1e-12)
            vmin -= delta; vmax += delta
        if self.norm_combo.currentText() == "log":
            if vmin <= 0 or vmax <= 0:
                raise ValueError("Log normalization requires positive color limits")
            norm = LogNorm(vmin=vmin, vmax=vmax)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)

        # Apply palette-shaping through a lightweight custom normalization wrapper.
        base_norm = norm
        gamma = float(self.gamma_spin.value())
        contrast = float(self.contrast_spin.value())
        floor = float(self.black_floor_spin.value())
        if self.norm_combo.currentText() == "linear" and (abs(gamma-1.0) > 1e-12 or abs(contrast-1.0) > 1e-12 or floor > 0):
            from matplotlib.colors import Normalize as _Normalize
            class _StyledNorm(_Normalize):
                def __call__(self, value, clip=None):
                    a = super().__call__(value, clip=clip)
                    a = np.asarray(a, dtype=float)
                    a = np.clip(a, 0.0, 1.0)
                    if floor > 0:
                        a = np.where(a < floor, 0.0, (a - floor) / max(1.0-floor, 1e-12))
                    a = np.clip((a - 0.5) * contrast + 0.5, 0.0, 1.0)
                    if gamma != 1.0:
                        a = np.power(a, gamma)
                    return a
                def inverse(self, value):
                    a = np.asarray(value, dtype=float)
                    if gamma != 1.0: a = np.power(np.clip(a,0,1), 1.0/gamma)
                    a = np.clip((a-0.5)/max(contrast,1e-12)+0.5,0,1)
                    if floor > 0: a = a*(1.0-floor)+floor
                    return self.vmin + a*(self.vmax-self.vmin)
            norm = _StyledNorm(vmin=vmin, vmax=vmax)

        needs_new_image = self._image is None or tuple(getattr(self._image.get_array(), "shape", ())) != tuple(data.shape)
        if needs_new_image:
            self._clear_colorbar()
            self._image = ax.imshow(data, origin="lower", extent=extent, aspect=self.aspect_combo.currentText(), cmap=cmap_name, norm=norm, interpolation=self.interp_combo.currentText())
        else:
            self._image.set_data(data)
            self._image.set_extent(extent)
            self._image.set_cmap(cmap_name)
            self._image.set_norm(norm)
            self._image.set_interpolation(self.interp_combo.currentText())
            ax.set_aspect(self.aspect_combo.currentText())

        contour_sig = (
            id(self.grid), self.grid.ndim,
            self.slice_axis.currentIndex() if self.grid.ndim == 3 else None,
            self.slice_index.value() if self.grid.ndim == 3 else None,
            self.smooth_2d_check.isChecked(), self.smooth_method.currentText(), self.smooth_window.value(),
            self.contour_overlay.isChecked(), self.n_contours.value(),
            self.contour_limits.isChecked(), round(self.contour_vmin.value(), 10), round(self.contour_vmax.value(), 10),
            self.contour_cmap.currentText(), round(vmin, 10), round(vmax, 10),
        )
        if self.contour_overlay.isChecked() and self._contour_artists and contour_sig == getattr(self, "_last_contour_sig", None):
            # Nothing that affects contour geometry or levels changed since
            # the last render (gamma/contrast/black_floor/colormap/aspect/
            # interpolation are pure display remaps and don't reach this
            # signature) -- reuse the existing ContourSet instead of paying
            # for another marching-squares pass, which dominates redraw
            # time on large fields (~100ms+ on a 1024x1024 image).
            pass
        else:
            for c in self._contour_artists:
                try: c.remove()
                except Exception: pass
            self._contour_artists = []
            if self.contour_overlay.isChecked():
                x = np.asarray(grid2d.axes[0].values(), dtype=float)
                y = np.asarray(grid2d.axes[1].values(), dtype=float)
                if x.size != data.shape[0] or y.size != data.shape[1]:
                    x = np.linspace(extent[0], extent[1], data.shape[0])
                    y = np.linspace(extent[2], extent[3], data.shape[1])
                X, Y = np.meshgrid(x, y, indexing="ij")
                levels = self.n_contours.value()
                if self.contour_limits.isChecked() and self.contour_vmin.value() < self.contour_vmax.value():
                    levels = np.linspace(self.contour_vmin.value(), self.contour_vmax.value(), self.n_contours.value())
                else:
                    levels = np.linspace(vmin, vmax, self.n_contours.value())
                cchoice = self.contour_cmap.currentText()
                if cchoice in {"black", "white"}:
                    contour = ax.contour(X, Y, data, levels=levels, colors=cchoice, linewidths=0.55, alpha=0.75)
                else:
                    contour = ax.contour(X, Y, data, levels=levels, cmap=cchoice, linewidths=0.55, alpha=0.85)
                # Modern Matplotlib exposes a ContourSet as one removable artist;
                # older versions exposed child collections. Store the ContourSet
                # itself so contour overlays work across both APIs.
                self._contour_artists = [contour]
            self._last_contour_sig = contour_sig if self.contour_overlay.isChecked() else None
        ax.set_aspect(self.aspect_combo.currentText())
        if self._cbar is None:
            self._cbar = self.canvas.figure.colorbar(self._image, ax=ax, location=self.cbar_position.currentText())
            self.canvas.mark_theme_dirty()  # a fresh colorbar axes needs its own theme styling
            # Apply user-controlled size in normalized figure coordinates.
            bbox = self._cbar.ax.get_position().bounds
            pos = self.cbar_position.currentText()
            w = float(self.cbar_width.value())
            h = float(self.cbar_height.value())
            if pos in ("left", "right"):
                self._cbar.ax.set_position([bbox[0], bbox[1] + (bbox[3]-h)/2, w, h])
            else:
                self._cbar.ax.set_position([bbox[0] + (bbox[2]-w)/2, bbox[1], w, h])
        else:
            self._cbar.update_normal(self._image)
            # Keep width/height responsive when the user changes them after
            # the colorbar has already been created. A manually dragged bar
            # retains its center while being resized.
            try:
                bx, by, bw, bh = self._cbar.ax.get_position().bounds
                w = float(self.cbar_width.value())
                h = float(self.cbar_height.value())
                nx = bx + (bw - w) / 2.0
                ny = by + (bh - h) / 2.0
                self._cbar.ax.set_position([nx, ny, w, h])
                if self._cbar_user_position is not None:
                    self._cbar_user_position = [nx, ny, w, h]
            except Exception:
                pass
        if self._cbar_user_position is not None:
            try:
                self._cbar.ax.set_position(self._cbar_user_position)
            except Exception:
                self._cbar_user_position = None
        self._cbar.outline.set_visible(self.cbar_box.isChecked())
        label = f"{grid2d.label} [{grid2d.units}]" if grid2d.units else grid2d.label
        self._cbar.set_label(label, rotation=self.cbar_label_rotation.value(), labelpad=self.cbar_label_pad.value())
        side = self.cbar_label_position.currentText()
        if side != "auto":
            try:
                if self.cbar_position.currentText() in ("left", "right"):
                    self._cbar.ax.yaxis.set_label_position(side)
                else:
                    self._cbar.ax.xaxis.set_label_position(side)
            except Exception:
                pass
        ax.set_xlabel(self._axis_label(0, grid2d)); ax.set_ylabel(self._axis_label(1, grid2d))
        ax.set_title(self.title_edit.text() or f"t = {grid2d.time:g} {grid2d.time_units}  (iter {grid2d.iteration})")
        if self.x_range_check.isChecked() and self.x_range_min.value() < self.x_range_max.value(): ax.set_xlim(self.x_range_min.value(), self.x_range_max.value())
        if self.y_range_check.isChecked() and self.y_range_min.value() < self.y_range_max.value(): ax.set_ylim(self.y_range_min.value(), self.y_range_max.value())
        if self.tick_format.currentText() != "Auto":
            from matplotlib.ticker import ScalarFormatter
            for axis in (ax.xaxis, ax.yaxis):
                fmt = ScalarFormatter(useMathText=True); fmt.set_scientific(self.tick_format.currentText() == "Scientific"); axis.set_major_formatter(fmt)

    def _on_cbar_position_changed(self):
        """Colorbar location (left/right/top/bottom) can only be set when the
        colorbar axes is created, so force a clean recreation. Any manual
        drag offset is reset since it applied to the old location/orientation."""
        self._cbar_user_position = None
        self._clear_colorbar()
        self.refresh_plot()

    def _on_canvas_press(self, event):
        self._press_info = None
        self._cbar_drag = None
        if self.grid is None or event.inaxes is None or event.x is None or event.y is None:
            return
        self._press_info = {"moved": False}
        if self._cbar is not None and event.inaxes == self._cbar.ax:
            self._cbar_drag = {"press_x": event.x, "press_y": event.y, "orig": self._cbar.ax.get_position().bounds}
            return
        if self._roi_mode is not None and event.xdata is not None and event.ydata is not None:
            self._roi_draft = {"x0": event.xdata, "y0": event.ydata, "ax": event.inaxes}

    def _on_canvas_motion(self, event):
        if self._cbar_drag is not None and self._cbar is not None and event.x is not None and event.y is not None:
            dpx = event.x - self._cbar_drag["press_x"]
            dpy = event.y - self._cbar_drag["press_y"]
            if self._press_info is not None and (dpx * dpx + dpy * dpy) ** 0.5 > 3:
                self._press_info["moved"] = True
            fig = self.canvas.figure
            width_px, height_px = fig.get_size_inches() * fig.dpi
            if width_px <= 0 or height_px <= 0:
                return
            x0, y0, w, h = self._cbar_drag["orig"]
            new_x0 = min(max(x0 + dpx / width_px, 0.0), max(0.0, 1.0 - w))
            new_y0 = min(max(y0 + dpy / height_px, 0.0), max(0.0, 1.0 - h))
            self._cbar.ax.set_position([new_x0, new_y0, w, h])
            self._cbar_user_position = [new_x0, new_y0, w, h]
            self.canvas.canvas.draw_idle()
            return
        if self._roi_draft is not None and event.xdata is not None and event.ydata is not None:
            self._update_roi_preview(event.xdata, event.ydata)

    def _on_canvas_release(self, event):
        drag, press = self._cbar_drag, self._press_info
        self._cbar_drag, self._press_info = None, None
        if drag is not None and press is not None and press.get("moved"):
            return  # dragged the colorbar -- don't also treat this as a click
        if self._roi_draft is not None:
            self._finalize_roi(event)
            return
        self._on_figure_click(event)

    def _update_roi_preview(self, x1, y1):
        """Live-updates a dashed preview patch while dragging out a ROI,
        without triggering a full refresh_plot() (which would recompute
        and redraw the whole image on every mouse-move event)."""
        from matplotlib.patches import Rectangle, Ellipse
        x0, y0, ax = self._roi_draft["x0"], self._roi_draft["y0"], self._roi_draft["ax"]
        if self._roi_preview_patch is not None:
            try: self._roi_preview_patch.remove()
            except Exception: pass
            self._roi_preview_patch = None
        xlo, xhi = min(x0, x1), max(x0, x1)
        ylo, yhi = min(y0, y1), max(y0, y1)
        if xhi <= xlo or yhi <= ylo:
            self.canvas.canvas.draw_idle()
            return
        if self._roi_mode == "rectangle":
            patch = Rectangle((xlo, ylo), xhi - xlo, yhi - ylo, fill=False, edgecolor="yellow", linewidth=1.5, linestyle="--")
        else:
            patch = Ellipse(((xlo + xhi) / 2, (ylo + yhi) / 2), xhi - xlo, yhi - ylo, fill=False, edgecolor="yellow", linewidth=1.5, linestyle="--")
        ax.add_patch(patch)
        self._roi_preview_patch = patch
        self.canvas.canvas.draw_idle()

    def _finalize_roi(self, event):
        x0, y0 = self._roi_draft["x0"], self._roi_draft["y0"]
        self._roi_draft = None
        if self._roi_preview_patch is not None:
            try: self._roi_preview_patch.remove()
            except Exception: pass
            self._roi_preview_patch = None
        shape, self._roi_mode = self._roi_mode, None
        if event.xdata is None or event.ydata is None:
            self.canvas.canvas.draw_idle()
            return
        try:
            roi = RegionOfInterest(shape, x0=x0, y0=y0, x1=event.xdata, y1=event.ydata)
        except ValueError as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>ROI not created: {exc}</span>")
            self.canvas.canvas.draw_idle()
            return
        self._rois.append(roi)
        self.roi_list.addItem(f"{roi.label} ({roi.shape})")
        self.roi_list.setCurrentRow(self.roi_list.count() - 1)
        self.refresh_plot()

    def start_roi_draw(self):
        if self.grid is None:
            QMessageBox.information(self, "No data loaded", "Load a field file first.")
            return
        self._deactivate_mouse_tools()
        self._roi_mode = "rectangle" if self.roi_shape.currentText() == "Rectangle" else "ellipse"
        self.info_label.setText(f"Click-drag on the plot to draw a {self._roi_mode} ROI.")

    def _on_roi_selected(self, row):
        self.refresh_plot()  # re-highlight the selected ROI's outline
        if 0 <= row < len(self._rois):
            self._show_roi_stats(self._rois[row])

    def remove_selected_roi(self):
        row = self.roi_list.currentRow()
        if 0 <= row < len(self._rois):
            del self._rois[row]
            self.roi_list.takeItem(row)
            self.refresh_plot()

    def clear_rois(self):
        self._rois = []
        self.roi_list.clear()
        self.roi_stats_label.setText("Click 'Draw ROI' then click-drag on the plot to measure a region.")
        self._last_roi_results = None
        self.refresh_plot()

    def _show_roi_stats(self, roi):
        try:
            grid2d = self._effective_2d_grid()
            x = np.asarray(grid2d.axes[0].values(), dtype=float)
            y = np.asarray(grid2d.axes[1].values(), dtype=float)
            result = roi_statistics(grid2d.data, x, y, roi)
        except Exception as exc:
            self.roi_stats_label.setText(f"<span style='color:#c0392b'>{exc}</span>")
            return
        self._last_roi_results = result
        lines = [
            f"<b>{roi.label}</b> ({roi.shape}) — {result['n_points']} point(s)",
            f"min={result['min']:.4g}  max={result['max']:.4g}  mean={result['mean']:.4g}",
            f"std={result['std']:.4g}  rms={result['rms']:.4g}",
            f"p25={result['p25']:.4g}  p50={result['p50']:.4g}  p75={result['p75']:.4g}",
            f"area (nominal)={result['roi_area_nominal']:.4g}  integral={result['integral']:.4g}",
        ]
        self.roi_stats_label.setText("<br>".join(lines))

    def export_roi_stats(self):
        if self._last_roi_results is None:
            QMessageBox.information(self, "No ROI statistics", "Draw a ROI and select it in the list first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export ROI statistics", "roi_stats.json", "JSON (*.json)")
        if not path:
            return
        try:
            export_roi_results(self._last_roi_results, path)
            self.info_label.setText(f"ROI statistics exported to {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def compute_roi_time_evolution(self):
        row = self.roi_list.currentRow()
        if not (0 <= row < len(self._rois)):
            QMessageBox.information(self, "No ROI selected", "Select a ROI from the list first.")
            return
        if not self.files:
            QMessageBox.information(self, "No files", "Open a folder of files first.")
            return
        roi = self._rois[row]
        files = list(self.files)

        def job():
            print(f"[ROI] Computing '{roi.label}' across {len(files)} frame(s)…", flush=True)

            def progress(i, total, path):
                print(f"[ROI]   frame {i}/{total}: {Path(path).name}", flush=True)

            return roi_time_series(files, loader=GridFile.load, roi=roi, progress_callback=progress)

        from .workers import run_in_background
        run_in_background(
            self, job,
            on_success=self._on_roi_time_evolution_done,
            on_error=lambda exc: QMessageBox.warning(self, "ROI time evolution failed", str(exc)),
            label=f"Computing '{roi.label}' across {len(files)} frame(s)…",
        )

    def _on_roi_time_evolution_done(self, results):
        self._last_roi_results = results
        n_ok = sum(1 for r in results if "error" not in r)
        self.info_label.setText(
            f"ROI time evolution computed for {n_ok}/{len(results)} frame(s). Use 'Export stats (JSON)' to save."
        )

    def _draw_rois(self, ax):
        from matplotlib.patches import Rectangle, Ellipse
        for patch in self._roi_patches:
            try: patch.remove()
            except Exception: pass
        self._roi_patches = []
        selected_row = self.roi_list.currentRow()
        for i, roi in enumerate(self._rois):
            color = "yellow" if i == selected_row else "cyan"
            if roi.shape == "rectangle":
                patch = Rectangle((roi.x0, roi.y0), roi.width, roi.height, fill=False, edgecolor=color, linewidth=1.5)
            else:
                patch = Ellipse(((roi.x0 + roi.x1) / 2, (roi.y0 + roi.y1) / 2), roi.width, roi.height, fill=False, edgecolor=color, linewidth=1.5)
            ax.add_patch(patch)
            self._roi_patches.append(patch)

    def _on_figure_click(self, event):
        if self.grid is None or event.inaxes is None:
            return
        if self._cbar is not None and event.inaxes == self._cbar.ax:
            norm = self._cbar.mappable.norm
            dlg = ColorRangeDialog(getattr(norm, "vmin", 0.0), getattr(norm, "vmax", 1.0), self)
            if dlg.exec_() != QDialog.Accepted: return
            if dlg.vmin.value() >= dlg.vmax.value():
                QMessageBox.warning(self, "Invalid range", "Minimum must be smaller than maximum.")
                return
            self.vmin_check.setChecked(True); self.vmax_check.setChecked(True)
            self.vmin.setValue(dlg.vmin.value()); self.vmax.setValue(dlg.vmax.value())
            return
        if event.xdata is None or event.ydata is None:
            return
        if self._annotation_mode == "text":
            dlg=TextAnnotationDialog(self)
            if dlg.exec_()==QDialog.Accepted and dlg.text.text().strip():
                self._annotations.append({"type":"text","x":float(event.xdata),"y":float(event.ydata),"text":dlg.text.text().strip()})
                self._annotation_mode=None; self.refresh_plot()
        elif self._annotation_mode == "arrow":
            if self._arrow_start is None:
                self._arrow_start=(float(event.xdata),float(event.ydata))
                self.info_label.setText("Click the arrow end point on the plot.")
            else:
                x0,y0=self._arrow_start; self._annotations.append({"type":"arrow","x0":x0,"y0":y0,"x1":float(event.xdata),"y1":float(event.ydata)})
                self._arrow_start=None; self._annotation_mode=None; self.refresh_plot()

    def _draw_annotations(self, ax):
        for artist in self._annotation_artists:
            try: artist.remove()
            except Exception: pass
        self._annotation_artists = []
        for a in self._annotations:
            if a.get("type") == "text":
                artist = ax.annotate(a["text"], (a["x"], a["y"]), xytext=(6, 6), textcoords="offset points",
                                    fontsize=10, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="black", alpha=0.8))
                self._annotation_artists.append(artist)
            elif a.get("type") == "arrow":
                artist = ax.annotate("", xy=(a["x1"], a["y1"]), xytext=(a["x0"], a["y0"]),
                                    arrowprops=dict(arrowstyle="->", lw=1.8))
                self._annotation_artists.append(artist)

    def _ensure_custom_mouse_mode(self):
        try:
            self.canvas.deactivate_navigation()
        except Exception:
            pass
        try:
            if self._rectangle_selector is not None:
                self._rectangle_selector.set_active(False)
        except Exception:
            pass

    def start_text_annotation(self):
        if self.mode_2d.isChecked():
            self._deactivate_mouse_tools()
            self._annotation_mode="text"
            self.info_label.setText("Click the position where the text should be placed.")

    def start_arrow_annotation(self):
        if self.mode_2d.isChecked():
            self._deactivate_mouse_tools()
            self._annotation_mode="arrow"
            self._arrow_start=None
            self.info_label.setText("Click the arrow start point, then click the end point.")

    def clear_annotations(self):
        self._annotations=[]; self._annotation_mode=None; self._arrow_start=None; self.info_label.setText("Annotations cleared."); self.refresh_plot()

    def enable_region_zoom(self):
        if self.grid is None or not self.mode_2d.isChecked(): return
        self._annotation_mode = None
        self._arrow_start = None
        self._series = None
        self._gpu_dialog = None
        self._gpu_widget = None
        self._image = None
        self._line_artist = None
        self._contour_artists = []
        self._last_contour_sig = None
        from matplotlib.widgets import RectangleSelector
        if self._rectangle_selector is not None:
            try: self._rectangle_selector.disconnect_events()
            except Exception: pass
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        if ax is None: return
        def onselect(eclick, erelease):
            if eclick.xdata is None or erelease.xdata is None: return
            if abs(erelease.xdata-eclick.xdata)<1e-14 or abs(erelease.ydata-eclick.ydata)<1e-14: return
            ax.set_xlim(min(eclick.xdata,erelease.xdata), max(eclick.xdata,erelease.xdata))
            ax.set_ylim(min(eclick.ydata,erelease.ydata), max(eclick.ydata,erelease.ydata))
            self._last_limits=(ax.get_xlim(), ax.get_ylim()); self.canvas.draw_idle()
            try: self._rectangle_selector.set_active(False)
            except Exception: pass
        self.canvas.deactivate_navigation()
        self._rectangle_selector=RectangleSelector(ax,onselect,useblit=False,button=[1],spancoords='data',interactive=False)
        self.info_label.setText("Drag a rectangle over the plot to zoom.")

    def reset_view(self):
        self._deactivate_mouse_tools()
        self.x_range_check.setChecked(False); self.y_range_check.setChecked(False)
        self._last_limits = None
        self._force_full_view = True
        # Re-render from the physical data limits, not from the user's previous view.
        self._default_limits = None
        self.refresh_plot()
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        if ax is not None and self.grid is not None:
            try:
                if self.mode_2d.isChecked() and self.grid.ndim >= 2:
                    ext = self.grid.extent()
                    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
                else:
                    ax.relim(); ax.autoscale_view()
                self._last_limits = (ax.get_xlim(), ax.get_ylim())
                self._default_limits = self._last_limits
                self.canvas.draw_idle()
            except Exception:
                pass

    def _plot_lineout_index(self, ax):
        if self.grid.ndim < 1 or self.grid.data is None:
            raise ValueError("No grid data are loaded")
        along_axis = min(self.lineout_axis.currentIndex(), self.grid.ndim - 1)
        if self.grid.ndim == 1:
            coord, values = self.grid.lineout(axis=0, index=None)
        else:
            fixed_axis = 1 - along_axis if self.grid.ndim == 2 else next(i for i in range(self.grid.ndim) if i != along_axis)
            fixed_physical_index = int(self.lineout_index.value())
            fixed_physical_index = max(0, min(fixed_physical_index, self.grid.axes[fixed_axis].n - 1))
            physical_indices = [self.grid.axes[i].n // 2 for i in range(self.grid.ndim)]
            physical_indices[fixed_axis] = fixed_physical_index
            # GridFile.lineout accepts physical-axis indices and performs the
            # Simulation-to-NumPy axis conversion internally.
            coord, values = self.grid.lineout(axis=along_axis, index=tuple(physical_indices))
        values = smooth_1d(values, self.smooth_method.currentText(), self.smooth_window.value())
        if self._line_artist is None or self._active_plot_mode not in {"line_index", "line_coord", "time_series"}:
            self._line_artist, = ax.plot(coord, values, lw=1.6, color=self.accent_hex())
        else:
            self._line_artist.set_data(coord, values)
            self._line_artist.set_color(self.accent_hex())
        ax.set_xlabel(self._axis_label(along_axis)); ax.set_ylabel(f"{self.grid.label} [{self.grid.units}]" if self.grid.units else self.grid.label)
        ax.set_title(f"t = {self.grid.time:g} {self.grid.time_units}  (iter {self.grid.iteration}), index lineout")

    def _plot_lineout_coord(self, ax):
        if self.grid.ndim != 2:
            raise ValueError("Physical-coordinate lineouts currently support 2D grid files only.")
        along_axis = self.lineout_axis.currentIndex()
        fixed_axis = 1 - along_axis
        coords = self.grid.axes[fixed_axis].values()
        position = float(self.lineout_coord.value())
        if not np.isfinite(position) or position < float(coords.min()) or position > float(coords.max()):
            raise ValueError(f"Fixed coordinate must be between {coords.min():g} and {coords.max():g} {self.grid.axes[fixed_axis].units}")
        coord, values = self.grid.lineout_at(along_axis=along_axis, fixed_value=position, fixed_axis=fixed_axis)
        values = smooth_1d(values, self.smooth_method.currentText(), self.smooth_window.value())
        if self._line_artist is None:
            self._line_artist, = ax.plot(coord, values, lw=1.6, color=self.accent_hex())
        else:
            self._line_artist.set_data(coord, values)
            self._line_artist.set_color(self.accent_hex())
        ax.set_xlabel(self._axis_label(along_axis)); ax.set_ylabel(f"{self.grid.label} [{self.grid.units}]" if self.grid.units else self.grid.label)
        ax.set_title(f"t = {self.grid.time:g} {self.grid.time_units}   ({self.grid.axes[fixed_axis].name} = {position:g})")

    def _plot_time_series(self, ax):
        if len(self.files) < 2: ax.text(0.5,0.5,"Open a folder with multiple time-step files to use time-series mode.",ha="center",va="center",transform=ax.transAxes); return
        quantity = self.grid.dataset_name if self.grid is not None else None
        cache_key = (tuple(self.files), quantity, self.reduction_combo.currentText(), self.average_direction.currentText(), self.smooth_method.currentText(), self.smooth_window.value())
        try:
            cached = self._time_series_cache.get(cache_key)
            if cached is None:
                reduction = self.reduction_combo.currentText()
                average_direction = self.average_direction.currentText() if reduction == "directional average" else None
                if reduction == "directional average":
                    reduction = "mean"
                cached = reduce_grid_series(
                    self.files, reduction=reduction,
                    smoothing={"method":self.smooth_method.currentText(),"window":self.smooth_window.value()},
                    quantity=quantity, average_direction=average_direction,
                )
                self._time_series_cache[cache_key] = cached
            times, iters, values, meta = cached
        except Exception as exc:
            ax.text(0.5,0.5,f"Error computing time series:\n{exc}",ha="center",va="center",transform=ax.transAxes); return
        if self._line_artist is None:
            self._line_artist, = ax.plot(times, values, "o-", lw=1.6, ms=4, color=self.accent_hex())
        else:
            self._line_artist.set_data(times, values); self._line_artist.set_color(self.accent_hex())
        ax.relim(); ax.autoscale_view()
        ax.set_xlabel("time"); unit_str = f" [{meta['units']}]" if meta["units"] else ""; ax.set_ylabel(f"{self.reduction_combo.currentText()}({meta['label']}) over x1,x2{unit_str}"); ax.set_title(f"{meta['label']} — {self.reduction_combo.currentText()} over space, {len(self.files)} time steps")

    def export_time_series(self):
        if len(self.files) < 1 or self.grid is None:
            QMessageBox.information(self, "No time series", "Open at least one compatible simulation frame first.")
            return
        try:
            reduction_label = self.reduction_combo.currentText()
            reduction = "mean" if reduction_label == "directional average" else reduction_label
            direction = self.average_direction.currentText() if reduction_label == "directional average" else None
            quantity = self.grid.dataset_name if self.grid is not None else None
            cache_key = (tuple(self.files), quantity, reduction_label, self.average_direction.currentText(), self.smooth_method.currentText(), self.smooth_window.value())
            cached = self._time_series_cache.get(cache_key)
            if cached is None:
                cached = reduce_grid_series(self.files, reduction=reduction, smoothing={"method":self.smooth_method.currentText(),"window":self.smooth_window.value()}, quantity=quantity, average_direction=direction)
                self._time_series_cache[cache_key] = cached
            times, iters, values, meta = cached
            path, _ = QFileDialog.getSaveFileName(self, "Export time series", "time_series.csv", "CSV (*.csv)")
            if not path: return
            header = f"time,iteration,value\n# quantity={meta.get('quantity','')}; reduction={reduction_label}; direction={direction or ''}"
            np.savetxt(path, np.column_stack((times, iters, values)), delimiter=",", header=header, comments="")
            self.info_label.setText(f"Time series exported: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Time-series export failed", str(exc))

    def _session_state(self):
        ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
        state = {
            "tab": "grid",
            "files": list(self.files),
            "current_index": self.file_list.currentRow(),
            "mode": "time_series" if self.mode_time_series.isChecked() else "line_coord" if self.mode_line_coord.isChecked() else "line_index" if self.mode_line_index.isChecked() else "2d",
            "slice_axis": self.slice_axis.currentText(), "slice_index": self.slice_index.value(),
            "lineout_axis": self.lineout_axis.currentText(), "lineout_index": self.lineout_index.value(), "lineout_coord": self.lineout_coord.value(),
            "reduction": self.reduction_combo.currentText(), "average_direction": self.average_direction.currentText(),
            "smooth_method": self.smooth_method.currentText(), "smooth_window": self.smooth_window.value(),
            "x_range_check": self.x_range_check.isChecked(), "x_min": self.x_range_min.value(), "x_max": self.x_range_max.value(),
            "y_range_check": self.y_range_check.isChecked(), "y_min": self.y_range_min.value(), "y_max": self.y_range_max.value(),
            "title": self.title_edit.text(), "cmap": self.cmap_combo.currentText(), "norm": self.norm_combo.currentText(),
        }
        if ax is not None:
            state["view_xlim"] = list(ax.get_xlim()); state["view_ylim"] = list(ax.get_ylim())
        return state

    def save_session(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save visualization session", "session.xml", "XML session (*.xml)")
        if not path: return
        try:
            save_xml_session(path, self._session_state())
            self.info_label.setText(f"Session saved: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Could not save session", str(exc))

    def load_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore visualization session", "", "XML session (*.xml)")
        if not path: return
        try:
            state = load_xml_session(path)
            self.files = [str(x) for x in state.get("files", []) if Path(str(x)).exists()]
            if not self.files:
                raise ValueError("None of the files recorded in this session are currently available.")
            self.file_list.clear(); self.file_list.addItems([Path(f).name for f in self.files])
            row = max(0, min(value_as_int(state.get("current_index"), 0), len(self.files)-1)); self.file_list.setCurrentRow(row)
            mode_map = {"2d": self.mode_2d, "line_index": self.mode_line_index, "line_coord": self.mode_line_coord, "time_series": self.mode_time_series}
            mode_map.get(state.get("mode"), self.mode_2d).setChecked(True)
            self.slice_axis.setCurrentText(str(state.get("slice_axis", self.slice_axis.currentText())))
            self.slice_index.setValue(value_as_int(state.get("slice_index"), self.slice_index.value()))
            self.lineout_axis.setCurrentText(str(state.get("lineout_axis", self.lineout_axis.currentText())))
            self.lineout_index.setValue(value_as_int(state.get("lineout_index"), self.lineout_index.value()))
            self.lineout_coord.setValue(value_as_float(state.get("lineout_coord"), self.lineout_coord.value()))
            self.reduction_combo.setCurrentText(str(state.get("reduction", self.reduction_combo.currentText())))
            self.average_direction.setCurrentText(str(state.get("average_direction", self.average_direction.currentText())))
            self.smooth_method.setCurrentText(str(state.get("smooth_method", self.smooth_method.currentText())))
            self.smooth_window.setValue(value_as_int(state.get("smooth_window"), self.smooth_window.value()))
            self.title_edit.setText(str(state.get("title", ""))); self.norm_combo.setCurrentText(str(state.get("norm", "linear")))
            self.apply_selection()
            self.x_range_check.setChecked(value_as_bool(state.get("x_range_check"))); self.x_range_min.setValue(value_as_float(state.get("x_min"), self.x_range_min.value())); self.x_range_max.setValue(value_as_float(state.get("x_max"), self.x_range_max.value()))
            self.y_range_check.setChecked(value_as_bool(state.get("y_range_check"))); self.y_range_min.setValue(value_as_float(state.get("y_min"), self.y_range_min.value())); self.y_range_max.setValue(value_as_float(state.get("y_max"), self.y_range_max.value()))
            ax = self.canvas.figure.axes[0] if self.canvas.figure.axes else None
            if ax is not None and "view_xlim" in state and "view_ylim" in state:
                ax.set_xlim(*[value_as_float(v) for v in state["view_xlim"]]); ax.set_ylim(*[value_as_float(v) for v in state["view_ylim"]]); self.canvas.draw_idle()
            self.info_label.setText(f"Session restored: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Could not restore session", str(exc))

    def _axis_label(self, i, grid=None):
        grid = grid if grid is not None else self.grid
        if i < len(grid.axes):
            ax = grid.axes[i]; return f"{ax.label} [{ax.units}]" if ax.units else ax.label
        return f"x{i+1}"
```

---

## `scientific_visualization/gui/main_window.py`

```py
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QTabWidget, QToolBar, QSpinBox

from .. import style
from .grid_tab import GridTab
from .particles_tab import ParticlesTab
from .tracks_tab import TracksTab
from .three_d_tab import ThreeDTab
from .ml_tab import MLTab
from .ai_tab import AITab
from .surrogate_tab import SurrogateTab
from .data_plotter_tab import DataPlotterTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Visualization (Python) — Simulation Visualization")
        self.resize(1250, 780)
        self.setMinimumSize(760, 480)  # window (and its splitters) stay freely resizable above this

        toolbar = QToolBar("Appearance")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addWidget(QLabel("  Theme: "))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(style.THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.set_theme)
        toolbar.addWidget(self.theme_combo)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("  Font: "))
        self.font_combo = QComboBox()
        self.font_combo.addItems(style.FONT_FAMILIES)
        self.font_combo.setCurrentText(style.current_font_preferences()[0])
        self.font_combo.currentTextChanged.connect(self.set_font)
        toolbar.addWidget(self.font_combo)
        toolbar.addWidget(QLabel("  Size: "))
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 32)
        self.font_size.setValue(int(round(style.current_font_preferences()[1])))
        self.font_size.valueChanged.connect(self.set_font_size)
        toolbar.addWidget(self.font_size)

        self.tabs = QTabWidget()
        self.grid_tab = GridTab()
        self.particles_tab = ParticlesTab()
        self.tracks_tab = TracksTab()
        self.three_d_tab = ThreeDTab()
        self.ml_tab = MLTab()
        self.ai_tab = AITab()
        self.surrogate_tab = SurrogateTab()
        self.data_plotter_tab = DataPlotterTab()
        self.grid_tab.dataset_changed.connect(self.ai_tab.set_dataset)
        self.grid_tab.open_in_3d_requested.connect(self.open_file_in_3d)
        self.three_d_tab.open_in_2d_requested.connect(self.open_file_in_2d)
        self.grid_tab.series_changed.connect(self.ai_tab.set_series)
        self.tabs.addTab(self.grid_tab, "Fields / Grid")
        self.tabs.addTab(self.particles_tab, "Particles")
        self.tabs.addTab(self.tracks_tab, "Tracks")
        self.tabs.addTab(self.three_d_tab, "3D Viewer")
        self.tabs.addTab(self.ml_tab, "Analysis & Modeling")
        self.tabs.addTab(self.ai_tab, "AI Analysis")
        self.tabs.addTab(self.surrogate_tab, "Surrogate Lab")
        self.tabs.addTab(self.data_plotter_tab, "Data Plotter")
        self.setCentralWidget(self.tabs)

        self.set_theme("Light")

    def open_file_in_3d(self, path: str):
        self.three_d_tab._pending_files = [path]
        self.three_d_tab.file_list.clear(); self.three_d_tab.file_list.addItem(path.split("/")[-1]); self.three_d_tab.file_list.setCurrentRow(0)
        self.three_d_tab.apply_selection()
        self.tabs.setCurrentWidget(self.three_d_tab)

    def open_file_in_2d(self, path: str):
        self.grid_tab.files = [path]
        self.grid_tab.file_list.clear(); self.grid_tab.file_list.addItem(path.split("/")[-1]); self.grid_tab.file_list.setCurrentRow(0)
        self.grid_tab.apply_selection()
        self.grid_tab.mode_2d.setChecked(True)
        self.tabs.setCurrentWidget(self.grid_tab)

    def set_font(self, family: str):
        self._apply_font_preferences(family, float(self.font_size.value()))

    def set_font_size(self, size: int):
        self._apply_font_preferences(self.font_combo.currentText(), float(size))

    def _apply_font_preferences(self, family: str, size: float):
        style.set_font_preferences(family, size)
        for tab in (self.grid_tab, self.particles_tab, self.tracks_tab, self.three_d_tab, self.ml_tab, self.ai_tab, self.surrogate_tab, self.data_plotter_tab):
            setter = getattr(tab, "set_typography", None)
            if setter is not None:
                setter(family, size)

    def set_theme(self, name: str):
        """Applies the theme to the whole application (Qt widget chrome)
        as well as to every tab's matplotlib figure, so 'Dark' really means
        the whole app goes dark, not just the plots."""
        app = QApplication.instance()
        if app is not None:
            style.apply_app_theme(app, name)
        for tab in (self.grid_tab, self.particles_tab, self.tracks_tab):
            tab.set_theme(name)
```

---

## `scientific_visualization/gui/ml_tab.py`

```py
from __future__ import annotations

import pickle
import time
from pathlib import Path
import numpy as np
from PyQt5.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QFileDialog, QWidget, QDoubleSpinBox, QHBoxLayout, QListWidget, QAbstractItemView
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..io.simulation import SimulationReader
from ..ml import (PCAAnalyzer, KMeansAnalyzer, IsolationForestAnalyzer, RegressionAnalyzer,
                   NeuralNetworkRegressorAnalyzer, GradientBoostingRegressorAnalyzer, AutoencoderAnalyzer,
                   dataset_to_features, sample_grid_features, estimator_available)


class MLTab(QWidget):
    """Train, evaluate, visualize, and save machine-learning models."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataset = None
        self.target_dataset = None
        self.feature_paths = []
        self.target_paths = []
        self.last_result = None
        self.figure = Figure(figsize=(6, 4), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        controls = QVBoxLayout()
        box = QGroupBox("Machine learning")
        form = QFormLayout(box)
        file_row = QHBoxLayout()
        open_btn = QPushButton("Open feature file…"); open_btn.clicked.connect(self.open_feature_file); file_row.addWidget(open_btn)
        folder_btn = QPushButton("Select feature folder…"); folder_btn.clicked.connect(self.open_feature_folder); file_row.addWidget(folder_btn)
        form.addRow(file_row)
        self.feature_files = QListWidget(); self.feature_files.setSelectionMode(QAbstractItemView.ExtendedSelection); form.addRow("Feature files:", self.feature_files)
        feature_select_row = QHBoxLayout()
        select_all = QPushButton("Select all"); select_all.clicked.connect(lambda: self._select_all(self.feature_files, True)); feature_select_row.addWidget(select_all)
        clear_sel = QPushButton("Clear selection"); clear_sel.clicked.connect(lambda: self._select_all(self.feature_files, False)); feature_select_row.addWidget(clear_sel)
        apply_features = QPushButton("Apply feature selection"); apply_features.clicked.connect(self.apply_feature_selection); feature_select_row.addWidget(apply_features)
        form.addRow(feature_select_row)
        target_row = QHBoxLayout()
        target_btn = QPushButton("Open target file…"); target_btn.clicked.connect(self.open_target_file); target_row.addWidget(target_btn)
        target_folder_btn = QPushButton("Select target folder…"); target_folder_btn.clicked.connect(self.open_target_folder); target_row.addWidget(target_folder_btn)
        form.addRow(target_row)
        self.target_files = QListWidget(); self.target_files.setSelectionMode(QAbstractItemView.ExtendedSelection); form.addRow("Target files:", self.target_files)
        target_apply = QPushButton("Apply target selection"); target_apply.clicked.connect(self.apply_target_selection); form.addRow(target_apply)
        self.method = QComboBox(); self.method.addItems([
            "PCA", "K-means clustering", "Isolation forest", "Random forest regression",
            "Gradient boosting regression", "Neural network regression", "Neural autoencoder"
        ]); self.method.currentTextChanged.connect(self._update_controls); form.addRow("Algorithm:", self.method)
        self.sample_count = QSpinBox(); self.sample_count.setRange(100, 1_000_000); self.sample_count.setValue(10_000); form.addRow("Maximum samples:", self.sample_count)
        self.components = QSpinBox(); self.components.setRange(2, 10); self.components.setValue(2); form.addRow("PCA components:", self.components)
        self.clusters = QSpinBox(); self.clusters.setRange(2, 100); self.clusters.setValue(3); form.addRow("K-means clusters:", self.clusters)
        self.test_size = QDoubleSpinBox(); self.test_size.setRange(0.05, 0.5); self.test_size.setValue(0.2); self.test_size.setSingleStep(0.05); form.addRow("Test fraction:", self.test_size)
        self.cv_folds = QSpinBox(); self.cv_folds.setRange(0, 10); self.cv_folds.setValue(5); form.addRow("Cross-validation folds (0=off):", self.cv_folds)
        self.hidden = QLabel("Advanced models: Gradient Boosting, Neural Network, Autoencoder"); self.hidden.setWordWrap(True); form.addRow(self.hidden)
        run_btn = QPushButton("Train / Run algorithm"); run_btn.clicked.connect(self.run_training); form.addRow(run_btn)
        save_btn = QPushButton("Save trained model…"); save_btn.clicked.connect(self.save_model); form.addRow(save_btn)
        self.feature_status = QLabel("Feature dataset: none"); self.target_status = QLabel("Target dataset: none"); self.feature_status.setWordWrap(True); self.target_status.setWordWrap(True); self.status = QLabel("Install scikit-learn to enable training." if not estimator_available() else "Ready. For supervised regression, load a feature dataset and a target dataset with matching shapes."); self.status.setWordWrap(True)
        form.addRow(self.feature_status); form.addRow(self.target_status); form.addRow(self.status)
        controls.addWidget(box); controls.addStretch(1)
        root.addLayout(controls, 0); root.addWidget(self.canvas, 1)
        self._update_controls(self.method.currentText())

    def _update_controls(self, method):
        regression = method in {"Random forest regression", "Gradient boosting regression", "Neural network regression"}
        self.target_status.setVisible(regression)
        self.test_size.setVisible(regression)
        self.cv_folds.setVisible(regression)

    def _select_all(self, widget, checked):
        for i in range(widget.count()):
            item = widget.item(i)
            item.setSelected(bool(checked))

    def open_feature_file(self):
        ds = self._open_dataset("Open feature dataset")
        if ds is None:
            return
        self.dataset = ds; self.feature_paths = [ds.source] if ds.source else []
        self.feature_files.clear();
        for path in self.feature_paths: self.feature_files.addItem(path)
        self.feature_files.selectAll()
        self.feature_status.setText(f"Feature dataset: {ds.summary()}")

    def open_feature_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select feature simulation folder")
        if not folder: return
        paths = sorted(str(p) for p in __import__('pathlib').Path(folder).iterdir() if p.suffix.lower() in {'.h5','.hdf5'})
        if not paths:
            QMessageBox.warning(self, "No files found", "No HDF5 files were found in the selected folder.")
            return
        self.feature_paths = paths
        self.feature_files.clear(); self.feature_files.addItems(paths); self.feature_files.selectAll()
        try:
            self.dataset = SimulationReader().load(paths[0])
            self.feature_status.setText(f"Feature folder: {len(paths)} files selected. First dataset: {self.dataset.name}, shape={self.dataset.shape}")
        except Exception as exc:
            QMessageBox.warning(self, "Feature folder", str(exc))

    def apply_feature_selection(self):
        self.feature_paths = [self.feature_files.item(i).text() for i in range(self.feature_files.count()) if self.feature_files.item(i).isSelected()]
        if not self.feature_paths: return
        try:
            self.dataset = SimulationReader().load(self.feature_paths[0])
            self.feature_status.setText(f"Applied {len(self.feature_paths)} feature file(s). First dataset: {self.dataset.name}, shape={self.dataset.shape}")
        except Exception as exc:
            QMessageBox.warning(self, "Feature selection", str(exc))

    def open_target_file(self):
        ds = self._open_dataset("Open target dataset")
        if ds is None: return
        self.target_dataset = ds; self.target_paths = [ds.source] if ds.source else []
        self.target_files.clear();
        for path in self.target_paths: self.target_files.addItem(path)
        self.target_files.selectAll()
        self.target_status.setText(f"Target dataset: {ds.summary()}")

    def open_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select target simulation folder")
        if not folder: return
        paths = sorted(str(p) for p in __import__('pathlib').Path(folder).iterdir() if p.suffix.lower() in {'.h5','.hdf5'})
        if not paths:
            QMessageBox.warning(self, "No files found", "No HDF5 files were found in the selected folder.")
            return
        self.target_paths = paths
        self.target_files.clear(); self.target_files.addItems(paths); self.target_files.selectAll()
        try:
            self.target_dataset = SimulationReader().load(paths[0])
            self.target_status.setText(f"Target folder: {len(paths)} files selected. First dataset: {self.target_dataset.name}, shape={self.target_dataset.shape}")
        except Exception as exc:
            QMessageBox.warning(self, "Target folder", str(exc))

    def apply_target_selection(self):
        self.target_paths = [self.target_files.item(i).text() for i in range(self.target_files.count()) if self.target_files.item(i).isSelected()]
        if not self.target_paths: return
        try:
            self.target_dataset = SimulationReader().load(self.target_paths[0])
            self.target_status.setText(f"Applied {len(self.target_paths)} target file(s). First dataset: {self.target_dataset.name}, shape={self.target_dataset.shape}")
        except Exception as exc:
            QMessageBox.warning(self, "Target selection", str(exc))

    def _open_dataset(self, title):
        path, _ = QFileDialog.getOpenFileName(self, title, "", "HDF5 files (*.h5 *.hdf5);;All files (*)")
        if not path: return None
        try: return SimulationReader().load(path)
        except Exception as exc: QMessageBox.critical(self, "Could not load dataset", str(exc)); return None

    def _selected_feature_paths(self):
        selected = [self.feature_files.item(i).text() for i in range(self.feature_files.count()) if self.feature_files.item(i).isSelected()]
        return selected or self.feature_paths[:1]

    def _collect_features(self, paths=None, sample_count=None):
        """Build the combined FeatureSet. Only reads widgets if the caller
        doesn't already supply ``paths``/``sample_count`` explicitly, so this
        stays safe to call from a background worker thread (see run_training)."""
        if paths is None:
            paths = self._selected_feature_paths()
        if sample_count is None:
            sample_count = self.sample_count.value()
        if not paths: raise ValueError("Select at least one feature file.")
        print(f"[ML] Collecting features from {len(paths)} file(s), up to {sample_count} samples each…", flush=True)
        parts = []
        local_indices = []
        for i, path in enumerate(paths, start=1):
            print(f"[ML]   loading file {i}/{len(paths)}: {Path(path).name}", flush=True)
            ds = SimulationReader().load(path)
            part = sample_grid_features(ds, sample_count, seed=i)
            parts.append(part)
            local_indices.append(np.asarray(part.metadata.get("sample_indices", np.arange(part.values.shape[0])), dtype=int))
        from ..ml.core import FeatureSet
        values = np.vstack([p.values for p in parts])
        coords = np.vstack([p.sample_coordinates for p in parts]) if all(p.sample_coordinates is not None for p in parts) else None
        meta = dict(parts[0].metadata)
        meta.update({"source_files": paths, "sample_count": int(values.shape[0]), "sample_indices_per_file": local_indices})
        print(f"[ML] Collected {values.shape[0]} total samples with {values.shape[1]} feature(s).", flush=True)
        return FeatureSet(values, parts[0].feature_names, coords, meta)

    def run_training(self):
        if not estimator_available(): QMessageBox.warning(self, "ML unavailable", "Install scikit-learn with: pip install scikit-learn"); return
        if self.dataset is None and not self._selected_feature_paths(): QMessageBox.information(self, "No feature dataset", "Select a feature file or folder first."); return
        # Read every widget value needed for training now, on the GUI thread.
        # Qt widgets are not safe to read from a worker thread, so the actual
        # background job below only ever touches plain Python/NumPy values.
        method = self.method.currentText()
        components = self.components.value()
        clusters = self.clusters.value()
        test_size = self.test_size.value()
        cv_folds = self.cv_folds.value()
        target_dataset = self.target_dataset
        target_paths = [self.target_files.item(i).text() for i in range(self.target_files.count()) if self.target_files.item(i).isSelected()] or self.target_paths[:1]
        feature_paths = self._selected_feature_paths()
        sample_count = self.sample_count.value()

        def job():
            print(f"[ML] === Starting training: method='{method}' ===", flush=True)
            t0 = time.time()
            features = self._collect_features(paths=feature_paths, sample_count=sample_count)
            print(f"[ML] Fitting {method}…", flush=True)
            result = self._fit_method(
                method, features,
                components=components, clusters=clusters, test_size=test_size, cv_folds=cv_folds,
                target_dataset=target_dataset, target_paths=target_paths, feature_paths=feature_paths,
            )
            print(f"[ML] Done in {time.time() - t0:.2f}s.", flush=True)
            return method, result

        from .workers import run_in_background
        run_in_background(
            self, job,
            on_success=lambda payload: self._on_training_success(*payload),
            on_error=lambda exc: QMessageBox.warning(self, "ML training failed", str(exc)),
            label="Training model… this keeps the window responsive.",
        )

    def _fit_method(self, method, features, *, components, clusters, test_size, cv_folds, target_dataset, target_paths, feature_paths):
        """Pure computation (no widget access): safe to run on a worker thread."""
        if method == "PCA":
            print(f"[ML]   PCA: reducing to {components} component(s)…", flush=True)
            return PCAAnalyzer(components).fit_transform(features)
        if method == "K-means clustering":
            print(f"[ML]   K-means: fitting {clusters} cluster(s)…", flush=True)
            return KMeansAnalyzer(clusters).fit_predict(features)
        if method == "Isolation forest":
            print("[ML]   Isolation forest: fitting anomaly detector…", flush=True)
            return IsolationForestAnalyzer().fit_predict(features)
        if method == "Neural autoencoder":
            print(f"[ML]   Autoencoder: training with bottleneck size {max(2, components)}…", flush=True)
            return AutoencoderAnalyzer(bottleneck=max(2, components), max_iter=250).fit_transform(features)

        if target_dataset is None: raise ValueError(f"{method} requires a target dataset.")
        if not target_paths: raise ValueError("Select at least one target file or folder.")
        if len(target_paths) not in {1, len(feature_paths)}:
            raise ValueError("Select either one target file to pair with all feature frames, or the same number of target and feature files.")
        index_groups = features.metadata.get("sample_indices_per_file")
        if index_groups is None:
            raise ValueError("Feature sampling metadata are unavailable for supervised training.")
        if len(target_paths) == 1:
            target_paths = target_paths * len(feature_paths)
        print(f"[ML]   Loading {len(target_paths)} target file(s)…", flush=True)
        target_parts = []
        for path, indices in zip(target_paths, index_groups):
            tds = SimulationReader().load(path)
            target_full = np.asarray(tds.data).reshape(-1)
            if indices.size and int(indices.max()) >= target_full.size:
                raise ValueError(f"Feature/target shapes are incompatible in '{path}': target has {target_full.size} samples but feature index {int(indices.max())} is required.")
            target_parts.append(target_full[indices])
        target = np.concatenate(target_parts)
        if method == "Random forest regression":
            print(f"[ML]   Random forest: fitting on {len(target)} samples (test_size={test_size})…", flush=True)
            return RegressionAnalyzer(test_size=test_size).fit_predict(features, target)
        if method == "Gradient boosting regression":
            print(f"[ML]   Gradient boosting: fitting on {len(target)} samples (test_size={test_size}, cv_folds={cv_folds})…", flush=True)
            return GradientBoostingRegressorAnalyzer().fit_predict(features, target, test_size=test_size, cv_folds=cv_folds)
        print(f"[ML]   Neural network regressor: fitting on {len(target)} samples (test_size={test_size}, cv_folds={cv_folds})…", flush=True)
        return NeuralNetworkRegressorAnalyzer().fit_predict(features, target, test_size=test_size, cv_folds=cv_folds)

    def _on_training_success(self, method, result):
        """Runs back on the GUI thread: safe to touch widgets/plots here."""
        if method == "PCA":
            self._plot_pca(result)
            self.status.setText(f"PCA trained. Explained variance: {np.round(result.metadata['explained_variance_ratio'], 4).tolist()}")
        elif method == "K-means clustering":
            self._plot_clusters(result)
            self.status.setText(f"K-means trained. Found {len(np.unique(result.output))} clusters for {len(result.output)} samples.")
        elif method == "Isolation forest":
            self._plot_anomalies(result)
            self.status.setText(f"Isolation forest trained. Anomalies: {int(np.sum(result.output == -1))} / {len(result.output)}.")
        elif method == "Neural autoencoder":
            self._plot_autoencoder(result)
            err = result.metadata["reconstruction_error"]
            self.status.setText(f"Autoencoder trained. Median reconstruction error={np.median(err):.4g}; 95th percentile={np.percentile(err,95):.4g}.")
        else:
            if method == "Random forest regression":
                self._plot_regression(result, title="Random forest regression: test set")
            elif method == "Gradient boosting regression":
                self._plot_regression(result, title="Gradient boosting regression: test set", show_importance=True)
            else:
                self._plot_neural_regression(result)
            m = result.metadata["metrics"]
            cv = result.metadata.get("cv")
            suffix = f", CV R²={cv['mean_r2']:.4f}±{cv['std_r2']:.4f}" if cv else ""
            self.status.setText(f"{result.method} trained. R²={m['r2']:.4f}, RMSE={m['rmse']:.4g}, MAE={m['mae']:.4g}{suffix}.")
        self.last_result = result

    def _reset_axes(self): self.figure.clear(); return self.figure.add_subplot(111)
    def _plot_pca(self, r):
        ax = self._reset_axes(); xy = r.output; ax.scatter(xy[:,0], xy[:,1], s=8, alpha=0.6); ax.set_xlabel("PC1"); ax.set_ylabel("PC2"); ax.set_title("PCA projection"); self.canvas.draw_idle()
    def _plot_clusters(self, r):
        ax = self._reset_axes(); xy = r.feature_set.values[:, -2:] if r.feature_set.values.shape[1] >= 2 else np.column_stack((np.arange(len(r.output)), r.feature_set.values[:,0])); ax.scatter(xy[:,0], xy[:,1], c=r.output, s=8, alpha=0.7); ax.set_title("K-means clusters"); ax.set_xlabel("feature 1 / coordinate"); ax.set_ylabel("feature 2 / coordinate"); self.canvas.draw_idle()
    def _plot_anomalies(self, r):
        ax = self._reset_axes(); xy = r.feature_set.values[:, -2:] if r.feature_set.values.shape[1] >= 2 else np.column_stack((np.arange(len(r.output)), r.feature_set.values[:,0])); normal = r.output == 1; ax.scatter(xy[normal,0],xy[normal,1],s=8,alpha=0.45,label="normal"); ax.scatter(xy[~normal,0],xy[~normal,1],s=20,alpha=0.9,label="anomaly"); ax.legend(); ax.set_title("Isolation forest anomaly map"); self.canvas.draw_idle()
    def _plot_regression(self, r, title="Regression: test set", show_importance=False):
        if show_importance:
            self.figure.clear(); axes = self.figure.subplots(1, 2)
            y = r.metadata["y_test"]; p = r.metadata["predicted"]
            axes[0].scatter(y, p, s=12, alpha=0.6)
            lo=float(min(y.min(),p.min())); hi=float(max(y.max(),p.max())); axes[0].plot([lo,hi],[lo,hi],linewidth=1)
            axes[0].set_xlabel("True target"); axes[0].set_ylabel("Predicted target"); axes[0].set_title(title)
            imp = np.asarray(r.metadata.get("feature_importances", [])); names=list(r.feature_set.feature_names)
            order=np.argsort(imp)
            axes[1].barh(np.arange(len(order)), imp[order]); axes[1].set_yticks(np.arange(len(order))); axes[1].set_yticklabels([names[i] for i in order]); axes[1].set_title("Feature importance")
            self.canvas.draw_idle(); return
        ax = self._reset_axes(); y = r.metadata["y_test"]; p = r.metadata["predicted"]; ax.scatter(y,p,s=12,alpha=0.6); lo=float(min(y.min(),p.min())); hi=float(max(y.max(),p.max())); ax.plot([lo,hi],[lo,hi],linewidth=1); ax.set_xlabel("True target"); ax.set_ylabel("Predicted target"); ax.set_title(title); self.canvas.draw_idle()

    def _plot_neural_regression(self, r):
        self.figure.clear(); axes = self.figure.subplots(1, 2)
        y = r.metadata["y_test"]; p = r.metadata["predicted"]; axes[0].scatter(y,p,s=12,alpha=0.6); lo=float(min(y.min(),p.min())); hi=float(max(y.max(),p.max())); axes[0].plot([lo,hi],[lo,hi],linewidth=1); axes[0].set_xlabel("True target"); axes[0].set_ylabel("Predicted target"); axes[0].set_title("Neural network regression")
        loss = r.metadata.get("loss_curve", []); axes[1].plot(np.arange(1,len(loss)+1), loss); axes[1].set_xlabel("Iteration"); axes[1].set_ylabel("Training loss"); axes[1].set_title("Training history")
        self.canvas.draw_idle()

    def _plot_autoencoder(self, r):
        xy = r.feature_set.sample_coordinates
        err = np.asarray(r.metadata["reconstruction_error"])
        self.figure.clear(); axes = self.figure.subplots(1, 2)
        if xy is not None and xy.shape[1] >= 2:
            sc = axes[0].scatter(xy[:,0], xy[:,1], c=err, s=8); axes[0].set_xlabel("x1"); axes[0].set_ylabel("x2"); axes[0].set_title("Autoencoder anomaly score"); self.figure.colorbar(sc, ax=axes[0], label="reconstruction MSE")
        else:
            axes[0].hist(err, bins=40); axes[0].set_title("Reconstruction-error distribution"); axes[0].set_xlabel("MSE")
        loss = r.metadata.get("loss_curve", []); axes[1].plot(np.arange(1,len(loss)+1), loss); axes[1].set_xlabel("Iteration"); axes[1].set_ylabel("Training loss"); axes[1].set_title("Autoencoder training history")
        self.canvas.draw_idle()
    def save_model(self):
        if not self.last_result or self.last_result.model is None: QMessageBox.information(self,"No model","Train an algorithm first."); return
        path, _ = QFileDialog.getSaveFileName(self,"Save trained model","model.pkl","Pickle model (*.pkl)")
        if not path: return
        try:
            with open(path,"wb") as f: pickle.dump({"model":self.last_result.model,"method":self.last_result.method,"metadata":self.last_result.metadata,"feature_names":self.last_result.feature_set.feature_names if self.last_result.feature_set else ()},f)
            self.status.setText(f"Model saved: {path}")
        except Exception as exc: QMessageBox.warning(self,"Model save failed",str(exc))
```

---

## `scientific_visualization/gui/particles_tab.py`

```py
import numpy as np
from matplotlib.colors import LogNorm
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QRadioButton, QSpinBox, QVBoxLayout,
)

from .. import style
from ..io.particles import ParticleFile
from .base_tab import BaseTab


class ParticlesTab(BaseTab):
    """View particle phase-space: scatter, hexbin, 2D histogram, or 1D
    histogram/spectrum, with density coloring and log-scale options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pf = None

        self.file_list = self.add_open_buttons(folder=True, label="particle file")
        self.file_list.currentRowChanged.connect(self.on_file_selected)

        opts_box = QGroupBox("Display")
        form = QFormLayout(opts_box)

        self.mode_scatter = QRadioButton("Scatter")
        self.mode_scatter_density = QRadioButton("Scatter (colored by local density)")
        self.mode_hexbin = QRadioButton("Hexbin")
        self.mode_hist2d = QRadioButton("2D histogram")
        self.mode_hist1d = QRadioButton("1D histogram / spectrum")
        self.mode_scatter.setChecked(True)
        for rb in (self.mode_scatter, self.mode_scatter_density, self.mode_hexbin, self.mode_hist2d, self.mode_hist1d):
            rb.toggled.connect(self._update_mode_widgets)
            rb.toggled.connect(self.refresh_plot)

        mode_row = QVBoxLayout()
        for rb in (self.mode_scatter, self.mode_scatter_density, self.mode_hexbin, self.mode_hist2d, self.mode_hist1d):
            mode_row.addWidget(rb)
        form.addRow("Mode:", mode_row)

        self.x_quant = QComboBox()
        self.y_quant = QComboBox()
        self.x_quant.currentTextChanged.connect(self.refresh_plot)
        self.y_quant.currentTextChanged.connect(self.refresh_plot)
        form.addRow("X quantity:", self.x_quant)
        self.y_row_label = QLabel("Y quantity:")
        form.addRow(self.y_row_label, self.y_quant)

        self.control_layout.addWidget(opts_box)

        color_box = QGroupBox("Color")
        color_form = QFormLayout(color_box)
        self.cmap_category = QComboBox()
        self.cmap_category.addItems(list(style.COLORMAPS.keys()))
        self.cmap_category.currentTextChanged.connect(self._populate_cmaps)
        color_form.addRow("Colormap group:", self.cmap_category)

        self.cmap_combo = QComboBox()
        self.cmap_combo.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Colormap:", self.cmap_combo)
        self._populate_cmaps(select="viridis")

        self.reverse_cmap = QCheckBox("Reverse colormap")
        self.reverse_cmap.stateChanged.connect(self.refresh_plot)
        color_form.addRow(self.reverse_cmap)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 16)
        self._update_color_preview()
        color_btn = self.add_color_picker_button(self._on_color_picked, "Pick plain-scatter color…")
        color_form.addRow(self.color_preview, color_btn)

        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.05, 1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setValue(0.4)
        self.alpha_spin.valueChanged.connect(self.refresh_plot)
        color_form.addRow("Point opacity:", self.alpha_spin)

        self.log_color = QCheckBox("Log color scale (counts)")
        self.log_color.stateChanged.connect(self.refresh_plot)
        color_form.addRow(self.log_color)

        self.control_layout.addWidget(color_box)

        binning_box = QGroupBox("Binning / sampling")
        binning_form = QFormLayout(binning_box)
        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(5, 500)
        self.bins_spin.setValue(80)
        self.bins_spin.valueChanged.connect(self.refresh_plot)
        binning_form.addRow("Bins:", self.bins_spin)

        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(100, 2_000_000)
        self.max_points_spin.setValue(20000)
        self.max_points_spin.setSingleStep(1000)
        self.max_points_spin.valueChanged.connect(self.refresh_plot)
        binning_form.addRow("Max points (scatter):", self.max_points_spin)
        self.control_layout.addWidget(binning_box)

        axes_box = QGroupBox("Axes")
        axes_form = QFormLayout(axes_box)
        self.log_x = QCheckBox("Log X axis")
        self.log_y = QCheckBox("Log Y axis")
        self.log_x.stateChanged.connect(self.refresh_plot)
        self.log_y.stateChanged.connect(self.refresh_plot)
        log_row = QHBoxLayout()
        log_row.addWidget(self.log_x)
        log_row.addWidget(self.log_y)
        axes_form.addRow("Scale:", log_row)

        self.show_stats = QCheckBox("Show statistics box")
        self.show_stats.setChecked(True)
        self.show_stats.stateChanged.connect(self.refresh_plot)
        axes_form.addRow(self.show_stats)
        self.control_layout.addWidget(axes_box)

        self.info_label = QLabel("No file loaded.")
        self.info_label.setWordWrap(True)
        self.control_layout.addWidget(self.info_label)

        self.finish_layout()
        self._update_mode_widgets()

    def _populate_cmaps(self, select=None):
        cat = self.cmap_category.currentText()
        self.cmap_combo.blockSignals(True)
        self.cmap_combo.clear()
        items = style.COLORMAPS.get(cat, style.ALL_COLORMAPS)
        self.cmap_combo.addItems(items)
        if select and select in items:
            self.cmap_combo.setCurrentText(select)
        self.cmap_combo.blockSignals(False)
        self.refresh_plot()

    def _on_color_picked(self, color):
        self._update_color_preview()
        self.refresh_plot()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(f"background-color: {self.accent_hex()}; border: 1px solid #888;")

    def _update_mode_widgets(self):
        need_y = not self.mode_hist1d.isChecked()
        self.y_quant.setEnabled(need_y)
        self.y_row_label.setEnabled(need_y)
        is_plain_scatter = self.mode_scatter.isChecked()
        needs_bins = not is_plain_scatter and not self.mode_scatter_density.isChecked()
        self.bins_spin.setEnabled(needs_bins)
        needs_maxpts = is_plain_scatter or self.mode_scatter_density.isChecked()
        self.max_points_spin.setEnabled(needs_maxpts)
        self.log_color.setEnabled(not is_plain_scatter)
        self.cmap_combo.setEnabled(not is_plain_scatter)
        self.cmap_category.setEnabled(not is_plain_scatter)
        self.reverse_cmap.setEnabled(not is_plain_scatter)

    # -- file handling -----------------------------------------------
    def on_file_selected(self, row):
        if row < 0 or row >= len(self.files):
            return
        try:
            self.pf = ParticleFile.info(self.files[row])
        except Exception as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>Error reading file:<br>{exc}</span>")
            return

        quants = self.pf.quants
        for combo, default in ((self.x_quant, "x1"), (self.y_quant, "p1" if "p1" in quants else quants[-1] if quants else "")):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(quants)
            if default in quants:
                combo.setCurrentText(default)
            combo.blockSignals(False)

        self.info_label.setText(
            f"<b>{self.pf.name}</b><br>"
            f"N particles: {self.pf.npar}<br>"
            f"quantities: {', '.join(quants)}<br>"
            f"time: {self.pf.time:g}  iter: {self.pf.iteration}"
        )
        self.refresh_plot()

    def _cmap_name(self):
        name = self.cmap_combo.currentText() or "viridis"
        if self.reverse_cmap.isChecked() and not name.endswith("_r"):
            name += "_r"
        return name

    # -- plotting ------------------------------------------------------
    def refresh_plot(self):
        if self.pf is None or not self.x_quant.currentText():
            return
        self.canvas.clear()
        ax = self.canvas.figure.add_subplot(111)

        xq = self.x_quant.currentText()
        x = self.pf.get(xq)
        xlabel = f"{self.pf.label(xq)} [{self.pf.unit(xq)}]" if self.pf.unit(xq) else self.pf.label(xq)
        cmap = self._cmap_name()
        color_norm = LogNorm() if self.log_color.isChecked() else None

        if self.mode_hist1d.isChecked():
            bins = np.geomspace(max(x.min(), 1e-12), x.max(), self.bins_spin.value()) if self.log_x.isChecked() and x.min() > 0 else self.bins_spin.value()
            ax.hist(x, bins=bins, color=self.accent_hex(), edgecolor="none")
            ax.set_xlabel(xlabel)
            ax.set_ylabel("count")
            if self.log_y.isChecked():
                ax.set_yscale("log")
            if self.log_x.isChecked():
                ax.set_xscale("log")
            if self.show_stats.isChecked():
                self._add_stats_box(ax, x)
        else:
            yq = self.y_quant.currentText()
            if not yq:
                self.canvas.draw()
                return
            y = self.pf.get(yq)
            ylabel = f"{self.pf.label(yq)} [{self.pf.unit(yq)}]" if self.pf.unit(yq) else self.pf.label(yq)

            if self.mode_scatter.isChecked() or self.mode_scatter_density.isChecked():
                n = len(x)
                max_pts = self.max_points_spin.value()
                if n > max_pts:
                    idx = np.random.default_rng(0).choice(n, max_pts, replace=False)
                    x_plot, y_plot = x[idx], y[idx]
                else:
                    x_plot, y_plot = x, y

                alpha = self.alpha_spin.value()
                if self.mode_scatter_density.isChecked() and len(x_plot) > 2:
                    density = self._point_density(x_plot, y_plot)
                    order = np.argsort(density)
                    sc = ax.scatter(x_plot[order], y_plot[order], c=density[order], s=4, cmap=cmap, alpha=alpha)
                    self.canvas.figure.colorbar(sc, ax=ax, label="local density")
                else:
                    ax.scatter(x_plot, y_plot, s=2, alpha=alpha, color=self.accent_hex())
            elif self.mode_hexbin.isChecked():
                hb = ax.hexbin(x, y, gridsize=self.bins_spin.value(), cmap=cmap, norm=color_norm, mincnt=1)
                self.canvas.figure.colorbar(hb, ax=ax, label="count")
            else:  # 2D histogram
                h = ax.hist2d(x, y, bins=self.bins_spin.value(), cmap=cmap, norm=color_norm)
                self.canvas.figure.colorbar(h[3], ax=ax, label="count")

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            if self.log_x.isChecked():
                ax.set_xscale("log")
            if self.log_y.isChecked():
                ax.set_yscale("log")

        ax.set_title(f"t = {self.pf.time:g}  (iter {self.pf.iteration})")
        self.canvas.draw()

    @staticmethod
    def _point_density(x, y):
        """Fast approximate point density via a coarse 2D histogram lookup
        (much cheaper than a full Gaussian KDE for large particle counts)."""
        bins = 60
        h, xedges, yedges = np.histogram2d(x, y, bins=bins)
        xi = np.clip(np.digitize(x, xedges) - 1, 0, bins - 1)
        yi = np.clip(np.digitize(y, yedges) - 1, 0, bins - 1)
        return h[xi, yi]

    @staticmethod
    def _add_stats_box(ax, x):
        text = f"mean = {np.mean(x):.3g}\nstd = {np.std(x):.3g}\nmin = {np.min(x):.3g}\nmax = {np.max(x):.3g}"
        ax.text(0.97, 0.97, text, transform=ax.transAxes, ha="right", va="top",
                fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.85))
```

---

## `scientific_visualization/gui/plot_canvas.py`

```py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .. import style


class PlotCanvas(QWidget):
    """A matplotlib Figure embedded in a Qt widget, with the standard
    pan/zoom/save toolbar plus a one-click high-resolution export button."""

    def __init__(self, parent=None, figsize=(6, 5)):
        super().__init__(parent)
        self.figure = Figure(figsize=figsize, tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.theme = "Light"
        # Reapplying the theme walks every Axes/tick/spine/label in the
        # figure (including the colorbar's own axes) -- real cost on a
        # large figure. Most redraws (dragging a gamma/contrast slider,
        # nudging a colorbar limit) don't add or restyle any new artist,
        # so there is nothing for a theme re-application to actually
        # change. Track "dirty" explicitly instead of reapplying on every
        # draw: only style changes and events that create fresh artists
        # (a new colorbar, a mode change that rebuilds the axes) need to
        # mark this again -- see grid_tab.py's refresh_plot().
        self._theme_dirty = True

        export_btn = QPushButton("Export HQ…")
        export_btn.setToolTip("Save this figure at publication resolution (300 dpi, PNG/PDF/SVG)")
        export_btn.clicked.connect(self.export_hq)

        toolbar_row = QHBoxLayout()
        toolbar_row.addWidget(self.toolbar)
        toolbar_row.addStretch(1)
        toolbar_row.addWidget(export_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar_row)
        layout.addWidget(self.canvas)

    def clear(self):
        self.figure.clear()
        self.mark_theme_dirty()  # a cleared figure's fresh axes need re-theming on next draw
        self.canvas.draw_idle()

    def deactivate_navigation(self):
        """Disable the Matplotlib toolbar interaction mode before custom mouse tools."""
        try:
            active = getattr(self.toolbar, "_active", None)
            if active == "ZOOM":
                self.toolbar.zoom()
            elif active == "PAN":
                self.toolbar.pan()
        except Exception:
            pass

    def mark_theme_dirty(self):
        """Call this whenever new artists were added/recreated (a fresh
        colorbar, a mode change that rebuilt the axes, new contour lines,
        annotations, ...) so the next draw() actually restyles them.
        Routine data-only updates don't need this."""
        self._theme_dirty = True

    def draw(self, apply_theme=None):
        if apply_theme is None:
            apply_theme = self._theme_dirty
        if apply_theme:
            style.apply_theme(self.figure, self.theme)
            self._theme_dirty = False
        self.canvas.draw_idle()

    def set_theme(self, theme_name: str):
        if theme_name != self.theme:
            self.theme = theme_name
            self._theme_dirty = True

    def export_hq(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export figure", "figure.png",
            "PNG image (*.png);;PDF document (*.pdf);;SVG vector (*.svg)"
        )
        if not path:
            return
        t = style.THEMES.get(self.theme, style.LIGHT)
        self.figure.savefig(
            path, dpi=300, facecolor=t["figure_facecolor"], bbox_inches="tight"
        )
```

---

## `scientific_visualization/gui/surrogate_tab.py`

```py
from __future__ import annotations
from pathlib import Path
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QSpinBox, QFormLayout, QTextEdit, QFileDialog, QMessageBox, QDoubleSpinBox
from ..io.simulation import SimulationReader
from ..ml.features import sample_grid_features
from ..ml.surrogate_lab import AdvancedSurrogate


class SurrogateTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.features_path = None; self.target_path = None; self.features = None; self.target = None; self.model = None
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.open_features = QPushButton("Open feature dataset…"); self.open_target = QPushButton("Open target dataset…"); self.train = QPushButton("Train surrogate"); self.export = QPushButton("Export report…")
        for b in (self.open_features, self.open_target, self.train, self.export): top.addWidget(b)
        top.addStretch(1); root.addLayout(top)
        form = QFormLayout()
        self.method = QComboBox(); self.method.addItems(["Extra Trees", "Random Forest", "Histogram Gradient Boosting", "Gaussian Process"])
        self.samples = QSpinBox(); self.samples.setRange(100, 2000000); self.samples.setValue(5000)
        self.criterion = QComboBox(); self.criterion.addItems(["Upper confidence bound", "Maximum uncertainty", "Expected improvement"])
        self.beta = QDoubleSpinBox(); self.beta.setRange(0.0, 10.0); self.beta.setValue(2.0); self.beta.setSingleStep(0.25)
        form.addRow("Surrogate:", self.method); form.addRow("Training samples:", self.samples); form.addRow("Active-learning criterion:", self.criterion); form.addRow("UCB beta:", self.beta); root.addLayout(form)
        self.status = QLabel("Load a feature dataset and a target dataset."); self.status.setWordWrap(True); root.addWidget(self.status)
        self.output = QTextEdit(); self.output.setReadOnly(True); root.addWidget(self.output, 1)
        self.open_features.clicked.connect(self._load_features); self.open_target.clicked.connect(self._load_target); self.train.clicked.connect(self._train); self.export.clicked.connect(self._export)

    def _pick(self, title):
        path, _ = QFileDialog.getOpenFileName(self, title, "", "HDF5 files (*.h5 *.hdf5);;All files (*)")
        return path
    def _load_features(self):
        path = self._pick("Open feature dataset")
        if not path: return
        try:
            ds = SimulationReader().load(path); self.features = sample_grid_features(ds, self.samples.value()); self.features_path = path
            self.status.setText(f"Features: {ds.name}, {self.features.values.shape[0]} samples, {self.features.values.shape[1]} columns")
        except Exception as e: QMessageBox.warning(self, "Feature dataset", str(e))
    def _load_target(self):
        path = self._pick("Open target dataset")
        if not path: return
        try:
            ds = SimulationReader().load(path); self.target_path = path
            n = min(ds.data.size, self.features.values.shape[0]) if self.features is not None else ds.data.size
            self.target = np.asarray(ds.data).reshape(-1)[:n]
            if self.features is not None and len(self.features.values) != len(self.target):
                self.features = self.features.__class__(self.features.values[:n], self.features.feature_names, self.features.sample_coordinates[:n] if self.features.sample_coordinates is not None else None, dict(self.features.metadata))
            self.status.setText(f"Target: {ds.name}, {len(self.target)} values")
        except Exception as e: QMessageBox.warning(self, "Target dataset", str(e))
    def _train(self):
        if self.features is None or self.target is None: QMessageBox.information(self, "Surrogate", "Load both feature and target datasets first."); return
        if len(self.features.values) != len(self.target): QMessageBox.warning(self, "Surrogate", "Feature and target sample counts differ."); return
        try:
            self.model = AdvancedSurrogate(self.method.currentText()).fit(self.features, self.target)
            self.model.set_target_cache(self.target)
            report = self.model.report(self.features, self.target, criterion=self.criterion.currentText())
            txt = [f"Method: {report.method}", "", "Validation", json_line(report.metrics), "", "Uncertainty", json_line(report.uncertainty), "", "Feature importance"]
            txt += [f"  {k}: {v:.6g}" for k, v in list(report.feature_importance.items())[:20]]
            txt += ["", f"Recommended next points ({report.acquisition['criterion']})"]
            for idx, score, mean, std in zip(report.acquisition['indices'], report.acquisition['scores'], report.acquisition['mean'], report.acquisition['std']): txt.append(f"  #{idx}: score={score:.6g}, mean={mean:.6g}, sigma={std:.6g}")
            self.output.setPlainText("\n".join(txt))
        except Exception as e: QMessageBox.warning(self, "Surrogate training failed", str(e))
    def _export(self):
        if self.model is None: return
        path, _ = QFileDialog.getSaveFileName(self, "Export surrogate report", "surrogate_report.json", "JSON files (*.json)")
        if not path: return
        try:
            report = self.model.report(self.features, self.target, criterion=self.criterion.currentText()); self.model.export_report(report, path); self.status.setText(f"Exported surrogate report: {Path(path).name}")
        except Exception as e: QMessageBox.warning(self, "Export failed", str(e))

def json_line(d):
    return ", ".join(f"{k}={float(v):.6g}" for k, v in d.items())
```

---

## `scientific_visualization/gui/three_d_tab.py`

```py
from __future__ import annotations

from pathlib import Path
import numpy as np
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog, QCheckBox, QListWidget,
    QSpinBox, QLineEdit,
)

from ..core.configuration import RenderingConfig
from ..io.simulation import SimulationReader
from ..visualization.three_d import ThreeDRenderer
from ..session import save_xml_session, load_xml_session, value_as_bool, value_as_float, value_as_int
from .base_tab import BaseTab


class ThreeDTab(BaseTab):
    open_in_2d_requested = pyqtSignal(str)
    """Interactive PyVista viewer for native 3D data and 2D-to-3D promotion.

    Inherits the same splitter + scrollable control panel + "Panel:
    Left/Right/Top/Bottom" placement control as the 2D Fields/Grid tab
    (see gui/base_tab.py) by supplying its PyVista viewport as a custom
    `view_widget` -- the panel-position feature is implemented exactly
    once, in BaseTab, and both tabs get it for free.
    """

    def __init__(self, parent=None):
        self.dataset = None
        self.reader = SimulationReader()
        self._series = None
        self.renderer = None
        self.files: list[str] = []
        self._pending_files: list[str] = []
        self.file_list = None

        view_container = self._build_view_widget()
        super().__init__(parent, view_widget=view_container)
        self._build_controls()
        self.finish_layout()

    def _build_view_widget(self) -> QWidget:
        """Build the 3D viewport (or a fallback message if PyVista/PyVistaQt
        aren't installed), plus the interaction hint shown just below it,
        as a single widget suitable for BaseTab's `view_widget`."""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        try:
            from pyvistaqt import QtInteractor
            self._qt_interactor = QtInteractor(container)
            self._qt_interactor.setMinimumHeight(500)
            vbox.addWidget(self._qt_interactor, 1)
            self.renderer = ThreeDRenderer(self._qt_interactor)
            try:
                self._qt_interactor.enable_trackball_style()
            except Exception:
                pass
            interaction = QLabel("3D interaction: left-drag rotate • wheel zoom • middle-drag pan. Use Isometric to reset orientation.")
            interaction.setWordWrap(True)
            vbox.addWidget(interaction)
        except ImportError:
            self._qt_interactor = None
            msg = QLabel("3D viewer unavailable. Install PyVista and PyVistaQt to enable it.")
            msg.setWordWrap(True)
            vbox.addWidget(msg, 1)
        return container

    def _build_controls(self):
        controls = QGroupBox("3D visualization")
        form = QFormLayout(controls)
        file_buttons = QHBoxLayout()
        open_btn = QPushButton("Open file…")
        open_btn.clicked.connect(self.open_file)
        folder_btn = QPushButton("Open folder…")
        folder_btn.clicked.connect(self.open_folder)
        file_buttons.addWidget(open_btn); file_buttons.addWidget(folder_btn)
        form.addRow(file_buttons)
        self.file_list = QListWidget()
        self.file_list.currentRowChanged.connect(self._pending_row_changed)
        layout_pending = QVBoxLayout()
        apply_btn = QPushButton("Apply selection")
        apply_btn.clicked.connect(self.apply_selection)
        layout_pending.addWidget(self.file_list)
        layout_pending.addWidget(apply_btn)
        nav = QHBoxLayout()
        self.prev_frame_btn = QPushButton("◀ Previous frame"); self.prev_frame_btn.clicked.connect(lambda: self._select_relative(-1))
        self.next_frame_btn = QPushButton("Next frame ▶"); self.next_frame_btn.clicked.connect(lambda: self._select_relative(1))
        nav.addWidget(self.prev_frame_btn); nav.addWidget(self.next_frame_btn)
        layout_pending.addLayout(nav)
        session_row = QHBoxLayout()
        save_session = QPushButton("Save .xml…"); save_session.clicked.connect(self.save_session)
        load_session = QPushButton("Restore .xml…"); load_session.clicked.connect(self.load_session)
        session_row.addWidget(save_session); session_row.addWidget(load_session)
        layout_pending.addLayout(session_row)
        self.mode = QComboBox(); self.mode.addItems([
            "2D plane", "2D surface", "2D extrusion",
            "3D orthogonal slices", "3D volume", "3D isosurfaces", "3D threshold", "3D clip plane",
        ])
        self.mode.currentTextChanged.connect(self._update_mode_controls)
        form.addRow("Mode:", self.mode)
        self.plane_axis = QComboBox(); self.plane_axis.addItems(["x1", "x2", "x3"])
        form.addRow("Plane normal / height axis:", self.plane_axis)
        self.position = QDoubleSpinBox(); self.position.setRange(-1e12,1e12); self.position.setDecimals(6); self.position.setValue(0.0)
        form.addRow("Plane/base position:", self.position)
        self.z_scale = QDoubleSpinBox(); self.z_scale.setRange(-1e6,1e6); self.z_scale.setDecimals(6); self.z_scale.setValue(1.0)
        form.addRow("Surface height scale:", self.z_scale)
        self.depth = QDoubleSpinBox(); self.depth.setRange(-1e12,1e12); self.depth.setDecimals(6); self.depth.setValue(1.0)
        form.addRow("Extrusion depth:", self.depth)

        self.isosurface_box = QGroupBox("Isosurface options")
        iso_form = QFormLayout(self.isosurface_box)
        self.isovalue_mode = QComboBox(); self.isovalue_mode.addItems(["Auto (percentiles)", "Manual list"])
        self.isovalue_mode.currentTextChanged.connect(self._update_isovalue_controls)
        iso_form.addRow("Isovalues:", self.isovalue_mode)
        self.isovalue_count = QSpinBox(); self.isovalue_count.setRange(1, 10); self.isovalue_count.setValue(3)
        iso_form.addRow("Number of surfaces:", self.isovalue_count)
        self.isovalue_manual = QLineEdit(); self.isovalue_manual.setPlaceholderText("e.g. 0.1, 0.3, 0.6")
        iso_form.addRow("Values (comma-separated):", self.isovalue_manual)
        self.isovalue_suggest_btn = QPushButton("Suggest values from data")
        self.isovalue_suggest_btn.clicked.connect(self._fill_suggested_isovalues)
        iso_form.addRow(self.isovalue_suggest_btn)
        form.addRow(self.isosurface_box)

        self.threshold_box = QGroupBox("Threshold options")
        th_form = QFormLayout(self.threshold_box)
        self.threshold_min = QDoubleSpinBox(); self.threshold_min.setRange(-1e300, 1e300); self.threshold_min.setDecimals(8)
        self.threshold_max = QDoubleSpinBox(); self.threshold_max.setRange(-1e300, 1e300); self.threshold_max.setDecimals(8); self.threshold_max.setValue(1.0)
        th_form.addRow("Lower:", self.threshold_min); th_form.addRow("Upper:", self.threshold_max)
        form.addRow(self.threshold_box)

        self.clip_box = QGroupBox("Clip plane options")
        clip_form = QFormLayout(self.clip_box)
        self.clip_normal = QComboBox(); self.clip_normal.addItems(["x", "y", "z"])
        clip_form.addRow("Plane normal:", self.clip_normal)
        self.clip_interactive = QCheckBox("Interactive (drag the plane widget in the viewport)")
        self.clip_interactive.setChecked(True)
        clip_form.addRow(self.clip_interactive)
        form.addRow(self.clip_box)

        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0.05,1.0); self.opacity.setSingleStep(0.05); self.opacity.setValue(1.0)
        form.addRow("Opacity:", self.opacity)
        self.cmap = QComboBox(); self.cmap.addItems(["viridis","plasma","inferno","magma","cividis","turbo","coolwarm","RdBu_r","twilight","gray"])
        form.addRow("Colormap:", self.cmap)
        self.reverse_colors = QCheckBox("Reverse colormap"); form.addRow(self.reverse_colors)
        self.symmetric = QCheckBox("Symmetric color limits"); self.symmetric.setChecked(False); form.addRow(self.symmetric)
        self.vmin = QDoubleSpinBox(); self.vmin.setRange(-1e300, 1e300); self.vmin.setDecimals(10); form.addRow("Color minimum:", self.vmin)
        self.vmax = QDoubleSpinBox(); self.vmax.setRange(-1e300, 1e300); self.vmax.setDecimals(10); form.addRow("Color maximum:", self.vmax)
        self.use_limits = QCheckBox("Use manual color limits"); form.addRow(self.use_limits)
        self.colorbar_position = QComboBox(); self.colorbar_position.addItems(["right", "left", "top", "bottom"])
        form.addRow("Colorbar position:", self.colorbar_position)
        self.colorbar_box = QCheckBox("Colorbar box/outline"); form.addRow(self.colorbar_box)
        self.colorbar_interactive = QCheckBox("Draggable colorbar (drag/resize with mouse)")
        self.colorbar_interactive.setChecked(True)
        form.addRow(self.colorbar_interactive)
        self.colorbar_width = QDoubleSpinBox(); self.colorbar_width.setRange(0.02, 1.0); self.colorbar_width.setDecimals(3); self.colorbar_width.setValue(0.10); self.colorbar_width.setSingleStep(0.01); form.addRow("Colorbar width:", self.colorbar_width)
        self.colorbar_height = QDoubleSpinBox(); self.colorbar_height.setRange(0.02, 1.0); self.colorbar_height.setDecimals(3); self.colorbar_height.setValue(0.80); self.colorbar_height.setSingleStep(0.01); form.addRow("Colorbar height:", self.colorbar_height)
        self.smooth_shading = QCheckBox("Smooth shading"); self.smooth_shading.setChecked(True); form.addRow(self.smooth_shading)
        self.show_edges = QCheckBox("Show mesh edges"); form.addRow(self.show_edges)
        advanced3d = QGroupBox("Advanced 3D rendering")
        adv_form = QFormLayout(advanced3d)
        self.render_quality = QComboBox(); self.render_quality.addItems(["High", "Balanced", "Fast"]); self.render_quality.setCurrentText("Balanced")
        adv_form.addRow("Render quality:", self.render_quality)
        self.lighting = QCheckBox("Surface lighting"); self.lighting.setChecked(True); adv_form.addRow(self.lighting)
        self.eye_dome_lighting = QCheckBox("Eye-dome lighting (depth enhancement)"); adv_form.addRow(self.eye_dome_lighting)
        self.depth_peeling = QCheckBox("Depth peeling (high-quality transparency)"); adv_form.addRow(self.depth_peeling)
        self.ssao = QCheckBox("SSAO (ambient occlusion)"); adv_form.addRow(self.ssao)
        self.stereo = QCheckBox("Stereo render") ; adv_form.addRow(self.stereo)
        self.hidden_line_removal = QCheckBox("Hidden-line geometry mode"); adv_form.addRow(self.hidden_line_removal)
        self.antialiasing = QCheckBox("Anti-aliasing"); self.antialiasing.setChecked(True); adv_form.addRow(self.antialiasing)
        self.show_edges_strength = QDoubleSpinBox(); self.show_edges_strength.setRange(0, 1); self.show_edges_strength.setValue(1); self.show_edges_strength.setSingleStep(0.1); adv_form.addRow("Edge opacity:", self.show_edges_strength)
        self.camera_preset = QComboBox(); self.camera_preset.addItems(["Current", "Isometric", "Front", "Back", "Left", "Right", "Top", "Bottom", "Fit to data"]); adv_form.addRow("Camera preset:", self.camera_preset)
        apply_cam = QPushButton("Apply camera preset"); apply_cam.clicked.connect(self.apply_camera_preset); adv_form.addRow(apply_cam)
        form.addRow(advanced3d)
        self.fast_render = QComboBox(); self.fast_render.addItems(["Full resolution", "75% resolution", "50% resolution", "25% resolution"]); self.fast_render.setToolTip("Render a lower-resolution copy for interactive exploration. Source data are unchanged."); form.addRow("Interactive resolution:", self.fast_render)
        self.show_bounding_box = QCheckBox("Show bounding box / axis ticks")
        self.show_bounding_box.stateChanged.connect(self._toggle_bounding_box)
        form.addRow(self.show_bounding_box)
        self.show_orientation_axes = QCheckBox("Show orientation widget")
        self.show_orientation_axes.setChecked(True)
        self.show_orientation_axes.stateChanged.connect(self._toggle_orientation_axes)
        form.addRow(self.show_orientation_axes)
        buttons = QHBoxLayout()
        render = QPushButton("Render / replace scene")
        render.clicked.connect(self.render)
        buttons.addWidget(render)
        add = QPushButton("Add to scene")
        add.clicked.connect(lambda: self.render(clear_scene=False))
        buttons.addWidget(add)
        clear = QPushButton("Clear scene")
        clear.clicked.connect(self.clear_scene)
        buttons.addWidget(clear)
        form.addRow(buttons)
        camera = QHBoxLayout()
        reset = QPushButton("Reset camera")
        reset.clicked.connect(self.reset_camera)
        camera.addWidget(reset)
        iso = QPushButton("Isometric")
        iso.clicked.connect(self.isometric_camera)
        camera.addWidget(iso)
        screenshot = QPushButton("Save screenshot…")
        screenshot.clicked.connect(self.save_screenshot)
        camera.addWidget(screenshot)
        form.addRow(camera)
        move_row = QHBoxLayout()
        self.move_left_btn = QPushButton("←"); self.move_left_btn.setToolTip("Move 3D view left"); self.move_left_btn.clicked.connect(lambda: self.move_camera(-1, 0))
        self.move_right_btn = QPushButton("→"); self.move_right_btn.setToolTip("Move 3D view right"); self.move_right_btn.clicked.connect(lambda: self.move_camera(1, 0))
        self.move_up_btn = QPushButton("↑"); self.move_up_btn.setToolTip("Move 3D view up"); self.move_up_btn.clicked.connect(lambda: self.move_camera(0, 1))
        self.move_down_btn = QPushButton("↓"); self.move_down_btn.setToolTip("Move 3D view down"); self.move_down_btn.clicked.connect(lambda: self.move_camera(0, -1))
        for b in (self.move_left_btn, self.move_right_btn, self.move_up_btn, self.move_down_btn): move_row.addWidget(b)
        form.addRow("Move view:", move_row)
        self.info = QLabel("No dataset loaded.")
        self.info.setWordWrap(True)
        form.addRow(self.info)
        self.control_layout.addWidget(controls)
        self.control_layout.addLayout(layout_pending)
        self._update_mode_controls(self.mode.currentText())

    def refresh_plot(self):
        """BaseTab (e.g. after a theme change) calls this expecting every
        tab to be able to re-render itself. The 3D tab otherwise renders
        only on explicit user action (the Render/Add/Clear buttons), so
        this just re-renders the current dataset with existing settings
        if one is already loaded, and is a no-op otherwise."""
        if self.dataset is not None:
            self.render(clear_scene=True)

    def _open_current_in_2d(self):
        if self.dataset is not None and getattr(self.dataset, "source", None):
            self.open_in_2d_requested.emit(str(self.dataset.source))

    def _pending_row_changed(self, row):
        if 0 <= row < len(self._pending_files):
            self.info.setText(f"Selected: {Path(self._pending_files[row]).name}. Click Apply selection to load it.")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HDF5 file", "", "HDF5 files (*.h5 *.hdf5);;All files (*)")
        if not path:
            return
        self._pending_files = [path]
        self.file_list.clear(); self.file_list.addItem(Path(path).name); self.file_list.setCurrentRow(0)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open data folder")
        if not folder:
            return
        files = sorted(str(p) for p in Path(folder).iterdir() if p.suffix.lower() in {".h5", ".hdf5"})
        if not files:
            QMessageBox.warning(self, "No files found", "No HDF5 files were found in that folder.")
            return
        self._pending_files = files
        self.file_list.clear()
        self.file_list.addItems([Path(f).name for f in files])
        self.file_list.setCurrentRow(0)

    def apply_selection(self):
        row = self.file_list.currentRow() if self.file_list is not None else -1
        if not (0 <= row < len(self._pending_files)):
            return
        path = self._pending_files[row]
        try:
            self.files = list(self._pending_files)
            from ..io.lazy import LazyGridSeries
            self._series = LazyGridSeries(self.files, cache_size=3) if len(self.files) > 1 else None
            if self._series is not None:
                row = self.file_list.currentRow()
                self.dataset = self._series.load(max(0, row)).to_dataset()
            else:
                self.dataset = self.reader.load(path)
            self.info.setText(self.dataset.summary() + " | 2D data can be rendered as plane, surface, or extrusion in 3D; 3D data can be sliced into 2D in the Fields / Grid tab.")
            self._configure_2d_axis_options()
            if self.dataset.ndim == 3:
                finite = self.dataset.data[np.isfinite(self.dataset.data)]
                if finite.size:
                    lo, hi = float(finite.min()), float(finite.max())
                    self.threshold_min.setRange(lo, hi); self.threshold_max.setRange(lo, hi)
                    self.threshold_min.setValue(lo + 0.20 * (hi - lo)); self.threshold_max.setValue(lo + 0.80 * (hi - lo))
                self.mode.blockSignals(True); self.mode.setCurrentText("3D orthogonal slices"); self.mode.blockSignals(False)
                self._update_mode_controls(self.mode.currentText())
            elif self.dataset.ndim == 2:
                self.mode.blockSignals(True); self.mode.setCurrentText("2D plane"); self.mode.blockSignals(False)
                self._update_mode_controls(self.mode.currentText())
            self.prev_frame_btn.setEnabled(self.file_list.currentRow() > 0)
            self.next_frame_btn.setEnabled(self.file_list.currentRow() < len(self.files) - 1)
            self.render()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load dataset", str(exc))

    def _select_relative(self, delta: int):
        count = self.file_list.count() if self.file_list is not None else 0
        if count == 0: return
        row = max(0, self.file_list.currentRow())
        new_row = max(0, min(count - 1, row + int(delta)))
        if new_row != row:
            self.file_list.blockSignals(True); self.file_list.setCurrentRow(new_row); self.file_list.blockSignals(False)
            self.apply_selection()

    def move_camera(self, dx: int, dy: int):
        if self.renderer is not None:
            try: self.renderer.move_camera_screen(dx, dy)
            except Exception as exc: QMessageBox.warning(self, "Camera movement failed", str(exc))

    def _camera_state(self):
        if self.renderer is None: return {}
        cam = self.renderer.plotter.camera
        return {"camera_position": list(cam.position), "camera_focal_point": list(cam.focal_point), "camera_up": list(cam.up)}

    def _session_state(self):
        state = {
            "tab": "3d", "files": list(self.files), "pending_files": list(self._pending_files),
            "current_index": self.file_list.currentRow(), "mode": self.mode.currentText(),
            "plane_axis": self.plane_axis.currentText(), "position": self.position.value(), "z_scale": self.z_scale.value(), "depth": self.depth.value(),
            "opacity": self.opacity.value(), "cmap": self.cmap.currentText(), "reverse_colors": self.reverse_colors.isChecked(),
            "symmetric": self.symmetric.isChecked(), "use_limits": self.use_limits.isChecked(), "vmin": self.vmin.value(), "vmax": self.vmax.value(),
            "colorbar_position": self.colorbar_position.currentText(), "smooth_shading": self.smooth_shading.isChecked(),
            "render_quality": self.render_quality.currentText(), "fast_render": self.fast_render.currentText(),
            "show_bounding_box": self.show_bounding_box.isChecked(), "show_orientation_axes": self.show_orientation_axes.isChecked(),
            "isovalue_mode": self.isovalue_mode.currentText(), "isovalue_count": self.isovalue_count.value(), "isovalue_manual": self.isovalue_manual.text(),
        }
        state.update(self._camera_state()); return state

    def save_session(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save 3D session", "session_3d.xml", "XML session (*.xml)")
        if not path: return
        try: save_xml_session(path, self._session_state()); self.info.setText(f"3D session saved: {path}")
        except Exception as exc: QMessageBox.warning(self, "Could not save session", str(exc))

    def load_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore 3D session", "", "XML session (*.xml)")
        if not path: return
        try:
            state = load_xml_session(path)
            self._pending_files = [str(x) for x in state.get("files", []) if Path(str(x)).exists()]
            if not self._pending_files: raise ValueError("None of the session's data files are currently available.")
            self.file_list.clear(); self.file_list.addItems([Path(f).name for f in self._pending_files])
            row = max(0, min(value_as_int(state.get("current_index"), 0), len(self._pending_files)-1)); self.file_list.setCurrentRow(row)
            self.mode.setCurrentText(str(state.get("mode", self.mode.currentText()))); self.plane_axis.setCurrentText(str(state.get("plane_axis", self.plane_axis.currentText())))
            self.position.setValue(value_as_float(state.get("position"), self.position.value())); self.z_scale.setValue(value_as_float(state.get("z_scale"), self.z_scale.value())); self.depth.setValue(value_as_float(state.get("depth"), self.depth.value()))
            self.opacity.setValue(value_as_float(state.get("opacity"), self.opacity.value())); self.cmap.setCurrentText(str(state.get("cmap", self.cmap.currentText()))); self.reverse_colors.setChecked(value_as_bool(state.get("reverse_colors")))
            self.symmetric.setChecked(value_as_bool(state.get("symmetric"))); self.use_limits.setChecked(value_as_bool(state.get("use_limits"))); self.vmin.setValue(value_as_float(state.get("vmin"), self.vmin.value())); self.vmax.setValue(value_as_float(state.get("vmax"), self.vmax.value()))
            self.colorbar_position.setCurrentText(str(state.get("colorbar_position", self.colorbar_position.currentText()))); self.smooth_shading.setChecked(value_as_bool(state.get("smooth_shading"))); self.render_quality.setCurrentText(str(state.get("render_quality", self.render_quality.currentText()))); self.fast_render.setCurrentText(str(state.get("fast_render", self.fast_render.currentText())))
            self.show_bounding_box.setChecked(value_as_bool(state.get("show_bounding_box"))); self.show_orientation_axes.setChecked(value_as_bool(state.get("show_orientation_axes")))
            self.isovalue_mode.setCurrentText(str(state.get("isovalue_mode", self.isovalue_mode.currentText()))); self.isovalue_count.setValue(value_as_int(state.get("isovalue_count"), self.isovalue_count.value())); self.isovalue_manual.setText(str(state.get("isovalue_manual", "")))
            self.apply_selection()
            if self.renderer is not None and all(k in state for k in ("camera_position", "camera_focal_point", "camera_up")):
                cam = self.renderer.plotter.camera
                cam.position = tuple(value_as_float(v) for v in state["camera_position"])
                cam.focal_point = tuple(value_as_float(v) for v in state["camera_focal_point"])
                cam.up = tuple(value_as_float(v) for v in state["camera_up"])
                self.renderer.plotter.reset_camera_clipping_range(); self.renderer.plotter.render()
            self.info.setText(f"3D session restored: {path}")
        except Exception as exc: QMessageBox.warning(self, "Could not restore 3D session", str(exc))

    def _configure_2d_axis_options(self):
        if self.dataset is None or self.dataset.ndim != 2:
            return
        present = [a.name.lower() for a in self.dataset.coordinates]
        missing = [a for a in ("x1", "x2", "x3") if a not in present]
        self.plane_axis.blockSignals(True)
        self.plane_axis.clear()
        self.plane_axis.addItems(missing or ["x3"])
        self.plane_axis.blockSignals(False)
        if missing:
            self.position.setRange(-1e12, 1e12)
            self.position.setValue(0.0)

    def _update_mode_controls(self, mode):
        is2d_plane_mode = mode in ("2D plane", "2D surface", "2D extrusion")
        self.plane_axis.setEnabled(is2d_plane_mode)
        self.position.setEnabled(is2d_plane_mode)
        self.z_scale.setEnabled(mode == "2D surface")
        self.depth.setEnabled(mode == "2D extrusion")
        self.isosurface_box.setVisible(mode == "3D isosurfaces")
        self.clip_box.setVisible(mode == "3D clip plane")
        self.threshold_box.setVisible(mode == "3D threshold")
        if mode == "3D isosurfaces":
            self._update_isovalue_controls(self.isovalue_mode.currentText())

    def _update_isovalue_controls(self, isovalue_mode_text):
        manual = isovalue_mode_text == "Manual list"
        self.isovalue_manual.setEnabled(manual)
        self.isovalue_count.setEnabled(not manual)
        self.isovalue_suggest_btn.setEnabled(manual)

    def _fill_suggested_isovalues(self):
        if self.dataset is None or self.dataset.ndim != 3:
            QMessageBox.information(self, "No 3D dataset", "Load a 3D dataset first.")
            return
        try:
            values = self.renderer.suggest_isovalues(self.dataset, n=self.isovalue_count.value())
        except Exception as exc:
            QMessageBox.warning(self, "Could not suggest isovalues", str(exc))
            return
        self.isovalue_manual.setText(", ".join(f"{v:.6g}" for v in values))

    def _toggle_bounding_box(self, _state=None):
        if self.renderer is not None:
            self.renderer.set_show_bounding_box(self.show_bounding_box.isChecked())
            self.renderer.plotter.render()

    def _toggle_orientation_axes(self, _state=None):
        if self.renderer is not None:
            self.renderer.set_show_orientation_axes(self.show_orientation_axes.isChecked())
            self.renderer.plotter.render()

    def save_screenshot(self):
        if self.renderer is None:
            QMessageBox.information(self, "3D viewer unavailable", "Install PyVista and PyVistaQt to enable screenshots.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save screenshot", "screenshot.png", "PNG image (*.png)")
        if not path:
            return
        try:
            self.renderer.save_screenshot(path)
            self.info.setText(f"Screenshot saved to {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Could not save screenshot", str(exc))

    def clear_scene(self):
        if self.renderer is not None:
            self.renderer.plotter.clear()
            self.renderer.plotter.render()

    def reset_camera(self):
        if self.renderer is not None:
            self.renderer.plotter.reset_camera()
            self.renderer.plotter.render()

    def isometric_camera(self):
        if self.renderer is not None:
            self.renderer.plotter.view_isometric()
            self.renderer.plotter.render()

    def apply_camera_preset(self):
        """Move the camera to a standard view. Directions follow the same
        convention as Blender's numpad views (verified empirically against
        PyVista's camera_position, not guessed):
          Front/Back look along the Y axis, Left/Right along X, Top/Bottom
          along Z. "Fit to data" re-frames the current camera direction so
          the whole scene is visible, without changing which way it faces.
        """
        if self.renderer is None:
            return
        preset = self.camera_preset.currentText()
        try:
            if preset == "Isometric": self.renderer.plotter.view_isometric()
            elif preset == "Front": self.renderer.plotter.view_xz()
            elif preset == "Back": self.renderer.plotter.view_xz(negative=True)
            elif preset == "Right": self.renderer.plotter.view_yz()
            elif preset == "Left": self.renderer.plotter.view_yz(negative=True)
            elif preset == "Top": self.renderer.plotter.view_xy()
            elif preset == "Bottom": self.renderer.plotter.view_xy(negative=True)
            elif preset == "Fit to data": pass  # just reset_camera_clipping_range()+reset_camera() below
            if preset in ("Fit to data", "Current"):
                self.renderer.plotter.reset_camera()
            self.renderer.plotter.reset_camera_clipping_range(); self.renderer.plotter.render()
        except Exception as exc:
            QMessageBox.warning(self, "Camera preset failed", str(exc))

    def render(self, clear_scene=True):
        if self.dataset is None or self.renderer is None:
            return
        if clear_scene:
            self.renderer.plotter.clear()
        cmap = self.cmap.currentText() + ("_r" if self.reverse_colors.isChecked() and not self.cmap.currentText().endswith("_r") else "")
        vmin = self.vmin.value() if self.use_limits.isChecked() else None
        vmax = self.vmax.value() if self.use_limits.isChecked() else None
        if self.use_limits.isChecked() and vmin >= vmax:
            QMessageBox.warning(self, "Invalid color range", "Color minimum must be smaller than color maximum.")
            return
        cfg = RenderingConfig(
            colormap=cmap, opacity=self.opacity.value(), vmin=vmin, vmax=vmax,
            symmetric_limits=self.symmetric.isChecked(),
            colorbar_position=self.colorbar_position.currentText(),
            colorbar_box=self.colorbar_box.isChecked(),
            colorbar_interactive=self.colorbar_interactive.isChecked(),
            colorbar_width=self.colorbar_width.value(), colorbar_height=self.colorbar_height.value(),
            smooth_shading=self.smooth_shading.isChecked(), show_edges=self.show_edges.isChecked(),
            lighting=self.lighting.isChecked(), eye_dome_lighting=self.eye_dome_lighting.isChecked(),
            depth_peeling=self.depth_peeling.isChecked(), ssao=self.ssao.isChecked(),
            stereo=self.stereo.isChecked(), hidden_line_removal=self.hidden_line_removal.isChecked(),
            antialiasing=self.antialiasing.isChecked(),
            render_decimation={"Full resolution":1.0,"75% resolution":0.75,"50% resolution":0.5,"25% resolution":0.25}[self.fast_render.currentText()],
        )
        try:
            if self.dataset.ndim == 2:
                mode = self.mode.currentText()
                if mode == "2D plane":
                    self.renderer.add_2d_plane(self.dataset, plane_axis=self.plane_axis.currentText(), position=self.position.value(), config=cfg)
                elif mode == "2D surface":
                    self.renderer.add_2d_surface(self.dataset, z_scale=self.z_scale.value(), height_axis=self.plane_axis.currentText(), base_position=self.position.value(), config=cfg)
                elif mode == "2D extrusion":
                    self.renderer.add_2d_extrusion(self.dataset, depth=self.depth.value(), extrusion_axis=self.plane_axis.currentText(), start_position=self.position.value(), config=cfg)
                else:
                    raise ValueError(f"'{mode}' requires a native 3D dataset; this file is 2D. Choose a 2D mode instead.")
            elif self.dataset.ndim == 3:
                mode = self.mode.currentText()
                if mode == "3D volume":
                    self.renderer.add_native_3d(self.dataset, config=cfg)
                elif mode == "3D isosurfaces":
                    isovalues = self._resolve_isovalues()
                    self.renderer.add_isosurfaces(self.dataset, isovalues, config=cfg, smooth=self.smooth_shading.isChecked())
                elif mode == "3D threshold":
                    self.renderer.add_threshold(self.dataset, lower=self.threshold_min.value(), upper=self.threshold_max.value(), config=cfg)
                elif mode == "3D clip plane":
                    self.renderer.add_clipped_volume(
                        self.dataset, config=cfg, normal=self.clip_normal.currentText(),
                        interactive=self.clip_interactive.isChecked(),
                    )
                elif mode in ("2D plane", "2D surface", "2D extrusion"):
                    raise ValueError(f"'{mode}' requires a 2D dataset; this file is 3D. Choose a 3D mode instead.")
                else:
                    self.renderer.add_native_3d_slices(self.dataset, config=cfg)
            else:
                raise ValueError("The 3D viewer supports 2D or 3D scalar datasets")
            if clear_scene:
                self.renderer.plotter.reset_camera()
                self.renderer.set_show_bounding_box(self.show_bounding_box.isChecked())
                self.renderer.set_show_orientation_axes(self.show_orientation_axes.isChecked())
            self.renderer.set_render_quality(self.render_quality.currentText())
            self.renderer.plotter.render()
        except Exception as exc:
            QMessageBox.warning(self, "Rendering failed", str(exc))

    def _resolve_isovalues(self) -> list[float]:
        """Isovalues per the current mode ("Auto (percentiles)" or "Manual
        list"), raising a clear error for unparsable manual input rather
        than silently ignoring it."""
        if self.isovalue_mode.currentText() == "Manual list":
            text = self.isovalue_manual.text().strip()
            if not text:
                raise ValueError("Enter one or more comma-separated isovalues, or switch to 'Auto (percentiles)'.")
            try:
                return [float(v) for v in text.split(",") if v.strip()]
            except ValueError:
                raise ValueError(f"Could not parse isovalues from '{text}'; use a comma-separated list of numbers, e.g. 0.1, 0.3, 0.6")
        return self.renderer.suggest_isovalues(self.dataset, n=self.isovalue_count.value())
```

---

## `scientific_visualization/gui/tracks_tab.py`

```py
import numpy as np
from matplotlib.collections import LineCollection
from PyQt5.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QSpinBox

from .. import style
from ..analysis import smooth_1d
from ..io.tracks import TracksFile
from .base_tab import BaseTab


class TracksTab(BaseTab):
    """View particle trajectories: quantity-vs-quantity (e.g. x1 vs x2) or
    quantity-vs-time, colored by track index, a chosen palette, or a
    physical quantity (e.g. energy) along the trajectory."""

    file_filter = "HDF5 files (*.h5 *.hdf5);;All files (*)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tf = None

        self.file_list = self.add_open_buttons(folder=False, label="tracks file")
        self.file_list.currentRowChanged.connect(self.on_file_selected)

        opts_box = QGroupBox("Display")
        form = QFormLayout(opts_box)

        self.x_quant = QComboBox()
        self.y_quant = QComboBox()
        self.x_quant.currentTextChanged.connect(self.refresh_plot)
        self.y_quant.currentTextChanged.connect(self.refresh_plot)
        form.addRow("X quantity:", self.x_quant)
        form.addRow("Y quantity:", self.y_quant)

        self.n_tracks_spin = QSpinBox()
        self.n_tracks_spin.setRange(1, 1)
        self.n_tracks_spin.valueChanged.connect(self.refresh_plot)
        form.addRow("Tracks to show:", self.n_tracks_spin)
        self.control_layout.addWidget(opts_box)

        color_box = QGroupBox("Color")
        color_form = QFormLayout(color_box)
        self.color_mode = QComboBox()
        self.color_mode.addItems(["Single color", "By track index", "By quantity along track"])
        self.color_mode.setCurrentText("By track index")
        self.color_mode.currentTextChanged.connect(self._update_color_widgets)
        self.color_mode.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Mode:", self.color_mode)

        self.palette_combo = QComboBox()
        self.palette_combo.addItems(list(style.LINE_PALETTES.keys()))
        self.palette_combo.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Index palette:", self.palette_combo)

        self.color_quant = QComboBox()
        self.color_quant.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Color by:", self.color_quant)

        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(style.ALL_COLORMAPS)
        self.cmap_combo.setCurrentText("viridis")
        self.cmap_combo.currentTextChanged.connect(self.refresh_plot)
        color_form.addRow("Colormap:", self.cmap_combo)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 16)
        self._update_color_preview()
        color_btn = self.add_color_picker_button(self._on_color_picked, "Pick single color…")
        color_form.addRow(self.color_preview, color_btn)

        self.control_layout.addWidget(color_box)

        smooth_box = QGroupBox("Smoothing (per track)")
        smooth_form = QFormLayout(smooth_box)
        self.smooth_method = QComboBox()
        self.smooth_method.addItems(["None", "Moving average", "Gaussian"])
        self.smooth_method.currentTextChanged.connect(self.refresh_plot)
        smooth_form.addRow("Method:", self.smooth_method)
        self.smooth_window = QSpinBox()
        self.smooth_window.setRange(1, 200)
        self.smooth_window.setValue(5)
        self.smooth_window.valueChanged.connect(self.refresh_plot)
        smooth_form.addRow("Window / sigma:", self.smooth_window)
        self.control_layout.addWidget(smooth_box)

        self.info_label = QLabel("No file loaded.")
        self.info_label.setWordWrap(True)
        self.control_layout.addWidget(self.info_label)

        self.finish_layout()
        self._update_color_widgets()

    def _on_color_picked(self, color):
        self._update_color_preview()
        self.refresh_plot()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(f"background-color: {self.accent_hex()}; border: 1px solid #888;")

    def _update_color_widgets(self):
        mode = self.color_mode.currentText()
        self.color_quant.setEnabled(mode == "By quantity along track")
        self.cmap_combo.setEnabled(mode != "Single color")
        self.palette_combo.setEnabled(mode == "By track index")

    def on_file_selected(self, row):
        if row < 0 or row >= len(self.files):
            return
        try:
            self.tf = TracksFile.info(self.files[row])
        except Exception as exc:
            self.info_label.setText(f"<span style='color:#c0392b'>Error reading file:<br>{exc}</span>")
            return

        quants = self.tf.quants
        for combo, default in ((self.x_quant, "t" if "t" in quants else quants[0] if quants else ""),
                                (self.y_quant, "x1" if "x1" in quants else (quants[1] if len(quants) > 1 else ""))):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(quants)
            if default in quants:
                combo.setCurrentText(default)
            combo.blockSignals(False)

        self.color_quant.blockSignals(True)
        self.color_quant.clear()
        self.color_quant.addItems(quants)
        if "ene" in quants:
            self.color_quant.setCurrentText("ene")
        self.color_quant.blockSignals(False)

        self.n_tracks_spin.setRange(1, max(1, self.tf.ntracks))
        self.n_tracks_spin.setValue(min(self.tf.ntracks, 20))

        self.info_label.setText(
            f"<b>{self.tf.name}</b><br>"
            f"N tracks: {self.tf.ntracks}<br>"
            f"quantities: {', '.join(quants)}<br>"
            f"dt: {self.tf.dt:g}"
        )
        self.refresh_plot()

    def refresh_plot(self):
        if self.tf is None or not self.x_quant.currentText() or not self.y_quant.currentText():
            return
        self.canvas.clear()
        ax = self.canvas.figure.add_subplot(111)

        xq = self.x_quant.currentText()
        yq = self.y_quant.currentText()
        n = self.n_tracks_spin.value()
        color_mode = self.color_mode.currentText()
        cmap_name = self.cmap_combo.currentText()
        smooth_method = self.smooth_method.currentText()
        smooth_window = self.smooth_window.value()

        index_colors = None
        if color_mode == "By track index":
            index_colors = style.line_color_cycle(self.palette_combo.currentText(), n, cmap_name)

        mappable = None
        cq = self.color_quant.currentText()
        vmin = vmax = None
        if color_mode == "By quantity along track" and cq:
            all_vals = []
            for i in range(n):
                trk = self.tf.get_track(i)
                if cq in trk:
                    all_vals.append(trk[cq])
            if all_vals:
                vmin = min(v.min() for v in all_vals)
                vmax = max(v.max() for v in all_vals)

        for i in range(n):
            trk = self.tf.get_track(i)
            if xq not in trk or yq not in trk:
                continue
            xv = smooth_1d(trk[xq], smooth_method, smooth_window)
            yv = smooth_1d(trk[yq], smooth_method, smooth_window)

            if color_mode == "By quantity along track" and cq in trk and vmin is not None:
                points = np.array([xv, yv]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                lc = LineCollection(segments, cmap=cmap_name, linewidths=1.2)
                lc.set_array(trk[cq])
                lc.set_clim(vmin, vmax)
                ax.add_collection(lc)
                mappable = lc
            elif color_mode == "By track index":
                ax.plot(xv, yv, lw=0.9, alpha=0.85, color=index_colors[i])
            else:
                ax.plot(xv, yv, lw=0.9, alpha=0.85, color=self.accent_hex())

        if color_mode == "By quantity along track" and mappable is not None:
            cbar = self.canvas.figure.colorbar(mappable, ax=ax)
            label = self.tf.label(cq)
            unit = self.tf.unit(cq)
            cbar.set_label(f"{label} [{unit}]" if unit else label)

        ax.autoscale_view()

        xlabel = f"{self.tf.label(xq)} [{self.tf.unit(xq)}]" if self.tf.unit(xq) else self.tf.label(xq)
        ylabel = f"{self.tf.label(yq)} [{self.tf.unit(yq)}]" if self.tf.unit(yq) else self.tf.label(yq)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{n} of {self.tf.ntracks} tracks")

        self.canvas.draw()
```

---

## `scientific_visualization/gui/workers.py`

```py
"""Generic background-execution helper for the Qt GUI layer.

Nothing in this module contains scientific logic: it only moves an
already-existing callable off the GUI thread so the application stays
responsive while it runs. This is intentionally tiny and dependency-free
(pure PyQt5) so it can be reused by any tab (ML training, movie export,
future long-running analysis) without introducing new coupling between
the GUI and the science/ML layers -- the worker is handed a plain
Python callable and only ever talks back to Qt through signals.

Threading note (important, and the reason for `_ResultBridge` below):
Qt's "auto" connection type decides whether a signal is delivered
directly (synchronously, in the emitting thread) or queued (asynchronously,
posted to the receiving object's own thread) by comparing the *receiver
object's* thread affinity against the emitting thread at emit time. That
only works when the receiver is an actual QObject living on a known
thread. Connecting a worker thread's signal straight to a plain Python
function/lambda (as an earlier version of this module did) gives Qt no
receiver object to check, so PyQt falls back to a direct connection --
meaning the "on the GUI thread" callback silently executes on the
*worker* thread instead. That, in turn, made cleanup's `thread.wait()`
call wait on its own thread (a no-op Qt just warns about and returns from
immediately), so the QThread could still be finishing up in the
background after Python believed it was done and dropped its last
reference -- a real "QThread destroyed while still running" crash, not
just a cosmetic issue.

The fix is `_ResultBridge`: a tiny QObject created on (and left on) the
GUI thread. Connecting the worker's signals to *its* bound methods gives
Qt a receiver whose thread affinity is unambiguous, so the connection is
correctly auto-queued back to the GUI thread, and cleanup only ever runs
there.
"""
from __future__ import annotations

from typing import Any, Callable

from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog, QWidget


class _CallableWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(Exception)

    def __init__(self, fn: Callable[[], Any]):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller, not swallowed
            self.failed.emit(exc)
        else:
            self.finished.emit(result)


class _ResultBridge(QObject):
    """Lives on the GUI thread for its entire life (never moved). Receiving
    the worker's finished/failed signals here -- instead of on a plain
    Python callable -- is what makes Qt correctly auto-queue the delivery
    back to the GUI thread. See the module docstring for why that matters.
    """

    def __init__(self, thread: QThread, worker: _CallableWorker, progress: QProgressDialog,
                 on_success: Callable[[Any], None], on_error: Callable[[Exception], None]):
        super().__init__()
        self._thread = thread
        self._worker = worker
        self._progress = progress
        self._on_success = on_success
        self._on_error = on_error
        self._cancelled = False

    def _cleanup(self):
        # Runs on the GUI thread (see class docstring), so this genuinely
        # waits for the *worker* thread to finish -- not a no-op self-wait.
        self._thread.quit()
        self._thread.wait()
        self._thread.deleteLater()
        self._worker.deleteLater()

    def on_finished(self, result: Any):
        # QProgressDialog.close() emits its own `canceled` signal internally,
        # even when closed programmatically (not by the user). Block signals
        # first so that self-inflicted close doesn't get misread as the user
        # pressing Cancel and suppress the real result below.
        self._progress.blockSignals(True)
        self._progress.close()
        self._cleanup()
        if not self._cancelled:
            self._on_success(result)

    def on_failed(self, exc: Exception):
        self._progress.blockSignals(True)
        self._progress.close()
        self._cleanup()
        if not self._cancelled:
            self._on_error(exc)

    def on_cancel(self):
        self._cancelled = True
        self._progress.close()


def run_in_background(
    parent: QWidget,
    fn: Callable[[], Any],
    *,
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None],
    label: str = "Working…",
):
    """Run ``fn`` on a worker thread while showing a busy dialog.

    ``fn`` must not touch any Qt widgets -- it should only call into the
    deterministic, Qt-independent science/ML/export APIs. ``on_success``
    and ``on_error`` run back on the GUI thread and are the only places
    that should update widgets, so existing tab code can keep its current
    widget-updating logic unchanged and simply call this wrapper instead
    of calling ``fn`` directly.

    The dialog's Cancel button does not interrupt ``fn`` (safely
    cancelling arbitrary NumPy/scikit-learn/OpenCV work mid-call is not
    generally possible) -- it only stops the GUI from waiting on/for the
    result, so the user is not stuck staring at a frozen window.
    """
    thread = QThread(parent)
    worker = _CallableWorker(fn)
    worker.moveToThread(thread)

    progress = QProgressDialog(label, "Cancel", 0, 0, parent)
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(True)
    progress.setAutoReset(True)

    bridge = _ResultBridge(thread, worker, progress, on_success, on_error)
    bridge.setParent(parent)
    # Belt-and-suspenders: also anchor a strong reference via the thread
    # object itself, so the bridge can't be garbage-collected early even
    # in a context where `parent` doesn't keep Qt-parented children alive
    # as expected (e.g. some test harnesses).
    thread._bridge = bridge  # type: ignore[attr-defined]

    thread.started.connect(worker.run)
    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    progress.canceled.connect(bridge.on_cancel)

    thread.start()
    progress.show()
```

---

## `scientific_visualization/inspect.py`

```py
from __future__ import annotations

import argparse
from .io.simulation import SimulationReader
from .io.hdf5.generic import discover_hdf5_datasets


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect an HDF5 scientific dataset")
    parser.add_argument("path")
    args = parser.parse_args(argv)
    for item in discover_hdf5_datasets(args.path):
        print(f"{item.name}\tshape={item.shape}\tunits={item.units}")
    try:
        ds = SimulationReader().load(args.path)
        print(ds.summary())
    except Exception as exc:
        print(f"Simulation interpretation: {exc}")


if __name__ == "__main__":
    main()
```

---

## `scientific_visualization/io/__init__.py`

```py
from .hdf5 import DataReader, DatasetDescriptor, HDF5ReaderRegistry, discover_hdf5_datasets, validate_file
from .simulation import SimulationReader

__all__ = ["DataReader", "DatasetDescriptor", "HDF5ReaderRegistry", "SimulationReader", "discover_hdf5_datasets", "validate_file"]
```

---

## `scientific_visualization/io/grid.py`

```py
"""
Reader for Simulation grid/field HDF5 files (e1, e2, b3, charge density, etc.)

Simulation grid files follow this layout (mirrors z_data_grid / hdf5_gridfileinfo.pro
from the original Scientific Visualization IDL package):

    /                       (root group)
        attrs: NAME, TYPE, TIME, ITER, UNITS, LABEL
        <quantity dataset(s)>   e.g. "e1", or several time-tagged datasets
            attrs: UNITS, LONG_NAME (a.k.a LABEL), TAG
    /AXIS/
        AXIS1, AXIS2, [AXIS3]   each a 2-element [min, max] dataset
            attrs: NAME, UNITS, LONG_NAME

Older files sometimes store UNITS/LABEL on the dataset instead of the root
group; both are checked, dataset-level attributes win.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np

from ..core.data import CoordinateAxis, Dataset


def _attr(obj, name, default=""):
    """Read an HDF5 attribute and normalize scalar/one-element arrays.

    Simulation files in the wild use both true scalar attributes and one-element
    NumPy arrays for metadata such as TIME and ITER. Returning a Python scalar
    for size-one arrays prevents ``float(array([...] ))`` / ``int(array([...] ))``
    conversion failures while preserving genuinely multi-valued attributes.
    """
    if name not in obj.attrs:
        return default
    val = obj.attrs[name]
    if isinstance(val, bytes):
        return val.decode("utf-8", "replace").strip()
    if isinstance(val, np.ndarray):
        if val.ndim == 0:
            val = val.item()
        elif val.size == 1:
            val = val.reshape(-1)[0]
            if isinstance(val, bytes):
                return val.decode("utf-8", "replace").strip()
            if isinstance(val, np.generic):
                return val.item()
            return val
        elif val.dtype.kind in ("S", "O", "U"):
            return [v.decode("utf-8", "replace").strip() if isinstance(v, bytes) else str(v) for v in val.reshape(-1)]
        else:
            return val
    if isinstance(val, np.generic):
        return val.item()
    if isinstance(val, str):
        return val.strip()
    return val


def _scalar_attr(obj, name, default, cast):
    """Read a scalar numeric attribute, accepting true or one-element scalars."""
    value = _attr(obj, name, default)
    if isinstance(value, np.ndarray):
        if value.size != 1:
            raise ValueError(
                f"HDF5 attribute '{name}' in '{getattr(obj, 'name', '/')}' must be scalar; "
                f"received array with shape {value.shape}"
            )
        value = value.reshape(-1)[0]
    if value is None or value == "":
        value = default
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid scalar HDF5 attribute '{name}': {value!r}") from exc


@dataclass
class AxisInfo:
    name: str
    label: str
    units: str
    min: float
    max: float
    n: int

    def values(self) -> np.ndarray:
        """Cell-centered coordinate values along this axis."""
        return self.min + (np.arange(self.n) + 0.5) * (self.max - self.min) / self.n


@dataclass
class GridFile:
    """Loaded representation of a single Simulation grid/field HDF5 file."""

    filename: str
    name: str = ""
    label: str = ""
    units: str = ""
    time: float = 0.0
    time_units: str = ""
    iteration: int = 0
    ndim: int = 0
    shape: tuple = field(default_factory=tuple)
    axes: list = field(default_factory=list)   # list[AxisInfo], axes[0] is fastest-varying (x1)
    data: Optional[np.ndarray] = None
    dataset_name: str = ""

    @classmethod
    def info(cls, filename: str) -> "GridFile":
        """Read metadata only (no field data) -- fast, for file browsing."""
        return cls._load(filename, read_data=False)

    @classmethod
    def load(cls, filename: str) -> "GridFile":
        """Read metadata and the field data array."""
        return cls._load(filename, read_data=True)

    @classmethod
    def _load(cls, filename: str, read_data: bool) -> "GridFile":
        gf = cls(filename=filename)
        with h5py.File(filename, "r") as f:
            root = f["/"]

            dataset_names = [k for k in root.keys() if isinstance(root[k], h5py.Dataset)]
            if not dataset_names:
                raise ValueError(f"'{filename}' has no datasets")

            # In Simulation files there is usually exactly one field dataset whose
            # name matches the physical quantity (e.g. "e1", "charge").
            ds_name = dataset_names[0]
            dset = root[ds_name]
            gf.dataset_name = ds_name

            gf.name = _attr(root, "NAME", ds_name) or ds_name
            gf.label = _attr(dset, "LONG_NAME", _attr(root, "LABEL", gf.name))
            gf.units = _attr(dset, "UNITS", _attr(root, "UNITS", ""))
            gf.time = _scalar_attr(root, "TIME", 0.0, float)
            gf.time_units = _attr(root, "TIME UNITS", "") or _attr(root, "TIME_UNITS", "")
            gf.iteration = _scalar_attr(root, "ITER", 0, int)
            gf.shape = tuple(dset.shape)
            gf.ndim = len(gf.shape)

            if "AXIS" in root and isinstance(root["AXIS"], h5py.Group):
                axgroup = root["AXIS"]
                axis_keys = sorted(axgroup.keys())  # AXIS1, AXIS2, AXIS3
                axes = []
                # numpy/HDF5 stores fastest-varying axis last in `shape`,
                # AXIS1 corresponds to the last shape index.
                for i, key in enumerate(axis_keys):
                    axds = axgroup[key]
                    rng = np.asarray(axds[()], dtype=float).flatten()
                    aname = _attr(axds, "NAME", key)
                    if isinstance(aname, str) and aname.endswith(" axis"):
                        aname = aname[: -len(" axis")]
                    n = gf.shape[gf.ndim - 1 - i] if gf.ndim >= i + 1 else 0
                    axes.append(
                        AxisInfo(
                            name=aname or key,
                            label=_attr(axds, "LONG_NAME", aname or key),
                            units=_attr(axds, "UNITS", ""),
                            min=float(rng[0]),
                            max=float(rng[1]) if len(rng) > 1 else float(rng[0]),
                            n=int(n),
                        )
                    )
                gf.axes = axes
            else:
                # No axis info -- fall back to plain index axes
                gf.axes = [
                    AxisInfo(name=f"x{i+1}", label=f"x{i+1}", units="", min=0.0, max=float(n), n=n)
                    for i, n in enumerate(reversed(gf.shape))
                ]

            if read_data:
                gf.data = np.asarray(dset[()])

        return gf

    # -- convenience -----------------------------------------------------
    def lineout(self, axis: int = 0, index: Optional[int] = None) -> tuple:
        """
        Extract a 1D lineout along `axis` (0 = x1, 1 = x2, ...), holding the
        other coordinate(s) fixed at `index` (defaults to the middle of the
        array). Returns (coord_values, data_values).
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load(), not .info()")

        data = self.data
        ndim = data.ndim
        # numpy axis order is reversed relative to Simulation x1,x2,... ordering
        np_axis = ndim - 1 - axis

        if index is None:
            index = tuple(s // 2 for s in data.shape)

        if ndim == 1:
            values = data
        else:
            slicer = list(index) if isinstance(index, (list, tuple)) else [index] * ndim
            slicer[np_axis] = slice(None)
            values = data[tuple(slicer)]

        coord = self.axes[axis].values()
        return coord, values

    def lineout_at(self, along_axis: int, fixed_value: float, fixed_axis: Optional[int] = None):
        """
        1D lineout along `along_axis`, holding the other axis at the
        *physical* coordinate `fixed_value` (linearly interpolated between
        the two nearest grid points -- no need to know array indices).
        For 2D data `fixed_axis` is inferred automatically.
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load(), not .info()")

        ndim = self.data.ndim
        if fixed_axis is None:
            remaining = [a for a in range(ndim) if a != along_axis]
            if len(remaining) != 1:
                raise ValueError("fixed_axis must be given explicitly when ndim > 2")
            fixed_axis = remaining[0]

        axis_info = self.axes[fixed_axis]
        coords = axis_info.values()
        frac_idx = float(np.interp(fixed_value, coords, np.arange(axis_info.n)))
        frac_idx = min(max(frac_idx, 0.0), axis_info.n - 1)
        i0 = int(np.floor(frac_idx))
        i1 = min(i0 + 1, axis_info.n - 1)
        w = frac_idx - i0

        np_axis = ndim - 1 - fixed_axis
        slicer0 = [slice(None)] * ndim
        slicer0[np_axis] = i0
        slicer1 = [slice(None)] * ndim
        slicer1[np_axis] = i1
        v0 = self.data[tuple(slicer0)]
        v1 = self.data[tuple(slicer1)]
        values = v0 * (1 - w) + v1 * w

        along_coords = self.axes[along_axis].values()
        return along_coords, values

    def to_dataset(self) -> Dataset:
        """Convert the legacy reader representation to the shared Dataset model.

        Simulation stores x1 in the last NumPy/HDF5 dimension, so the returned
        Dataset is transposed into physical axis order (x1, x2, ...).
        No additional copy is requested by NumPy where a view is possible.
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load() first")
        data = self.data
        axes = tuple(self.axes)
        if self.ndim > 1:
            data = np.transpose(data, axes=tuple(reversed(range(self.ndim))))
        coordinates = tuple(
            CoordinateAxis(name=ax.name, values=ax.values(), units=ax.units, label=ax.label)
            for ax in axes
        )
        return Dataset(
            name=self.name or self.dataset_name,
            data=data,
            axes=tuple(ax.name for ax in axes),
            coordinates=coordinates,
            units=self.units,
            time=self.time,
            time_units=self.time_units,
            metadata={"dataset_name": self.dataset_name, "label": self.label, "iteration": self.iteration},
            source=self.filename,
            simulation_metadata={"format": "Simulation", "iteration": self.iteration},
        )

    def extent(self) -> list:
        """Return [xmin, xmax, ymin, ymax] suitable for matplotlib imshow."""
        if len(self.axes) >= 2:
            return [self.axes[0].min, self.axes[0].max, self.axes[1].min, self.axes[1].max]
        elif len(self.axes) == 1:
            return [self.axes[0].min, self.axes[0].max, 0, 1]
        return [0, 1, 0, 1]

    def slice2d(self, axis: int, index: int) -> "GridFile":
        """Extract a 2D slice from a 3D grid, holding `axis` (0=x1, 1=x2,
        2=x3) fixed at grid index `index`. Returns a new GridFile carrying
        only the remaining two axes, so every existing 2D code path
        (plotting, lineouts, colorbar, derived quantities, ...) can consume
        it exactly like a genuinely 2D dataset -- no special-casing needed
        downstream. Does not modify `self` or its underlying array (the
        slice is a NumPy view, not a copy).

        This is what lets 3D Simulation files (e.g. a "thin" 3D run with
        only a couple of points along one axis) be opened and viewed in
        the 2D tab instead of failing outright.
        """
        if self.data is None:
            raise ValueError("data not loaded; call GridFile.load(), not .info()")
        if self.ndim != 3:
            raise ValueError(f"slice2d requires a 3D dataset; this dataset is {self.ndim}D")
        if axis not in (0, 1, 2):
            raise ValueError("axis must be 0, 1, or 2 (corresponding to x1, x2, x3)")
        fixed_axis = self.axes[axis]
        if not (0 <= index < fixed_axis.n):
            raise ValueError(
                f"slice index {index} is out of range for axis {fixed_axis.name} "
                f"which has {fixed_axis.n} point(s) (valid range 0..{fixed_axis.n - 1})"
            )
        # numpy axis order is reversed relative to Simulation x1,x2,... ordering
        np_axis = self.ndim - 1 - axis
        slicer = [slice(None)] * self.ndim
        slicer[np_axis] = index
        data2d = self.data[tuple(slicer)]
        remaining_axes = [a for i, a in enumerate(self.axes) if i != axis]
        fixed_value = float(fixed_axis.values()[index])

        return GridFile(
            filename=self.filename,
            name=self.name,
            label=f"{self.label} (slice: {fixed_axis.name}={fixed_value:.6g} {fixed_axis.units})".strip(),
            units=self.units,
            time=self.time,
            time_units=self.time_units,
            iteration=self.iteration,
            ndim=2,
            shape=tuple(data2d.shape),
            axes=remaining_axes,
            data=data2d,
            dataset_name=self.dataset_name,
        )


def is_grid_file(filename: str) -> bool:
    """Best-effort check for whether an HDF5 file looks like an Simulation grid file."""
    try:
        with h5py.File(filename, "r") as f:
            has_dataset = any(isinstance(f[k], h5py.Dataset) for k in f.keys())
            return has_dataset and "AXIS" in f
    except Exception:
        return False
```

---

## `scientific_visualization/io/hdf5/__init__.py`

```py
from .base import DataReader, DatasetDescriptor, HDF5ReaderRegistry
from .generic import discover_hdf5_datasets, validate_file

__all__ = ["DataReader", "DatasetDescriptor", "HDF5ReaderRegistry", "discover_hdf5_datasets", "validate_file"]
```

---

## `scientific_visualization/io/hdf5/base.py`

```py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DatasetDescriptor:
    name: str
    shape: tuple[int, ...]
    units: str = ""
    kind: str = "scalar"


class DataReader(ABC):
    @abstractmethod
    def can_read(self, path: str | Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def discover(self, path: str | Path) -> list[DatasetDescriptor]:
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str | Path, quantity: str | None = None):
        raise NotImplementedError


class HDF5ReaderRegistry:
    """Format-neutral entry point. Concrete readers are selected by file inspection."""

    def __init__(self, readers: Iterable[DataReader] = ()):
        self.readers = list(readers)

    def register(self, reader: DataReader):
        self.readers.append(reader)

    def reader_for(self, path: str | Path) -> DataReader:
        for reader in self.readers:
            if reader.can_read(path):
                return reader
        raise ValueError(f"No supported HDF5 reader recognized '{path}'")

    def load(self, path: str | Path, quantity: str | None = None):
        return self.reader_for(path).load(path, quantity=quantity)
```

---

## `scientific_visualization/io/hdf5/generic.py`

```py
from __future__ import annotations

from pathlib import Path

import h5py

from .base import DatasetDescriptor


def discover_hdf5_datasets(path: str | Path) -> list[DatasetDescriptor]:
    """Discover datasets without reading their array payloads."""
    path = str(path)
    try:
        with h5py.File(path, "r") as f:
            out: list[DatasetDescriptor] = []
            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    units = obj.attrs.get("UNITS", "")
                    if isinstance(units, bytes):
                        units = units.decode("utf-8", "replace")
                    out.append(DatasetDescriptor(name=name, shape=tuple(obj.shape), units=str(units), kind="scalar"))
            f.visititems(visitor)
            return out
    except OSError as exc:
        raise ValueError(f"Invalid or truncated HDF5 file '{path}': {exc}") from exc


def validate_file(path: str | Path) -> None:
    try:
        with h5py.File(path, "r"):
            pass
    except OSError as exc:
        raise ValueError(f"Invalid or truncated HDF5 file '{path}': {exc}") from exc
```

---

## `scientific_visualization/io/lazy.py`

```py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class LazyFrame:
    path: str
    index: int
    time: float | None = None
    iteration: int | None = None
    name: str = ""
    shape: tuple[int, ...] = ()


class LazyGridSeries:
    """Metadata-lazy sequence for scientific grid frames.

    Construction performs no HDF5 opens. Metadata for a frame is read only
    when that frame is selected, loaded, or when a consumer explicitly asks
    for the complete time/iteration arrays.
    """

    def __init__(self, paths, info_loader: Callable | None = None, cache_size: int = 2):
        from .grid import GridFile
        self.paths = [str(Path(p)) for p in paths]
        self._info_loader = info_loader or GridFile.info
        self._loader = GridFile.load
        self._cache_size = max(0, int(cache_size))
        self._cache = {}
        self.frames = [LazyFrame(path=p, index=i) for i, p in enumerate(self.paths)]

    def _ensure_metadata(self, index: int) -> LazyFrame:
        frame = self.frames[index]
        if frame.time is None or not frame.shape:
            info = self._info_loader(frame.path)
            frame.time = float(info.time)
            frame.iteration = int(info.iteration)
            frame.name = info.name
            frame.shape = tuple(info.shape)
        return frame

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, index):
        if index < 0:
            index += len(self.frames)
        return self._ensure_metadata(index)

    def load(self, index: int, use_cache: bool = True):
        if not self.frames:
            raise IndexError("No simulation frames are available.")
        index = int(index)
        if index < 0:
            index += len(self.frames)
        if not 0 <= index < len(self.frames):
            raise IndexError(index)
        frame = self._ensure_metadata(index)
        if use_cache and index in self._cache:
            return self._cache[index]
        grid = self._loader(frame.path)
        if use_cache and self._cache_size:
            self._cache[index] = grid
            while len(self._cache) > self._cache_size:
                self._cache.pop(next(iter(self._cache)))
        return grid

    def metadata(self, index: int) -> LazyFrame:
        return self._ensure_metadata(int(index))

    def discover_metadata(self) -> list[LazyFrame]:
        for i in range(len(self.frames)):
            self._ensure_metadata(i)
        return self.frames

    def clear_cache(self):
        self._cache.clear()

    @property
    def times(self):
        import numpy as np
        self.discover_metadata()
        return np.asarray([f.time for f in self.frames], dtype=float)

    @property
    def iterations(self):
        import numpy as np
        self.discover_metadata()
        return np.asarray([f.iteration for f in self.frames], dtype=int)
```

---

## `scientific_visualization/io/particles.py`

```py
"""
Reader for Simulation particle-diagnostic HDF5 files.

Layout (mirrors hdf5_partfileinfo.pro / hdf5_partfiledata.pro):

    /                      (root group)
        attrs: NAME, TIME, ITER, QUANTS (list of quantity names, e.g.
               ['x1','x2','p1','p2','p3','q','ene',...]), LABELS, UNITS
        <quant> dataset for each entry in QUANTS, each a 1D array of length
        NPAR (one value per particle in this dump).

Older files don't have a QUANTS attribute; in that case every dataset in the
root group is itself a quantity, named after the dataset.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np

from .grid import _attr, _scalar_attr
from ..core.data import Dataset


@dataclass
class ParticleFile:
    filename: str
    name: str = ""
    time: float = 0.0
    iteration: int = 0
    npar: int = 0
    quants: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    _data: dict = field(default_factory=dict)

    @classmethod
    def info(cls, filename: str) -> "ParticleFile":
        pf = cls(filename=filename)
        with h5py.File(filename, "r") as f:
            root = f["/"]
            pf.name = _attr(root, "NAME", "")
            pf.time = _scalar_attr(root, "TIME", 0.0, float)
            pf.iteration = _scalar_attr(root, "ITER", 0, int)

            quants = _attr(root, "QUANTS", None)
            if not quants:
                quants = [k for k in root.keys() if isinstance(root[k], h5py.Dataset)]
            elif isinstance(quants, str):
                quants = [quants]
            else:
                quants = list(quants)

            labels = _attr(root, "LABELS", None)
            units = _attr(root, "UNITS", None)
            if isinstance(labels, str):
                labels = [labels]
            if isinstance(units, str):
                units = [units]

            pf.quants = quants
            for i, q in enumerate(quants):
                if q not in root:
                    continue
                pf.labels[q] = labels[i] if labels and i < len(labels) else q
                pf.units[q] = units[i] if units and i < len(units) else _attr(root[q], "UNITS", "")

            if quants and quants[0] in root:
                pf.npar = int(root[quants[0]].shape[-1]) if root[quants[0]].shape else 0
        return pf

    def get(self, quant: str) -> np.ndarray:
        """Load (and cache) one quantity array by name, e.g. 'x1', 'p1', 'ene'."""
        if quant in self._data:
            return self._data[quant]
        with h5py.File(self.filename, "r") as f:
            if quant not in f:
                raise KeyError(f"quantity '{quant}' not found in {self.filename}")
            arr = np.asarray(f[quant][()])
        self._data[quant] = arr
        return arr

    def label(self, quant: str) -> str:
        return self.labels.get(quant, quant)

    def unit(self, quant: str) -> str:
        return self.units.get(quant, "")

    def to_dataset(self, quant: str) -> Dataset:
        return Dataset(
            name=quant, data=self.get(quant), axes=("particle",), units=self.unit(quant),
            time=self.time, metadata={"label": self.label(quant), "iteration": self.iteration},
            source=self.filename, simulation_metadata={"format": "Simulation", "iteration": self.iteration},
        )


def is_particle_file(filename: str) -> bool:
    try:
        with h5py.File(filename, "r") as f:
            if "AXIS" in f:
                return False
            root = f["/"]
            quants = _attr(root, "QUANTS", None)
            if quants:
                return True
            # heuristic: several 1D datasets of equal length, no AXIS group
            datasets = [k for k in root.keys() if isinstance(root[k], h5py.Dataset)]
            if len(datasets) < 2:
                return False
            shapes = {root[k].shape for k in datasets}
            return len(shapes) == 1 and len(next(iter(shapes))) == 1
    except Exception:
        return False
```

---

## `scientific_visualization/io/simulation/__init__.py`

```py
from .grid import GridFile, AxisInfo, is_grid_file
from .particles import ParticleFile, is_particle_file
from .tracks import TracksFile, is_tracks_file
from .reader import SimulationReader

__all__ = ["GridFile", "AxisInfo", "ParticleFile", "TracksFile", "SimulationReader", "is_grid_file", "is_particle_file", "is_tracks_file"]
```

---

## `scientific_visualization/io/simulation/grid.py`

```py
from ..grid import *
```

---

## `scientific_visualization/io/simulation/particles.py`

```py
from ..particles import *
```

---

## `scientific_visualization/io/simulation/reader.py`

```py
from __future__ import annotations

from pathlib import Path

from ..hdf5.base import DataReader, DatasetDescriptor
from ..grid import GridFile, is_grid_file
from ..particles import ParticleFile, is_particle_file
from ..tracks import TracksFile, is_tracks_file


class SimulationReader(DataReader):
    """Simulation-aware HDF5 reader that converts native readers to shared models."""

    def can_read(self, path: str | Path) -> bool:
        path = str(path)
        return is_grid_file(path) or is_particle_file(path) or is_tracks_file(path)

    def discover(self, path: str | Path) -> list[DatasetDescriptor]:
        if is_grid_file(path):
            info = GridFile.info(str(path))
            return [DatasetDescriptor(info.dataset_name, info.shape, info.units)]
        if is_particle_file(path):
            info = ParticleFile.info(str(path))
            return [DatasetDescriptor(q, (info.npar,), info.unit(q)) for q in info.quants]
        if is_tracks_file(path):
            info = TracksFile.info(str(path))
            return [DatasetDescriptor(q, (sum(info._counts) if info._counts is not None else 0,), info.unit(q)) for q in info.quants]
        raise ValueError(f"Unsupported Simulation HDF5 structure: '{path}'")

    def load(self, path: str | Path, quantity: str | None = None):
        if is_grid_file(path):
            return GridFile.load(str(path)).to_dataset()
        if is_particle_file(path):
            pf = ParticleFile.info(str(path))
            q = quantity or (pf.quants[0] if pf.quants else None)
            if q is None:
                raise ValueError(f"No particle quantities found in '{path}'")
            return pf.to_dataset(q)
        if is_tracks_file(path):
            tf = TracksFile.info(str(path))
            q = quantity or (tf.quants[0] if tf.quants else None)
            if q is None:
                raise ValueError(f"No track quantities found in '{path}'")
            return tf.to_dataset(q)
        raise ValueError(f"Unsupported Simulation HDF5 structure: '{path}'")
```

---

## `scientific_visualization/io/simulation/tracks.py`

```py
from ..tracks import *
```

---

## `scientific_visualization/io/tracks.py`

```py
"""
Reader for Simulation particle-tracking HDF5 files ("*-tracks.h5").

Standard Simulation tracks file layout:

    /                     (root group)
        attrs: NAME, NTRACKS, NDUMP, DT, QUANTS (e.g. ['t','x1','x2','p1',
               'p2','p3','ene','q']), LABELS, UNITS
        data       -- float array, shape (total_points, n_quants); the
                      per-track records concatenated one after another
        itermap    -- integer array, shape (n_tracks, 2); column 0 is the
                      starting iteration of the track, column 1 is the
                      number of saved points (dumps) for that track

This mirrors the structure written by z_data_tracks::Save in the original
Scientific Visualization IDL package.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np

from .grid import _attr, _scalar_attr
from ..core.data import Dataset


@dataclass
class TracksFile:
    filename: str
    name: str = ""
    ntracks: int = 0
    ndump: int = 0
    dt: float = 0.0
    quants: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    _offsets: Optional[np.ndarray] = None   # (ntracks,) start row into `data`
    _counts: Optional[np.ndarray] = None    # (ntracks,) number of points
    _data: Optional[np.ndarray] = None      # cached full data array

    @classmethod
    def info(cls, filename: str) -> "TracksFile":
        tf = cls(filename=filename)
        with h5py.File(filename, "r") as f:
            root = f["/"]
            tf.name = _attr(root, "NAME", "")
            tf.ndump = _scalar_attr(root, "NDUMP", 0, int)
            tf.dt = _scalar_attr(root, "DT", 0.0, float)

            quants = _attr(root, "QUANTS", None)
            if isinstance(quants, str):
                quants = [quants]
            tf.quants = list(quants) if quants else []

            labels = _attr(root, "LABELS", None)
            units = _attr(root, "UNITS", None)
            if isinstance(labels, str):
                labels = [labels]
            if isinstance(units, str):
                units = [units]
            for i, q in enumerate(tf.quants):
                tf.labels[q] = labels[i] if labels and i < len(labels) else q
                tf.units[q] = units[i] if units and i < len(units) else ""

            if "itermap" in root:
                itermap = np.asarray(root["itermap"][()])
                tf._offsets = np.concatenate(([0], np.cumsum(itermap[:, 1])[:-1])).astype(int)
                tf._counts = itermap[:, 1].astype(int)
                tf.ntracks = _scalar_attr(root, "NTRACKS", itermap.shape[0], int)
            else:
                tf.ntracks = _scalar_attr(root, "NTRACKS", 0, int)

            if not tf.quants and "data" in root:
                ncol = root["data"].shape[1] if root["data"].ndim > 1 else 1
                tf.quants = [f"q{i}" for i in range(ncol)]
        return tf

    def _load_data(self) -> np.ndarray:
        if self._data is None:
            with h5py.File(self.filename, "r") as f:
                self._data = np.asarray(f["data"][()])
        return self._data

    def get_track(self, index: int) -> dict:
        """Return {quant_name: 1D array} for a single track (0-based index)."""
        data = self._load_data()
        if self._offsets is not None:
            start = self._offsets[index]
            count = self._counts[index]
            rows = data[start:start + count]
        else:
            # Fallback: assume equal-length tracks, data is (ntracks, npoints, nquants)
            rows = data[index]
        return {q: rows[:, i] for i, q in enumerate(self.quants)}

    def get_all(self, quant_x: str, quant_y: str, max_tracks: Optional[int] = None):
        """Return a list of (x_array, y_array) tuples, one per track."""
        n = self.ntracks if max_tracks is None else min(self.ntracks, max_tracks)
        ix = self.quants.index(quant_x)
        iy = self.quants.index(quant_y)
        out = []
        for i in range(n):
            trk = self.get_track(i)
            out.append((trk[quant_x] if quant_x in trk else None,
                        trk[quant_y] if quant_y in trk else None))
        return out

    def label(self, quant: str) -> str:
        return self.labels.get(quant, quant)

    def unit(self, quant: str) -> str:
        return self.units.get(quant, "")

    def to_dataset(self, quant: str) -> Dataset:
        if quant not in self.quants:
            raise KeyError(quant)
        col = self.quants.index(quant)
        data = self._load_data()[:, col]
        return Dataset(
            name=quant, data=data, axes=("point",), units=self.unit(quant),
            metadata={"label": self.label(quant), "ntracks": self.ntracks}, source=self.filename,
            simulation_metadata={"format": "Simulation tracks", "ntracks": self.ntracks},
        )


def is_tracks_file(filename: str) -> bool:
    try:
        with h5py.File(filename, "r") as f:
            root = f["/"]
            return "data" in root and ("itermap" in root or "NTRACKS" in root.attrs)
    except Exception:
        return False
```

---

## `scientific_visualization/ml/__init__.py`

```py
from .core import FeatureSet, MLResult, require_sklearn, estimator_available
from .features import feature_matrix_from_dataset, dataset_to_features, sample_grid_features
from .unsupervised import PCAAnalyzer, KMeansAnalyzer, IsolationForestAnalyzer, AnomalyAnalyzer
from .supervised import RegressionAnalyzer
from .advanced import NeuralNetworkRegressorAnalyzer, GradientBoostingRegressorAnalyzer, AutoencoderAnalyzer
from .surrogate import SurrogateModel
from .active_learning import ActiveLearningAdvisor
from .surrogate_lab import AdvancedSurrogate, SurrogateReport
__all__=["FeatureSet","MLResult","require_sklearn","estimator_available","feature_matrix_from_dataset","dataset_to_features","sample_grid_features","PCAAnalyzer","KMeansAnalyzer","IsolationForestAnalyzer","AnomalyAnalyzer","RegressionAnalyzer","NeuralNetworkRegressorAnalyzer","GradientBoostingRegressorAnalyzer","AutoencoderAnalyzer","SurrogateModel","ActiveLearningAdvisor","AdvancedSurrogate","SurrogateReport"]
```

---

## `scientific_visualization/ml/active_learning.py`

```py
from __future__ import annotations
import numpy as np
from .surrogate import SurrogateModel

class ActiveLearningAdvisor:
    """Select promising next simulation points from a trained surrogate using uncertainty/exploration."""
    def __init__(self, surrogate=None): self.surrogate=surrogate or SurrogateModel()
    def recommend(self, candidate_features, batch_size=5, ensemble_predictions=None):
        X=np.asarray(candidate_features,dtype=float)
        if ensemble_predictions is None:
            raise ValueError("Provide ensemble predictions for uncertainty-aware recommendations")
        preds=np.asarray(ensemble_predictions,dtype=float)
        if preds.ndim!=2 or preds.shape[1]!=len(X): raise ValueError("Ensemble predictions must be [models,candidates]")
        score=np.std(preds,axis=0)
        idx=np.argsort(score)[::-1][:int(batch_size)]
        return {"indices":idx.tolist(),"scores":score[idx].tolist(),"features":X[idx].tolist(),"criterion":"predictive_uncertainty"}
```

---

## `scientific_visualization/ml/advanced.py`

```py
from __future__ import annotations

import numpy as np

from .core import FeatureSet, MLResult, require_sklearn


class NeuralNetworkRegressorAnalyzer:
    """Scaled MLP regression with a training-history output."""

    def __init__(self, hidden_layers=(128, 64), max_iter=300, learning_rate_init=1e-3,
                 early_stopping=True, random_state=42):
        self.hidden_layers = tuple(int(v) for v in hidden_layers)
        self.max_iter = int(max_iter)
        self.learning_rate_init = float(learning_rate_init)
        self.early_stopping = bool(early_stopping)
        self.random_state = int(random_state)

    def fit_predict(self, features: FeatureSet, target, test_size=0.2, cv_folds=0) -> MLResult:
        require_sklearn()
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split, KFold, cross_val_score
        from sklearn.neural_network import MLPRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        y = np.asarray(target, dtype=float).reshape(-1)
        if y.size != features.values.shape[0]:
            raise ValueError("Regression target must contain one value per sample")
        X_train, X_test, y_train, y_test = train_test_split(
            features.values, y, test_size=test_size, random_state=self.random_state
        )
        model = Pipeline([
            ("scale", StandardScaler()),
            ("mlp", MLPRegressor(
                hidden_layer_sizes=self.hidden_layers,
                max_iter=self.max_iter,
                learning_rate_init=self.learning_rate_init,
                early_stopping=self.early_stopping,
                random_state=self.random_state,
                solver="adam",
            )),
        ])
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = {
            "r2": float(r2_score(y_test, pred)),
            "mae": float(mean_absolute_error(y_test, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        }
        cv = None
        if int(cv_folds) >= 2:
            folds = min(int(cv_folds), max(2, len(y) // 5))
            scores = cross_val_score(model, features.values, y,
                                     cv=KFold(n_splits=folds, shuffle=True, random_state=self.random_state),
                                     scoring="r2", n_jobs=1)
            cv = {"folds": int(folds), "scores": scores.tolist(),
                  "mean_r2": float(np.mean(scores)), "std_r2": float(np.std(scores))}
        mlp = model.named_steps["mlp"]
        metadata = {
            "metrics": metrics,
            "y_test": y_test,
            "predicted": pred,
            "loss_curve": getattr(mlp, "loss_curve_", []),
            "cv": cv,
            "hidden_layers": self.hidden_layers,
        }
        return MLResult("Neural Network Regression", pred, model, features, metadata)


class GradientBoostingRegressorAnalyzer:
    """Gradient boosting regression with feature importance and optional CV."""

    def __init__(self, n_estimators=250, learning_rate=0.05, max_depth=3, random_state=42):
        self.n_estimators = int(n_estimators)
        self.learning_rate = float(learning_rate)
        self.max_depth = int(max_depth)
        self.random_state = int(random_state)

    def fit_predict(self, features: FeatureSet, target, test_size=0.2, cv_folds=0) -> MLResult:
        require_sklearn()
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split, KFold, cross_val_score

        y = np.asarray(target, dtype=float).reshape(-1)
        if y.size != features.values.shape[0]:
            raise ValueError("Regression target must contain one value per sample")
        X_train, X_test, y_train, y_test = train_test_split(
            features.values, y, test_size=test_size, random_state=self.random_state
        )
        model = GradientBoostingRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_state=self.random_state,
        )
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = {
            "r2": float(r2_score(y_test, pred)),
            "mae": float(mean_absolute_error(y_test, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        }
        cv = None
        if int(cv_folds) >= 2:
            folds = min(int(cv_folds), max(2, len(y) // 5))
            scores = cross_val_score(model, features.values, y,
                                     cv=KFold(n_splits=folds, shuffle=True, random_state=self.random_state),
                                     scoring="r2", n_jobs=1)
            cv = {"folds": int(folds), "scores": scores.tolist(),
                  "mean_r2": float(np.mean(scores)), "std_r2": float(np.std(scores))}
        return MLResult(
            "Gradient Boosting Regression", pred, model, features,
            {"metrics": metrics, "y_test": y_test, "predicted": pred,
             "feature_importances": model.feature_importances_.tolist(), "cv": cv}
        )


class AutoencoderAnalyzer:
    """Neural-network autoencoder for nonlinear field compression/anomaly scoring."""

    def __init__(self, bottleneck=8, max_iter=250, random_state=42):
        self.bottleneck = max(2, int(bottleneck))
        self.max_iter = int(max_iter)
        self.random_state = int(random_state)

    def fit_transform(self, features: FeatureSet) -> MLResult:
        require_sklearn()
        from sklearn.neural_network import MLPRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        X = np.asarray(features.values, dtype=float)
        hidden = (max(self.bottleneck * 4, 16), self.bottleneck, max(self.bottleneck * 4, 16))
        model = Pipeline([
            ("scale", StandardScaler()),
            ("autoencoder", MLPRegressor(
                hidden_layer_sizes=hidden,
                max_iter=self.max_iter,
                random_state=self.random_state,
                early_stopping=True,
            )),
        ])
        model.fit(X, X)
        reconstructed = model.predict(X)
        errors = np.mean((X - reconstructed) ** 2, axis=1)
        ae = model.named_steps["autoencoder"]
        return MLResult(
            "Neural Autoencoder", reconstructed, model, features,
            {"reconstruction_error": errors,
             "loss_curve": getattr(ae, "loss_curve_", []),
             "bottleneck": self.bottleneck, "hidden_layers": hidden}
        )
```

---

## `scientific_visualization/ml/core.py`

```py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import sklearn  # noqa: F401
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


@dataclass
class FeatureSet:
    """Numerical feature matrix plus provenance information."""
    values: np.ndarray
    feature_names: tuple[str, ...]
    sample_coordinates: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.values = np.asarray(self.values, dtype=float)
        if self.values.ndim != 2:
            raise ValueError("Feature matrix must be two-dimensional")
        if len(self.feature_names) != self.values.shape[1]:
            raise ValueError("feature_names must match the number of columns")
        if self.sample_coordinates is not None:
            coords = np.asarray(self.sample_coordinates, dtype=float)
            if coords.ndim != 2 or coords.shape[0] != self.values.shape[0]:
                raise ValueError("sample_coordinates must have one row per sample")
            self.sample_coordinates = coords


@dataclass
class MLResult:
    """Standard result container for ML operations."""
    method: str
    output: Any
    model: Any = None
    feature_set: FeatureSet | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def estimator_available() -> bool:
    return _SKLEARN_AVAILABLE


def require_sklearn() -> None:
    if not _SKLEARN_AVAILABLE:
        raise ImportError(
            "Machine-learning features require scikit-learn. "
            "Install it with `pip install scikit-learn`."
        )
```

---

## `scientific_visualization/ml/features.py`

```py
from __future__ import annotations

import numpy as np

from ..core.data import Dataset
from .core import FeatureSet


def dataset_to_features(dataset: Dataset, *, flatten: bool = True, include_coordinates: bool = True) -> FeatureSet:
    if dataset.is_vector:
        raise ValueError("dataset_to_features currently expects a scalar Dataset")
    data = np.asarray(dataset.data)
    if data.ndim == 0:
        values = data.reshape(1, 1).astype(float)
        coords = None
    else:
        values = data.reshape(-1, 1).astype(float) if flatten else data.astype(float)
        coords = None
        if include_coordinates and dataset.coordinates:
            meshes = np.meshgrid(*[c.values for c in dataset.coordinates], indexing="ij")
            coords = np.column_stack([m.reshape(-1) for m in meshes])
    names = [dataset.name]
    if include_coordinates:
        names.extend(c.name for c in dataset.coordinates)
        if coords is not None:
            values = np.column_stack([values, coords])
    return FeatureSet(values, tuple(names), coords, {"source": dataset.source, "dataset": dataset.name, "sample_indices": np.arange(values.shape[0], dtype=int)})


def sample_grid_features(dataset: Dataset, max_samples: int = 10000, seed: int = 0) -> FeatureSet:
    """Draw a bounded random subsample of grid points as ML features.

    For grids larger than ``max_samples`` this selects the sample indices
    *first* and only computes values/coordinates at those indices, instead
    of materializing a full coordinate meshgrid and flattened value array
    for every point in the grid and then discarding almost all of it. This
    matters in practice: for a 200^3 PIC field (8,000,000 points) sampling
    10,000 points previously built and discarded 7,990,000 rows of a
    (N, 1+ndim) array plus a full meshgrid, which dominates runtime and
    memory for large 3D simulations.
    """
    if dataset.is_vector:
        raise ValueError("sample_grid_features currently expects a scalar Dataset")
    data = np.asarray(dataset.data)
    n = data.size if data.ndim else 1
    if n <= max_samples:
        return dataset_to_features(dataset)

    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(n, size=max_samples, replace=False))

    flat_values = data.reshape(-1)[idx].astype(float).reshape(-1, 1)
    names = [dataset.name]
    coords = None
    values = flat_values
    if dataset.coordinates:
        # `data` is stored in the same axis order as `dataset.coordinates`
        # (see GridFile.to_dataset), so unravel_index against data.shape
        # gives the per-axis index for each sampled flat index directly,
        # with no need to build the full per-point coordinate mesh.
        unravel = np.unravel_index(idx, data.shape)
        coord_cols = [np.asarray(c.values, dtype=float)[u] for c, u in zip(dataset.coordinates, unravel)]
        coords = np.column_stack(coord_cols)
        names.extend(c.name for c in dataset.coordinates)
        values = np.column_stack([flat_values, coords])

    return FeatureSet(
        values,
        tuple(names),
        coords,
        {
            "source": dataset.source,
            "dataset": dataset.name,
            "sample_count": max_samples,
            "sample_indices": idx,
        },
    )

# Backward-compatible public name used by earlier GUI/test integrations.
def feature_matrix_from_dataset(dataset: Dataset, *, flatten: bool = True, include_coordinates: bool = True) -> FeatureSet:
    return dataset_to_features(dataset, flatten=flatten, include_coordinates=include_coordinates)
```

---

## `scientific_visualization/ml/jax_models.py`

```py
"""Optional JAX-accelerated neural-network models.

Why here, specifically, and not just for the physics operators: scikit-learn's
`MLPRegressor` trains with a fairly Python-loop-heavy optimizer and cannot use
a GPU at all. Gradient-descent training of a small MLP -- many repeated
forward+backward passes over the *same* computational graph -- is exactly the
workload JAX's JIT compilation (and, on a GPU-equipped machine, `jax.devices()`
automatically including a GPU) is built for. This is a much better fit for
JAX than the physics differential operators in `native_backend`/`jax_backend`,
where the existing C++/OpenMP backend already wins on CPU (see that module's
docstring and `tests/test_jax_physics_backend.py` for the honest numbers).

This module deliberately does not depend on Flax/Optax/etc. to keep the
optional dependency footprint to just `jax`+`jaxlib`: the network and the
Adam optimizer are both the standard textbook formulas, implemented directly
with `jax.grad`/`jax.jit`.

Everything here is optional: if JAX isn't installed, `JAX_AVAILABLE` is
False and callers should fall back to `ml.advanced`'s sklearn-based
classes, which remain the default. Nothing else in the application
requires this module to be usable.
"""
from __future__ import annotations

from functools import partial

import numpy as np

try:
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    JAX_AVAILABLE = True
except ImportError:
    jax = None
    jnp = None
    JAX_AVAILABLE = False

from .core import FeatureSet, MLResult


def require_jax() -> None:
    if not JAX_AVAILABLE:
        raise ImportError(
            "JAX-accelerated models require the 'jax' package. "
            "Install it with `pip install jax` (or `jax[cuda12]` etc. for GPU support)."
        )


def _init_params(key, layer_sizes):
    params = []
    for n_in, n_out in zip(layer_sizes[:-1], layer_sizes[1:]):
        key, wkey, bkey = jax.random.split(key, 3)
        scale = jnp.sqrt(2.0 / n_in)  # He initialization, matches ReLU below
        w = jax.random.normal(wkey, (n_in, n_out)) * scale
        b = jnp.zeros((n_out,))
        params.append((w, b))
    return params


def _forward(params, x):
    for w, b in params[:-1]:
        x = jax.nn.relu(x @ w + b)
    w, b = params[-1]
    return x @ w + b  # linear output layer, standard for regression


def _mse_loss(params, x, y):
    pred = _forward(params, x)
    return jnp.mean((pred - y.reshape(pred.shape)) ** 2)


@partial(jax.jit, static_argnames=("learning_rate",)) if JAX_AVAILABLE else (lambda f: f)
def _adam_step(params, m, v, t, x, y, learning_rate):
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    loss, grads = jax.value_and_grad(_mse_loss)(params, x, y)
    new_params, new_m, new_v = [], [], []
    for (w, b), (gw, gb), (mw, mb), (vw, vb) in zip(params, grads, m, v):
        mw = beta1 * mw + (1 - beta1) * gw; mb = beta1 * mb + (1 - beta1) * gb
        vw = beta2 * vw + (1 - beta2) * gw ** 2; vb = beta2 * vb + (1 - beta2) * gb ** 2
        mw_hat = mw / (1 - beta1 ** t); mb_hat = mb / (1 - beta1 ** t)
        vw_hat = vw / (1 - beta2 ** t); vb_hat = vb / (1 - beta2 ** t)
        w = w - learning_rate * mw_hat / (jnp.sqrt(vw_hat) + eps)
        b = b - learning_rate * mb_hat / (jnp.sqrt(vb_hat) + eps)
        new_params.append((w, b)); new_m.append((mw, mb)); new_v.append((vw, vb))
    return new_params, new_m, new_v, loss


def _train(X, y, hidden_layers, max_iter, learning_rate, random_state, X_val=None, y_val=None,
           early_stopping=True, patience=15, chunk_size=20):
    """Train with `jax.lax.scan` over chunks of steps, not a plain Python
    loop. A naive Python `for` loop calling a jitted single-step function
    forces a host<->device round-trip on every iteration (to read the loss
    back for the loss curve / early-stopping check), which dominates
    runtime for a small MLP and erases JAX's advantage entirely -- an
    earlier version of this module did exactly that and was measured to
    be *both* slower and less accurate than sklearn's MLPRegressor for
    this reason. Scanning `chunk_size` steps at a time inside a single
    compiled call cuts the number of host round-trips by that same
    factor, while still checking validation loss between chunks for
    (approximate) early stopping."""
    require_jax()
    n_features = X.shape[1]
    n_out = 1 if y.ndim == 1 else y.shape[1]
    layer_sizes = [n_features, *hidden_layers, n_out]
    key = jax.random.PRNGKey(int(random_state))
    params = _init_params(key, layer_sizes)
    m = [(jnp.zeros_like(w), jnp.zeros_like(b)) for w, b in params]
    v = [(jnp.zeros_like(w), jnp.zeros_like(b)) for w, b in params]

    Xj = jnp.asarray(X, dtype=jnp.float64)
    yj = jnp.asarray(y, dtype=jnp.float64)
    Xv = jnp.asarray(X_val, dtype=jnp.float64) if X_val is not None else None
    yv = jnp.asarray(y_val, dtype=jnp.float64) if y_val is not None else None

    def scan_body(carry, t):
        params, m, v = carry
        params, m, v, loss = _adam_step(params, m, v, t, Xj, yj, learning_rate)
        return (params, m, v), loss

    loss_curve = []
    best_val = np.inf
    best_params = params
    stall = 0
    step = 0
    while step < max_iter:
        n_steps = min(chunk_size, max_iter - step)
        ts = jnp.arange(step + 1, step + n_steps + 1, dtype=jnp.float64)
        (params, m, v), losses = jax.lax.scan(scan_body, (params, m, v), ts)
        loss_curve.extend(np.asarray(losses).tolist())
        step += n_steps
        if early_stopping and Xv is not None:
            val_loss = float(_mse_loss(params, Xv, yv))
            if val_loss < best_val - 1e-9:
                best_val = val_loss; best_params = params; stall = 0
            else:
                stall += n_steps
                if stall >= patience:
                    break
    return (best_params if early_stopping and X_val is not None else params), loss_curve


class JaxMLPRegressor:
    """JAX/Adam-trained MLP regressor. Same external contract (`fit_predict`
    returning an `MLResult` with the same metadata keys) as
    `ml.advanced.NeuralNetworkRegressorAnalyzer`, so the GUI/ML tab can
    offer this as a drop-in alternative backend."""

    def __init__(self, hidden_layers=(128, 64), max_iter=300, learning_rate_init=1e-3,
                 early_stopping=True, random_state=42):
        require_jax()
        self.hidden_layers = tuple(int(v) for v in hidden_layers)
        self.max_iter = int(max_iter)
        self.learning_rate_init = float(learning_rate_init)
        self.early_stopping = bool(early_stopping)
        self.random_state = int(random_state)

    def fit_predict(self, features: FeatureSet, target, test_size=0.2, cv_folds=0) -> MLResult:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split, KFold

        y = np.asarray(target, dtype=float).reshape(-1)
        if y.size != features.values.shape[0]:
            raise ValueError("Regression target must contain one value per sample")

        X_train, X_test, y_train, y_test = train_test_split(
            features.values, y, test_size=test_size, random_state=self.random_state
        )
        mu, sigma = X_train.mean(axis=0), X_train.std(axis=0) + 1e-12
        X_train_s = (X_train - mu) / sigma
        X_test_s = (X_test - mu) / sigma

        # Hold out a validation slice from the training data for early stopping,
        # matching sklearn MLPRegressor's own early_stopping behavior.
        if self.early_stopping and len(X_train_s) >= 10:
            X_fit, X_val, y_fit, y_val = train_test_split(X_train_s, y_train, test_size=0.1, random_state=self.random_state)
        else:
            X_fit, y_fit, X_val, y_val = X_train_s, y_train, None, None

        params, loss_curve = _train(
            X_fit, y_fit, self.hidden_layers, self.max_iter, self.learning_rate_init,
            self.random_state, X_val, y_val, early_stopping=self.early_stopping,
        )
        pred = np.asarray(_forward(params, jnp.asarray(X_test_s))).reshape(-1)
        metrics = {
            "r2": float(r2_score(y_test, pred)),
            "mae": float(mean_absolute_error(y_test, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        }

        cv = None
        if int(cv_folds) >= 2:
            folds = min(int(cv_folds), max(2, len(y) // 5))
            scores = []
            for train_idx, test_idx in KFold(n_splits=folds, shuffle=True, random_state=self.random_state).split(features.values):
                Xtr, Xte = features.values[train_idx], features.values[test_idx]
                ytr, yte = y[train_idx], y[test_idx]
                mu_k, sigma_k = Xtr.mean(axis=0), Xtr.std(axis=0) + 1e-12
                p_k, _ = _train((Xtr - mu_k) / sigma_k, ytr, self.hidden_layers, self.max_iter,
                                 self.learning_rate_init, self.random_state, early_stopping=False)
                pred_k = np.asarray(_forward(p_k, jnp.asarray((Xte - mu_k) / sigma_k))).reshape(-1)
                scores.append(r2_score(yte, pred_k))
            scores = np.asarray(scores)
            cv = {"folds": int(folds), "scores": scores.tolist(),
                  "mean_r2": float(np.mean(scores)), "std_r2": float(np.std(scores))}

        model = {"params": params, "mu": mu, "sigma": sigma, "predict": lambda X: np.asarray(
            _forward(params, jnp.asarray((np.asarray(X) - mu) / sigma))).reshape(-1)}
        metadata = {
            "metrics": metrics, "y_test": y_test, "predicted": pred,
            "loss_curve": loss_curve, "cv": cv, "hidden_layers": self.hidden_layers,
            "backend": "jax",
        }
        return MLResult("Neural Network Regression (JAX)", pred, model, features, metadata)


class JaxAutoencoder:
    """JAX/Adam-trained autoencoder, mirroring `ml.advanced.AutoencoderAnalyzer`."""

    def __init__(self, bottleneck=8, max_iter=250, random_state=42, learning_rate_init=1e-3):
        require_jax()
        self.bottleneck = max(2, int(bottleneck))
        self.max_iter = int(max_iter)
        self.random_state = int(random_state)
        self.learning_rate_init = float(learning_rate_init)

    def fit_transform(self, features: FeatureSet) -> MLResult:
        X = np.asarray(features.values, dtype=float)
        mu, sigma = X.mean(axis=0), X.std(axis=0) + 1e-12
        Xs = (X - mu) / sigma
        hidden = (max(self.bottleneck * 4, 16), self.bottleneck, max(self.bottleneck * 4, 16))

        n = len(Xs)
        if n >= 10:
            idx = np.random.RandomState(self.random_state).permutation(n)
            n_val = max(1, n // 10)
            val_idx, fit_idx = idx[:n_val], idx[n_val:]
            X_val = Xs[val_idx]
        else:
            fit_idx, X_val = np.arange(n), None

        params, loss_curve = _train(
            Xs[fit_idx], Xs[fit_idx], hidden, self.max_iter, self.learning_rate_init,
            self.random_state, X_val, X_val, early_stopping=X_val is not None,
        )
        reconstructed_s = np.asarray(_forward(params, jnp.asarray(Xs)))
        reconstructed = reconstructed_s * sigma + mu
        errors = np.mean((X - reconstructed) ** 2, axis=1)
        model = {"params": params, "mu": mu, "sigma": sigma}
        return MLResult(
            "Neural Autoencoder (JAX)", reconstructed, model, features,
            {"reconstruction_error": errors, "loss_curve": loss_curve,
             "bottleneck": self.bottleneck, "hidden_layers": hidden, "backend": "jax"}
        )
```

---

## `scientific_visualization/ml/supervised.py`

```py
from __future__ import annotations

import numpy as np

from .core import FeatureSet, MLResult, require_sklearn


class RegressionAnalyzer:
    """Train/test regression workflow for scientific datasets."""

    def __init__(self, estimator=None, test_size=0.2, random_state=42):
        self.estimator = estimator
        self.test_size = test_size
        self.random_state = random_state

    def fit_predict(self, features: FeatureSet, target) -> MLResult:
        require_sklearn()
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split

        y = np.asarray(target, dtype=float).reshape(-1)
        if y.shape[0] != features.values.shape[0]:
            raise ValueError("Regression target must contain one value per sample")
        X_train, X_test, y_train, y_test = train_test_split(features.values, y, test_size=self.test_size, random_state=self.random_state)
        model = self.estimator or RandomForestRegressor(n_estimators=150, random_state=self.random_state, n_jobs=-1)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = {"r2": float(r2_score(y_test, pred)), "mae": float(mean_absolute_error(y_test, pred)), "rmse": float(np.sqrt(mean_squared_error(y_test, pred)))}
        return MLResult("Random Forest Regression", pred, model, features, {"metrics": metrics, "y_test": y_test, "predicted": pred})
```

---

## `scientific_visualization/ml/surrogate.py`

```py
from __future__ import annotations
import numpy as np
from .core import FeatureSet, MLResult, require_sklearn

class SurrogateModel:
    """Reusable surrogate-model wrapper for simulation response surfaces."""
    def __init__(self, model=None, scale=True):
        self.model=model
        self.scale=scale

    def fit(self, features:FeatureSet, target):
        require_sklearn()
        from sklearn.ensemble import ExtraTreesRegressor
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        model=self.model or ExtraTreesRegressor(n_estimators=300,random_state=42,n_jobs=1)
        self.model = make_pipeline(StandardScaler(),model) if self.scale else model
        y=np.asarray(target,dtype=float).reshape(-1)
        if y.size != len(features.values): raise ValueError("Target length must match features")
        self.model.fit(features.values,y)
        return self

    def predict(self, features:FeatureSet):
        if self.model is None: raise RuntimeError("Surrogate model has not been trained")
        return self.model.predict(features.values)
```

---

## `scientific_visualization/ml/surrogate_lab.py`

```py
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np

from .core import FeatureSet, require_sklearn


@dataclass
class SurrogateReport:
    method: str
    metrics: dict
    feature_importance: dict
    uncertainty: dict
    acquisition: dict


class AdvancedSurrogate:
    """Fast, uncertainty-aware surrogate toolkit for simulation design loops.

    The class keeps training and acquisition independent from the GUI so that
    the same workflow can later be moved to the native C++ core.
    """
    def __init__(self, method="Extra Trees", random_state=42):
        self.method = method
        self.random_state = int(random_state)
        self.model = None
        self.models = []
        self.feature_names = ()

    def _make_model(self):
        require_sklearn()
        from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor, HistGradientBoostingRegressor, RandomForestClassifier
        if self.method == "Extra Trees":
            return ExtraTreesRegressor(n_estimators=256, random_state=self.random_state, n_jobs=-1, max_features=1.0, bootstrap=False)
        if self.method == "Random Forest":
            return RandomForestRegressor(n_estimators=192, random_state=self.random_state, n_jobs=-1, max_features=1.0)
        if self.method == "Histogram Gradient Boosting":
            return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, l2_regularization=1e-3, random_state=self.random_state)
        if self.method == "Gaussian Process":
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
            return GaussianProcessRegressor(kernel=ConstantKernel(1.0) * RBF(1.0) + WhiteKernel(1e-4), normalize_y=True, random_state=self.random_state)
        raise ValueError(f"Unknown surrogate method: {self.method}")

    def fit(self, features: FeatureSet, target):
        require_sklearn()
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
        X = np.asarray(features.values, dtype=float)
        y = np.asarray(target, dtype=float).reshape(-1)
        if X.ndim != 2 or len(X) != len(y):
            raise ValueError("Feature and target sizes do not match")
        self.feature_names = tuple(features.feature_names)
        self.models = []
        if self.method == "Gaussian Process":
            self.model = make_pipeline(StandardScaler(), self._make_model())
        else:
            self.model = self._make_model()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(Xtr, ytr)
        pred = self.model.predict(Xte)
        self._holdout = {"r2": float(r2_score(yte, pred)), "mae": float(mean_absolute_error(yte, pred)), "rmse": float(np.sqrt(mean_squared_error(yte, pred)))}
        # A small ensemble is used only for uncertainty, while preserving the
        # primary fast model for prediction.
        if self.method in {"Extra Trees", "Random Forest"}:
            self.models = [self.model]
            for k in range(3):
                m = self._make_model(); m.set_params(random_state=self.random_state + k + 1)
                m.fit(Xtr, ytr); self.models.append(m)
        return self

    def predict(self, X):
        if self.model is None: raise RuntimeError("Surrogate is not trained")
        return np.asarray(self.model.predict(np.asarray(X, dtype=float)))

    def predict_with_uncertainty(self, X):
        X = np.asarray(X, dtype=float)
        if self.model is None: raise RuntimeError("Surrogate is not trained")
        if self.models:
            p = np.vstack([m.predict(X) for m in self.models])
            return p.mean(axis=0), p.std(axis=0), p
        if self.method == "Gaussian Process":
            gp = self.model[-1]
            mean, std = gp.predict(self.model[0].transform(X), return_std=True) if False else self._gp_predict(X)
            return mean, std, np.vstack([mean - std, mean, mean + std])
        mean = self.predict(X)
        scale = max(self._holdout.get("rmse", 0.0), 1e-12)
        return mean, np.full_like(mean, scale), None

    def _gp_predict(self, X):
        # Pipeline exposes predict(return_std) only on the final estimator.
        sc = self.model.named_steps["standardscaler"]
        gp = self.model.named_steps["gaussianprocessregressor"]
        return gp.predict(sc.transform(X), return_std=True)

    def diagnostics(self, features: FeatureSet):
        require_sklearn()
        importance = {}
        if hasattr(self.model, "feature_importances_"):
            raw = np.asarray(self.model.feature_importances_, dtype=float)
        elif self.models and hasattr(self.models[0], "feature_importances_"):
            raw = np.asarray(self.models[0].feature_importances_, dtype=float)
        else:
            # permutation importance is intentionally optional and sampled
            # to keep the interactive UI responsive.
            from sklearn.inspection import permutation_importance
            n = min(len(features.values), 2500)
            r = permutation_importance(self.model, features.values[:n], np.asarray(self._cached_y)[:n], n_repeats=3, random_state=1, n_jobs=-1)
            raw = r.importances_mean
        order = np.argsort(raw)[::-1]
        for i in order:
            importance[str(self.feature_names[i])] = float(raw[i])
        return importance

    def recommend(self, candidates, batch_size=8, criterion="Upper confidence bound", beta=2.0, observed_y=None):
        X = np.asarray(candidates, dtype=float)
        mean, std, ensemble = self.predict_with_uncertainty(X)
        if criterion == "Maximum uncertainty":
            score = std
        elif criterion == "Expected improvement":
            require_sklearn()
            from scipy.stats import norm
            best = float(np.max(observed_y)) if observed_y is not None and len(observed_y) else float(np.max(mean))
            s = np.maximum(std, 1e-12); z = (mean - best) / s
            score = (mean - best) * norm.cdf(z) + s * norm.pdf(z)
        else:
            score = mean + float(beta) * std
        idx = np.argsort(score)[::-1][:int(batch_size)]
        return {"indices": idx.tolist(), "scores": score[idx].tolist(), "mean": mean[idx].tolist(), "std": std[idx].tolist(), "features": X[idx].tolist(), "criterion": criterion}

    def set_target_cache(self, y):
        self._cached_y = np.asarray(y, dtype=float)

    def report(self, features, y, candidates=None, criterion="Upper confidence bound"):
        self.set_target_cache(y)
        importance = self.diagnostics(features)
        acquisition = self.recommend(candidates if candidates is not None else features.values, criterion=criterion) if self.model is not None else {}
        pred, std, _ = self.predict_with_uncertainty(features.values)
        residual = np.asarray(y) - pred
        return SurrogateReport(self.method, dict(self._holdout), importance, {"mean_std": float(np.mean(std)), "max_std": float(np.max(std)), "rmse_all": float(np.sqrt(np.mean(residual**2)))}, acquisition)

    def export_report(self, report: SurrogateReport, path):
        payload = {"method": report.method, "metrics": report.metrics, "feature_importance": report.feature_importance, "uncertainty": report.uncertainty, "acquisition": report.acquisition, "feature_names": list(self.feature_names)}
        Path(path).write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
```

---

## `scientific_visualization/ml/unsupervised.py`

```py
from __future__ import annotations

from .core import FeatureSet, MLResult, require_sklearn


class PCAAnalyzer:
    def __init__(self, n_components=2):
        self.n_components = n_components

    def fit_transform(self, features: FeatureSet) -> MLResult:
        require_sklearn()
        from sklearn.decomposition import PCA
        model = PCA(n_components=self.n_components)
        output = model.fit_transform(features.values)
        return MLResult("PCA", output, model, features, {"explained_variance_ratio": model.explained_variance_ratio_.tolist()})


class KMeansAnalyzer:
    def __init__(self, n_clusters=3, random_state=0, n_init="auto"):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.n_init = n_init

    def fit_predict(self, features: FeatureSet) -> MLResult:
        require_sklearn()
        from sklearn.cluster import KMeans
        model = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=self.n_init)
        labels = model.fit_predict(features.values)
        return MLResult("KMeans", labels, model, features, {"centers": model.cluster_centers_.tolist()})


class IsolationForestAnalyzer:
    def __init__(self, contamination="auto", random_state=0):
        self.contamination = contamination
        self.random_state = random_state

    def fit_predict(self, features: FeatureSet) -> MLResult:
        require_sklearn()
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(contamination=self.contamination, random_state=self.random_state)
        labels = model.fit_predict(features.values)
        return MLResult("IsolationForest", labels, model, features)

# Backward-compatible alias used by the GUI and prior releases.
AnomalyAnalyzer = IsolationForestAnalyzer
```

---

## `scientific_visualization/physics/__init__.py`

```py
from .engine import PhysicsEngine, PhysicsAnalysis
from . import native_backend
from . import particle_field
__all__ = ["PhysicsEngine", "PhysicsAnalysis", "native_backend", "particle_field"]
```

---

## `scientific_visualization/physics/engine.py`

```py
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Mapping
from ..core.data import Dataset
from . import native_backend as _native

@dataclass(frozen=True)
class PhysicsAnalysis:
    name: str
    result: Dataset

class PhysicsEngine:
    """Coordinate-aware vector calculus and common field operations.

    Differential operators (gradient/divergence/curl/laplacian) use the
    OpenMP-parallelized native backend automatically whenever every
    coordinate axis involved is confirmed uniformly spaced (see
    `CoordinateAxis.is_uniform`); otherwise they fall back to the
    np.gradient-based implementation below, which correctly handles
    non-uniform spacing. Both paths produce numerically equivalent
    results -- see tests/test_native_physics_backend.py -- so this
    switch never changes a scientific result, only how fast it runs.
    Call `PhysicsEngine().backend_status()` to see which path is active.
    """

    @staticmethod
    def backend_status() -> str:
        return _native.backend_name()

    def _check_compatible(self, fields: Mapping[str, Dataset]):
        vals = list(fields.values())
        if not vals:
            raise ValueError("At least one field is required")
        base = vals[0]
        for ds in vals[1:]:
            if ds.shape != base.shape or ds.axes != base.axes:
                raise ValueError("Fields must have compatible shape and axes")
        return base

    def magnitude(self, components: Mapping[str, Dataset], name="|A|") -> Dataset:
        base = self._check_compatible(components)
        data = np.sqrt(sum(np.asarray(ds.data, dtype=float) ** 2 for ds in components.values()))
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {**dict(base.metadata), "physics_operation":"magnitude", "components":tuple(components)},
                       base.source, base.simulation_metadata, derived_from=tuple(components))

    def dot(self, a: Mapping[str, Dataset], b: Mapping[str, Dataset], name="A·B") -> Dataset:
        names = set(a) & set(b)
        if not names: raise ValueError("Dot product requires matching component names")
        base = self._check_compatible({k:a[k] for k in names})
        self._check_compatible({k:b[k] for k in names})
        data = sum(np.asarray(a[k].data) * np.asarray(b[k].data) for k in names)
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {"physics_operation":"dot", "components":tuple(sorted(names))}, base.source, base.simulation_metadata,
                       derived_from=tuple(sorted(names)))

    def cross(self, a: Mapping[str, Dataset], b: Mapping[str, Dataset], names=("x1","x2","x3")):
        if any(k not in a or k not in b for k in names): raise ValueError("Cross product requires x1, x2, x3 components")
        base = self._check_compatible({k:a[k] for k in names})
        self._check_compatible({k:b[k] for k in names})
        out = np.cross(np.stack([a[k].data for k in names], axis=-1), np.stack([b[k].data for k in names], axis=-1), axis=-1)
        return {
            k: Dataset(f"(A×B)_{k}", out[...,i], base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {"physics_operation":"cross", "component":k}, base.source, base.simulation_metadata)
            for i,k in enumerate(names)
        }

    def gradient(self, dataset: Dataset, axis: str|int):
        ai = dataset.axis_index(axis)
        coord = dataset.coordinates[ai]
        if len(coord.values) < 2: raise ValueError("At least two coordinate points are required")
        if coord.is_uniform:
            data = _native.gradient_uniform(np.asarray(dataset.data, dtype=float), coord.spacing, ai,
                                             edge_order=2 if coord.size > 2 else 1)
        else:
            order = 2 if len(coord.values) > 2 else 1
            data = np.gradient(dataset.data, coord.values, axis=ai, edge_order=order)
        return Dataset(f"∂{dataset.name}/∂{dataset.axes[ai]}", data, dataset.axes, dataset.coordinates, dataset.units,
                       dataset.time, dataset.time_units, {"physics_operation":"gradient", "axis":dataset.axes[ai]},
                       dataset.source, dataset.simulation_metadata, derived_from=(dataset.name,))

    @staticmethod
    def _edge_order(coord) -> int:
        return 2 if coord.size > 2 else 1

    def divergence(self, vector: Mapping[str, Dataset], name="div(A)") -> Dataset:
        base = self._check_compatible(vector)
        comps, coords = [], []
        for i, axis in enumerate(base.axes):
            comp_key = axis.lower()
            ds = vector.get(comp_key) or vector.get(f"x{i+1}")
            if ds is None: raise ValueError(f"Missing vector component for axis {axis}")
            comps.append(ds)
            coords.append(base.coordinates[i])
        if all(c.is_uniform for c in coords):
            edge_orders = [self._edge_order(c) for c in coords]
            if len(set(edge_orders)) == 1:
                # Common case (all axes have >2 or all have exactly 2 points):
                # one fused, single-pass native call across every axis.
                data = _native.divergence_uniform(
                    [np.asarray(ds.data, dtype=float) for ds in comps],
                    [c.spacing for c in coords], edge_order=edge_orders[0],
                )
            else:
                # Rare: axes disagree on edge order (e.g. one axis has only 2
                # points). Still native-accelerated per axis, just summed in
                # Python instead of fused in C++, to keep each axis's exact
                # edge handling.
                data = sum(
                    _native.gradient_uniform(np.asarray(ds.data, dtype=float), c.spacing, i, edge_order=eo)
                    for i, (ds, c, eo) in enumerate(zip(comps, coords, edge_orders))
                )
        else:
            terms = []
            for i, (ds, coord) in enumerate(zip(comps, coords)):
                order = 2 if len(coord.values) > 2 else 1
                terms.append(np.gradient(ds.data, coord.values, axis=i, edge_order=order))
            data = sum(terms)
        return Dataset(name, data, base.axes, base.coordinates, base.units, base.time, base.time_units,
                       {"physics_operation":"divergence"}, base.source, base.simulation_metadata)


    def curl(self, vector: Mapping[str, Dataset], name="curl(A)"):
        base = self._check_compatible(vector)
        if base.ndim != 3:
            raise ValueError("Curl requires a 3D vector field")
        comps = {}
        for k in ("x1", "x2", "x3"):
            if k in vector: comps[k] = vector[k]
        if len(comps) != 3:
            raise ValueError("Curl requires x1, x2, x3 components")
        c1, c2, c3 = comps["x1"], comps["x2"], comps["x3"]
        coords = base.coordinates
        if all(coord.is_uniform for coord in coords):
            edge_orders = [self._edge_order(c) for c in coords]
            d1, d2, d3 = (np.asarray(c.data, dtype=float) for c in (c1, c2, c3))
            if len(set(edge_orders)) == 1:
                out1, out2, out3 = _native.curl_uniform_3d(
                    d1, d2, d3, coords[0].spacing, coords[1].spacing, coords[2].spacing,
                    edge_order=edge_orders[0],
                )
            else:
                g = lambda arr, axis: _native.gradient_uniform(arr, coords[axis].spacing, axis, edge_order=edge_orders[axis])
                out1 = g(d3, 1) - g(d2, 2)
                out2 = g(d1, 2) - g(d3, 0)
                out3 = g(d2, 0) - g(d1, 1)
            out = np.stack([out1, out2, out3], axis=-1)
        else:
            d = lambda ds, axis: np.gradient(ds.data, base.coordinates[base.axis_index(axis)].values, axis=base.axis_index(axis), edge_order=2 if ds.shape[base.axis_index(axis)] > 2 else 1)
            out = np.stack([d(c3, "x2") - d(c2, "x3"), d(c1, "x3") - d(c3, "x1"), d(c2, "x1") - d(c1, "x2")], axis=-1)
        return {k: Dataset(f"({name})_{k}", out[..., i], base.axes, base.coordinates, base.units, base.time, base.time_units, {"physics_operation":"curl","component":k}, base.source, base.simulation_metadata) for i,k in enumerate(("x1","x2","x3"))}

    def electric_magnitude(self, fields: Mapping[str, Dataset]):
        return self.magnitude(fields, name="|E|")

    def magnetic_magnitude(self, fields: Mapping[str, Dataset]):
        return self.magnitude(fields, name="|B|")

    def laplacian(self, dataset: Dataset, name=None) -> Dataset:
        if dataset.coordinates and all(c.is_uniform for c in dataset.coordinates):
            edge_orders = [self._edge_order(c) for c in dataset.coordinates]
            data_arr = np.asarray(dataset.data, dtype=float)
            if len(set(edge_orders)) == 1:
                result = _native.laplacian_uniform(data_arr, [c.spacing for c in dataset.coordinates], edge_order=edge_orders[0])
            else:
                result = np.zeros_like(data_arr)
                for axis, (coord, eo) in enumerate(zip(dataset.coordinates, edge_orders)):
                    first = _native.gradient_uniform(data_arr, coord.spacing, axis, edge_order=eo)
                    result += _native.gradient_uniform(first, coord.spacing, axis, edge_order=eo)
        else:
            result = np.zeros_like(np.asarray(dataset.data,dtype=float))
            for axis in dataset.axes:
                first=self.gradient(dataset, axis)
                result += np.gradient(first.data, dataset.coordinates[dataset.axis_index(axis)].values, axis=dataset.axis_index(axis), edge_order=2 if dataset.shape[dataset.axis_index(axis)]>2 else 1)
        return Dataset(name or f"∇²({dataset.name})", result, dataset.axes, dataset.coordinates, dataset.units,
                       dataset.time, dataset.time_units, {"physics_operation":"laplacian"}, dataset.source, dataset.simulation_metadata)
```

---

## `scientific_visualization/physics/jax_backend.py`

```py
"""Optional JAX-accelerated backend for uniform-grid physics operators.

This mirrors `native_backend.py`'s pure-NumPy formulas exactly (same edge
handling, same double-differentiation definition of the Laplacian) so
switching to this backend never changes a scientific result -- only how
it's computed. See `tests/test_jax_physics_backend.py` for the numerical
equivalence checks.

Why JAX, alongside the existing C++/OpenMP native backend:
  * No compiler required -- `pip install jax` vs. a C++ toolchain + OpenMP.
    This matters on platforms where a compiler isn't readily available.
  * Transparent GPU/TPU support: the exact same Python code in this file
    runs on whatever `jax.devices()` reports (CPU here; a CUDA or TPU
    device automatically if one is present and jaxlib was built for it),
    with no code changes.
  * JIT compilation (`jax.jit`) is a good fit for this application's
    typical workload: the same operator applied to many arrays of the
    *same shape* in a row (every frame of a movie export, every timestep
    of a time-series analysis). The first call to a given (shape, axis,
    edge_order) combination pays a one-time tracing/compilation cost;
    every subsequent call with the same combination reuses the compiled
    executable. A single one-off call on an unusual shape can therefore be
    *slower* than plain NumPy -- this backend is opt-in for that reason
    (see `native_backend.set_backend`), not silently substituted by
    default.

Correctness note: JAX defaults to float32 even for float64 NumPy input,
silently discarding precision, unless 64-bit mode is enabled -- which
this module does at import time. Without this, results computed on this
backend would quietly be less precise than the NumPy/C++ backends,
exactly the kind of silent scientific-result degradation this project's
design rules forbid.
"""
from __future__ import annotations

from functools import lru_cache, partial
from typing import Sequence

try:
    import jax
    jax.config.update("jax_enable_x64", True)  # see module docstring
    import jax.numpy as jnp
    JAX_AVAILABLE = True
except ImportError:
    jax = None
    jnp = None
    JAX_AVAILABLE = False

import numpy as np


def require_jax() -> None:
    if not JAX_AVAILABLE:
        raise ImportError(
            "The JAX physics backend requires the 'jax' package. "
            "Install it with `pip install jax` (add `jax[cuda12]` etc. "
            "instead for GPU support, per JAX's own install instructions)."
        )


def device_name() -> str:
    if not JAX_AVAILABLE:
        return "unavailable"
    try:
        return str(jax.devices()[0])
    except Exception:
        return "unknown"


def backend_summary() -> str:
    if not JAX_AVAILABLE:
        return "JAX not installed"
    return f"JAX {jax.__version__} on {jax.default_backend()} ({device_name()})"


# ---------------------------------------------------------------------
# JIT-compiled kernels. `axis`/`edge_order` are static: JAX specializes
# (recompiles) per distinct value, which is exactly what we want since the
# formulas branch structurally on them.
# ---------------------------------------------------------------------

@partial(jax.jit, static_argnames=("axis", "edge_order")) if JAX_AVAILABLE else (lambda f: f)
def _gradient_uniform_jax(data, h, axis: int, edge_order: int):
    n = data.shape[axis]
    take = lambda i: jnp.take(data, jnp.asarray(i), axis=axis)

    if n == 2:
        d = (take([1]) - take([0])) / h
        return jnp.concatenate([d, d], axis=axis)

    interior = (take(np.arange(2, n)) - take(np.arange(0, n - 2))) / (2.0 * h)

    if edge_order >= 2:
        left = (-3.0 * take([0]) + 4.0 * take([1]) - take([2])) / (2.0 * h)
        right = (3.0 * take([n - 1]) - 4.0 * take([n - 2]) + take([n - 3])) / (2.0 * h)
    else:
        left = (take([1]) - take([0])) / h
        right = (take([n - 1]) - take([n - 2])) / h

    return jnp.concatenate([left, interior, right], axis=axis)


def gradient_uniform(data, h: float, axis: int, edge_order: int = 2):
    require_jax()
    result = _gradient_uniform_jax(jnp.asarray(data, dtype=jnp.float64), float(h), int(axis), int(edge_order))
    return np.asarray(result)


def divergence_uniform(components: Sequence, spacings: Sequence[float], edge_order: int = 2):
    require_jax()
    comps = [jnp.asarray(c, dtype=jnp.float64) for c in components]
    total = jnp.zeros_like(comps[0])
    for axis, (comp, h) in enumerate(zip(comps, spacings)):
        total = total + _gradient_uniform_jax(comp, float(h), axis, int(edge_order))
    return np.asarray(total)


def laplacian_uniform(data, spacings: Sequence[float], edge_order: int = 2):
    require_jax()
    arr = jnp.asarray(data, dtype=jnp.float64)
    total = jnp.zeros_like(arr)
    for axis, h in enumerate(spacings):
        first = _gradient_uniform_jax(arr, float(h), axis, int(edge_order))
        total = total + _gradient_uniform_jax(first, float(h), axis, int(edge_order))
    return np.asarray(total)


def curl_uniform_3d(c1, c2, c3, h1: float, h2: float, h3: float, edge_order: int = 2):
    require_jax()
    d1 = jnp.asarray(c1, dtype=jnp.float64)
    d2 = jnp.asarray(c2, dtype=jnp.float64)
    d3 = jnp.asarray(c3, dtype=jnp.float64)
    eo = int(edge_order)
    out1 = _gradient_uniform_jax(d3, float(h2), 1, eo) - _gradient_uniform_jax(d2, float(h3), 2, eo)
    out2 = _gradient_uniform_jax(d1, float(h3), 2, eo) - _gradient_uniform_jax(d3, float(h1), 0, eo)
    out3 = _gradient_uniform_jax(d2, float(h1), 0, eo) - _gradient_uniform_jax(d1, float(h2), 1, eo)
    return np.asarray(out1), np.asarray(out2), np.asarray(out3)


@jax.jit if JAX_AVAILABLE else (lambda f: f)
def _sample_field_trilinear_jax(field, origin, spacing, points):
    g = (points - origin) / spacing
    n0, n1, n2 = field.shape
    g0 = jnp.clip(g[:, 0], 0.0, n0 - 1)
    g1 = jnp.clip(g[:, 1], 0.0, n1 - 1)
    g2 = jnp.clip(g[:, 2], 0.0, n2 - 1)

    i0 = jnp.floor(g0).astype(jnp.int32); i1 = jnp.minimum(i0 + 1, n0 - 1)
    j0 = jnp.floor(g1).astype(jnp.int32); j1 = jnp.minimum(j0 + 1, n1 - 1)
    k0 = jnp.floor(g2).astype(jnp.int32); k1 = jnp.minimum(k0 + 1, n2 - 1)
    tx = g0 - i0; ty = g1 - j0; tz = g2 - k0

    c00 = field[i0, j0, k0] * (1 - tx) + field[i1, j0, k0] * tx
    c01 = field[i0, j0, k1] * (1 - tx) + field[i1, j0, k1] * tx
    c10 = field[i0, j1, k0] * (1 - tx) + field[i1, j1, k0] * tx
    c11 = field[i0, j1, k1] * (1 - tx) + field[i1, j1, k1] * tx
    c0 = c00 * (1 - ty) + c10 * ty
    c1 = c01 * (1 - ty) + c11 * ty
    return c0 * (1 - tz) + c1 * tz


def sample_field_trilinear(field, origin, spacing, points):
    require_jax()
    result = _sample_field_trilinear_jax(
        jnp.asarray(field, dtype=jnp.float64),
        jnp.asarray(origin, dtype=jnp.float64),
        jnp.asarray(spacing, dtype=jnp.float64),
        jnp.asarray(points, dtype=jnp.float64),
    )
    return np.asarray(result)
```

---

## `scientific_visualization/physics/native_backend.py`

```py
"""Optional accelerated backends for uniform-grid physics operators.

This module is the single place that knows which of three interchangeable
backends is active for the physics differential operators used by
`physics/engine.py` and `physics/particle_field.py`:

  * **numpy** -- always available, the reference implementation every
    other backend is verified against (see the test suite).
  * **native** -- the compiled C++/OpenMP extension in
    `native/src/native_physics.cpp` (built by `native/build.sh`).
  * **jax** -- `physics/jax_backend.py`, JIT-compiled with JAX. Needs
    only `pip install jax` (no compiler), and transparently uses a GPU/TPU
    if `jax.devices()` reports one and jaxlib was built for it.

All three produce numerically equivalent results (see
`tests/test_native_physics_backend.py` and `tests/test_jax_physics_backend.py`)
so switching backends never changes a scientific result, only how fast it
runs. Per the project's design rules, none of the accelerated backends are
required: the pure-NumPy path always works.

**Which one is actually fastest depends on your hardware and problem
size -- there is no universally-correct default.** Measured on a
single-core, GPU-less CI sandbox with representative grid sizes, the
native C++/OpenMP backend was consistently fastest, including after JAX's
JIT warm-up cost was excluded, because the C++ code hand-fuses multiple
passes into single-pass loops in a way this project's JAX kernels
currently do not, and because JAX's per-call dispatch overhead is
comparatively higher for these kernel sizes. JAX's own documented
advantages -- automatic GPU/TPU execution, and being the natural
foundation for autodiff-based features (e.g. physics-informed loss
functions, gradient-based uncertainty quantification) -- are real but
were not things this sandbox could measure (no GPU present here). If you
have a CUDA-capable GPU, benchmark `set_backend("jax")` against the
default yourself; it is very plausible it wins there even though it did
not in this environment.

The default is "auto", which behaves exactly as before this module
supported multiple backends: native C++ if compiled, else pure NumPy.
JAX is never selected automatically -- call `set_backend("jax")` to opt in.
"""
from __future__ import annotations

import importlib.util

import numpy as np

try:
    from . import _native as _ext  # compiled extension, built by native/build.sh
    NATIVE_AVAILABLE = True
except ImportError:
    _ext = None
    NATIVE_AVAILABLE = False

# JAX is *never* imported here at module load time, even though it's a
# valid backend choice. Importing `jax` triggers jaxlib/XLA runtime
# initialization (hardware backend discovery, plugin scanning, etc.),
# which is genuinely slow -- multiple seconds, observed directly in this
# project. Since `physics.engine` (and therefore this module) is imported
# by essentially every GUI tab at application startup, an eager `import
# jax_backend` here meant *every user paid that multi-second cost on every
# launch*, regardless of whether they ever selected the JAX backend (which
# is opt-in-only by design -- see set_backend() below). `JAX_AVAILABLE` is
# answered with `importlib.util.find_spec`, which only checks whether the
# package *could* be imported (fast, no execution); the actual `import
# jax_backend` (and therefore `import jax`) happens lazily, only inside
# `_jax_module()`, the first time a caller actually requests the JAX
# backend via `set_backend("jax")`.
_jax = None
JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _jax_module():
    """Import and cache `jax_backend` on first actual use of the JAX
    backend. Not called at module import time -- see note above."""
    global _jax
    if _jax is None:
        from . import jax_backend as _jax_mod
        _jax = _jax_mod
    return _jax

_VALID_BACKENDS = ("auto", "numpy", "native", "jax")
_backend = "auto"


def set_backend(name: str) -> None:
    """Choose which backend the functions below dispatch to.

    - "auto" (default): native C++ if compiled, else pure NumPy. Never
      selects JAX automatically (see module docstring for why).
    - "numpy": always use the pure-NumPy reference implementation,
      regardless of what's installed/compiled. Useful for comparison/
      debugging, or on hardware where the accelerated paths are slower.
    - "native": require the compiled C++/OpenMP extension; raises if it
      isn't built.
    - "jax": require JAX; raises if it isn't installed.
    """
    if name not in _VALID_BACKENDS:
        raise ValueError(f"Unknown physics backend {name!r}; expected one of {_VALID_BACKENDS}")
    if name == "native" and not NATIVE_AVAILABLE:
        raise RuntimeError("The native C++ backend isn't built. Run native/build.sh, or choose a different backend.")
    if name == "jax" and not JAX_AVAILABLE:
        raise RuntimeError("JAX isn't installed. `pip install jax`, or choose a different backend.")
    global _backend
    _backend = name


def get_backend() -> str:
    """The backend name last passed to `set_backend` (default: "auto")."""
    return _backend


def _active_backend() -> str:
    """Which backend a call will actually use right now, resolving "auto"."""
    if _backend == "auto":
        return "native" if NATIVE_AVAILABLE else "numpy"
    return _backend


def openmp_enabled() -> bool:
    """Whether the compiled extension was itself built with OpenMP support."""
    return bool(NATIVE_AVAILABLE and _ext.openmp_enabled())


def max_threads() -> int:
    """OpenMP's reported max thread count (1 if native/OpenMP unavailable)."""
    if NATIVE_AVAILABLE:
        return int(_ext.omp_max_threads())
    return 1


def backend_name() -> str:
    active = _active_backend()
    if active == "jax":
        return f"JAX ({_jax_module().backend_summary()})"
    if active == "native":
        if openmp_enabled():
            return f"Native C++ (OpenMP, up to {max_threads()} threads)"
        return "Native C++ (single-threaded, OpenMP not available at build time)"
    return "Pure NumPy" + ("" if _backend != "auto" else " (native extension not built -- see native/build.sh)")


# ---------------------------------------------------------------------
# Pure-NumPy fallbacks. These exist independently of the C++ extension
# and are exercised directly by tests to prove every backend agrees.
# ---------------------------------------------------------------------

def _np_gradient_pass(data: np.ndarray, h: float, axis: int, edge_order: int) -> np.ndarray:
    coord = np.arange(data.shape[axis]) * h
    order = 2 if data.shape[axis] > 2 else 1
    if edge_order < order:
        order = edge_order if data.shape[axis] > 2 else 1
    return np.gradient(data, coord, axis=axis, edge_order=order)


def gradient_uniform(data: np.ndarray, h: float, axis: int, edge_order: int = 2) -> np.ndarray:
    active = _active_backend()
    if active == "jax":
        return _jax_module().gradient_uniform(data, h, axis, edge_order)
    if active == "native":
        return _ext.gradient_uniform(np.ascontiguousarray(data, dtype=float), float(h), int(axis), int(edge_order))
    return _np_gradient_pass(np.asarray(data, dtype=float), h, axis, edge_order)


def divergence_uniform(components: list[np.ndarray], spacings: list[float], edge_order: int = 2) -> np.ndarray:
    active = _active_backend()
    if active == "jax":
        return _jax_module().divergence_uniform(components, spacings, edge_order)
    components = [np.ascontiguousarray(c, dtype=float) for c in components]
    if active == "native":
        return _ext.divergence_uniform(components, [float(h) for h in spacings], int(edge_order))
    total = np.zeros_like(components[0])
    for axis, (comp, h) in enumerate(zip(components, spacings)):
        total += _np_gradient_pass(comp, h, axis, edge_order)
    return total


def laplacian_uniform(data: np.ndarray, spacings: list[float], edge_order: int = 2) -> np.ndarray:
    active = _active_backend()
    if active == "jax":
        return _jax_module().laplacian_uniform(data, spacings, edge_order)
    data = np.ascontiguousarray(data, dtype=float)
    if active == "native":
        return _ext.laplacian_uniform(data, [float(h) for h in spacings], int(edge_order))
    total = np.zeros_like(data)
    for axis, h in enumerate(spacings):
        first = _np_gradient_pass(data, h, axis, edge_order)
        total += _np_gradient_pass(first, h, axis, edge_order)
    return total


def curl_uniform_3d(c1, c2, c3, h1: float, h2: float, h3: float, edge_order: int = 2):
    active = _active_backend()
    if active == "jax":
        return _jax_module().curl_uniform_3d(c1, c2, c3, h1, h2, h3, edge_order)
    c1 = np.ascontiguousarray(c1, dtype=float)
    c2 = np.ascontiguousarray(c2, dtype=float)
    c3 = np.ascontiguousarray(c3, dtype=float)
    if active == "native":
        return _ext.curl_uniform_3d(c1, c2, c3, float(h1), float(h2), float(h3), int(edge_order))
    d = lambda arr, axis, h: _np_gradient_pass(arr, h, axis, edge_order)
    out_a = d(c3, 1, h2) - d(c2, 2, h3)
    out_b = d(c1, 2, h3) - d(c3, 0, h1)
    out_c = d(c2, 0, h1) - d(c1, 1, h2)
    return out_a, out_b, out_c


def sample_field_trilinear(field: np.ndarray, origin, spacing, points: np.ndarray) -> np.ndarray:
    """Sample a 3D scalar field at arbitrary physical points via trilinear
    interpolation, clamping out-of-bounds points to the grid boundary.

    `origin`/`spacing` are the (x1, x2, x3) minimum coordinate and grid
    spacing; `points` is an (N, 3) array of physical (x1, x2, x3) positions,
    e.g. a particle trajectory's x1(t), x2(t), x3(t).
    """
    active = _active_backend()
    if active == "jax":
        if field.ndim != 3:
            raise ValueError("sample_field_trilinear requires a 3D field")
        if np.asarray(points).ndim != 2 or np.asarray(points).shape[1] != 3:
            raise ValueError("points must have shape (N, 3)")
        if any(float(h) == 0.0 for h in spacing):
            raise ValueError("grid spacing must be non-zero")
        return _jax_module().sample_field_trilinear(field, origin, spacing, points)

    field = np.ascontiguousarray(field, dtype=float)
    points = np.ascontiguousarray(points, dtype=float)
    if field.ndim != 3:
        raise ValueError("sample_field_trilinear requires a 3D field")
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    origin = tuple(float(v) for v in origin)
    spacing = tuple(float(v) for v in spacing)
    if any(h == 0.0 for h in spacing):
        raise ValueError("grid spacing must be non-zero")

    if active == "native":
        return _ext.sample_field_trilinear(field, origin, spacing, points)

    n0, n1, n2 = field.shape
    g = (points - np.asarray(origin)) / np.asarray(spacing)
    g[:, 0] = np.clip(g[:, 0], 0, n0 - 1)
    g[:, 1] = np.clip(g[:, 1], 0, n1 - 1)
    g[:, 2] = np.clip(g[:, 2], 0, n2 - 1)

    i0 = np.floor(g[:, 0]).astype(int); i1 = np.minimum(i0 + 1, n0 - 1)
    j0 = np.floor(g[:, 1]).astype(int); j1 = np.minimum(j0 + 1, n1 - 1)
    k0 = np.floor(g[:, 2]).astype(int); k1 = np.minimum(k0 + 1, n2 - 1)
    tx = g[:, 0] - i0
    ty = g[:, 1] - j0
    tz = g[:, 2] - k0

    c00 = field[i0, j0, k0] * (1 - tx) + field[i1, j0, k0] * tx
    c01 = field[i0, j0, k1] * (1 - tx) + field[i1, j0, k1] * tx
    c10 = field[i0, j1, k0] * (1 - tx) + field[i1, j1, k0] * tx
    c11 = field[i0, j1, k1] * (1 - tx) + field[i1, j1, k1] * tx
    c0 = c00 * (1 - ty) + c10 * ty
    c1 = c01 * (1 - ty) + c11 * ty
    return c0 * (1 - tz) + c1 * tz
```

---

## `scientific_visualization/physics/particle_field.py`

```py
"""Particle <-> field correlation analysis.

Connects the three data sources the application already has separately
(grid/field snapshots, particle diagnostics, particle tracks) so a user can
answer questions like "what field did this particle actually experience
along its trajectory?" -- item #6 of the scientific-AI-workbench roadmap.

Everything here is a plain, deterministic, Qt-independent function
operating on `Dataset`/NumPy arrays, so it is callable from the GUI, from
scripts, or from the AI assistant's tool-calling layer without any of them
needing to know how the sampling is implemented.

Scope note: sampling currently requires a *uniform*, *static* 3D grid
(one time snapshot) -- the common case for a single OSIRIS/PIC dump. Time-
interpolating between multiple field snapshots to match a track's time
samples is future work and is called out explicitly rather than silently
approximated.

Unit-system note: `kinetic_energy_from_momentum` and `lorentz_force` use
the normalized-units convention common to OSIRIS/PIC codes (momentum in
units of m*c, fields already in the code's own normalized units, m=c=1 by
default). Pass explicit `rest_mass`/`c` if your data uses different
normalization -- this module does not guess or silently assume physical
(SI) units.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np

from ..core.data import Dataset
from . import native_backend as _native


def sample_dataset_along_trajectory(field: Dataset, x1: np.ndarray, x2: np.ndarray, x3: np.ndarray) -> np.ndarray:
    """Trilinearly sample a static 3D scalar field at trajectory points.

    `x1`, `x2`, `x3` are 1D arrays of physical coordinates (e.g. a
    particle track's x1(t), x2(t), x3(t)), all the same length. Points
    outside the grid are clamped to the boundary rather than raising,
    since a particle a fraction of a cell outside the box due to floating
    point error is expected, not exceptional.
    """
    if field.ndim != 3:
        raise ValueError(f"sample_dataset_along_trajectory requires a 3D field; got {field.ndim}D")
    if not field.coordinates or len(field.coordinates) != 3:
        raise ValueError("Field dataset is missing 3D coordinate axes")
    non_uniform = [c.name for c in field.coordinates if not c.is_uniform]
    if non_uniform:
        raise ValueError(
            f"Trilinear sampling requires a uniform grid; axis(es) {non_uniform} are not uniformly spaced"
        )
    x1, x2, x3 = np.asarray(x1, dtype=float), np.asarray(x2, dtype=float), np.asarray(x3, dtype=float)
    if not (x1.shape == x2.shape == x3.shape):
        raise ValueError("x1, x2, x3 must have the same shape")
    origin = tuple(c.values[0] for c in field.coordinates)
    spacing = tuple(c.spacing for c in field.coordinates)
    points = np.stack([x1, x2, x3], axis=-1)
    return _native.sample_field_trilinear(np.asarray(field.data, dtype=float), origin, spacing, points)


def sample_fields_along_trajectory(fields: Mapping[str, Dataset], x1: np.ndarray, x2: np.ndarray, x3: np.ndarray) -> dict[str, np.ndarray]:
    """Convenience wrapper: sample several fields (e.g. E1, E2, E3, B1, B2,
    B3) at the same trajectory points. Returns {name: sampled_values}."""
    return {name: sample_dataset_along_trajectory(ds, x1, x2, x3) for name, ds in fields.items()}


def magnitude3(a1: np.ndarray, a2: np.ndarray, a3: np.ndarray) -> np.ndarray:
    """|A| for per-point vector components, e.g. |E| or |B| along a track."""
    a1, a2, a3 = np.asarray(a1, dtype=float), np.asarray(a2, dtype=float), np.asarray(a3, dtype=float)
    return np.sqrt(a1 ** 2 + a2 ** 2 + a3 ** 2)


def dot3(a1, a2, a3, b1, b2, b3) -> np.ndarray:
    """A·B for per-point vector components, e.g. E·v (power delivered to the particle)."""
    return np.asarray(a1) * np.asarray(b1) + np.asarray(a2) * np.asarray(b2) + np.asarray(a3) * np.asarray(b3)


def cross3(a1, a2, a3, b1, b2, b3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A x B for per-point vector components, e.g. v x B."""
    a1, a2, a3 = np.asarray(a1, dtype=float), np.asarray(a2, dtype=float), np.asarray(a3, dtype=float)
    b1, b2, b3 = np.asarray(b1, dtype=float), np.asarray(b2, dtype=float), np.asarray(b3, dtype=float)
    return a2 * b3 - a3 * b2, a3 * b1 - a1 * b3, a1 * b2 - a2 * b1


def velocity_from_momentum(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, rest_mass: float = 1.0, c: float = 1.0):
    """Relativistic velocity (v1, v2, v3) from normalized momentum (p/mc convention).

    gamma = sqrt(1 + |p|^2), v = p*c / (gamma * rest_mass) in the same
    normalized-units convention as the rest of this module.
    """
    p1, p2, p3 = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float), np.asarray(p3, dtype=float)
    gamma = np.sqrt(1.0 + p1 ** 2 + p2 ** 2 + p3 ** 2)
    scale = c / (gamma * rest_mass)
    return p1 * scale, p2 * scale, p3 * scale, gamma


def kinetic_energy_from_momentum(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, rest_mass: float = 1.0, c: float = 1.0) -> np.ndarray:
    """Relativistic kinetic energy (gamma - 1) * m * c^2 from normalized momentum."""
    p1, p2, p3 = np.asarray(p1, dtype=float), np.asarray(p2, dtype=float), np.asarray(p3, dtype=float)
    gamma = np.sqrt(1.0 + p1 ** 2 + p2 ** 2 + p3 ** 2)
    return (gamma - 1.0) * rest_mass * c ** 2


def lorentz_force(e1, e2, e3, b1, b2, b3, v1, v2, v3, charge: float = 1.0):
    """F = q(E + v x B), componentwise, in the caller's normalized units."""
    vxb1, vxb2, vxb3 = cross3(v1, v2, v3, b1, b2, b3)
    return (
        charge * (np.asarray(e1) + vxb1),
        charge * (np.asarray(e2) + vxb2),
        charge * (np.asarray(e3) + vxb3),
    )


def energy_gain(energy: np.ndarray) -> np.ndarray:
    """Per-step change in a scalar energy series along a trajectory (length N-1)."""
    energy = np.asarray(energy, dtype=float)
    if energy.size < 2:
        raise ValueError("Need at least two points to compute an energy gain")
    return np.diff(energy)
```

---

## `scientific_visualization/rendering_colors.py`

```py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

PALETTES = {
    "Jade Fire": ["#071a17", "#0b5d4d", "#19a974", "#d8f36b", "#ff9f43", "#ff3b30"],
    "Neon Pulse": ["#050018", "#3a0ca3", "#7209b7", "#f72585", "#4cc9f0", "#fef08a"],
    "Cyber Dream": ["#090b1a", "#2426a5", "#00b4d8", "#72efdd", "#f15bb5", "#fee440"],
    "Rainbow Prism": ["#5e35b1", "#1976d2", "#00a86b", "#fdd835", "#f57c00", "#d81b60"],
    "Tropical Bloom": ["#0b132b", "#3a506b", "#5bc0be", "#9bc53d", "#fde74c", "#fa7921"],
    "Solar Flare": ["#120d00", "#5b2200", "#c94800", "#ff8f00", "#ffd166", "#fff3b0"],
    "Candy Plasma": ["#10002b", "#5a189a", "#9d4edd", "#f15bb5", "#ff6f91", "#feeafa"],
    "Aurora": ["#05051a", "#0b4f6c", "#00a896", "#7ae582", "#f1fa8c", "#d6eaff"],
    "Ultraviolet": ["#090016", "#240046", "#5a189a", "#9d4edd", "#e0aaff", "#f7ecff"],
    "Ember": ["#100000", "#4a0404", "#9b2226", "#ca6702", "#ee9b00", "#ffe08a"],
    "Ocean": ["#02040f", "#023e8a", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8"],
    "Spectral": ["#5e239d", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"],
    "Scientific Blue-Red": ["#313695", "#4575b4", "#74add1", "#f7f7f7", "#f46d43", "#d73027", "#a50026"],
    "Viridis": ["#440154", "#31688e", "#35b779", "#fde725"],
    "Magma": ["#000004", "#51127c", "#b73779", "#fc8961", "#fcfdbf"],
    "Grayscale": ["#050505", "#808080", "#ffffff"],
}

CYCLIC_PALETTES = {
    "Phase Twilight": ["#e56b6f", "#9d4edd", "#4361ee", "#4cc9f0", "#2a9d8f", "#f4a261", "#e56b6f"],
    "Phase Turbo": ["#30123b", "#4145ab", "#2db6a3", "#b8de29", "#f9e721", "#f8961e", "#d62828", "#30123b"],
    "HSV Phase": ["#ff0000", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ff00ff", "#ff0000"],
}

ALL_PALETTES = {**PALETTES, **CYCLIC_PALETTES}


def make_palette(name: str, reverse: bool = False, phase: float = 0.0, samples: int = 512):
    colors = ALL_PALETTES.get(name)
    if colors is None:
        raise ValueError(f"Unknown palette: {name}")
    cmap = LinearSegmentedColormap.from_list(f"custom_{name}", colors, N=samples)
    lut = cmap(np.linspace(0, 1, samples))
    if phase:
        shift = int(round((phase % 1.0) * samples))
        lut = np.roll(lut, shift, axis=0)
    if reverse:
        lut = lut[::-1]
    return LinearSegmentedColormap.from_list(f"custom_{name}_phase", lut, N=samples)


@dataclass(frozen=True)
class ColorEngineConfig:
    palette: str = "Viridis"
    reverse: bool = False
    phase: float = 0.0
    gamma: float = 1.0
    contrast: float = 1.0
    black_floor: float = 0.0
    mapping: str = "Scalar"


def palette_preview_data(name: str, n: int = 256):
    cmap = make_palette(name, samples=n)
    x = np.linspace(0, 1, n)
    return cmap(x).reshape(1, n, 4)
```

---

## `scientific_visualization/session.py`

```py
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET


def _set_value(node, key, value):
    node.set(key, str(value))


def save_xml_session(path: str | Path, state: dict):
    root = ET.Element("scientific_visualization_session", version="1")
    def encode(parent, name, obj):
        node = ET.SubElement(parent, name)
        if isinstance(obj, dict):
            node.set("type", "dict")
            for k, v in obj.items():
                encode(node, str(k), v)
        elif isinstance(obj, (list, tuple)):
            node.set("type", "list")
            for v in obj:
                encode(node, "item", v)
        else:
            node.set("type", "value")
            node.text = "" if obj is None else str(obj)
        return node
    encode(root, "state", state)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
    return str(path)


def load_xml_session(path: str | Path) -> dict:
    root = ET.parse(str(path)).getroot()
    if root.tag != "scientific_visualization_session":
        raise ValueError("Not a Scientific Visualization session file")
    state = root.find("state")
    if state is None:
        raise ValueError("Session file contains no state")

    def decode(node):
        kind = node.get("type")
        if kind == "value":
            return node.text or ""
        if kind == "list":
            return [decode(child) for child in node.findall("item")]
        if kind == "dict":
            return {child.tag: decode(child) for child in node}
        raise ValueError(f"Unknown session value type: {kind!r}")

    return decode(state)


def value_as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def value_as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def value_as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
```

---

## `scientific_visualization/simulation/__init__.py`

```py
from .runner import SimulationRunner, SimulationRun
__all__=["SimulationRunner","SimulationRun"]
```

---

## `scientific_visualization/simulation/runner.py`

```py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
from typing import Sequence

@dataclass
class SimulationRun:
    command: Sequence[str]
    working_directory: str | None = None
    output: str = ""
    return_code: int | None = None

class SimulationRunner:
    """Safe handoff point from active learning recommendations to a simulation code.

    Commands are explicit argument lists rather than shell strings. This avoids shell
    interpolation and allows Simulation or another simulator to be integrated later.
    """
    def run(self, command: Sequence[str], working_directory: str | Path | None = None, timeout: float | None = None) -> SimulationRun:
        wd = str(working_directory) if working_directory is not None else None
        proc = subprocess.run(list(command), cwd=wd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return SimulationRun(command=list(command), working_directory=wd, output=proc.stdout, return_code=proc.returncode)
```

---

## `scientific_visualization/style.py`

```py
"""
Modern plotting look-and-feel for Scientific Visualization (Python).

Two themes (light/dark) with clean typography, subtle grids, and no
chartjunk. Call `apply_theme(fig, theme)` right before drawing.
"""
from __future__ import annotations

import matplotlib as mpl

LIGHT = dict(
    figure_facecolor="#ffffff",
    axes_facecolor="#ffffff",
    text_color="#1a1a1a",
    grid_color="#d8d8d8",
    spine_color="#888888",
    accent="#2a6fdb",
)

DARK = dict(
    figure_facecolor="#111318",
    axes_facecolor="#171a21",
    text_color="#e8e8e8",
    grid_color="#33373f",
    spine_color="#5a5f68",
    accent="#5aa2ff",
)

THEMES = {"Light": LIGHT, "Dark": DARK}

# Colormap groupings, shown to the user by category for quicker, more
# deliberate choices than one long flat list.
COLORMAPS = {
    "Sequential": ["viridis", "plasma", "inferno", "magma", "cividis", "cubehelix"],
    "Diverging (signed fields)": ["RdBu_r", "coolwarm", "seismic", "PuOr", "PRGn"],
    "Perceptual / misc": ["turbo", "twilight_shifted", "gray"],
}
ALL_COLORMAPS = [c for group in COLORMAPS.values() for c in group]

DIVERGING_CMAPS = set(COLORMAPS["Diverging (signed fields)"])

# Qualitative line-color palettes for tracks/lineouts (index-based coloring),
# offered as named choices so results are reproducible and colorblind-aware.
LINE_PALETTES = {
    "Viridis-based": None,     # sampled from a continuous cmap at draw time
    "Okabe-Ito (colorblind-safe)": [
        "#E69F00", "#56B4E9", "#009E73", "#F0E442",
        "#0072B2", "#D55E00", "#CC79A7", "#000000",
    ],
    "Tableau 10": [
        "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
        "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    ],
    "Bright": [
        "#FF3B30", "#FF9500", "#FFCC00", "#34C759",
        "#00C7BE", "#30B0C7", "#007AFF", "#AF52DE",
    ],
}

DEFAULT_ACCENT = {"Light": "#2a6fdb", "Dark": "#5aa2ff"}

FONT_FAMILIES = ["DejaVu Sans", "Arial", "Helvetica", "Liberation Sans", "Times New Roman", "STIXGeneral", "Computer Modern Roman"]
_FONT_FAMILY = "DejaVu Sans"
_FONT_SIZE = 10.5

def set_font_preferences(family: str | None = None, size: float | None = None):
    global _FONT_FAMILY, _FONT_SIZE
    if family:
        _FONT_FAMILY = family
    if size is not None:
        _FONT_SIZE = float(size)
    mpl.rcParams["font.family"] = _FONT_FAMILY
    mpl.rcParams["font.size"] = _FONT_SIZE
    mpl.rcParams["axes.titlesize"] = _FONT_SIZE * 1.15
    mpl.rcParams["axes.labelsize"] = _FONT_SIZE
    mpl.rcParams["xtick.labelsize"] = max(6.0, _FONT_SIZE * 0.9)
    mpl.rcParams["ytick.labelsize"] = max(6.0, _FONT_SIZE * 0.9)
    mpl.rcParams["legend.fontsize"] = max(6.0, _FONT_SIZE * 0.9)

def current_font_preferences():
    return _FONT_FAMILY, _FONT_SIZE


def line_color_cycle(palette_name: str, n: int, cmap_fallback: str = "viridis"):
    """Return a list of `n` hex colors for index-based line coloring."""
    import matplotlib.cm as cm
    palette = LINE_PALETTES.get(palette_name)
    if palette:
        return [palette[i % len(palette)] for i in range(n)]
    cmap = cm.get_cmap(cmap_fallback, max(n, 1))
    return [cmap(i) for i in range(n)]


def base_rcparams():
    """Global rcParams applied once at app start -- modern, minimal chrome."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.titleweight": "medium",
        "axes.labelsize": 10.5,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "axes.linewidth": 0.8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "image.interpolation": "nearest",
    })


def apply_theme(fig, theme_name: str = "Light"):
    """Apply colors for the given theme to a Figure and all its Axes."""
    t = THEMES.get(theme_name, LIGHT)
    fig.set_facecolor(t["figure_facecolor"])
    for ax in fig.get_axes():
        ax.set_facecolor(t["axes_facecolor"])
        ax.title.set_color(t["text_color"])
        ax.xaxis.label.set_color(t["text_color"])
        ax.yaxis.label.set_color(t["text_color"])
        family, size = current_font_preferences()
        ax.title.set_fontfamily(family); ax.title.set_fontsize(size * 1.15)
        ax.xaxis.label.set_fontfamily(family); ax.xaxis.label.set_fontsize(size)
        ax.yaxis.label.set_fontfamily(family); ax.yaxis.label.set_fontsize(size)
        ax.tick_params(colors=t["text_color"], labelsize=max(6.0, size * 0.9))
        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontfamily(family)
        for spine in ax.spines.values():
            spine.set_color(t["spine_color"])
        ax.grid(True, color=t["grid_color"], linewidth=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        legend = ax.get_legend()
        if legend is not None:
            for text in legend.get_texts():
                text.set_color(t["text_color"])
    return t


# ---------------------------------------------------------------------
# Whole-application (Qt widget chrome) dark/light mode -- distinct from
# the per-figure `apply_theme` above but meant to be kept in sync with it
# by the main window, so "Dark" means the whole app goes dark, not just
# the plots.
# ---------------------------------------------------------------------

LIGHT_QSS = ""  # empty stylesheet == Qt platform default light look

DARK_QSS = """
QWidget {
    background-color: #202226;
    color: #e8e8e8;
    selection-background-color: #3a6fd8;
    selection-color: #ffffff;
}
QMainWindow, QScrollArea, QSplitter {
    background-color: #202226;
}
QGroupBox {
    border: 1px solid #3a3d44;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #cfd3da;
}
QPushButton {
    background-color: #33363d;
    border: 1px solid #45484f;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover { background-color: #3d4148; }
QPushButton:pressed { background-color: #2a2d33; }
QComboBox, QSpinBox, QDoubleSpinBox, QListWidget, QLineEdit {
    background-color: #2a2d33;
    border: 1px solid #45484f;
    border-radius: 4px;
    padding: 3px;
}
QComboBox QAbstractItemView {
    background-color: #2a2d33;
    selection-background-color: #3a6fd8;
}
QTabWidget::pane { border: 1px solid #3a3d44; }
QTabBar::tab {
    background: #2a2d33;
    padding: 6px 14px;
    border: 1px solid #3a3d44;
    border-bottom: none;
}
QTabBar::tab:selected { background: #33363d; color: #ffffff; }
QScrollBar:vertical {
    background: #202226;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #45484f;
    border-radius: 5px;
    min-height: 24px;
}
QToolBar { background-color: #26282c; border: none; spacing: 6px; }
QLabel { background: transparent; }
QCheckBox, QRadioButton { spacing: 6px; }
"""


def apply_app_theme(app, theme_name: str):
    """Apply (or remove) the whole-application dark stylesheet."""
    app.setStyleSheet(DARK_QSS if theme_name == "Dark" else LIGHT_QSS)
```

---

## `scientific_visualization/uncertainty/__init__.py`

```py
from .quantification import UncertaintyEstimator
__all__=["UncertaintyEstimator"]
```

---

## `scientific_visualization/uncertainty/quantification.py`

```py
from __future__ import annotations
import numpy as np

class UncertaintyEstimator:
    """Model-agnostic uncertainty helpers based on ensemble predictions and residuals."""
    @staticmethod
    def ensemble_interval(predictions, confidence=0.95):
        pred=np.asarray(predictions,dtype=float)
        if pred.ndim != 2: raise ValueError("predictions must be [models, samples]")
        alpha=(1.0-confidence)/2.0
        return {"mean":np.mean(pred,axis=0),"lower":np.quantile(pred,alpha,axis=0),"upper":np.quantile(pred,1-alpha,axis=0),"std":np.std(pred,axis=0)}

    @staticmethod
    def residual_summary(y_true,y_pred):
        r=np.asarray(y_true,dtype=float)-np.asarray(y_pred,dtype=float)
        return {"bias":float(np.mean(r)),"rmse":float(np.sqrt(np.mean(r*r))),"mae":float(np.mean(np.abs(r))),"std":float(np.std(r))}
```

---

## `scientific_visualization/visualization/__init__.py`

```py
from .base import Renderer
from .one_d import plot_dataset, plot_time_series
from .two_d import plot_2d
from .three_d import ThreeDRenderer

__all__ = ["Renderer", "plot_dataset", "plot_time_series", "plot_2d", "ThreeDRenderer"]
```

---

## `scientific_visualization/visualization/base.py`

```py
from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.configuration import RenderingConfig
from ..core.data import Dataset


class Renderer(ABC):
    @abstractmethod
    def render(self, dataset: Dataset, config: RenderingConfig):
        raise NotImplementedError
```

---

## `scientific_visualization/visualization/gpu/__init__.py`

```py
from .vispy_renderer import VISPY_AVAILABLE, VisPyFieldRenderer
__all__ = ['VISPY_AVAILABLE', 'VisPyFieldRenderer']
```

---

## `scientific_visualization/visualization/gpu/qt_widget.py`

```py
from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from .vispy_renderer import VISPY_AVAILABLE, VisPyFieldRenderer

class GPUFieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.renderer = None
        if VISPY_AVAILABLE:
            self.renderer = VisPyFieldRenderer(self)
            self.layout.addWidget(self.renderer.widget())
        else:
            self.layout.addWidget(QLabel('GPU rendering is unavailable. Install VisPy and an OpenGL-capable Qt environment.'))

    def set_data(self, data, extent=None, cmap='viridis'):
        if self.renderer:
            self.renderer.set_data(data, extent=extent, cmap=cmap)

    def set_clim(self, vmin, vmax):
        if self.renderer:
            self.renderer.set_clim(vmin, vmax)

    def reset_view(self):
        if self.renderer:
            self.renderer.reset_view()
```

---

## `scientific_visualization/visualization/gpu/vispy_renderer.py`

```py
from __future__ import annotations

try:
    from vispy import scene
    from vispy.scene import visuals
    VISPY_AVAILABLE = True
except Exception:
    scene = None
    visuals = None
    VISPY_AVAILABLE = False

class VisPyFieldRenderer:
    """GPU-backed 2D field renderer. Imports VisPy lazily and is optional."""
    def __init__(self, parent=None):
        if not VISPY_AVAILABLE:
            raise RuntimeError('VisPy is not installed. Install vispy and a working OpenGL driver.')
        self.canvas = scene.SceneCanvas(keys='interactive', show=False, bgcolor='white', parent=parent)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.image = None
        self._extent = None

    def widget(self):
        return self.canvas.native

    def set_data(self, data, extent=None, cmap='viridis'):
        import numpy as np
        arr = np.asarray(data, dtype=np.float32)
        if arr.ndim != 2:
            raise ValueError('VisPy 2D field rendering requires a 2D array.')
        if self.image is None:
            self.image = visuals.Image(arr, cmap=cmap, interpolation='nearest', parent=self.view.scene)
        else:
            self.image.set_data(arr)
            try:
                self.image.cmap = cmap
            except Exception:
                pass
        if extent is not None:
            self._extent = tuple(extent)
        self.view.camera.set_range(x=(0, arr.shape[1]), y=(0, arr.shape[0]), margin=0.02)
        self.canvas.update()

    def set_clim(self, vmin, vmax):
        if self.image is not None:
            try:
                self.image.clim = (float(vmin), float(vmax))
            except Exception:
                pass
            self.canvas.update()

    def set_opacity(self, value):
        if self.image is not None:
            self.image.opacity = float(value)
            self.canvas.update()

    def reset_view(self):
        if self.image is not None:
            shape = self.image.size
            self.view.camera.set_range(x=(0, shape[1]), y=(0, shape[0]), margin=0.02)
```

---

## `scientific_visualization/visualization/one_d/__init__.py`

```py
from .matplotlib import plot_dataset, plot_time_series

__all__ = ["plot_dataset", "plot_time_series"]
```

---

## `scientific_visualization/visualization/one_d/matplotlib.py`

```py
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ...core.configuration import RenderingConfig
from ...core.data import Dataset


def label_with_units(label: str, units: str) -> str:
    return f"{label} [{units}]" if units else label


def plot_dataset(dataset: Dataset, ax: Axes | None = None, x_axis: str | int = 0, config: RenderingConfig | None = None, label: str | None = None):
    config = config or RenderingConfig()
    config.validate()
    if dataset.ndim != 1:
        raise ValueError("plot_dataset expects a 1D dataset")
    ax = ax or plt.subplots(figsize=(config.figure_width, config.figure_height))[1]
    x = dataset.coordinates[dataset.axis_index(x_axis)].values
    ax.plot(x, dataset.data, label=label or dataset.name)
    ax.set_xlabel(label_with_units(dataset.coordinates[0].label or dataset.axes[0], dataset.coordinates[0].units))
    ax.set_ylabel(label_with_units(dataset.name, dataset.units))
    if config.title:
        ax.set_title(config.title)
    if label:
        ax.legend()
    return ax


def plot_time_series(times, values, *, ax=None, config=None, label="quantity", time_units=""):
    config = config or RenderingConfig()
    config.validate()
    if ax is None:
        _, ax = plt.subplots(figsize=(config.figure_width, config.figure_height))
    ax.plot(times, values, label=label)
    ax.set_xlabel(label_with_units("time", time_units))
    ax.set_ylabel(label)
    ax.legend()
    return ax
```

---

## `scientific_visualization/visualization/three_d/__init__.py`

```py
from .pyvista_renderer import ThreeDRenderer

__all__ = ["ThreeDRenderer"]
```

---

## `scientific_visualization/visualization/three_d/pyvista_renderer.py`

```py
from __future__ import annotations

from collections import OrderedDict

import numpy as np

try:
    import pyvista as pv
except Exception:
    pv = None

from ...core.configuration import RenderingConfig
from ...core.data import Dataset


class ThreeDRenderer:
    """Fast PyVista renderer for native 3D data and 2D data promoted to geometry."""

    def __init__(self, plotter=None):
        if pv is None:
            raise ImportError("3D visualization requires optional dependency 'pyvista'")
        self.plotter = plotter or pv.Plotter()
        self._grid_cache = OrderedDict()
        self._grid_cache_size = 4

    @staticmethod
    def _require_2d(dataset):
        if dataset.ndim != 2:
            raise ValueError("2D-to-3D modes require a 2D dataset")
        if len(dataset.coordinates) != 2:
            raise ValueError("2D dataset must provide two coordinate axes")

    @staticmethod
    def _world_axes(dataset):
        names = tuple(a.name.lower() for a in dataset.coordinates)
        out = []
        for i, name in enumerate(names):
            out.append(name if name in {"x1", "x2", "x3"} else f"x{i+1}")
        if len(set(out)) != 2:
            raise ValueError("2D dataset coordinates must map to two distinct spatial axes")
        return tuple(out)

    @staticmethod
    def _make_plane_coordinates(dataset, normal_axis, position):
        axes = ThreeDRenderer._world_axes(dataset)
        if normal_axis in axes:
            raise ValueError(f"Plane normal {normal_axis} must be the axis absent from the 2D dataset ({axes})")
        coords = {axes[0]: np.asarray(dataset.coordinates[0].values), axes[1]: np.asarray(dataset.coordinates[1].values)}
        u_axis, v_axis = axes
        uu, vv = np.meshgrid(coords[u_axis], coords[v_axis], indexing="ij")
        mapping = {
            u_axis: uu.astype(np.float32, copy=False),
            v_axis: vv.astype(np.float32, copy=False),
            normal_axis: np.full(uu.shape, float(position), dtype=np.float32),
        }
        return mapping["x1"], mapping["x2"], mapping["x3"]

    @staticmethod
    def _mesh_options(config):
        return dict(
            smooth_shading=bool(getattr(config, "smooth_shading", True)),
            show_edges=bool(getattr(config, "show_edges", False)),
            edge_color=getattr(config, "edge_color", "black"),
        )

    def _add_mesh(self, grid, dataset, config, name, *, volume=False):
        # These are optional VTK features. Missing support on an older VTK build
        # never prevents normal scientific rendering.
        try:
            if getattr(config, "depth_peeling", False):
                self.plotter.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
        except Exception:
            pass
        try:
            if getattr(config, "ssao", False):
                self.plotter.enable_ssao(radius=0.5, bias=0.0)
        except Exception:
            pass
        try:
            if getattr(config, "stereo", False):
                self.plotter.enable_stereo_render()
        except Exception:
            pass
        try:
            if getattr(config, "hidden_line_removal", False) and not volume:
                grid = grid.extract_geometry() if hasattr(grid, "extract_geometry") else grid
        except Exception:
            pass
        if getattr(config, "antialiasing", True):
            try: self.plotter.enable_anti_aliasing()
            except Exception: pass
        if getattr(config, "eye_dome_lighting", False):
            try: self.plotter.enable_eye_dome_lighting()
            except Exception: pass
        common = dict(
            scalars=dataset.name,
            cmap=config.colormap,
            clim=self._clim(dataset, config),
            opacity=config.opacity,
            name=name,
            show_scalar_bar=False,
        )
        if volume:
            actor = self.plotter.add_volume(grid, opacity="sigmoid", **{k: v for k, v in common.items() if k != "opacity"})
        else:
            common.update(self._mesh_options(config))
            n_points = int(getattr(grid, "n_points", 0) or 0)
            if common.get("smooth_shading") and n_points > 300_000:
                # smooth_shading triggers VTK's compute_normals pass, whose
                # cost scales with mesh size and can dominate rendering time
                # on its own for a very dense/complex mesh (measured: ~11s
                # for a 6.2M-point isosurface) for a visually negligible
                # difference at that triangle density. Auto-downgrade to
                # flat shading rather than silently stalling; the checkbox
                # still forces it on for meshes under the threshold.
                common["smooth_shading"] = False
                print(f"[3D] Using flat shading for a large mesh ({n_points:,} points) to avoid a slow normal-computation pass.", flush=True)
            common["lighting"] = bool(getattr(config, "lighting", True))
            actor = self.plotter.add_mesh(grid, **common)
        self._add_scalar_bar(actor, dataset, config)
        return actor

    def add_2d_plane(self, dataset: Dataset, plane_axis="x3", position=0.0, config=None, name=None):
        self._require_2d(dataset); config = config or RenderingConfig()
        X, Y, Z = self._make_plane_coordinates(dataset, plane_axis, position)
        grid = pv.StructuredGrid(X, Y, Z)
        grid[dataset.name] = np.asarray(dataset.data).ravel(order="F")
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_plane")

    def add_2d_surface(self, dataset: Dataset, z_scale=1.0, height_axis="x3", base_position=0.0, config=None, name=None):
        self._require_2d(dataset); config = config or RenderingConfig()
        X, Y, Z = self._make_plane_coordinates(dataset, height_axis, base_position)
        values = np.asarray(dataset.data, dtype=np.float32)
        height = values * float(z_scale)
        if height_axis == "x1": X = X + height
        elif height_axis == "x2": Y = Y + height
        elif height_axis == "x3": Z = Z + height
        else: raise ValueError("height_axis must be x1, x2, or x3")
        grid = pv.StructuredGrid(X, Y, Z)
        grid[dataset.name] = values.ravel(order="F")
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_surface")

    def add_2d_extrusion(self, dataset: Dataset, depth=1.0, extrusion_axis="x3", start_position=0.0, config=None, name=None):
        self._require_2d(dataset); config = config or RenderingConfig()
        axes = self._world_axes(dataset)
        if extrusion_axis in axes:
            raise ValueError(f"Extrusion axis {extrusion_axis} must be the axis absent from the 2D dataset ({axes})")
        X0, Y0, Z0 = self._make_plane_coordinates(dataset, extrusion_axis, start_position)
        X1, Y1, Z1 = X0.copy(), Y0.copy(), Z0.copy()
        if extrusion_axis == "x1": X1 += float(depth)
        elif extrusion_axis == "x2": Y1 += float(depth)
        else: Z1 += float(depth)
        nx, ny = X0.shape
        n = nx * ny
        p0 = np.column_stack((X0.ravel(), Y0.ravel(), Z0.ravel()))
        p1 = np.column_stack((X1.ravel(), Y1.ravel(), Z1.ravel()))
        points = np.vstack((p0, p1))
        grid = pv.PolyData(points)
        # Vectorized quad generation, replacing the old Python loop over every cell.
        ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
        base = (ii * ny + jj).ravel()
        quads0 = np.column_stack((np.full(base.size, 4), base, base + ny, base + ny + 1, base + 1))
        quads1 = quads0.copy(); quads1[:, 1:] += n
        grid.faces = np.vstack((quads0, quads1)).astype(np.int64, copy=False).ravel()
        grid[dataset.name] = np.tile(np.asarray(dataset.data, dtype=np.float32).ravel(order="C"), 2)
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_extrusion")

    @staticmethod
    def _grid_cache_key(dataset):
        coords_key = tuple((c.name, c.size, float(c.values[0]) if c.size else 0.0,
                            float(c.values[-1]) if c.size else 0.0,
                            bool(c.is_uniform)) for c in dataset.coordinates)
        arr = np.asarray(dataset.data)
        return (id(dataset), id(arr), arr.shape, str(arr.dtype), coords_key)

    def clear_grid_cache(self):
        self._grid_cache.clear()

    def _build_3d_grid(self, dataset: Dataset):
        """Build a VTK grid without allocating coordinate meshes for uniform grids."""
        if dataset.ndim != 3:
            raise ValueError("A native 3D VTK grid requires a 3D dataset")
        key = self._grid_cache_key(dataset)
        cached = self._grid_cache.get(key)
        if cached is not None:
            return cached
        coords = dataset.coordinates
        if all(c.is_uniform for c in coords):
            dims = tuple(int(c.size) for c in coords)
            origin = tuple(float(c.values[0]) if c.size else 0.0 for c in coords)
            spacing = tuple(float(c.spacing) if c.size > 1 else 1.0 for c in coords)
            grid = pv.ImageData(dimensions=dims, origin=origin, spacing=spacing)
        else:
            x, y, z = (np.asarray(c.values, dtype=np.float32) for c in coords)
            xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
            grid = pv.StructuredGrid(xx, yy, zz)
        grid[dataset.name] = np.asarray(dataset.data, dtype=np.float32).ravel(order="F")
        self._grid_cache[key] = grid
        self._grid_cache.move_to_end(key)
        while len(self._grid_cache) > self._grid_cache_size:
            self._grid_cache.popitem(last=False)
        return grid

    def _render_grid(self, dataset: Dataset, config: RenderingConfig):
        grid = self._build_3d_grid(dataset)
        factor = float(getattr(config, "render_decimation", 1.0) or 1.0)
        if factor >= 0.999:
            return grid
        if isinstance(grid, pv.ImageData):
            dims = tuple(int(v) for v in grid.dimensions)
            extents = []
            for dim in dims:
                step = max(1, int(round(1.0 / factor)))
                extents.extend([0, max(0, dim - 1), step])
            try:
                return grid.extract_subset(extents)
            except Exception:
                return grid
        return grid

    def add_native_3d_slices(self, dataset: Dataset, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Native 3D slicing requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        slices = grid.slice_orthogonal()
        return self._add_mesh(slices, dataset, config, name or f"{dataset.name}_slices")

    def add_native_3d(self, dataset: Dataset, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Native 3D rendering requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_volume", volume=True)

    @staticmethod
    def suggest_isovalues(dataset: Dataset, n: int = 3) -> list[float]:
        if n < 1: raise ValueError("n must be at least 1")
        data = np.asarray(dataset.data, dtype=float); finite = data[np.isfinite(data)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values to derive isovalues from")
        percentiles = np.linspace(100.0 / (n + 1), 100.0 * n / (n + 1), n)
        return [float(v) for v in np.percentile(finite, percentiles)]

    def add_isosurfaces(self, dataset: Dataset, isovalues, config=None, name=None, smooth=True,
                         max_smooth_points=60_000, smooth_iterations=20):
        if dataset.ndim != 3: raise ValueError("Isosurfaces require a 3D dataset")
        isovalues = sorted({float(v) for v in isovalues})
        if not isovalues: raise ValueError("Provide at least one isovalue")
        data = np.asarray(dataset.data, dtype=float); finite = data[np.isfinite(data)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values")
        lo, hi = float(finite.min()), float(finite.max())
        bad = [v for v in isovalues if v < lo or v > hi]
        if bad:
            raise ValueError(f"Isovalue(s) {bad} are outside the field '{dataset.name}' range {lo:.6g} to {hi:.6g}.")
        contours = self._render_grid(dataset, config or RenderingConfig()).contour(isosurfaces=isovalues, scalars=dataset.name)
        if contours.n_points == 0:
            raise ValueError(f"No isosurface exists at value(s) {isovalues}; the field ranges from {lo:.6g} to {hi:.6g}.")
        if smooth and contours.n_points > 20:
            if contours.n_points > max_smooth_points:
                # Laplacian smoothing cost scales with n_iter * n_points;
                # a noisy or high-resolution field can produce an
                # isosurface with hundreds of thousands of points, which
                # made this an unbounded, silent multi-second-to-minutes
                # stall (measured: 23s alone for a 3.4M-point volume,
                # dwarfing the ~2.5s isosurface extraction itself, which
                # is already VTK/C++). Skip rather than hang, and say why,
                # instead of leaving the user thinking the app has frozen.
                print(
                    f"[3D] Skipping isosurface smoothing: this isosurface has {contours.n_points:,} "
                    f"points (> {max_smooth_points:,}), which would make smoothing very slow. "
                    f"Showing the unsmoothed surface. Reduce the source grid resolution or the "
                    f"number of isosurfaces to enable smoothing.", flush=True,
                )
            else:
                try: contours = contours.smooth(n_iter=smooth_iterations, relaxation_factor=0.01, feature_smoothing=False)
                except Exception: pass
        return self._add_mesh(contours, dataset, config or RenderingConfig(), name or f"{dataset.name}_isosurfaces")

    def add_threshold(self, dataset: Dataset, lower=None, upper=None, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Threshold rendering requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        finite = np.asarray(dataset.data, dtype=float); finite = finite[np.isfinite(finite)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values")
        lo = float(finite.min()) if lower is None else float(lower); hi = float(finite.max()) if upper is None else float(upper)
        if lo >= hi: raise ValueError("Threshold lower bound must be smaller than upper bound")
        mesh = grid.threshold(value=(lo, hi), scalars=dataset.name)
        return self._add_mesh(mesh, dataset, config, name or f"{dataset.name}_threshold")

    def add_clipped_volume(self, dataset: Dataset, config=None, name=None, normal="x", interactive=True):
        if dataset.ndim != 3: raise ValueError("Clipping requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        common = dict(scalars=dataset.name, cmap=config.colormap, clim=self._clim(dataset, config), opacity=config.opacity, show_scalar_bar=False)
        if interactive:
            actor = self.plotter.add_mesh_clip_plane(grid, normal=normal, name=name or f"{dataset.name}_clip", **common)
        else:
            actor = self.plotter.add_mesh(grid.clip(normal=normal), name=name or f"{dataset.name}_clip", **common)
        self._add_scalar_bar(actor, dataset, config); return actor

    def move_camera_screen(self, dx: float = 0.0, dy: float = 0.0, scale: float = 0.02):
        """Translate camera and focal point in the camera's screen plane."""
        cam = self.plotter.camera
        pos = np.asarray(cam.position, dtype=float)
        focal = np.asarray(cam.focal_point, dtype=float)
        direction = focal - pos
        distance = max(float(np.linalg.norm(direction)), 1e-9)
        forward = direction / distance
        up = np.asarray(cam.up, dtype=float)
        up /= max(float(np.linalg.norm(up)), 1e-9)
        right = np.cross(forward, up)
        right /= max(float(np.linalg.norm(right)), 1e-9)
        step = distance * float(scale)
        shift = right * float(dx) * step + up * float(dy) * step
        cam.position = tuple(pos + shift)
        cam.focal_point = tuple(focal + shift)
        self.plotter.render()

    def set_show_bounding_box(self, show: bool):
        try: self.plotter.remove_bounds_axes()
        except Exception: pass
        if show: self.plotter.show_bounds(grid=True, location="outer", all_edges=True)

    def set_show_orientation_axes(self, show: bool):
        if show: self.plotter.show_axes()
        else: self.plotter.hide_axes()

    def set_background(self, color):
        self.plotter.set_background(color)
        self.plotter.render()

    def save_screenshot(self, filepath: str):
        self.plotter.screenshot(filepath); return filepath

    @staticmethod
    def scalar_bar_geometry(position: str):
        geometries = {
            "right":  (True, 0.87, 0.10, 0.10, 0.80),
            "left":   (True, 0.03, 0.10, 0.10, 0.80),
            "top":    (False, 0.15, 0.90, 0.70, 0.08),
            "bottom": (False, 0.15, 0.02, 0.70, 0.08),
        }
        if position not in geometries: raise ValueError(f"Invalid colorbar position: {position!r}")
        return geometries[position]

    def set_render_quality(self, quality: str):
        quality = quality.lower()
        try:
            if quality == "high": self.plotter.enable_anti_aliasing()
            elif quality == "balanced": self.plotter.enable_anti_aliasing(aa_type="ssaa")
            elif quality == "fast": self.plotter.disable_anti_aliasing()
        except Exception: pass
        try: self.plotter.render()
        except Exception: pass

    def add_box_clip(self, dataset: Dataset, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Box clipping requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        clipped = grid.clip_box(invert=False)
        return self._add_mesh(clipped, dataset, config, name or f"{dataset.name}_boxclip")

    def add_slice(self, dataset: Dataset, axis: str = "x3", value=None, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Slice requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        bounds = grid.bounds
        idx = {"x1":0,"x2":1,"x3":2}[axis]
        v = [0.5*(bounds[0]+bounds[1]), 0.5*(bounds[2]+bounds[3]), 0.5*(bounds[4]+bounds[5])][idx] if value is None else float(value)
        normal = [0,0,0]; normal[idx]=1
        sl = grid.slice(normal=normal, origin=[0,0,0] if value is None else [v if idx==0 else 0, v if idx==1 else 0, v if idx==2 else 0])
        return self._add_mesh(sl, dataset, config, name or f"{dataset.name}_{axis}_slice")

    def _add_scalar_bar(self, actor, dataset: Dataset, config):
        if not config.show_colorbar: return None
        vertical, x, y, w, h = self.scalar_bar_geometry(getattr(config, "colorbar_position", "right"))
        title = f"{dataset.name} [{dataset.units}]" if dataset.units else dataset.name
        width = getattr(config, "colorbar_width", None) or w
        height = getattr(config, "colorbar_height", None) or h
        kwargs = dict(title=title, vertical=vertical, position_x=x, position_y=y, width=float(width), height=float(height), outline=bool(getattr(config, "colorbar_box", False)), interactive=bool(getattr(config, "colorbar_interactive", True)))
        mapper = getattr(actor, "mapper", None)
        if mapper is not None: kwargs["mapper"] = mapper
        try: return self.plotter.add_scalar_bar(**kwargs)
        except TypeError:
            kwargs.pop("interactive", None)
            return self.plotter.add_scalar_bar(**kwargs)

    @staticmethod
    def _clim(dataset, config):
        finite = np.asarray(dataset.data)[np.isfinite(dataset.data)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values")
        vmin = config.vmin if config.vmin is not None else float(finite.min())
        vmax = config.vmax if config.vmax is not None else float(finite.max())
        if config.symmetric_limits:
            m = max(abs(vmin), abs(vmax)); vmin, vmax = -m, m
        return (vmin, vmax)
```

---

## `scientific_visualization/visualization/two_d/__init__.py`

```py
from .matplotlib import plot_2d

__all__ = ["plot_2d"]
```

---

## `scientific_visualization/visualization/two_d/matplotlib.py`

```py
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize, SymLogNorm
from matplotlib.axes import Axes

from ...core.configuration import RenderingConfig
from ...core.data import Dataset
from ...core.coordinates import coordinate_edges


def _norm_and_limits(data, config):
    finite = np.asarray(data)[np.isfinite(data)]
    if finite.size == 0:
        raise ValueError("Dataset contains no finite values")
    vmin = config.vmin if config.vmin is not None else float(np.min(finite))
    vmax = config.vmax if config.vmax is not None else float(np.max(finite))
    if config.symmetric_limits:
        m = max(abs(vmin), abs(vmax))
        vmin, vmax = -m, m
    if config.normalization == "log":
        positive = finite[finite > 0]
        if positive.size == 0:
            raise ValueError("Log normalization requires at least one positive value")
        vmin = vmin if vmin is not None and vmin > 0 else float(np.min(positive))
        vmax = vmax if vmax is not None and vmax > vmin else float(np.max(positive))
        return LogNorm(vmin=vmin, vmax=vmax), vmin, vmax
    return Normalize(vmin=vmin, vmax=vmax), vmin, vmax


def plot_2d(dataset: Dataset, ax: Axes | None = None, config: RenderingConfig | None = None):
    config = config or RenderingConfig()
    config.validate()
    if dataset.ndim != 2:
        raise ValueError("plot_2d expects a 2D dataset")
    ax = ax or plt.subplots(figsize=(config.figure_width, config.figure_height))[1]
    norm, _, _ = _norm_and_limits(dataset.data, config)
    x = dataset.coordinates[0].values
    y = dataset.coordinates[1].values
    im = ax.pcolormesh(coordinate_edges(x), coordinate_edges(y), dataset.data.T, cmap=config.colormap, norm=norm, shading="auto")
    if config.show_colorbar:
        orientation = "vertical" if config.colorbar_position in ("left", "right") else "horizontal"
        cbar = ax.figure.colorbar(im, ax=ax, orientation=orientation, location=config.colorbar_position,
                                  fraction=min(max(config.colorbar_width or 0.10, 0.02), 0.5))
        cbar.set_label(label_with_units(dataset.name, dataset.units), rotation=config.colorbar_label_rotation,
                       labelpad=config.colorbar_label_pad)
        if config.colorbar_label_position != "auto":
            if orientation == "vertical":
                cbar.ax.yaxis.set_label_position(config.colorbar_label_position)
            else:
                cbar.ax.xaxis.set_label_position(config.colorbar_label_position)
        cbar.outline.set_visible(bool(config.colorbar_box))
    ax.set_aspect(config.aspect)
    ax.set_xlabel(config.xlabel or label_with_units(dataset.coordinates[0].label or dataset.axes[0], dataset.coordinates[0].units))
    ax.set_ylabel(config.ylabel or label_with_units(dataset.coordinates[1].label or dataset.axes[1], dataset.coordinates[1].units))
    ax.set_title(config.title or dataset.name)
    return ax


def label_with_units(label, units):
    return f"{label} [{units}]" if units else label
```

---

## `scientific_visualization/workflow.py`

```py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class WorkflowStage(str, Enum):
    SIMULATION="simulation"
    DATA="data"
    EXPLORATION="exploration"
    PHYSICS="physics"
    FEATURES="feature_engineering"
    ML="machine_learning"
    VALIDATION="validation"
    UNCERTAINTY="uncertainty_quantification"
    SURROGATE="surrogate_model"
    ACTIVE_LEARNING="active_learning"
    RECOMMEND="recommend_next_simulation"
    RETRAIN="retrain"

@dataclass
class WorkflowState:
    stage: WorkflowStage = WorkflowStage.DATA
    artifacts: dict[str, Any] = field(default_factory=dict)
    history: list[WorkflowStage] = field(default_factory=list)

    def advance(self, stage: WorkflowStage, **artifacts):
        self.stage=stage; self.artifacts.update(artifacts); self.history.append(stage); return self

class ScientificWorkflow:
    """Lightweight orchestration state. Heavy work remains in domain services."""
    def __init__(self): self.state=WorkflowState()
    def register(self, stage:WorkflowStage, **artifacts): return self.state.advance(stage, **artifacts)
```

---

## `tests/make_sample_files.py`

```py
"""Generate small synthetic HDF5 files that mimic Simulation output, purely for
testing the Python readers/GUI (no real Simulation files needed)."""
import os
import h5py
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "sample_data")
os.makedirs(OUT, exist_ok=True)


def make_grid_file(path, nx1=128, nx2=64, iteration=200, time=4.0):
    x1 = np.linspace(-10, 10, nx1, endpoint=False)
    x2 = np.linspace(-5, 5, nx2, endpoint=False)
    X2, X1 = np.meshgrid(x2, x1, indexing="ij")  # shape (nx2, nx1) -> matches HDF5 (slowest..fastest)
    data = np.sin(X1) * np.exp(-0.05 * X2 ** 2)

    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "e1"
        f.attrs["TYPE"] = "grid"
        f.attrs["TIME"] = time
        f.attrs["ITER"] = iteration
        f.attrs["UNITS"] = "m_e c omega_p e^-1"
        f.attrs["LABEL"] = "E_1"

        dset = f.create_dataset("e1", data=data.astype(np.float32))
        dset.attrs["UNITS"] = "m_e c omega_p e^-1"
        dset.attrs["LONG_NAME"] = "E_1"
        dset.attrs["TAG"] = "e1"

        axis = f.create_group("AXIS")
        a1 = axis.create_dataset("AXIS1", data=np.array([-10.0, 10.0]))
        a1.attrs["NAME"] = "x1"
        a1.attrs["UNITS"] = "c / omega_p"
        a1.attrs["LONG_NAME"] = "x_1"
        a2 = axis.create_dataset("AXIS2", data=np.array([-5.0, 5.0]))
        a2.attrs["NAME"] = "x2"
        a2.attrs["UNITS"] = "c / omega_p"
        a2.attrs["LONG_NAME"] = "x_2"


def make_particle_file(path, npar=5000, iteration=200, time=4.0):
    rng = np.random.default_rng(0)
    x1 = rng.normal(0, 2.0, npar)
    x2 = rng.normal(0, 1.0, npar)
    p1 = rng.normal(0, 0.5, npar) + 0.1 * x1
    p2 = rng.normal(0, 0.3, npar)
    ene = 0.5 * (p1 ** 2 + p2 ** 2)
    q = -np.ones(npar) / npar

    quants = ["x1", "x2", "p1", "p2", "ene", "q"]
    arrays = {"x1": x1, "x2": x2, "p1": p1, "p2": p2, "ene": ene, "q": q}
    labels = ["x_1", "x_2", "p_1", "p_2", "\\gamma - 1", "q"]
    units = ["c/\\omega_p", "c/\\omega_p", "m_e c", "m_e c", "m_e c^2", "e"]

    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "electrons"
        f.attrs["TIME"] = time
        f.attrs["ITER"] = iteration
        f.attrs["QUANTS"] = quants
        f.attrs["LABELS"] = labels
        f.attrs["UNITS"] = units
        for q_name in quants:
            f.create_dataset(q_name, data=arrays[q_name].astype(np.float32))


def make_tracks_file(path, ntracks=10, npoints=100):
    rng = np.random.default_rng(1)
    quants = ["t", "x1", "x2", "p1", "p2", "ene"]
    rows = []
    counts = []
    starts = []
    for i in range(ntracks):
        t = np.arange(npoints) * 0.5
        phase = rng.uniform(0, 2 * np.pi)
        x1 = 2.0 * np.sin(0.05 * t + phase) + rng.normal(0, 0.05, npoints).cumsum() * 0.02
        x2 = 0.1 * t + rng.normal(0, 0.2)
        p1 = 0.05 * np.cos(0.05 * t + phase)
        p2 = np.full(npoints, 0.1 * rng.normal())
        ene = 0.5 * (p1 ** 2 + p2 ** 2)
        block = np.stack([t, x1, x2, p1, p2, ene], axis=1)
        rows.append(block)
        counts.append(npoints)
        starts.append(0)

    data = np.concatenate(rows, axis=0).astype(np.float64)
    itermap = np.array([[s, c] for s, c in zip(starts, counts)], dtype=np.int32)

    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "electrons-tracks"
        f.attrs["NTRACKS"] = ntracks
        f.attrs["NDUMP"] = 1
        f.attrs["DT"] = 0.5
        f.attrs["QUANTS"] = quants
        f.attrs["LABELS"] = quants
        f.attrs["UNITS"] = ["1/\\omega_p", "c/\\omega_p", "c/\\omega_p", "m_ec", "m_ec", "m_ec^2"]
        f.create_dataset("data", data=data)
        f.create_dataset("itermap", data=itermap)


def make_grid_series(folder, n=10):
    """A short time series of grid files, with an amplitude that grows then
    decays, for testing the 'time series (reduced over space)' feature."""
    os.makedirs(folder, exist_ok=True)
    for i in range(n):
        it = i * 100
        t = i * 2.0
        amp = np.sin(np.pi * i / (n - 1)) * 2.0  # rises then falls
        nx1, nx2 = 128, 64
        x1 = np.linspace(-10, 10, nx1, endpoint=False)
        x2 = np.linspace(-5, 5, nx2, endpoint=False)
        X2, X1 = np.meshgrid(x2, x1, indexing="ij")
        data = amp * np.sin(X1) * np.exp(-0.05 * X2 ** 2)

        path = os.path.join(folder, f"b3-{it:06d}.h5")
        with h5py.File(path, "w") as f:
            f.attrs["NAME"] = "b3"
            f.attrs["TIME"] = t
            f.attrs["ITER"] = it
            f.attrs["UNITS"] = "m_e c omega_p e^-1"
            f.attrs["LABEL"] = "B_3"
            dset = f.create_dataset("b3", data=data.astype(np.float32))
            dset.attrs["UNITS"] = "m_e c omega_p e^-1"
            dset.attrs["LONG_NAME"] = "B_3"
            axis = f.create_group("AXIS")
            a1 = axis.create_dataset("AXIS1", data=np.array([-10.0, 10.0]))
            a1.attrs["NAME"] = "x1"; a1.attrs["UNITS"] = "c / omega_p"; a1.attrs["LONG_NAME"] = "x_1"
            a2 = axis.create_dataset("AXIS2", data=np.array([-5.0, 5.0]))
            a2.attrs["NAME"] = "x2"; a2.attrs["UNITS"] = "c / omega_p"; a2.attrs["LONG_NAME"] = "x_2"


if __name__ == "__main__":
    make_grid_file(os.path.join(OUT, "e1-000200.h5"))
    make_particle_file(os.path.join(OUT, "electrons-000200.h5"))
    make_tracks_file(os.path.join(OUT, "electrons-tracks.h5"))
    make_grid_series(os.path.join(OUT, "b3_series"))
    print("Sample files written to", OUT)
```

---

## `tests/test_3d_to_2d_slicing.py`

```py
"""Tests for opening 3D grid files in the 2D view.

Regression coverage for a real crash: a 3D Simulation file (e.g. a "thin"
run with only a couple of grid points along one axis) selected while the
Grid tab was in "2D map" mode used to be passed straight to
`ax.imshow()` as a 3D array, raising "Invalid shape (...) for image data"
instead of being viewable at all.

The fix has two parts, tested separately:
  * `GridFile.slice2d` (io/grid.py): a pure, GUI-independent slicing
    operation on the data model.
  * `GridTab._effective_2d_grid` / the new "3D slice" control group
    (gui/grid_tab.py): wires user-selected slice axis/index into the
    existing 2D plotting code path.
"""
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from scientific_visualization.io.grid import GridFile


def _make_3d_grid_file(tmp_path, shape=(2, 6, 5), axis_names=("x", "y", "z")):
    """shape is in numpy/HDF5 order: (n_x3, n_x2, n_x1)."""
    p = tmp_path / "b1-000005.h5"
    n_x3, n_x2, n_x1 = shape
    data = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "b1"; f.attrs["TIME"] = 0.14; f.attrs["ITER"] = 5
        f.attrs["LABEL"] = "B_1"; f.attrs["UNITS"] = "m_e omega_p e^-1"
        d = f.create_dataset("b1", data=data)
        d.attrs["UNITS"] = "m_e omega_p e^-1"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, float(n_x1)]); a1.attrs["NAME"] = axis_names[0]
        a2 = g.create_dataset("AXIS2", data=[0.0, float(n_x2)]); a2.attrs["NAME"] = axis_names[1]
        a3 = g.create_dataset("AXIS3", data=[0.0, float(n_x3)]); a3.attrs["NAME"] = axis_names[2]
    return str(p)


def _make_2d_grid_file(tmp_path, shape=(10, 10)):
    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.random.RandomState(0).rand(*shape).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    return str(p)


# --- GridFile.slice2d ---

def test_slice2d_matches_raw_numpy_indexing(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))  # x3 has only 2 points
    gf = GridFile.load(path)
    assert gf.ndim == 3
    assert gf.axes[2].n == 2  # x3 (the outermost/slowest numpy axis) is the thin one

    for idx in range(gf.axes[2].n):
        sliced = gf.slice2d(axis=2, index=idx)
        assert sliced.ndim == 2
        assert sliced.shape == (gf.axes[1].n, gf.axes[0].n)
        np.testing.assert_array_equal(sliced.data, gf.data[idx, :, :])
        # remaining axes preserve order: fastest-varying first
        assert [a.name for a in sliced.axes] == [gf.axes[0].name, gf.axes[1].name]


def test_slice2d_all_three_axes_are_consistent_with_raw_indexing(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(3, 4, 5))
    gf = GridFile.load(path)
    for axis in (0, 1, 2):
        np_axis = gf.ndim - 1 - axis
        for idx in range(gf.axes[axis].n):
            sliced = gf.slice2d(axis=axis, index=idx)
            expected = np.take(gf.data, idx, axis=np_axis)
            np.testing.assert_array_equal(sliced.data, expected)


def test_slice2d_to_dataset_has_correct_shape_and_axes(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    sliced = gf.slice2d(axis=2, index=0)
    ds = sliced.to_dataset()
    assert ds.data.shape == (5, 6)  # physical order: (x1, x2)
    assert ds.axes == ("x", "y")


def test_slice2d_label_records_the_fixed_axis_and_value(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    sliced = gf.slice2d(axis=2, index=1)
    assert "z" in sliced.label
    assert "slice" in sliced.label.lower()


def test_slice2d_rejects_wrong_dimensionality(tmp_path):
    path = _make_2d_grid_file(tmp_path)
    gf = GridFile.load(path)
    with pytest.raises(ValueError, match="3D"):
        gf.slice2d(axis=0, index=0)


def test_slice2d_rejects_out_of_range_index(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    with pytest.raises(ValueError, match="out of range"):
        gf.slice2d(axis=2, index=99)
    with pytest.raises(ValueError):
        gf.slice2d(axis=2, index=-1)


def test_slice2d_rejects_invalid_axis(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.load(path)
    with pytest.raises(ValueError, match="axis"):
        gf.slice2d(axis=5, index=0)


def test_slice2d_requires_loaded_data(tmp_path):
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    gf = GridFile.info(path)  # metadata only
    with pytest.raises(ValueError, match="not loaded"):
        gf.slice2d(axis=2, index=0)


# --- GridTab wiring ---

@pytest.fixture
def grid_tab_3d(tmp_path):
    from scientific_visualization.gui.grid_tab import GridTab
    path = _make_3d_grid_file(tmp_path, shape=(2, 6, 5))
    tab = GridTab()
    tab.files = [path]
    tab.file_list.addItem("b1-000005.h5")
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    return tab


def test_grid_tab_shows_slice_controls_for_3d_file(grid_tab_3d):
    assert grid_tab_3d.grid.ndim == 3
    # auto-selects the axis with the fewest points (x3, the "thin" one)
    assert grid_tab_3d.slice_axis.currentIndex() == 2
    assert grid_tab_3d.slice_index.maximum() == 1


def test_grid_tab_hides_slice_controls_for_2d_file(tmp_path):
    from scientific_visualization.gui.grid_tab import GridTab
    path = _make_2d_grid_file(tmp_path)
    tab = GridTab()
    tab.files = [path]
    tab.file_list.addItem("e1-000000.h5")
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    assert tab.grid.ndim == 2
    assert tab.slice_box.property("_auto_selected_for") is None or not tab.slice_box.isVisibleTo(tab.slice_box.window())


def test_grid_tab_2d_mode_renders_a_3d_file_without_crashing(grid_tab_3d):
    grid_tab_3d.mode_2d.setChecked(True)
    grid_tab_3d.refresh_plot()
    assert grid_tab_3d._image is not None
    assert grid_tab_3d._image.get_array().shape == (6, 5)  # x2 by x1, sliced at x3


def test_grid_tab_changing_slice_axis_updates_the_rendered_shape(grid_tab_3d):
    grid_tab_3d.mode_2d.setChecked(True)
    grid_tab_3d.slice_axis.setCurrentIndex(0)  # slice out x1 (5 points) instead
    grid_tab_3d.refresh_plot()
    assert grid_tab_3d._image.get_array().shape == (2, 6)  # x3 by x2


def test_grid_tab_changing_slice_index_changes_the_data(grid_tab_3d):
    grid_tab_3d.mode_2d.setChecked(True)
    grid_tab_3d.refresh_plot()
    data_at_0 = grid_tab_3d._image.get_array().copy()
    grid_tab_3d.slice_index.setValue(1)
    grid_tab_3d.refresh_plot()
    data_at_1 = grid_tab_3d._image.get_array()
    assert not np.array_equal(data_at_0, data_at_1)


def test_grid_tab_manual_ranges_track_the_remaining_axes_after_slicing(grid_tab_3d):
    # Default slice axis is x3 (index 2); remaining axes are x(=x1), y(=x2).
    assert grid_tab_3d.x_range_min.value() == pytest.approx(0.0)
    assert grid_tab_3d.x_range_max.value() == pytest.approx(5.0)
    assert grid_tab_3d.y_range_min.value() == pytest.approx(0.0)
    assert grid_tab_3d.y_range_max.value() == pytest.approx(6.0)

    grid_tab_3d.slice_axis.setCurrentIndex(0)  # now slicing out x1; remaining (in order) are x2, x3
    assert grid_tab_3d.x_range_max.value() == pytest.approx(6.0)
    assert grid_tab_3d.y_range_max.value() == pytest.approx(2.0)


def test_grid_tab_slice_coord_label_reports_physical_position(grid_tab_3d):
    text = grid_tab_3d.slice_coord_label.text()
    assert "z" in text
    assert "index 0 of 2" in text
```

---

## `tests/test_architecture.py`

```py
from pathlib import Path

import numpy as np
import pytest

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.io.hdf5.generic import discover_hdf5_datasets, validate_file
from scientific_visualization.io.simulation import SimulationReader
from scientific_visualization.analysis import DerivedQuantityEngine, LineoutAnalyzer, statistics, reduce_grid_series
from scientific_visualization.visualization.two_d import plot_2d

DATA = Path(__file__).parent / "sample_data"


def test_simulation_grid_to_dataset_physical_axis_order():
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    assert ds.ndim == 2
    assert ds.axes == ("x1", "x2")
    assert ds.shape == (128, 64)
    assert ds.coordinates[0].size == 128
    assert ds.coordinates[1].size == 64


def test_coordinate_lineout_and_statistics():
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    x, y = LineoutAnalyzer().lineout(ds, axis="x1", position=0.0)
    assert x.shape == (128,)
    assert y.shape == (128,)
    stats = statistics(y)
    assert stats["count"] == 128


def test_derived_quantity():
    c = CoordinateAxis("x1", np.arange(4.0))
    a = Dataset("A", np.arange(4.0), ("x1",), (c,))
    b = Dataset("B", np.ones(4), ("x1",), (c,))
    out = DerivedQuantityEngine().binary("add", a, b)
    np.testing.assert_allclose(out.data, [1,2,3,4])


def test_generic_discovery():
    result = discover_hdf5_datasets(DATA / "e1-000200.h5")
    assert any(d.name == "e1" for d in result)



def test_simulation_scalar_array_metadata(tmp_path):
    import h5py
    import numpy as np
    p = tmp_path / "array_metadata.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"
        f.attrs["TIME"] = np.asarray([2.5])
        f.attrs["ITER"] = np.asarray([123])
        f.attrs["UNITS"] = "arb"
        f.create_dataset("e1", data=np.ones((4, 8), dtype=np.float32))
        axis = f.create_group("AXIS")
        axis.create_dataset("AXIS1", data=np.asarray([0.0, 1.0]))
        axis.create_dataset("AXIS2", data=np.asarray([0.0, 2.0]))
    from scientific_visualization.io.grid import GridFile
    info = GridFile.info(p)
    assert info.time == 2.5
    assert info.iteration == 123


def test_invalid_hdf5_is_reported(tmp_path):
    p = tmp_path / "bad.h5"
    p.write_bytes(b"not an hdf5 file")
    with pytest.raises(ValueError, match="Invalid or truncated HDF5"):
        validate_file(p)


def test_time_series_reduction():
    files = sorted((DATA / "b3_series").glob("*.h5"))
    times, _, values, _ = reduce_grid_series(files, reduction="mean")
    assert len(times) == len(files)
    assert values.shape == times.shape


def test_plot_2d_noninteractive():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    ax = plot_2d(ds)
    assert len(ax.images) == 0
    fig = ax.figure
    fig.savefig(Path("/tmp/scientific_visualization_test_plot.png"), dpi=80)
    plt.close(fig)


def test_ml_feature_extraction():
    from scientific_visualization.ml import dataset_to_features
    ds = SimulationReader().load(DATA / "e1-000200.h5")
    fs = dataset_to_features(ds, include_coordinates=True)
    assert fs.values.shape[0] == ds.data.size
    assert fs.values.shape[1] == 3


def test_ml_pca_optional():
    from scientific_visualization.ml import PCAAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    fs = FeatureSet(np.random.default_rng(0).normal(size=(20, 3)), ("a", "b", "c"))
    result = PCAAnalyzer(2).fit_transform(fs)
    assert result.output.shape == (20, 2)


def test_main_application_imports():
    pytest.importorskip("PyQt5")
    from scientific_visualization.app import main
    assert callable(main)


def test_ml_regression_training():
    from scientific_visualization.ml import RegressionAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    rng = np.random.default_rng(1)
    X = rng.normal(size=(60, 3))
    y = X[:, 0] * 2.0 + X[:, 1] * 0.5 + rng.normal(scale=0.1, size=60)
    result = RegressionAnalyzer(test_size=0.25).fit_predict(FeatureSet(X, ("x", "y", "z")), y)
    assert result.output.shape[0] == 15
    assert result.metadata["metrics"]["r2"] > 0.5


def test_animation_gif_export(tmp_path):
    from scientific_visualization.export.animation import export_grid_movie
    files = sorted((DATA / "b3_series").glob("*.h5"))[:3]
    out = tmp_path / "movie.gif"
    n = export_grid_movie(files, out, fps=4, dpi=50)
    assert n == 3
    assert out.exists() and out.stat().st_size > 0


def test_2d_to_3d_geometry_helpers():
    import numpy as np
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")
    c1 = CoordinateAxis("x1", np.linspace(0, 1, 4))
    c2 = CoordinateAxis("x2", np.linspace(-1, 1, 3))
    ds = Dataset("E1", np.arange(12, dtype=float).reshape(4, 3), ("x1", "x2"), (c1, c2))
    r = ThreeDRenderer(pv.Plotter(off_screen=True))
    plane = r.add_2d_plane(ds, plane_axis="x3", position=2.0)
    surf = r.add_2d_surface(ds, height_axis="x3", base_position=0.5, z_scale=2.0)
    ext = r.add_2d_extrusion(ds, extrusion_axis="x3", depth=3.0)
    assert plane is not None and surf is not None and ext is not None


def test_ml_gradient_boosting_and_neural_network():
    from scientific_visualization.ml import GradientBoostingRegressorAnalyzer, NeuralNetworkRegressorAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    rng = np.random.default_rng(5)
    X = rng.normal(size=(90, 4))
    y = 2 * X[:, 0] - 0.7 * X[:, 1] + 0.3 * X[:, 2] ** 2
    fs = FeatureSet(X, ("x1", "x2", "x3", "x4"))
    gb = GradientBoostingRegressorAnalyzer(n_estimators=50).fit_predict(fs, y, test_size=0.2, cv_folds=3)
    assert gb.metadata["metrics"]["r2"] > 0.5
    assert len(gb.metadata["feature_importances"]) == 4
    nn = NeuralNetworkRegressorAnalyzer(hidden_layers=(24, 12), max_iter=250, early_stopping=False).fit_predict(fs, y, test_size=0.2, cv_folds=0)
    assert nn.metadata["metrics"]["r2"] > 0.5
    assert len(nn.metadata["loss_curve"]) > 0


def test_ml_autoencoder():
    from scientific_visualization.ml import AutoencoderAnalyzer, FeatureSet, estimator_available
    if not estimator_available():
        pytest.skip("scikit-learn not installed")
    rng = np.random.default_rng(6)
    X = rng.normal(size=(50, 5))
    result = AutoencoderAnalyzer(bottleneck=3, max_iter=60).fit_transform(FeatureSet(X, tuple(f"x{i}" for i in range(5))))
    assert result.output.shape == X.shape
    assert result.metadata["reconstruction_error"].shape == (50,)

def test_simulation_series_ai_and_spectral():
    from pathlib import Path
    from scientific_visualization.analysis.ai import AIAnalysisEngine
    from scientific_visualization.analysis.spectral import fft_1d, k_omega
    files = sorted(str(p) for p in Path('tests/sample_data/b3_series').glob('*.h5'))
    report = AIAnalysisEngine().analyze_series(files=files, quantity='b3', max_frames=100)
    assert report['n_files_discovered'] == 10
    assert report['n_frames_analyzed'] == 10
    assert report['times'].size == 10

    x = np.linspace(0, 1, 128, endpoint=False)
    y = np.sin(2*np.pi*5*x)
    spec = fft_1d(y, x)
    assert abs(float(spec.frequencies[np.argmax(spec.power[1:])+1]) - 5.0) < 1e-9


def test_coordinate_aware_integral_and_komega():
    import numpy as np
    from scientific_visualization.analysis.spectral import k_omega
    from scientific_visualization.io.grid import GridFile
    gf = GridFile.load('tests/sample_data/b3_series/b3-000000.h5')
    # The integral path must use physical coordinates and remain finite.
    from scientific_visualization.analysis.time_series import reduce_grid_series
    t, it, vals, meta = reduce_grid_series([gf.filename], reduction='integral', quantity='b3')
    assert np.isfinite(vals[0])
    x = np.linspace(0, 1, 64, endpoint=False)
    times = np.arange(32)*0.1
    field = np.sin(2*np.pi*2*times)[:, None] * np.sin(2*np.pi*4*x)[None, :]
    omega, k, power = k_omega(field, x, times)
    assert power.shape == (len(omega), len(k))
```

---

## `tests/test_colorbar_features.py`

```py
"""Tests for the 2D colorbar fixes/features and 3D scalar-bar options.

Covers:
  * The reverse-colormap bug: `_plot_2d` used to unconditionally overwrite
    the plain matplotlib colormap selection with a hard-coded custom
    palette, so the "Reverse legacy matplotlib colormap" checkbox had no
    visible effect. Fixed by adding a sentinel ("use Colormap dropdown")
    to the palette preset list, defaulted so the plain colormap path is
    live out of the box.
  * 2D colorbar position (right/left/top/bottom) and box/outline toggle.
  * 2D colorbar drag-to-move via mouse press/motion/release, without
    breaking the existing "plain click opens the color-range dialog"
    behavior.
  * 3D scalar bar position/box/interactive options (PyVista backend).
"""
import os
import tempfile

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])


def _make_sample_grid_file(tmp_path, shape=(20, 16)):
    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.linspace(0, 1, shape[0] * shape[1]).reshape(shape).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    return str(p)


class _FakeMplEvent:
    def __init__(self, x, y, inaxes=None, xdata=None, ydata=None):
        self.x = x; self.y = y; self.inaxes = inaxes; self.xdata = xdata; self.ydata = ydata


@pytest.fixture
def grid_tab(tmp_path):
    from scientific_visualization.gui.grid_tab import GridTab, USE_LEGACY_CMAP
    from scientific_visualization.io.grid import GridFile

    path = _make_sample_grid_file(tmp_path)
    tab = GridTab()
    tab.grid = GridFile.load(path)
    tab.files = [path]
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    return tab


def test_palette_combo_defaults_to_legacy_colormap_sentinel(grid_tab):
    from scientific_visualization.gui.grid_tab import USE_LEGACY_CMAP
    assert grid_tab.palette_combo.currentText() == USE_LEGACY_CMAP


def test_reverse_legacy_colormap_checkbox_actually_changes_the_plot(grid_tab):
    """Regression test: this checkbox used to be silently overridden and
    had zero effect on the rendered colormap."""
    cmap_before = grid_tab._image.get_cmap().name
    grid_tab.reverse_cmap.setChecked(True)
    grid_tab.refresh_plot()
    cmap_after = grid_tab._image.get_cmap().name
    assert cmap_after != cmap_before
    assert cmap_after.endswith("_r")

    grid_tab.reverse_cmap.setChecked(False)
    grid_tab.refresh_plot()
    assert grid_tab._image.get_cmap().name == cmap_before


def test_custom_palette_preset_still_works_when_explicitly_selected(grid_tab):
    """Choosing an actual palette preset (not the sentinel) should still
    render via the custom palette system, unaffected by reverse_cmap."""
    from scientific_visualization.rendering_colors import ALL_PALETTES
    preset_name = next(iter(ALL_PALETTES))
    grid_tab.palette_combo.setCurrentText(preset_name)
    grid_tab.refresh_plot()
    cmap_before = grid_tab._image.get_cmap()
    grid_tab.palette_reverse.setChecked(True)
    grid_tab.refresh_plot()
    cmap_after = grid_tab._image.get_cmap()
    # Reversing a custom palette changes its color sequence.
    assert not np.array_equal(cmap_before(np.linspace(0, 1, 8)), cmap_after(np.linspace(0, 1, 8)))


@pytest.mark.parametrize("position,expected_orientation", [
    ("right", "vertical"), ("left", "vertical"), ("top", "horizontal"), ("bottom", "horizontal"),
])
def test_colorbar_position_sets_orientation(grid_tab, position, expected_orientation):
    grid_tab.cbar_position.setCurrentText(position)
    assert grid_tab._cbar is not None
    assert grid_tab._cbar.orientation == expected_orientation


def test_colorbar_box_toggle_controls_outline_visibility(grid_tab):
    grid_tab.cbar_box.setChecked(False)
    grid_tab.refresh_plot()
    assert grid_tab._cbar.outline.get_visible() is False
    grid_tab.cbar_box.setChecked(True)
    grid_tab.refresh_plot()
    assert grid_tab._cbar.outline.get_visible() is True


def test_dragging_the_colorbar_moves_it_and_suppresses_the_click_dialog(grid_tab, monkeypatch):
    cbar_ax = grid_tab._cbar.ax
    orig_bounds = cbar_ax.get_position().bounds

    dialog_opened = {"count": 0}
    from scientific_visualization.gui import grid_tab as grid_tab_module

    class _ExplodingDialog:
        def __init__(self, *a, **kw):
            dialog_opened["count"] += 1
        def exec_(self):
            raise AssertionError("Color-range dialog should not open for a drag")

    monkeypatch.setattr(grid_tab_module, "ColorRangeDialog", _ExplodingDialog)

    grid_tab._on_canvas_press(_FakeMplEvent(100, 100, inaxes=cbar_ax))
    assert grid_tab._cbar_drag is not None
    grid_tab._on_canvas_motion(_FakeMplEvent(150, 130, inaxes=cbar_ax))
    assert grid_tab._press_info["moved"] is True
    moved_bounds = cbar_ax.get_position().bounds
    assert moved_bounds != orig_bounds

    grid_tab._on_canvas_release(_FakeMplEvent(150, 130, inaxes=cbar_ax))
    assert dialog_opened["count"] == 0
    # position persists after release
    assert tuple(cbar_ax.get_position().bounds) == moved_bounds


def test_plain_click_without_drag_still_opens_color_range_dialog(grid_tab, monkeypatch):
    cbar_ax = grid_tab._cbar.ax
    dialog_opened = {"count": 0}
    from scientific_visualization.gui import grid_tab as grid_tab_module

    class _FakeDialog:
        Accepted = 1
        def __init__(self, *a, **kw):
            dialog_opened["count"] += 1
        def exec_(self):
            return 0  # Rejected, so refresh_plot's state isn't touched further
        vmin = type("W", (), {"value": lambda self: 0.0})()
        vmax = type("W", (), {"value": lambda self: 1.0})()

    monkeypatch.setattr(grid_tab_module, "ColorRangeDialog", _FakeDialog)

    grid_tab._on_canvas_press(_FakeMplEvent(100, 100, inaxes=cbar_ax))
    # no motion event at all -> not a drag
    grid_tab._on_canvas_release(_FakeMplEvent(100, 100, inaxes=cbar_ax))
    assert dialog_opened["count"] == 1


def test_colorbar_drag_does_not_move_when_clicking_outside_colorbar(grid_tab):
    ax = grid_tab.canvas.figure.axes[0]
    grid_tab._on_canvas_press(_FakeMplEvent(10, 10, inaxes=ax))
    assert grid_tab._cbar_drag is None


# --- 3D scalar bar (PyVista) ---

def test_three_d_scalar_bar_position_and_box_options():
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.core.configuration import RenderingConfig
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")

    c1 = CoordinateAxis("x1", np.linspace(0, 1, 4))
    c2 = CoordinateAxis("x2", np.linspace(-1, 1, 3))
    ds = Dataset("E1", np.arange(12, dtype=float).reshape(4, 3), ("x1", "x2"), (c1, c2))

    # Reuse a single off-screen plotter across positions rather than
    # creating/destroying many VTK render windows in one process, which is
    # unnecessary here and can be unreliable under software rendering.
    plotter = pv.Plotter(off_screen=True)
    try:
        for position in ("right", "left", "top", "bottom"):
            plotter.clear()
            renderer = ThreeDRenderer(plotter)
            cfg = RenderingConfig(colorbar_position=position, colorbar_box=True, colorbar_interactive=True)
            renderer.add_2d_plane(ds, plane_axis="x3", position=0.0, config=cfg)
            assert "E1" in plotter.scalar_bars
    finally:
        plotter.close()


def test_three_d_scalar_bar_can_be_hidden():
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.core.configuration import RenderingConfig
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")
    c1 = CoordinateAxis("x1", np.linspace(0, 1, 4))
    c2 = CoordinateAxis("x2", np.linspace(-1, 1, 3))
    ds = Dataset("E1", np.arange(12, dtype=float).reshape(4, 3), ("x1", "x2"), (c1, c2))
    plotter = pv.Plotter(off_screen=True)
    renderer = ThreeDRenderer(plotter)
    cfg = RenderingConfig(show_colorbar=False)
    renderer.add_2d_plane(ds, plane_axis="x3", position=0.0, config=cfg)
    assert "E1" not in plotter.scalar_bars
    plotter.close()


def test_rendering_config_rejects_invalid_colorbar_position():
    from scientific_visualization.core.configuration import RenderingConfig
    with pytest.raises(ValueError, match="colorbar_position"):
        RenderingConfig(colorbar_position="diagonal").validate()
```

---

## `tests/test_data_plotter_parser.py`

```py
from pathlib import Path
import numpy as np
import pytest
from scientific_visualization.data_plotter.parser import Delimiter, parse_text_file

def test_parse_csv_with_header_comments_and_invalid(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_text("# comment\nTime,Energy\n0,1\n1,bad\n2,3\n", encoding="utf-8")
    result = parse_text_file(p, Delimiter.AUTO)
    assert result.has_header is True
    assert result.columns == ["Time", "Energy"]
    assert result.skipped_comments == 1
    assert np.isnan(result.values[1, 1])

def test_parse_whitespace_txt_without_header(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("0 1\n1 2\n2 3\n", encoding="utf-8")
    result = parse_text_file(p)
    assert result.has_header is False
    assert result.values.shape == (3, 2)
    assert result.delimiter == " "

def test_parse_empty_file_fails(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        parse_text_file(p)
```

---

## `tests/test_data_plotter_renderer.py`

```py
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
```

---

## `tests/test_data_plotter_transform.py`

```py
import numpy as np
from scientific_visualization.data_plotter.transform import TransformPipeline, apply_transforms

def test_transform_pipeline_does_not_modify_inputs():
    x = np.array([1., 2., 3.])
    y = np.array([2., 4., 8.])
    xx, yy = apply_transforms(x, y, TransformPipeline(x_scale=0.1, y_scale=2, y_offset=-1))
    assert np.allclose(x, [1, 2, 3])
    assert np.allclose(y, [2, 4, 8])
    assert np.allclose(xx, [0.1, 0.2, 0.3])
    assert np.allclose(yy, [3, 7, 15])

def test_normalization():
    _, yy = apply_transforms([0, 1], [2, 4], TransformPipeline(normalize_y="max"))
    assert np.allclose(yy, [0.5, 1.0])

def test_invalid_normalization_fails():
    try:
        apply_transforms([0, 1], [1, 2], TransformPipeline(normalize_y="bad"))
    except ValueError as exc:
        assert "Unknown Y normalization" in str(exc)
    else:
        raise AssertionError("invalid normalization was accepted")
```

---

## `tests/test_directional_average.py`

```py
import numpy as np
from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.analysis.derived import DerivedQuantityEngine, parse_average_direction
from scientific_visualization.analysis import reduce_grid_series


def make_dataset():
    a = np.arange(24, dtype=float).reshape(2,3,4)
    coords = tuple(CoordinateAxis(f'x{i+1}', np.arange(n, dtype=float)) for i,n in enumerate(a.shape))
    return Dataset('f', a, ('x1','x2','x3'), coords, units='u')


def test_parse_directions():
    assert parse_average_direction('average,dir=x') == ('x',)
    assert parse_average_direction('(x,y,z)') == ('x','y','z')


def test_directional_average_shapes_and_values():
    ds=make_dataset(); eng=DerivedQuantityEngine()
    ax=eng.directional_average(ds,'x')
    assert ax.shape==(3,4); np.testing.assert_allclose(ax.data, ds.data.mean(axis=0))
    all_=eng.directional_average(ds,'average,dir=(x,y,z)')
    assert all_.data.shape==(); np.testing.assert_allclose(all_.data, ds.data.mean())
```

---

## `tests/test_fast_3d_helpers.py`

```py
import numpy as np
from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.core.configuration import RenderingConfig

def _ds(shape=(12, 10, 8)):
    coords = tuple(CoordinateAxis(f"x{i+1}", np.linspace(0, 1, n)) for i, n in enumerate(shape))
    x = np.linspace(0, 1, shape[0])[:,None,None]
    y = np.linspace(0, 1, shape[1])[None,:,None]
    z = np.linspace(0, 1, shape[2])[None,None,:]
    data = (x + 2*y + 3*z).astype(np.float32)
    return Dataset("f", data, ("x1","x2","x3"), coords)

def test_rendering_config_accepts_scalar_bar_size_and_fast_resolution():
    cfg = RenderingConfig(colorbar_width=.22, colorbar_height=.65, render_decimation=.5)
    cfg.validate()

def test_rendering_config_rejects_invalid_scalar_bar_size():
    import pytest
    with pytest.raises(ValueError): RenderingConfig(colorbar_width=1.1).validate()

def test_renderer_grid_cache_reuses_regular_grid():
    import pytest
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None: pytest.skip("pyvista not installed")
    p = pv.Plotter(off_screen=True)
    try:
        r=ThreeDRenderer(p); ds=_ds()
        a=r._build_3d_grid(ds); b=r._build_3d_grid(ds)
        assert a is b
        assert isinstance(a, pv.ImageData)
    finally: p.close()

def test_threshold_produces_mesh_for_in_range_values():
    import pytest
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None: pytest.skip("pyvista not installed")
    p=pv.Plotter(off_screen=True)
    try:
        r=ThreeDRenderer(p); ds=_ds(); a=r.add_threshold(ds, lower=1.0, upper=3.0)
        assert a is not None
    finally: p.close()
```

---

## `tests/test_gui_contracts.py`

```py
from pathlib import Path

from scientific_visualization.io.grid import GridFile

DATA = Path(__file__).parent / "sample_data" / "e1-000200.h5"

def test_grid_metadata_is_safe_without_loading_field():
    grid = GridFile.info(DATA)
    assert grid.data is None
    assert grid.shape == (64, 128)
    assert grid.name
    # The shared model requires data, so conversion is intentionally deferred.
    try:
        grid.to_dataset()
    except ValueError as exc:
        assert "data not loaded" in str(exc)
    else:
        raise AssertionError("metadata-only GridFile unexpectedly converted to Dataset")
```

---

## `tests/test_jax_physics_backend.py`

```py
"""Correctness tests for the optional JAX physics backend.

`jax_backend.py`'s own docstring promises these checks exist; they didn't
(this file was missing entirely, discovered while investigating a startup
performance bug -- see native_backend.py's lazy-import fix). Every JAX
kernel here is checked against the same pure-NumPy reference formulas used
to validate the native C++ backend, so switching backends is guaranteed to
never silently change a scientific result.

All tests are skipped (not failed) if JAX isn't installed, since it's an
optional dependency.
"""
import numpy as np
import pytest

from scientific_visualization.physics import native_backend as nb

jax_backend = pytest.importorskip(
    "scientific_visualization.physics.jax_backend",
    reason="JAX is an optional dependency",
)

if not jax_backend.JAX_AVAILABLE:
    pytest.skip("jax package not installed", allow_module_level=True)


@pytest.fixture(autouse=True)
def _restore_backend():
    """Every test in this file explicitly selects a backend; always
    restore the global default afterwards so other test modules aren't
    affected by test execution order."""
    original = nb.get_backend()
    yield
    nb.set_backend(original)


def test_jax_available_flag_matches_actual_import():
    assert nb.JAX_AVAILABLE is True
    assert jax_backend.JAX_AVAILABLE is True


def test_set_backend_jax_then_auto_round_trips():
    nb.set_backend("jax")
    assert nb.get_backend() == "jax"
    assert "JAX" in nb.backend_name()
    nb.set_backend("auto")
    assert nb.get_backend() == "auto"


def test_backend_summary_reports_a_device():
    summary = jax_backend.backend_summary()
    assert "JAX" in summary
    assert jax_backend.device_name() != "unavailable"


@pytest.mark.parametrize("shape", [(37,), (21, 17), (14, 11, 9)])
def test_jax_gradient_matches_np_gradient(shape):
    rng = np.random.RandomState(1)
    data = rng.rand(*shape)
    h = 0.37
    for axis in range(len(shape)):
        coord = np.arange(shape[axis]) * h
        order = 2 if shape[axis] > 2 else 1
        expected = np.gradient(data, coord, axis=axis, edge_order=order)
        got = jax_backend.gradient_uniform(data, h, axis, edge_order=2)
        assert np.allclose(got, expected, atol=1e-8)


def test_jax_gradient_matches_numpy_fallback_exactly():
    rng = np.random.RandomState(2)
    data = rng.rand(12, 9, 7)
    h = 0.2
    jax_result = jax_backend.gradient_uniform(data, h, axis=1, edge_order=2)
    numpy_result = nb._np_gradient_pass(data, h, axis=1, edge_order=2)
    assert np.allclose(jax_result, numpy_result, atol=1e-8)


def test_jax_divergence_matches_numpy_fallback():
    rng = np.random.RandomState(3)
    shape = (16, 14, 12)
    comps = [rng.rand(*shape) for _ in range(3)]
    spacings = [0.1, 0.2, 0.15]
    jax_result = jax_backend.divergence_uniform(comps, spacings)
    numpy_result = sum(
        nb._np_gradient_pass(c, h, axis, 2) for axis, (c, h) in enumerate(zip(comps, spacings))
    )
    assert np.allclose(jax_result, numpy_result, atol=1e-8)


def test_jax_divergence_matches_native_backend():
    rng = np.random.RandomState(3)
    shape = (16, 14, 12)
    comps = [rng.rand(*shape) for _ in range(3)]
    spacings = [0.1, 0.2, 0.15]
    jax_result = jax_backend.divergence_uniform(comps, spacings)
    native_result = nb.divergence_uniform(comps, spacings)  # uses whatever backend was active
    assert np.allclose(jax_result, native_result, atol=1e-8)


def test_jax_laplacian_matches_numpy_fallback():
    rng = np.random.RandomState(4)
    data = rng.rand(18, 13, 10)
    spacings = [0.1, 0.2, 0.15]
    jax_result = jax_backend.laplacian_uniform(data, spacings)
    total = np.zeros_like(data)
    for axis, h in enumerate(spacings):
        first = nb._np_gradient_pass(data, h, axis, 2)
        total += nb._np_gradient_pass(first, h, axis, 2)
    assert np.allclose(jax_result, total, atol=1e-7)


def test_jax_curl_matches_numpy_fallback():
    rng = np.random.RandomState(5)
    shape = (12, 10, 8)
    c1, c2, c3 = rng.rand(*shape), rng.rand(*shape), rng.rand(*shape)
    h1, h2, h3 = 0.1, 0.2, 0.15
    jax_result = jax_backend.curl_uniform_3d(c1, c2, c3, h1, h2, h3)

    d = lambda arr, axis, h: nb._np_gradient_pass(arr, h, axis, 2)
    expected = (
        d(c3, 1, h2) - d(c2, 2, h3),
        d(c1, 2, h3) - d(c3, 0, h1),
        d(c2, 0, h1) - d(c1, 1, h2),
    )
    for got, exp in zip(jax_result, expected):
        assert np.allclose(got, exp, atol=1e-8)


def test_jax_trilinear_sampling_exact_on_linear_field():
    n0, n1, n2 = 20, 18, 16
    origin = (0.0, -1.0, 2.0)
    spacing = (0.05, 0.1, 0.07)
    X = origin[0] + spacing[0] * np.arange(n0)[:, None, None]
    Y = origin[1] + spacing[1] * np.arange(n1)[None, :, None]
    Z = origin[2] + spacing[2] * np.arange(n2)[None, None, :]
    a, b, c, d_ = 2.3, -1.7, 0.5, 4.0
    field = np.broadcast_to(a * X + b * Y + c * Z + d_, (n0, n1, n2)).copy()

    rng = np.random.RandomState(6)
    bounds_lo = np.array(origin)
    bounds_hi = np.array(origin) + np.array(spacing) * (np.array([n0, n1, n2]) - 1)
    pts = rng.uniform(bounds_lo, bounds_hi, size=(200, 3))
    expected = a * pts[:, 0] + b * pts[:, 1] + c * pts[:, 2] + d_

    result = jax_backend.sample_field_trilinear(field, origin, spacing, pts)
    assert np.allclose(result, expected, atol=1e-6)


def test_engine_dispatches_to_jax_when_selected():
    """End-to-end: PhysicsEngine itself, not just the backend module
    directly, must route through JAX once selected."""
    from scientific_visualization.core.data import CoordinateAxis, Dataset
    from scientific_visualization.physics.engine import PhysicsEngine

    shape = (10, 9, 8)
    rng = np.random.RandomState(0)
    data = rng.rand(*shape)
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.arange(shape[i]) * 0.1) for i in range(3)
    )
    ds = Dataset("f", data, ("x1", "x2", "x3"), coords, "V/m", 0.0, "s", {}, "s")

    nb.set_backend("numpy")
    numpy_result = PhysicsEngine().gradient(ds, "x1")
    nb.set_backend("jax")
    jax_result = PhysicsEngine().gradient(ds, "x1")
    assert np.allclose(numpy_result.data, jax_result.data, atol=1e-8)
```

---

## `tests/test_lineout.py`

```py
import numpy as np
from scientific_visualization.io.grid import GridFile, AxisInfo


def make_grid():
    # Stored HDF5 layout is reversed physical axis order: shape=(x3,x2,x1).
    arr=np.zeros((3,4,5),dtype=float)
    for k in range(3):
        for j in range(4):
            for i in range(5):
                arr[k,j,i]=i + 10*j + 100*k
    return GridFile(filename='synthetic', name='f', label='f', ndim=3, shape=arr.shape,
                    axes=[AxisInfo('x1','x1','',0,5,5), AxisInfo('x2','x2','',0,4,4), AxisInfo('x3','x3','',0,3,3)], data=arr, dataset_name='f')


def test_3d_index_lineout_uses_physical_axis_indices():
    gf=make_grid(); coord, values=gf.lineout(axis=0,index=(1,2,0))
    np.testing.assert_allclose(values, gf.data[1,2,:])
    assert len(coord)==5
```

---

## `tests/test_native_physics_backend.py`

```py
"""Tests for the optional native C++/OpenMP physics backend.

These tests must pass identically whether or not the compiled extension
(`scientific_visualization/physics/_native*.so`, built by `native/build.sh`)
is present, since `native_backend` transparently falls back to pure NumPy.
A few tests specifically force the fallback path (even when the extension
is built) to prove the two implementations agree numerically.
"""
import numpy as np
import pytest

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.physics import native_backend as nb
from scientific_visualization.physics.engine import PhysicsEngine


def _force_fallback(monkeypatch):
    monkeypatch.setattr(nb, "NATIVE_AVAILABLE", False)


def _uniform_dataset(shape, spacings, seed=0):
    rng = np.random.RandomState(seed)
    data = rng.rand(*shape)
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.arange(shape[i]) * spacings[i], units="m", label=f"x{i+1}")
        for i in range(len(shape))
    )
    return Dataset(name="f", data=data, axes=tuple(f"x{i+1}" for i in range(len(shape))),
                    coordinates=coords, units="V/m", time=0.0, time_units="s", metadata={}, source="synthetic")


def test_coordinate_axis_is_uniform():
    uniform = CoordinateAxis(name="x1", values=np.linspace(0, 1, 20))
    assert uniform.is_uniform
    assert uniform.spacing == pytest.approx(uniform.values[1] - uniform.values[0])

    non_uniform = CoordinateAxis(name="x1", values=np.array([0.0, 1.0, 3.0, 10.0]))
    assert not non_uniform.is_uniform
    with pytest.raises(ValueError):
        non_uniform.spacing

    tiny = CoordinateAxis(name="x1", values=np.array([0.0, 1.0]))
    assert tiny.is_uniform  # fewer than 3 points is trivially "uniform"


@pytest.mark.parametrize("shape", [(37,), (21, 17), (14, 11, 9)])
def test_gradient_uniform_matches_np_gradient(shape):
    rng = np.random.RandomState(1)
    data = rng.rand(*shape)
    h = 0.37
    for axis in range(len(shape)):
        coord = np.arange(shape[axis]) * h
        order = 2 if shape[axis] > 2 else 1
        expected = np.gradient(data, coord, axis=axis, edge_order=order)
        got = nb.gradient_uniform(data, h, axis, edge_order=2)
        assert np.allclose(got, expected, atol=1e-10)


def test_gradient_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(2)
    data = rng.rand(12, 9, 7)
    h = 0.2
    native_result = nb.gradient_uniform(data, h, axis=1, edge_order=2)
    _force_fallback(monkeypatch)
    fallback_result = nb.gradient_uniform(data, h, axis=1, edge_order=2)
    assert np.allclose(native_result, fallback_result, atol=1e-10)


def test_divergence_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(3)
    shape = (16, 14, 12)
    comps = [rng.rand(*shape) for _ in range(3)]
    spacings = [0.1, 0.2, 0.15]
    native_result = nb.divergence_uniform(comps, spacings)
    _force_fallback(monkeypatch)
    fallback_result = nb.divergence_uniform(comps, spacings)
    assert np.allclose(native_result, fallback_result, atol=1e-9)


def test_laplacian_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(4)
    data = rng.rand(18, 13, 10)
    spacings = [0.1, 0.2, 0.15]
    native_result = nb.laplacian_uniform(data, spacings)
    _force_fallback(monkeypatch)
    fallback_result = nb.laplacian_uniform(data, spacings)
    assert np.allclose(native_result, fallback_result, atol=1e-9)


def test_curl_uniform_native_matches_fallback(monkeypatch):
    rng = np.random.RandomState(5)
    shape = (12, 10, 8)
    c1, c2, c3 = rng.rand(*shape), rng.rand(*shape), rng.rand(*shape)
    h1, h2, h3 = 0.1, 0.2, 0.15
    native_result = nb.curl_uniform_3d(c1, c2, c3, h1, h2, h3)
    _force_fallback(monkeypatch)
    fallback_result = nb.curl_uniform_3d(c1, c2, c3, h1, h2, h3)
    for a, b in zip(native_result, fallback_result):
        assert np.allclose(a, b, atol=1e-9)


def test_trilinear_sampling_exact_on_linear_field(monkeypatch):
    n0, n1, n2 = 20, 18, 16
    origin = (0.0, -1.0, 2.0)
    spacing = (0.05, 0.1, 0.07)
    X = origin[0] + spacing[0] * np.arange(n0)[:, None, None]
    Y = origin[1] + spacing[1] * np.arange(n1)[None, :, None]
    Z = origin[2] + spacing[2] * np.arange(n2)[None, None, :]
    a, b, c, d = 2.3, -1.7, 0.5, 4.0
    field = np.broadcast_to(a * X + b * Y + c * Z + d, (n0, n1, n2)).copy()

    rng = np.random.RandomState(6)
    bounds_lo = np.array(origin)
    bounds_hi = np.array(origin) + np.array(spacing) * (np.array([n0, n1, n2]) - 1)
    pts = rng.uniform(bounds_lo, bounds_hi, size=(500, 3))
    expected = a * pts[:, 0] + b * pts[:, 1] + c * pts[:, 2] + d

    native_result = nb.sample_field_trilinear(field, origin, spacing, pts)
    assert np.allclose(native_result, expected, atol=1e-9)

    _force_fallback(monkeypatch)
    fallback_result = nb.sample_field_trilinear(field, origin, spacing, pts)
    assert np.allclose(fallback_result, expected, atol=1e-9)


def test_trilinear_sampling_clamps_out_of_bounds():
    field = np.arange(2 * 2 * 2, dtype=float).reshape(2, 2, 2)
    origin = (0.0, 0.0, 0.0)
    spacing = (1.0, 1.0, 1.0)
    inside = nb.sample_field_trilinear(field, origin, spacing, np.array([[0.0, 0.0, 0.0]]))
    far_outside = nb.sample_field_trilinear(field, origin, spacing, np.array([[-500.0, -500.0, -500.0]]))
    assert np.allclose(inside, far_outside)  # both clamp to the same corner


def test_backend_status_reports_something_sensible():
    status = nb.backend_name()
    assert isinstance(status, str) and len(status) > 0
    assert nb.max_threads() >= 1


# --- integration through PhysicsEngine, proving the wiring is correct ---

def test_engine_gradient_uniform_grid_uses_native_and_matches_manual_numpy():
    ds = _uniform_dataset((25, 20), (0.1, 0.2))
    engine = PhysicsEngine()
    result = engine.gradient(ds, "x1")
    coord = np.arange(25) * 0.1
    expected = np.gradient(ds.data, coord, axis=0, edge_order=2)
    assert np.allclose(result.data, expected, atol=1e-9)


def test_engine_divergence_uniform_grid_matches_non_uniform_fallback_path():
    """Build the *same* field values on a uniform grid and re-run through
    the non-uniform (np.gradient) code path by using non-evenly-spaced
    coordinates that happen to still be uniform numerically -- this checks
    the native and np.gradient code paths agree end to end via the public
    PhysicsEngine API, not just the native_backend module directly."""
    shape = (16, 14, 12)
    rng = np.random.RandomState(7)
    comps_data = [rng.rand(*shape) for _ in range(3)]
    spacings = (0.1, 0.2, 0.15)

    uniform_coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.arange(shape[i]) * spacings[i]) for i in range(3)
    )
    # Non-uniform-looking (but numerically identical spacing) coordinate
    # values force the np.gradient fallback path inside PhysicsEngine.
    forced_non_uniform_coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=(np.arange(shape[i]) * spacings[i]) + 0.0) for i in range(3)
    )

    engine = PhysicsEngine()
    vector_uniform = {
        f"x{i+1}": Dataset(f"x{i+1}", comps_data[i], ("x1", "x2", "x3"), uniform_coords, "V/m", 0.0, "s", {}, "s")
        for i in range(3)
    }
    result_native = engine.divergence(vector_uniform)

    import scientific_visualization.physics.engine as engine_mod
    # Force the "non-uniform" branch by monkeypatching is_uniform to False
    # for this call only, to compare against the np.gradient-based path.
    orig_is_uniform = CoordinateAxis.is_uniform
    try:
        CoordinateAxis.is_uniform = property(lambda self: False)
        vector_forced = {
            f"x{i+1}": Dataset(f"x{i+1}", comps_data[i], ("x1", "x2", "x3"), forced_non_uniform_coords, "V/m", 0.0, "s", {}, "s")
            for i in range(3)
        }
        result_fallback = engine.divergence(vector_forced)
    finally:
        CoordinateAxis.is_uniform = orig_is_uniform

    assert np.allclose(result_native.data, result_fallback.data, atol=1e-9)


def test_engine_backend_status():
    assert isinstance(PhysicsEngine.backend_status(), str)
```

---

## `tests/test_particle_field.py`

```py
import numpy as np
import pytest

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.physics import particle_field as pf


def _linear_field_dataset(a, b, c, d, shape=(20, 18, 16), origin=(0.0, -1.0, 2.0), spacing=(0.05, 0.1, 0.07)):
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=origin[i] + spacing[i] * np.arange(shape[i]))
        for i in range(3)
    )
    X = coords[0].values[:, None, None]
    Y = coords[1].values[None, :, None]
    Z = coords[2].values[None, None, :]
    data = np.broadcast_to(a * X + b * Y + c * Z + d, shape).copy()
    return Dataset(name="e1", data=data, axes=("x1", "x2", "x3"), coordinates=coords,
                    units="V/m", time=0.0, time_units="s", metadata={}, source="synthetic")


def test_sample_dataset_along_trajectory_exact_on_linear_field():
    field = _linear_field_dataset(2.0, -1.0, 0.5, 3.0)
    rng = np.random.RandomState(0)
    n = 50
    x1 = rng.uniform(0.0, 0.05 * 19, n)
    x2 = rng.uniform(-1.0, -1.0 + 0.1 * 17, n)
    x3 = rng.uniform(2.0, 2.0 + 0.07 * 15, n)
    sampled = pf.sample_dataset_along_trajectory(field, x1, x2, x3)
    expected = 2.0 * x1 - 1.0 * x2 + 0.5 * x3 + 3.0
    assert np.allclose(sampled, expected, atol=1e-9)


def test_sample_dataset_along_trajectory_rejects_non_uniform_grid():
    coords = (
        CoordinateAxis(name="x1", values=np.array([0.0, 1.0, 3.0, 10.0])),
        CoordinateAxis(name="x2", values=np.linspace(0, 1, 4)),
        CoordinateAxis(name="x3", values=np.linspace(0, 1, 4)),
    )
    data = np.zeros((4, 4, 4))
    field = Dataset("e1", data, ("x1", "x2", "x3"), coords, "V/m", 0.0, "s", {}, "s")
    with pytest.raises(ValueError, match="uniform"):
        pf.sample_dataset_along_trajectory(field, [0.0], [0.0], [0.0])


def test_sample_dataset_along_trajectory_rejects_2d_field():
    coords = (CoordinateAxis(name="x1", values=np.linspace(0, 1, 4)), CoordinateAxis(name="x2", values=np.linspace(0, 1, 4)))
    field = Dataset("e1", np.zeros((4, 4)), ("x1", "x2"), coords, "V/m", 0.0, "s", {}, "s")
    with pytest.raises(ValueError, match="3D"):
        pf.sample_dataset_along_trajectory(field, [0.0], [0.0], [0.0])


def test_sample_fields_along_trajectory_multiple_components():
    e1 = _linear_field_dataset(1.0, 0.0, 0.0, 0.0)
    e2 = _linear_field_dataset(0.0, 1.0, 0.0, 0.0)
    e3 = _linear_field_dataset(0.0, 0.0, 1.0, 0.0)
    x1 = np.array([0.1, 0.2])
    x2 = np.array([-0.9, -0.8])
    x3 = np.array([2.1, 2.2])
    result = pf.sample_fields_along_trajectory({"E1": e1, "E2": e2, "E3": e3}, x1, x2, x3)
    assert set(result) == {"E1", "E2", "E3"}
    assert np.allclose(result["E1"], x1, atol=1e-9)
    assert np.allclose(result["E2"], x2, atol=1e-9)
    assert np.allclose(result["E3"], x3, atol=1e-9)


def test_magnitude_dot_cross():
    a = (np.array([1.0]), np.array([0.0]), np.array([0.0]))
    b = (np.array([0.0]), np.array([1.0]), np.array([0.0]))
    assert np.allclose(pf.magnitude3(3.0, 4.0, 0.0), 5.0)
    assert np.allclose(pf.dot3(*a, *b), 0.0)
    cx, cy, cz = pf.cross3(*a, *b)
    assert np.allclose(np.array([cx, cy, cz]).ravel(), [0.0, 0.0, 1.0])  # x_hat cross y_hat = z_hat


def test_velocity_and_kinetic_energy_from_momentum_zero_momentum_at_rest():
    v1, v2, v3, gamma = pf.velocity_from_momentum(0.0, 0.0, 0.0)
    assert np.allclose([v1, v2, v3], 0.0)
    assert np.allclose(gamma, 1.0)
    ke = pf.kinetic_energy_from_momentum(0.0, 0.0, 0.0)
    assert np.allclose(ke, 0.0)


def test_kinetic_energy_increases_with_momentum():
    ke_low = pf.kinetic_energy_from_momentum(0.1, 0.0, 0.0)
    ke_high = pf.kinetic_energy_from_momentum(1.0, 0.0, 0.0)
    assert ke_high > ke_low > 0


def test_lorentz_force_pure_electric_field_no_velocity():
    fx, fy, fz = pf.lorentz_force(1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, charge=1.0)
    assert np.allclose([fx, fy, fz], [1.0, 2.0, 3.0])


def test_lorentz_force_magnetic_only_perpendicular_to_velocity():
    # v = x_hat, B = z_hat -> v x B = -y_hat, F should be along -y with no E
    fx, fy, fz = pf.lorentz_force(0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, charge=1.0)
    assert np.allclose([fx, fy, fz], [0.0, -1.0, 0.0])


def test_energy_gain():
    energy = np.array([1.0, 1.5, 2.5, 2.0])
    gain = pf.energy_gain(energy)
    assert np.allclose(gain, [0.5, 1.0, -0.5])


def test_energy_gain_requires_two_points():
    with pytest.raises(ValueError):
        pf.energy_gain([1.0])
```

---

## `tests/test_performance_and_robustness_fixes.py`

```py
"""Regression tests for issues found and fixed during a robustness/performance review.

Each test documents the bug it guards against so a future refactor doesn't
silently reintroduce it.
"""
import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.ml.features import sample_grid_features, dataset_to_features


def _make_grid_dataset(shape, seed=0):
    rng = np.random.RandomState(seed)
    data = rng.rand(*shape).astype(np.float32)
    coords = tuple(
        CoordinateAxis(name=f"x{i+1}", values=np.linspace(0.0, 1.0, shape[i]), units="m", label=f"x{i+1}")
        for i in range(len(shape))
    )
    return Dataset(
        name="e1", data=data, axes=tuple(f"x{i+1}" for i in range(len(shape))),
        coordinates=coords, units="V/m", time=0.0, time_units="s", metadata={}, source="synthetic",
    )


def test_sample_grid_features_matches_brute_force_subsample():
    """sample_grid_features must select the same rows/values as the original
    'materialize everything then subsample' implementation, just without
    building the full (N, 1+ndim) array and coordinate meshgrid first."""
    ds = _make_grid_dataset((20, 24, 18), seed=1)
    max_samples = 500

    fast = sample_grid_features(ds, max_samples=max_samples, seed=7)

    full = dataset_to_features(ds)
    rng = np.random.default_rng(7)
    idx = np.sort(rng.choice(full.values.shape[0], size=max_samples, replace=False))
    expected_values = full.values[idx]

    assert fast.values.shape == (max_samples, 1 + ds.ndim)
    np.testing.assert_allclose(fast.values, expected_values)
    assert fast.feature_names == full.feature_names
    np.testing.assert_array_equal(fast.metadata["sample_indices"], idx)


def test_sample_grid_features_small_grid_returns_all_points():
    """When the grid already fits under max_samples, behavior is unchanged:
    every point is returned (this path is untouched by the optimization)."""
    ds = _make_grid_dataset((4, 5))
    fs = sample_grid_features(ds, max_samples=1000)
    assert fs.values.shape[0] == 20


def test_sample_grid_features_large_grid_is_fast():
    """A 200^3 field (8,000,000 points) sampling 10,000 points must not
    materialize the full grid's coordinate mesh; this used to take several
    seconds and should now be near-instant."""
    import time
    ds = _make_grid_dataset((200, 200, 200))
    t0 = time.time()
    fs = sample_grid_features(ds, max_samples=10_000, seed=0)
    elapsed = time.time() - t0
    assert fs.values.shape == (10_000, 4)
    assert elapsed < 1.0, f"sample_grid_features took {elapsed:.2f}s; expected well under 1s"


def test_export_grid_movie_uses_thread_safe_agg_figure(tmp_path):
    """export_grid_movie must not depend on pyplot's global current-figure
    state, since it can be invoked from a background worker thread while the
    Qt GUI thread is simultaneously drawing its own embedded canvas."""
    import h5py
    from scientific_visualization.export.animation import export_grid_movie

    paths = []
    for i in range(3):
        p = tmp_path / f"e1-{i:06d}.h5"
        with h5py.File(p, "w") as f:
            f.attrs["NAME"] = "e1"; f.attrs["TIME"] = float(i); f.attrs["ITER"] = i
            d = f.create_dataset("e1", data=np.random.rand(16, 20).astype(np.float32))
            d.attrs["UNITS"] = "V/m"
            g = f.create_group("AXIS")
            a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
            a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
        paths.append(str(p))

    out = tmp_path / "movie.gif"
    n = export_grid_movie([str(p) for p in paths], str(out))
    assert n == 3
    assert out.exists() and out.stat().st_size > 0

    import matplotlib.pyplot as plt
    assert plt.get_fignums() == [], "export_grid_movie must not leak a figure into pyplot's global state"


def test_three_d_tab_reset_camera_does_not_raise():
    """Regression test for a NameError: reset_camera() referenced a bare
    name `clear_scene` (the sibling method's parameter name) instead of
    always resetting the camera, so clicking 'Reset camera' in the 3D tab
    crashed whenever a renderer was active."""
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.three_d_tab import ThreeDTab

    calls = {"reset": 0, "render": 0}

    class FakePlotter:
        def reset_camera(self):
            calls["reset"] += 1

        def render(self):
            calls["render"] += 1

    class FakeRenderer:
        plotter = FakePlotter()

    tab = ThreeDTab()
    tab.renderer = FakeRenderer()
    tab.reset_camera()  # must not raise NameError
    assert calls == {"reset": 1, "render": 1}


def test_run_in_background_success_and_error():
    """Smoke test for the generic worker helper used by ML training and
    movie export: it must call on_success with the callable's return value,
    and on_error with the exception, back on the calling (GUI) thread."""
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import QEventLoop, QTimer
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.workers import run_in_background

    parent = QWidget()

    # -- success path --
    result_box = {}

    def ok_job():
        return 42

    loop = QEventLoop()
    run_in_background(parent, ok_job, on_success=lambda r: (result_box.setdefault("v", r), loop.quit()),
                       on_error=lambda e: loop.quit())
    QTimer.singleShot(5000, loop.quit)  # safety timeout
    loop.exec_()
    assert result_box.get("v") == 42

    # -- error path --
    error_box = {}

    def bad_job():
        raise ValueError("boom")

    loop2 = QEventLoop()
    run_in_background(parent, bad_job, on_success=lambda r: loop2.quit(),
                       on_error=lambda e: (error_box.setdefault("e", e), loop2.quit()))
    QTimer.singleShot(5000, loop2.quit)
    loop2.exec_()
    assert isinstance(error_box.get("e"), ValueError)
    assert str(error_box["e"]) == "boom"


def test_run_in_background_does_not_destroy_qthread_while_running():
    """Regression test for a real crash: an earlier version of this module
    connected the worker's finished/failed signals directly to plain Python
    closures instead of a QObject's bound methods. Qt can only tell a
    connection needs to be auto-queued back to the GUI thread by checking
    the *receiver object's* thread affinity -- a bare closure has none, so
    PyQt ran the "GUI thread" cleanup callback on the worker thread itself.
    That made `thread.wait()` wait on its own thread (a documented Qt no-op
    that just warns and returns immediately), so the QThread could still be
    tearing itself down after Python considered it finished and dropped the
    last reference -- observed as an intermittent "QThread: Destroyed while
    thread is still running" crash under load. This runs many trials with
    immediate post-completion deletion to make that race, if reintroduced,
    show up reliably rather than depending on system timing/load."""
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import QEventLoop, QTimer
    import sys
    import warnings
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.workers import run_in_background

    for trial in range(30):
        parent = QWidget()
        result = {}

        def ok_job(trial=trial):
            return trial

        loop = QEventLoop()
        run_in_background(
            parent, ok_job,
            on_success=lambda r: (result.setdefault("v", r), loop.quit()),
            on_error=lambda e: (result.setdefault("e", e), loop.quit()),
        )
        QTimer.singleShot(2000, loop.quit)
        loop.exec_()
        assert result.get("v") == trial, f"trial {trial}: unexpected result {result}"
        # Immediately drop every reference the test holds, right after
        # completion, to maximize the chance of exposing a premature-
        # destruction race if the underlying bug were reintroduced.
        del parent, loop, result


def _make_grid_series(tmp_path, count=3, shape=(24, 24), name="e1"):
    import h5py
    import numpy as np
    paths = []
    for i in range(count):
        p = tmp_path / f"{name}-{i:06d}.h5"
        with h5py.File(p, "w") as f:
            f.attrs["NAME"] = name; f.attrs["TIME"] = float(i); f.attrs["ITER"] = i
            d = f.create_dataset(name, data=np.random.RandomState(i).rand(*shape).astype(np.float32))
            d.attrs["UNITS"] = "V/m"
            g = f.create_group("AXIS")
            a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
            a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
        paths.append(str(p))
    return paths


def test_frame_navigation_reuses_lazy_series_cache_not_a_fresh_disk_read(tmp_path):
    """Regression test: on_file_selected() used to unconditionally call
    GridFile.info() (a fresh HDF5 open) and _ensure_grid_loaded() used to
    unconditionally call GridFile.load() (another fresh open), even when
    the exact same frame's fully-loaded GridFile was already sitting in
    self._series's bounded cache from a recent visit. Revisiting a
    recently-seen frame must now come from the cache, not from disk."""
    import os
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab
    from scientific_visualization.io.grid import GridFile

    paths = _make_grid_series(tmp_path, count=3)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()

    tab._select_relative(1)  # visit frame 1 -> now cached
    cached_grid = tab._series._cache.get(1)
    assert cached_grid is not None and cached_grid.data is not None

    read_count = {"n": 0}
    original_load = GridFile.load

    def counting_load(path):
        read_count["n"] += 1
        return original_load(path)

    GridFile.load = staticmethod(counting_load)
    original_info = GridFile.info

    def counting_info(path):
        read_count["n"] += 1
        return original_info(path)

    GridFile.info = staticmethod(counting_info)
    try:
        tab._select_relative(-1)  # back to frame 0 (cached from initial load)
        tab._select_relative(1)   # forward to frame 1 (cached from the visit above)
    finally:
        GridFile.load = original_load
        GridFile.info = original_info

    assert read_count["n"] == 0, (
        f"expected zero fresh HDF5 opens when revisiting cached frames, got {read_count['n']}"
    )


def test_frame_navigation_does_not_force_full_axes_rebuild_every_time(tmp_path):
    """Regression test: on_file_selected() used to unconditionally reset
    _active_plot_mode to None, forcing refresh_plot() to treat every
    single frame change as a "mode change" -- tearing down the axes,
    rebuilding the colorbar from scratch, and re-applying the full theme
    -- even when scrubbing between frames of the same quantity/shape.
    The image object (and colorbar) must now be reused via set_data(),
    not recreated, when only the frame (not the plot type) changes."""
    import os
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    paths = _make_grid_series(tmp_path, count=3)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()

    image_before = tab._image
    cbar_before = tab._cbar
    assert image_before is not None and cbar_before is not None

    tab._select_relative(1)  # same shape/quantity -> should reuse, not recreate

    assert tab._image is image_before, "AxesImage was recreated for a same-shape frame change"
    assert tab._cbar is cbar_before, "Colorbar was recreated for a same-shape frame change"


def test_genuine_mode_switch_still_rebuilds_axes_correctly(tmp_path):
    """The fix above must not break the legitimate case: switching between
    plot *types* (2D image vs. line plot) still needs a full axes rebuild,
    since those artist sets are incompatible on the same Axes."""
    import os
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    paths = _make_grid_series(tmp_path, count=2)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    assert tab._image is not None

    tab.mode_line_index.setChecked(True)
    tab.refresh_plot()
    ax = tab.canvas.figure.axes[0]
    assert len(ax.images) == 0
    assert tab._line_artist is not None

    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    assert tab._image is not None
    assert len(ax.images) == 1


def test_frame_navigation_still_updates_correctly_across_different_shapes(tmp_path):
    """A different-shaped/different-quantity file must still produce a
    correctly updated plot (new image, new extent, new colorbar label),
    even though same-shape frame changes now skip the full rebuild."""
    import os
    import sys
    import h5py
    import numpy as np
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    p1 = tmp_path / "e1-000000.h5"
    with h5py.File(p1, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.random.rand(20, 20).astype(np.float32)); d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    p2 = tmp_path / "b3-000000.h5"
    with h5py.File(p2, "w") as f:
        f.attrs["NAME"] = "b3"; f.attrs["TIME"] = 1.0; f.attrs["ITER"] = 1
        d = f.create_dataset("b3", data=np.random.rand(35, 40).astype(np.float32)); d.attrs["UNITS"] = "T"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 2.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 3.0]); a2.attrs["NAME"] = "x2 axis"

    tab = GridTab()
    tab.files = [str(p1)]
    tab.file_list.addItem("e1-000000.h5")
    tab.file_list.setCurrentRow(0); tab.on_file_selected(0); tab.mode_2d.setChecked(True); tab.refresh_plot()
    assert tab._image.get_array().shape == (20, 20)

    tab.files = [str(p2)]
    tab.file_list.clear(); tab.file_list.addItem("b3-000000.h5")
    tab.file_list.setCurrentRow(0); tab.on_file_selected(0); tab.refresh_plot()

    assert tab._image.get_array().shape == (35, 40)
    assert tab._image.get_extent() == [0.0, 2.0, 0.0, 3.0]
    label = tab._cbar.ax.get_ylabel() or tab._cbar.ax.get_xlabel()
    assert "b3" in label and "T" in label


def test_plot_canvas_skips_theme_reapplication_on_routine_redraw():
    """Regression test: PlotCanvas.draw() used to unconditionally re-apply
    the full theme (walking every axes/tick/spine/label, including the
    colorbar's own axes) on every single redraw, even when nothing about
    the theme had changed. Only actual theme changes, figure clears, or
    explicit mark_theme_dirty() calls should trigger it now."""
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.plot_canvas import PlotCanvas
    from unittest.mock import patch

    canvas = PlotCanvas()
    with patch("scientific_visualization.gui.plot_canvas.style.apply_theme") as mock_apply:
        canvas.draw()  # first draw: dirty by default
        assert mock_apply.call_count == 1
        canvas.draw()  # routine redraw: nothing changed, should be skipped
        canvas.draw()
        assert mock_apply.call_count == 1

        canvas.mark_theme_dirty()
        canvas.draw()
        assert mock_apply.call_count == 2

        canvas.set_theme("Dark")  # actual theme change marks dirty
        canvas.draw()
        assert mock_apply.call_count == 3

        canvas.set_theme("Dark")  # setting the same theme again should not
        canvas.draw()
        assert mock_apply.call_count == 3

        canvas.clear()  # clearing the figure marks dirty (fresh axes need it)
        canvas.draw()
        assert mock_apply.call_count == 4


def test_contour_overlay_is_not_recomputed_for_unrelated_setting_changes(tmp_path):
    """Regression test: contour overlays (which dominate redraw time on
    large fields -- matplotlib/contourpy's marching-squares pass) used to
    be unconditionally removed and recreated on every single redraw, even
    when the trigger was a pure display remap (gamma/contrast/black
    floor/colormap) that cannot possibly change the contour geometry.
    They must now be reused unless something that actually affects the
    contour lines changed."""
    import sys
    import h5py
    import numpy as np
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from scientific_visualization.gui.grid_tab import GridTab

    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=(np.random.RandomState(0).rand(64, 64)).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"

    tab = GridTab()
    tab.files = [str(p)]
    tab.file_list.addItem("e1-000000.h5")
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    tab.contour_overlay.setChecked(True)
    tab.refresh_plot()
    contour_before = tab._contour_artists[0]

    # Pure display remaps: must NOT recompute the contour.
    tab.gamma_spin.setValue(1.3)
    tab.refresh_plot()
    assert tab._contour_artists[0] is contour_before
    tab.contrast_spin.setValue(1.2)
    tab.refresh_plot()
    assert tab._contour_artists[0] is contour_before
    tab.black_floor_spin.setValue(0.1)
    tab.refresh_plot()
    assert tab._contour_artists[0] is contour_before

    # Settings that DO affect contour geometry/levels: must recompute.
    tab.n_contours.setValue(tab.n_contours.value() + 2)
    tab.refresh_plot()
    assert tab._contour_artists[0] is not contour_before
```

---

## `tests/test_performance_backends.py`

```py
from pathlib import Path

from scientific_visualization.io.lazy import LazyGridSeries
from scientific_visualization.export.opencv_movie import OPENCV_AVAILABLE, export_grid_movie_opencv


def test_lazy_grid_series_metadata_first():
    paths = sorted(str(p) for p in Path(__file__).parent.joinpath("sample_data/b3_series").glob("*.h5"))
    seq = LazyGridSeries(paths)
    assert len(seq) == 10
    assert seq[0].shape == (64, 128)
    assert seq._cache == {}
    grid = seq.load(0)
    assert grid.data is not None
    assert 0 in seq._cache


def test_opencv_movie_encoder(tmp_path):
    if not OPENCV_AVAILABLE:
        return
    paths = sorted(str(p) for p in Path(__file__).parent.joinpath("sample_data/b3_series").glob("*.h5"))
    out = tmp_path / "movie.mp4"
    n = export_grid_movie_opencv(paths, out, frame_end=2, fps=5)
    assert n == 3
    assert out.exists() and out.stat().st_size > 1000


def test_lazy_constructor_does_not_open_hdf5():
    paths = sorted(str(p) for p in Path(__file__).parent.joinpath("sample_data/b3_series").glob("*.h5"))
    calls = {"n": 0}
    from scientific_visualization.io.grid import GridFile
    def info(path):
        calls["n"] += 1
        return GridFile.info(path)
    seq = LazyGridSeries(paths, info_loader=info)
    assert calls["n"] == 0
    _ = seq[0]
    assert calls["n"] == 1
```

---

## `tests/test_roi_analysis.py`

```py
"""Tests for scientific_visualization.analysis.roi (plan.md section 4.4:
ROI and measurement tools).
"""
import json

import numpy as np
import pytest

from scientific_visualization.analysis.roi import (
    RegionOfInterest, roi_statistics, roi_time_series, export_roi_results,
)


def test_roi_normalizes_reversed_coordinates():
    roi = RegionOfInterest("rectangle", x0=1.0, y0=1.0, x1=0.0, y1=0.5)
    assert roi.x0 == 0.0 and roi.x1 == 1.0
    assert roi.y0 == 0.5 and roi.y1 == 1.0


def test_roi_rejects_invalid_shape():
    with pytest.raises(ValueError, match="rectangle"):
        RegionOfInterest("triangle", 0, 0, 1, 1)


def test_roi_rejects_zero_size():
    with pytest.raises(ValueError):
        RegionOfInterest("rectangle", 0, 0, 0, 1)
    with pytest.raises(ValueError):
        RegionOfInterest("rectangle", 0, 0, 1, 0)


def test_roi_gets_a_default_label():
    roi = RegionOfInterest("rectangle", 0, 0, 1, 1)
    assert roi.label == f"ROI {roi.id}"


def test_roi_ids_are_unique():
    roi1 = RegionOfInterest("rectangle", 0, 0, 1, 1)
    roi2 = RegionOfInterest("rectangle", 0, 0, 1, 1)
    assert roi1.id != roi2.id


def test_rectangle_mask_matches_exact_bounding_box():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 4, 5)
    roi = RegionOfInterest("rectangle", x0=2.5, y0=1.5, x1=6.5, y1=3.5)
    mask = roi.mask(x, y)
    assert mask.shape == (5, 10)
    expected = np.zeros((5, 10), dtype=bool)
    expected[2:4, 3:7] = True  # y in {2,3}, x in {3,4,5,6}
    np.testing.assert_array_equal(mask, expected)


def test_ellipse_mask_contains_center_and_excludes_far_corner():
    x = np.linspace(-5, 5, 11)
    y = np.linspace(-5, 5, 11)
    roi = RegionOfInterest("ellipse", x0=-4, y0=-4, x1=4, y1=4)
    mask = roi.mask(x, y)
    cx = cy = 5  # index of coordinate 0.0
    assert mask[cy, cx]  # center is inside
    assert not mask[0, 0]  # far corner (-5,-5) is outside the ellipse
    assert not mask[10, 10]


def test_rectangle_area_is_exact():
    roi = RegionOfInterest("rectangle", 0, 0, 2, 3)
    assert roi.area == pytest.approx(6.0)


def test_ellipse_area_matches_pi_r1_r2():
    roi = RegionOfInterest("ellipse", -2, -3, 2, 3)  # semi-axes 2, 3
    assert roi.area == pytest.approx(np.pi * 2 * 3, rel=1e-9)


def test_roi_statistics_on_known_constant_region():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 9, 10)
    data = np.zeros((10, 10))
    data[2:5, 2:5] = 3.0  # a known 3x3 block of constant value 3
    roi = RegionOfInterest("rectangle", x0=2, y0=2, x1=4, y1=4)
    result = roi_statistics(data, x, y, roi)
    assert result["n_points"] == 9
    assert result["mean"] == pytest.approx(3.0)
    assert result["min"] == pytest.approx(3.0)
    assert result["max"] == pytest.approx(3.0)
    assert result["std"] == pytest.approx(0.0)
    assert result["p50"] == pytest.approx(3.0)


def test_roi_statistics_integral_matches_value_times_area_for_uniform_region():
    x = np.linspace(0, 10, 11)  # spacing 1.0
    y = np.linspace(0, 10, 11)
    data = np.full((11, 11), 2.0)
    roi = RegionOfInterest("rectangle", x0=2, y0=2, x1=6, y1=6)
    result = roi_statistics(data, x, y, roi)
    # 5x5 grid points at spacing 1 => covered area ~16 (4x4 cells), integral ~= 2*area
    assert result["integral"] == pytest.approx(result["roi_area_covered"] * 2.0, rel=0.2)


def test_roi_statistics_rejects_shape_mismatch():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 4, 5)
    data = np.zeros((5, 11))  # wrong x length
    roi = RegionOfInterest("rectangle", 0, 0, 1, 1)
    with pytest.raises(ValueError, match="shape"):
        roi_statistics(data, x, y, roi)


def test_roi_statistics_rejects_roi_with_no_overlap():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 9, 10)
    data = np.zeros((10, 10))
    roi = RegionOfInterest("rectangle", x0=100, y0=100, x1=101, y1=101)
    with pytest.raises(ValueError, match="no finite data"):
        roi_statistics(data, x, y, roi)


def test_roi_statistics_ignores_nan_but_counts_only_finite():
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    data = np.ones((5, 5))
    data[2, 2] = np.nan
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)
    result = roi_statistics(data, x, y, roi)
    assert result["n_points"] == 8  # 3x3 block minus the one NaN


def test_roi_to_dict_and_from_dict_round_trip():
    roi = RegionOfInterest("ellipse", 0, 0, 2, 2, label="my region")
    d = roi.to_dict()
    restored = RegionOfInterest.from_dict(d)
    assert restored.shape == roi.shape
    assert restored.x0 == roi.x0 and restored.x1 == roi.x1
    assert restored.label == roi.label
    assert restored.id != roi.id  # fresh id on reconstruction, by design


class _FakeAxis:
    def __init__(self, values):
        self._values = np.asarray(values, dtype=float)
    def values(self):
        return self._values


class _FakeGrid:
    def __init__(self, data, x, y, time, iteration):
        self.data = data
        self.axes = [_FakeAxis(x), _FakeAxis(y)]
        self.time = time
        self.time_units = "s"
        self.iteration = iteration


def test_roi_time_series_computes_stats_for_every_frame():
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    grids = {f"frame{i}.h5": _FakeGrid(np.full((5, 5), float(i)), x, y, float(i), i) for i in range(4)}
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)

    progress = []
    results = roi_time_series(
        list(grids.keys()), loader=lambda p: grids[p], roi=roi,
        progress_callback=lambda i, total, p: progress.append((i, total, p)),
    )
    assert len(results) == 4
    for i, r in enumerate(results):
        assert r["mean"] == pytest.approx(float(i))
        assert r["iteration"] == i
    assert progress == [(1, 4, "frame0.h5"), (2, 4, "frame1.h5"), (3, 4, "frame2.h5"), (4, 4, "frame3.h5")]


def test_roi_time_series_records_error_for_bad_frame_without_aborting_others():
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    good = _FakeGrid(np.full((5, 5), 7.0), x, y, 0.0, 0)
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)

    def loader(path):
        if path == "bad.h5":
            raise RuntimeError("corrupt file")
        return good

    results = roi_time_series(["good1.h5", "bad.h5", "good2.h5"], loader=loader, roi=roi)
    assert results[0]["mean"] == pytest.approx(7.0)
    assert "error" in results[1] and "corrupt" in results[1]["error"]
    assert results[2]["mean"] == pytest.approx(7.0)


def test_export_roi_results_writes_valid_json(tmp_path):
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    data = np.full((5, 5), 3.0)
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3, label="test region")
    result = roi_statistics(data, x, y, roi)

    out = tmp_path / "roi.json"
    export_roi_results(result, str(out))
    loaded = json.loads(out.read_text())
    assert loaded["mean"] == pytest.approx(3.0)
    assert loaded["roi"]["label"] == "test region"


def test_export_roi_results_handles_list_of_results(tmp_path):
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    grids = [_FakeGrid(np.full((5, 5), float(i)), x, y, float(i), i) for i in range(3)]
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)
    results = roi_time_series([f"f{i}" for i in range(3)], loader=lambda p: grids[int(p[1:])], roi=roi)

    out = tmp_path / "roi_series.json"
    export_roi_results(results, str(out))
    loaded = json.loads(out.read_text())
    assert len(loaded) == 3
    assert [r["mean"] for r in loaded] == [0.0, 1.0, 2.0]
```

---

## `tests/test_roi_gui.py`

```py
"""Tests for the ROI/measurement tool's GUI wiring in gui/grid_tab.py
(plan.md section 4.4). The underlying analysis logic (masks, statistics,
time series, export) is tested independently in test_roi_analysis.py --
this file covers mouse-driven drawing, list management, persistence
across frame navigation, and the export/time-evolution actions.
"""
import json
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

_app = QApplication.instance() or QApplication([])

from scientific_visualization.gui.grid_tab import GridTab


class _FakeMplEvent:
    def __init__(self, xdata=None, ydata=None, inaxes=None, x=100, y=100):
        self.xdata = xdata; self.ydata = ydata; self.inaxes = inaxes; self.x = x; self.y = y


def _make_grid_series(tmp_path, count=2, shape=(20, 20), name="e1"):
    paths = []
    for i in range(count):
        p = tmp_path / f"{name}-{i:06d}.h5"
        with h5py.File(p, "w") as f:
            f.attrs["NAME"] = name; f.attrs["TIME"] = float(i); f.attrs["ITER"] = i
            d = f.create_dataset(name, data=np.arange(shape[0] * shape[1]).reshape(shape).astype(np.float32))
            d.attrs["UNITS"] = "V/m"
            g = f.create_group("AXIS")
            a1 = g.create_dataset("AXIS1", data=[0.0, float(shape[1])]); a1.attrs["NAME"] = "x1 axis"
            a2 = g.create_dataset("AXIS2", data=[0.0, float(shape[0])]); a2.attrs["NAME"] = "x2 axis"
        paths.append(str(p))
    return paths


@pytest.fixture
def tab_with_grid(tmp_path):
    paths = _make_grid_series(tmp_path)
    tab = GridTab()
    tab.files = paths
    for p in paths:
        tab.file_list.addItem(os.path.basename(p))
    tab.file_list.setCurrentRow(0)
    tab.on_file_selected(0)
    tab.mode_2d.setChecked(True)
    tab.refresh_plot()
    return tab


def _draw_rectangle_roi(tab, x0=2.0, y0=3.0, x1=8.0, y1=10.0):
    ax = tab.canvas.figure.axes[0]
    tab.start_roi_draw()
    tab._on_canvas_press(_FakeMplEvent(x0, y0, inaxes=ax))
    tab._on_canvas_motion(_FakeMplEvent(x1, y1, inaxes=ax))
    tab._on_canvas_release(_FakeMplEvent(x1, y1, inaxes=ax))


def test_start_roi_draw_without_data_shows_info_not_crash(monkeypatch):
    tab = GridTab()
    infos = []
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a) or QMessageBox.Ok))
    tab.start_roi_draw()
    assert len(infos) == 1
    assert tab._roi_mode is None


def test_drawing_a_rectangle_roi_adds_it_to_the_list(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    assert len(tab_with_grid._rois) == 1
    assert tab_with_grid._rois[0].shape == "rectangle"
    assert tab_with_grid.roi_list.count() == 1
    assert tab_with_grid.roi_list.currentRow() == 0


def test_drawing_an_ellipse_roi(tab_with_grid):
    tab_with_grid.roi_shape.setCurrentText("Ellipse")
    _draw_rectangle_roi(tab_with_grid, 2, 2, 8, 8)
    assert tab_with_grid._rois[0].shape == "ellipse"


def test_roi_preview_patch_is_cleaned_up_after_finalizing(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    assert tab_with_grid._roi_preview_patch is None
    assert tab_with_grid._roi_draft is None
    assert tab_with_grid._roi_mode is None


def test_roi_statistics_populate_after_drawing(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    text = tab_with_grid.roi_stats_label.text()
    assert "min=" in text and "mean=" in text
    assert tab_with_grid._last_roi_results is not None


def test_multiple_simultaneous_rois(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 5, 5)
    tab_with_grid.roi_shape.setCurrentText("Ellipse")
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 15)
    assert len(tab_with_grid._rois) == 2
    assert tab_with_grid.roi_list.count() == 2


def test_selecting_a_different_roi_updates_stats(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 3, 3)
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 18)
    tab_with_grid.roi_list.setCurrentRow(0)
    stats0 = tab_with_grid.roi_stats_label.text()
    tab_with_grid.roi_list.setCurrentRow(1)
    stats1 = tab_with_grid.roi_stats_label.text()
    assert stats0 != stats1


def test_remove_selected_roi(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 3, 3)
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 18)
    tab_with_grid.roi_list.setCurrentRow(0)
    tab_with_grid.remove_selected_roi()
    assert len(tab_with_grid._rois) == 1
    assert tab_with_grid.roi_list.count() == 1


def test_clear_all_rois(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid, 0, 0, 3, 3)
    _draw_rectangle_roi(tab_with_grid, 10, 10, 15, 18)
    tab_with_grid.clear_rois()
    assert tab_with_grid._rois == []
    assert tab_with_grid.roi_list.count() == 0
    assert tab_with_grid._last_roi_results is None


def test_roi_too_small_shows_error_not_crash(tab_with_grid):
    ax = tab_with_grid.canvas.figure.axes[0]
    tab_with_grid.start_roi_draw()
    tab_with_grid._on_canvas_press(_FakeMplEvent(5.0, 5.0, inaxes=ax))
    tab_with_grid._on_canvas_release(_FakeMplEvent(5.0, 5.0, inaxes=ax))  # zero-size
    assert tab_with_grid._rois == []
    assert "not created" in tab_with_grid.info_label.text()


def test_roi_persists_across_frame_navigation(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    assert len(tab_with_grid._rois) == 1
    tab_with_grid._select_relative(1)
    assert len(tab_with_grid._rois) == 1  # ROI survives moving to the next frame
    tab_with_grid._show_roi_stats(tab_with_grid._rois[0])
    assert "min=" in tab_with_grid.roi_stats_label.text()  # still computable on the new frame's data


def test_roi_drawn_patches_appear_on_the_axes(tab_with_grid):
    _draw_rectangle_roi(tab_with_grid)
    ax = tab_with_grid.canvas.figure.axes[0]
    assert len(tab_with_grid._roi_patches) == 1
    assert tab_with_grid._roi_patches[0] in ax.patches


def test_export_roi_stats_without_selection_shows_info(monkeypatch):
    tab = GridTab()
    infos = []
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a) or QMessageBox.Ok))
    tab.export_roi_stats()
    assert len(infos) == 1


def test_export_roi_stats_writes_json(tab_with_grid, tmp_path, monkeypatch):
    _draw_rectangle_roi(tab_with_grid)
    out = tmp_path / "roi.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "")))
    tab_with_grid.export_roi_stats()
    assert out.exists()
    data = json.loads(out.read_text())
    assert "mean" in data


def test_compute_time_evolution_without_selection_shows_info(monkeypatch):
    tab = GridTab()
    infos = []
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a) or QMessageBox.Ok))
    tab.compute_roi_time_evolution()
    assert len(infos) == 1


def test_compute_time_evolution_runs_in_background_and_reports_results(tab_with_grid):
    """Uses the same run_in_background worker as ML training/movie export
    (see gui/workers.py), so this drives the Qt event loop briefly to let
    the background thread finish rather than mocking it away."""
    from PyQt5.QtCore import QEventLoop, QTimer
    _draw_rectangle_roi(tab_with_grid)
    loop = QEventLoop()
    orig_done = tab_with_grid._on_roi_time_evolution_done

    def wrapped(results):
        orig_done(results)
        loop.quit()

    tab_with_grid._on_roi_time_evolution_done = wrapped
    tab_with_grid.compute_roi_time_evolution()
    QTimer.singleShot(10000, loop.quit)  # safety timeout
    loop.exec_()
    assert tab_with_grid._last_roi_results is not None
    assert isinstance(tab_with_grid._last_roi_results, list)
    assert len(tab_with_grid._last_roi_results) == len(tab_with_grid.files)
    assert "computed for" in tab_with_grid.info_label.text()


def test_deactivate_mouse_tools_cancels_in_progress_roi_draw(tab_with_grid):
    ax = tab_with_grid.canvas.figure.axes[0]
    tab_with_grid.start_roi_draw()
    tab_with_grid._on_canvas_press(_FakeMplEvent(2.0, 2.0, inaxes=ax))
    tab_with_grid._on_canvas_motion(_FakeMplEvent(5.0, 5.0, inaxes=ax))
    assert tab_with_grid._roi_preview_patch is not None
    tab_with_grid._deactivate_mouse_tools()
    assert tab_with_grid._roi_mode is None
    assert tab_with_grid._roi_draft is None
    assert tab_with_grid._roi_preview_patch is None
```

---

## `tests/test_session_xml.py`

```py
from scientific_visualization.session import save_xml_session, load_xml_session


def test_xml_session_roundtrip(tmp_path):
    state = {'files':['a.h5','b.h5'], 'current_index':1, 'view_xlim':[0.2,4.0], 'camera_position':[1,2,3], 'settings':{'direction':'(x,y,z)','enabled':True}}
    path=tmp_path/'session.xml'; save_xml_session(path,state)
    restored=load_xml_session(path)
    assert restored['files']==state['files']
    assert restored['current_index']=='1'
    assert restored['camera_position']==['1','2','3']
    assert restored['settings']['direction']=='(x,y,z)'
    assert restored['settings']['enabled']=='True'
```

---

## `tests/test_surrogate_lab.py`

```py
import numpy as np
import pytest


def test_advanced_surrogate_uq_and_acquisition():
    from scientific_visualization.ml import FeatureSet, AdvancedSurrogate, estimator_available
    if not estimator_available():
        pytest.skip('scikit-learn not installed')
    rng = np.random.default_rng(11)
    X = rng.uniform(-1, 1, (90, 3))
    y = 1.5 * X[:, 0] - 0.8 * X[:, 1] ** 2 + 0.15 * X[:, 2]
    fs = FeatureSet(X, ('p1','p2','p3'))
    model = AdvancedSurrogate('Extra Trees').fit(fs, y)
    mean, std, ens = model.predict_with_uncertainty(X[:10])
    assert mean.shape == (10,) and std.shape == (10,) and ens.shape[1] == 10
    rec = model.recommend(X, batch_size=5, criterion='Maximum uncertainty')
    assert len(rec['indices']) == 5
    report = model.report(fs, y, criterion='Upper confidence bound')
    assert report.metrics['rmse'] >= 0
    assert set(report.feature_importance) == {'p1','p2','p3'}


def test_edge_workspace_removed():
    from pathlib import Path
    root = Path(__file__).parents[1] / 'scientific_visualization'
    assert not (root / 'edge_compute.py').exists()
    assert not (root / 'gui' / 'edge_tab.py').exists()
```

---

## `tests/test_three_d_advanced_features.py`

```py
"""Tests for the advanced 3D features: isosurfaces, volume rendering,
interactive clip planes, bounding box/orientation-axes toggles, and
screenshot export.

Covers both layers:
  * `ThreeDRenderer` directly (pure, GUI-independent) -- correctness of
    the geometry/values produced.
  * `ThreeDTab` (GUI wiring) -- mode dispatch, isovalue parsing/validation,
    and error handling, using a real off-screen-rendered `ThreeDRenderer`
    injected into the tab (pyvistaqt, needed only for the *interactive*
    embedded widget, is not required for this).
"""
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QMessageBox

_app = QApplication.instance() or QApplication([])

from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.core.configuration import RenderingConfig
from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv


def _gaussian_blob_dataset(n=24, name="blob"):
    coords = tuple(CoordinateAxis(f"x{i+1}", np.linspace(-2, 2, n)) for i in range(3))
    X, Y, Z = np.meshgrid(coords[0].values, coords[1].values, coords[2].values, indexing="ij")
    data = np.exp(-(X ** 2 + Y ** 2 + Z ** 2))
    return Dataset(name, data, ("x1", "x2", "x3"), coords, "a.u.", 0.0, "s", {}, "synthetic")


def _make_3d_hdf5_file(tmp_path, n=16, name="blob"):
    p = tmp_path / f"{name}-000000.h5"
    x = np.linspace(-2, 2, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    data = np.exp(-(X ** 2 + Y ** 2 + Z ** 2)).astype(np.float32)
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = name; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset(name, data=data); d.attrs["UNITS"] = "a.u."
        g = f.create_group("AXIS")
        for i in range(3):
            a = g.create_dataset(f"AXIS{i+1}", data=[-2.0, 2.0]); a.attrs["NAME"] = f"x{i+1}"
    return str(p)


@pytest.fixture
def offscreen_plotter():
    if pv is None:
        pytest.skip("pyvista not installed")
    plotter = pv.Plotter(off_screen=True)
    yield plotter
    plotter.close()


# --- ThreeDRenderer: _build_3d_grid ---

def test_build_3d_grid_uses_imagedata_for_uniform_spacing(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=10)
    r = ThreeDRenderer(offscreen_plotter)
    grid = r._build_3d_grid(ds)
    assert isinstance(grid, pv.ImageData)
    assert grid.n_points == 10 ** 3
    np.testing.assert_allclose(grid["blob"].reshape(10, 10, 10, order="F"), ds.data)


def test_build_3d_grid_falls_back_to_structured_grid_for_non_uniform_spacing(offscreen_plotter):
    values = np.array([0.0, 1.0, 3.0, 10.0])  # non-uniform
    coords = (
        CoordinateAxis("x1", values),
        CoordinateAxis("x2", np.linspace(0, 1, 4)),
        CoordinateAxis("x3", np.linspace(0, 1, 4)),
    )
    data = np.random.RandomState(0).rand(4, 4, 4)
    ds = Dataset("f", data, ("x1", "x2", "x3"), coords, "", 0.0, "s", {}, "s")
    r = ThreeDRenderer(offscreen_plotter)
    grid = r._build_3d_grid(ds)
    assert isinstance(grid, pv.StructuredGrid)
    assert grid.n_points == 64


# --- suggest_isovalues ---

def test_suggest_isovalues_returns_sorted_values_within_data_range():
    ds = _gaussian_blob_dataset(n=12)
    values = ThreeDRenderer.suggest_isovalues(ds, n=3)
    assert len(values) == 3
    assert values == sorted(values)
    lo, hi = float(ds.data.min()), float(ds.data.max())
    assert all(lo <= v <= hi for v in values)


def test_suggest_isovalues_respects_n():
    ds = _gaussian_blob_dataset(n=12)
    for n in (1, 2, 5):
        assert len(ThreeDRenderer.suggest_isovalues(ds, n=n)) == n


def test_suggest_isovalues_rejects_n_less_than_one():
    ds = _gaussian_blob_dataset(n=8)
    with pytest.raises(ValueError):
        ThreeDRenderer.suggest_isovalues(ds, n=0)


def test_suggest_isovalues_rejects_all_nan_data():
    ds = _gaussian_blob_dataset(n=6)
    ds.data[:] = np.nan
    with pytest.raises(ValueError, match="no finite"):
        ThreeDRenderer.suggest_isovalues(ds)


# --- add_isosurfaces ---

def test_add_isosurfaces_produces_a_visible_mesh(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=20)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=2)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig())
    assert actor is not None
    assert f"{ds.name} [{ds.units}]" in offscreen_plotter.scalar_bars


def test_add_isosurfaces_rejects_2d_dataset(offscreen_plotter):
    coords = (CoordinateAxis("x1", np.linspace(0, 1, 5)), CoordinateAxis("x2", np.linspace(0, 1, 5)))
    ds = Dataset("f", np.random.rand(5, 5), ("x1", "x2"), coords, "", 0.0, "s", {}, "s")
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError, match="3D"):
        r.add_isosurfaces(ds, [0.5])


def test_add_isosurfaces_rejects_empty_isovalue_list(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=8)
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError, match="at least one"):
        r.add_isosurfaces(ds, [])


def test_add_isosurfaces_out_of_range_value_raises_actionable_error(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=12)
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError) as excinfo:
        r.add_isosurfaces(ds, [999.0])
    msg = str(excinfo.value)
    assert "999" in msg
    assert "range" in msg  # reports the actual data range, not just "failed"


# --- add_clipped_volume ---

def test_add_clipped_volume_interactive(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=12)
    r = ThreeDRenderer(offscreen_plotter)
    actor = r.add_clipped_volume(ds, config=RenderingConfig(), normal="x", interactive=True)
    assert actor is not None


def test_add_clipped_volume_noninteractive_actually_clips_geometry(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=16)
    r = ThreeDRenderer(offscreen_plotter)
    full_grid = r._build_3d_grid(ds)
    actor = r.add_clipped_volume(ds, config=RenderingConfig(), normal="x", interactive=False)
    assert actor is not None
    # A one-shot clip should produce strictly fewer points than the full grid.
    clipped_mesh = actor.mapper.dataset
    assert clipped_mesh.n_points < full_grid.n_points


def test_add_clipped_volume_rejects_2d_dataset(offscreen_plotter):
    coords = (CoordinateAxis("x1", np.linspace(0, 1, 5)), CoordinateAxis("x2", np.linspace(0, 1, 5)))
    ds = Dataset("f", np.random.rand(5, 5), ("x1", "x2"), coords, "", 0.0, "s", {}, "s")
    r = ThreeDRenderer(offscreen_plotter)
    with pytest.raises(ValueError, match="3D"):
        r.add_clipped_volume(ds)


# --- volume rendering, bounding box, axes, screenshot ---

def test_add_native_3d_volume_render(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=10)
    r = ThreeDRenderer(offscreen_plotter)
    actor = r.add_native_3d(ds, config=RenderingConfig())
    assert actor is not None


def test_bounding_box_and_axes_toggles_do_not_raise(offscreen_plotter):
    ds = _gaussian_blob_dataset(n=8)
    r = ThreeDRenderer(offscreen_plotter)
    r.add_native_3d_slices(ds, config=RenderingConfig())
    r.set_show_bounding_box(True)
    r.set_show_bounding_box(False)
    r.set_show_orientation_axes(True)
    r.set_show_orientation_axes(False)


def test_save_screenshot_writes_a_real_image(offscreen_plotter, tmp_path):
    ds = _gaussian_blob_dataset(n=10)
    r = ThreeDRenderer(offscreen_plotter)
    r.add_native_3d_slices(ds, config=RenderingConfig())
    out = tmp_path / "shot.png"
    r.save_screenshot(str(out))
    assert out.exists() and out.stat().st_size > 0


# --- GUI wiring: ThreeDTab ---

@pytest.fixture
def tab_with_3d_dataset(tmp_path):
    from scientific_visualization.gui.three_d_tab import ThreeDTab
    if pv is None:
        pytest.skip("pyvista not installed")
    tab = ThreeDTab()
    tab.renderer = ThreeDRenderer(pv.Plotter(off_screen=True))
    # Pick a 3D-compatible mode *before* apply_selection() (which renders
    # immediately on load) -- the mode combo defaults to "2D plane" for
    # newly-constructed tabs, and applying a 3D file under a 2D-only mode
    # correctly raises a validation error that pops a blocking QMessageBox,
    # which would otherwise hang this fixture.
    tab.mode.setCurrentText("3D orthogonal slices")
    path = _make_3d_hdf5_file(tmp_path, n=16)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("blob-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()
    assert tab.dataset is not None and tab.dataset.ndim == 3
    return tab


def _actor_count(tab):
    return len(tab.renderer.plotter.renderer.actors)


def test_mode_combo_offers_all_3d_modes(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    options = [tab.mode.itemText(i) for i in range(tab.mode.count())]
    for expected in ("3D orthogonal slices", "3D volume", "3D isosurfaces", "3D clip plane"):
        assert expected in options


def test_gui_volume_mode_renders(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D volume")
    tab.render()
    assert _actor_count(tab) > 0


def test_gui_isosurfaces_auto_mode_renders(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Auto (percentiles)")
    tab.isovalue_count.setValue(3)
    tab.render()
    assert _actor_count(tab) > 0


def test_gui_isosurfaces_manual_mode_with_suggested_values(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Manual list")
    tab._fill_suggested_isovalues()
    assert tab.isovalue_manual.text().strip() != ""
    tab.render()
    assert _actor_count(tab) > 0


def test_gui_isosurfaces_bad_manual_input_shows_warning_not_crash(tab_with_3d_dataset, monkeypatch):
    tab = tab_with_3d_dataset
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else "") or QMessageBox.Ok))
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Manual list")
    tab.isovalue_manual.setText("not,a,number")
    tab.render()
    assert len(warnings) == 1
    assert "Could not parse" in warnings[0]


def test_gui_clip_plane_modes_render(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D clip plane")
    for interactive in (False, True):
        tab.clip_interactive.setChecked(interactive)
        tab.render()
        assert _actor_count(tab) > 0


def test_gui_2d_mode_on_3d_dataset_warns_instead_of_crashing(tab_with_3d_dataset, monkeypatch):
    tab = tab_with_3d_dataset
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: warnings.append(a[2] if len(a) > 2 else "") or QMessageBox.Ok))
    tab.mode.setCurrentText("2D plane")
    tab.render()
    assert len(warnings) == 1
    assert "2D" in warnings[0] and "3D" in warnings[0]


def test_gui_bounding_box_and_axes_checkboxes_wired(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.show_bounding_box.setChecked(True)   # must not raise
    tab.show_bounding_box.setChecked(False)
    tab.show_orientation_axes.setChecked(False)
    tab.show_orientation_axes.setChecked(True)


def test_gui_save_screenshot_writes_real_file(tab_with_3d_dataset, tmp_path, monkeypatch):
    tab = tab_with_3d_dataset
    out = tmp_path / "shot.png"
    from PyQt5.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), "")))
    tab.save_screenshot()
    assert out.exists() and out.stat().st_size > 0
    assert str(out) in tab.info.text()


def test_isovalue_mode_toggle_enables_correct_widgets(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.mode.setCurrentText("3D isosurfaces")
    tab.isovalue_mode.setCurrentText("Manual list")
    assert tab.isovalue_manual.isEnabled()
    assert not tab.isovalue_count.isEnabled()
    tab.isovalue_mode.setCurrentText("Auto (percentiles)")
    assert not tab.isovalue_manual.isEnabled()
    assert tab.isovalue_count.isEnabled()


def test_mode_switch_shows_correct_option_groups(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.show()  # setVisible()'s effect only shows up in isVisible() once the top-level window is shown
    tab.mode.setCurrentText("3D isosurfaces")
    assert tab.isosurface_box.isVisible()
    assert not tab.clip_box.isVisible()
    tab.mode.setCurrentText("3D clip plane")
    assert tab.clip_box.isVisible()
    assert not tab.isosurface_box.isVisible()
    tab.mode.setCurrentText("3D volume")
    assert not tab.isosurface_box.isVisible()
    assert not tab.clip_box.isVisible()


# --- Camera presets (plan.md 6.6) ---

def test_camera_preset_options_include_all_six_directions_plus_isometric_and_fit(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    options = [tab.camera_preset.itemText(i) for i in range(tab.camera_preset.count())]
    for expected in ("Isometric", "Front", "Back", "Left", "Right", "Top", "Bottom", "Fit to data"):
        assert expected in options


@pytest.mark.parametrize("preset,expected_direction", [
    ("Top", (0, 0, 1)),
    ("Bottom", (0, 0, -1)),
    ("Front", (0, -1, 0)),
    ("Back", (0, 1, 0)),
    ("Right", (1, 0, 0)),
    ("Left", (-1, 0, 0)),
])
def test_camera_preset_points_the_camera_in_the_correct_direction(tab_with_3d_dataset, preset, expected_direction):
    """Regression test: the previous Top/Bottom mapping was backwards
    (labeled "Top" actually looked from below, and vice versa), and
    Front/Back/Left/Right didn't exist at all. Directions are verified
    against PyVista's actual camera_position, not assumed -- matches the
    same convention as Blender's numpad views (Front/Back along Y,
    Left/Right along X, Top/Bottom along Z)."""
    tab = tab_with_3d_dataset
    tab.camera_preset.setCurrentText(preset)
    tab.apply_camera_preset()
    pos, focal, up = tab.renderer.plotter.camera_position
    vec = np.array(pos) - np.array(focal)
    vec = vec / np.linalg.norm(vec)
    assert np.allclose(vec, expected_direction, atol=1e-2), (
        f"{preset}: camera direction {tuple(vec)} does not match expected {expected_direction}"
    )


def test_camera_preset_isometric_and_fit_to_data_do_not_raise(tab_with_3d_dataset):
    tab = tab_with_3d_dataset
    tab.camera_preset.setCurrentText("Isometric")
    tab.apply_camera_preset()
    tab.camera_preset.setCurrentText("Fit to data")
    tab.apply_camera_preset()


def test_camera_preset_no_renderer_does_not_raise():
    from scientific_visualization.gui.three_d_tab import ThreeDTab
    tab = ThreeDTab()  # renderer may be None (no pyvistaqt installed)
    tab.renderer = None
    tab.camera_preset.setCurrentText("Top")
    tab.apply_camera_preset()  # must not raise


# --- Isosurface performance guards ---
# Regression tests for a real, severe bottleneck: add_isosurfaces() used to
# unconditionally call mesh.smooth(n_iter=20, ...) and request
# smooth_shading (which triggers VTK's compute_normals) on *any* resulting
# isosurface mesh, regardless of size. For a noisy or high-resolution 3D
# field, the extracted isosurface can have millions of points, and both of
# those operations scale with mesh size -- measured 34.7s total (23.3s in
# .smooth() alone, 11.3s more in compute_normals) for a 150^3 noisy volume,
# against ~2.5s for the actual (already VTK/C++) isosurface extraction.
# Both are now skipped above a size threshold, with a printed explanation,
# rather than silently stalling.

def _noisy_large_dataset(n=70, seed=0):
    """Deliberately noisy (not smooth) data: an isosurface of this has a
    large, highly-detailed point count even at a modest grid resolution,
    which is what actually triggers the slow path -- not raw voxel count."""
    coords = tuple(CoordinateAxis(f"x{i+1}", np.linspace(-2, 2, n)) for i in range(3))
    rng = np.random.RandomState(seed)
    data = rng.rand(n, n, n)  # pure noise: maximally complex isosurface
    return Dataset("noisy", data, ("x1", "x2", "x3"), coords, "a.u.", 0.0, "s", {}, "synthetic")


def test_isosurface_smoothing_is_skipped_for_a_very_large_mesh(offscreen_plotter, capsys):
    ds = _noisy_large_dataset(n=70)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig(), max_smooth_points=1000)
    assert actor is not None
    out = capsys.readouterr().out
    assert "Skipping isosurface smoothing" in out


def test_isosurface_smoothing_still_applies_for_a_small_mesh(offscreen_plotter, capsys):
    ds = _gaussian_blob_dataset(n=20)  # smooth data -> small, simple isosurface
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig())
    assert actor is not None
    out = capsys.readouterr().out
    assert "Skipping isosurface smoothing" not in out


def test_isosurface_flat_shading_kicks_in_for_a_very_large_mesh(offscreen_plotter, capsys):
    ds = _noisy_large_dataset(n=70)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    r.add_isosurfaces(ds, values, config=RenderingConfig(), max_smooth_points=1000)
    out = capsys.readouterr().out
    assert "Using flat shading for a large mesh" in out


def test_isosurface_smooth_shading_preserved_for_a_small_mesh(offscreen_plotter, capsys):
    ds = _gaussian_blob_dataset(n=20)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    r.add_isosurfaces(ds, values, config=RenderingConfig())
    out = capsys.readouterr().out
    assert "Using flat shading" not in out


def test_isosurface_disabling_smooth_flag_never_calls_smooth(offscreen_plotter, capsys):
    ds = _gaussian_blob_dataset(n=20)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    actor = r.add_isosurfaces(ds, values, config=RenderingConfig(), smooth=False)
    assert actor is not None
    out = capsys.readouterr().out
    assert "Skipping isosurface smoothing" not in out  # smoothing was never attempted, not "skipped"


def test_isosurface_large_noisy_volume_completes_quickly(offscreen_plotter):
    """The actual performance assertion: this used to take 30+ seconds."""
    import time
    ds = _noisy_large_dataset(n=70)
    r = ThreeDRenderer(offscreen_plotter)
    values = r.suggest_isovalues(ds, n=1)
    t0 = time.perf_counter()
    r.add_isosurfaces(ds, values, config=RenderingConfig())
    elapsed = time.perf_counter() - t0
    assert elapsed < 10.0, f"isosurface rendering took {elapsed:.1f}s; expected well under 10s"
```

---

## `tests/test_three_d_panel_position.py`

```py
"""Tests for the 3D tab's panel-position control.

`ThreeDTab` used to be a standalone QWidget that never inherited the
"Panel: Left/Right/Top/Bottom" placement feature already available on the
2D Fields/Grid tab (via BaseTab). This verifies ThreeDTab now shares that
same, single implementation -- and that every existing 3D-tab behavior
(file loading, rendering, camera controls, colorbar options) still works
after the refactor that made it possible.

Testing note: `pyvistaqt` (needed for the *interactive* Qt-embedded 3D
widget) is not required to run these tests, and may not be installed.
Without it, `ThreeDTab.renderer` is `None` and `render()` is a silent
no-op -- so tests that only assert "render() doesn't raise" can pass
without ever actually exercising the renderer. Tests below that need to
verify real rendering behavior explicitly inject a `ThreeDRenderer`
backed by an off-screen `pv.Plotter` (no pyvistaqt needed for that), the
same pattern already used for the pure-renderer tests in
test_colorbar_features.py.
"""
import os

import h5py
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

from scientific_visualization.gui.three_d_tab import ThreeDTab
from scientific_visualization.gui.base_tab import BaseTab


def _make_2d_grid_file(tmp_path, shape=(10, 10)):
    p = tmp_path / "e1-000000.h5"
    with h5py.File(p, "w") as f:
        f.attrs["NAME"] = "e1"; f.attrs["TIME"] = 0.0; f.attrs["ITER"] = 0
        d = f.create_dataset("e1", data=np.random.RandomState(0).rand(*shape).astype(np.float32))
        d.attrs["UNITS"] = "V/m"
        g = f.create_group("AXIS")
        a1 = g.create_dataset("AXIS1", data=[0.0, 1.0]); a1.attrs["NAME"] = "x1 axis"
        a2 = g.create_dataset("AXIS2", data=[0.0, 1.0]); a2.attrs["NAME"] = "x2 axis"
    return str(p)


def _give_real_offscreen_renderer(tab):
    """Inject a real ThreeDRenderer backed by an off-screen pv.Plotter, so
    render() actually renders instead of being a no-op when pyvistaqt
    isn't installed. Returns the renderer so callers can inspect
    `renderer.plotter` (e.g. actor counts) for real assertions."""
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None:
        pytest.skip("pyvista not installed")
    tab.renderer = ThreeDRenderer(pv.Plotter(off_screen=True))
    return tab.renderer


def _actor_count(renderer):
    return len(renderer.plotter.renderer.actors)


def test_three_d_tab_inherits_base_tab():
    assert issubclass(ThreeDTab, BaseTab)


def test_three_d_tab_has_panel_position_control():
    tab = ThreeDTab()
    assert hasattr(tab, "_panel_position")
    options = [tab._panel_position.itemText(i) for i in range(tab._panel_position.count())]
    assert options == ["Left", "Right", "Top", "Bottom"]


@pytest.mark.parametrize("position,expect_horizontal,expect_panel_first", [
    ("Left", True, True),
    ("Right", True, False),
    ("Top", False, True),
    ("Bottom", False, False),
])
def test_three_d_tab_panel_position_moves_the_view(position, expect_horizontal, expect_panel_first):
    tab = ThreeDTab()
    tab.show()
    tab._panel_position.setCurrentText(position)
    orientation_ok = (tab._splitter.orientation() == Qt.Horizontal) == expect_horizontal
    panel_is_first = tab._splitter.widget(0) is not tab.canvas
    assert orientation_ok
    assert panel_is_first == expect_panel_first


def test_three_d_tab_set_theme_does_not_crash_without_a_dataset():
    tab = ThreeDTab()
    tab.set_theme("Dark")  # must not raise even though canvas isn't a PlotCanvas
    tab.set_theme("Light")


def test_three_d_tab_set_theme_rerenders_when_a_dataset_is_loaded(tmp_path):
    tab = ThreeDTab()
    renderer = _give_real_offscreen_renderer(tab)
    path = _make_2d_grid_file(tmp_path)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("e1-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()
    assert tab.dataset is not None
    before = _actor_count(renderer)
    assert before > 0  # apply_selection() already rendered something real
    tab.set_theme("Dark")  # must not raise; refresh_plot() re-renders via render()
    assert _actor_count(renderer) > 0


def test_three_d_tab_reset_camera_still_works_after_refactor():
    """Regression guard: an earlier bug made reset_camera() raise NameError.
    Re-verify it's still fine after moving ThreeDTab onto BaseTab."""
    tab = ThreeDTab()

    class FakePlotter:
        def __init__(self):
            self.reset_calls = 0
            self.render_calls = 0
        def reset_camera(self):
            self.reset_calls += 1
        def render(self):
            self.render_calls += 1

    class FakeRenderer:
        def __init__(self):
            self.plotter = FakePlotter()

    tab.renderer = FakeRenderer()
    tab.reset_camera()
    assert tab.renderer.plotter.reset_calls == 1
    assert tab.renderer.plotter.render_calls == 1


def test_three_d_tab_file_open_and_apply_flow_still_works(tmp_path):
    tab = ThreeDTab()
    path = _make_2d_grid_file(tmp_path)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("e1-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()
    assert tab.dataset is not None
    assert tab.dataset.shape == (10, 10)
    assert "shape=(10, 10)" in tab.info.text()


def test_three_d_tab_colorbar_controls_still_present_and_wired(tmp_path):
    tab = ThreeDTab()
    renderer = _give_real_offscreen_renderer(tab)
    path = _make_2d_grid_file(tmp_path)
    tab._pending_files = [path]
    tab.file_list.clear(); tab.file_list.addItem("e1-000000.h5"); tab.file_list.setCurrentRow(0)
    tab.apply_selection()  # calls render() once already
    for position in ("right", "left", "top", "bottom"):
        tab.colorbar_position.setCurrentText(position)
        tab.render()
        assert _actor_count(renderer) > 0
        assert "e1 [V/m]" in renderer.plotter.scalar_bars
```
