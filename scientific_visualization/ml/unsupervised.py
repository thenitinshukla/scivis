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
