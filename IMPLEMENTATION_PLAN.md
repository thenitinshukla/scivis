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
