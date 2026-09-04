from __future__ import annotations
import numpy as np
from .surrogate import SurrogateModel

class ActiveLearningAdvisor:
    """Select promising next simulation points from a trained surrogate using uncertainty/exploration."""
    def __init__(self, surrogate=None): self.surrogate=surrogate or SurrogateModel()
    def recommend(self, candidate_features, batch_size=5, ensemble_predictions=None):
        X=np.asarray(candidate_features,dtype=float)
        if ensemble_predictions is None:
            raise ValueError("Provide ensemble predictions for uncertainty-aware recommendations")
        preds=np.asarray(ensemble_predictions,dtype=float)
        if preds.ndim!=2 or preds.shape[1]!=len(X): raise ValueError("Ensemble predictions must be [models,candidates]")
        score=np.std(preds,axis=0)
        idx=np.argsort(score)[::-1][:int(batch_size)]
        return {"indices":idx.tolist(),"scores":score[idx].tolist(),"features":X[idx].tolist(),"criterion":"predictive_uncertainty"}
