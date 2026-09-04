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
