from __future__ import annotations
import numpy as np

class UncertaintyEstimator:
    """Model-agnostic uncertainty helpers based on ensemble predictions and residuals."""
    @staticmethod
    def ensemble_interval(predictions, confidence=0.95):
        pred=np.asarray(predictions,dtype=float)
        if pred.ndim != 2: raise ValueError("predictions must be [models, samples]")
        alpha=(1.0-confidence)/2.0
        return {"mean":np.mean(pred,axis=0),"lower":np.quantile(pred,alpha,axis=0),"upper":np.quantile(pred,1-alpha,axis=0),"std":np.std(pred,axis=0)}

    @staticmethod
    def residual_summary(y_true,y_pred):
        r=np.asarray(y_true,dtype=float)-np.asarray(y_pred,dtype=float)
        return {"bias":float(np.mean(r)),"rmse":float(np.sqrt(np.mean(r*r))),"mae":float(np.mean(np.abs(r))),"std":float(np.std(r))}
