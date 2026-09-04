from __future__ import annotations

import numpy as np


def statistics(data, finite_only=True):
    arr = np.asarray(data)
    if finite_only:
        arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("No finite samples available")
    return {"min": float(np.min(arr)), "max": float(np.max(arr)), "mean": float(np.mean(arr)), "std": float(np.std(arr)), "rms": float(np.sqrt(np.mean(arr**2))), "count": int(arr.size)}
