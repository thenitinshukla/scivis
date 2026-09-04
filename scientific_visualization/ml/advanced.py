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
