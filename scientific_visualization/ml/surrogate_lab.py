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
