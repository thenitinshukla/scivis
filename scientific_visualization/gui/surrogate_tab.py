from __future__ import annotations
from pathlib import Path
import json
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
