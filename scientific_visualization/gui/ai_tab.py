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
