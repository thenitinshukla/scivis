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
