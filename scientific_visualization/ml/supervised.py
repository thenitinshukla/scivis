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
