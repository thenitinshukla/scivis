# Data Plotter architecture

The Data Plotter is intentionally split into small layers:

- `parser.py`: CSV/TXT parsing, delimiter and header detection.
- `batch.py`: parallel batch loading for multiple CSV/TXT files.
- `model.py`: data tables and per-dataset plot configuration.
- `transform.py`: reusable X/Y transformations.
- `comparison.py`: comparison and scaling presets such as normalization, speedup, and efficiency.
- `renderer.py`: Matplotlib-only rendering with no Qt dependencies.
- `gui/data_plotter_tab.py`: Qt controls and user interaction.

This separation is important for performance and maintainability. Parsing and numerical operations remain independent of the GUI and can therefore be tested without starting Qt. Matplotlib and NumPy already execute their core numerical loops in compiled code, so a C++ rewrite should only be considered after profiling identifies a custom numerical kernel as the bottleneck.

## Scientific paper plotting presets

The Data Plotter accepts multiple CSV/TXT files as one experiment. Common aligned whitespace headers such as `Node    Total GPUs      Simulation time` are parsed without splitting multi-word column names.

The Scientific figures presets include strong-scaling runtime, speedup and efficiency, weak-scaling normalized runtime, runtime per workload and efficiency, histograms, empirical CDFs, and compact bar summaries. Strong-scaling figures use the smallest positive resource count in each file as the baseline. Weak-scaling figures require an explicit relative workload factor for each file, because problem size should not be inferred from filenames.

Scaling column detection recognizes common aliases such as `Total GPUs`, `GPUs`, `Nodes`, `Processors`, `Runtime`, `Simulation time`, `Wall time`, and `Elapsed time`.
