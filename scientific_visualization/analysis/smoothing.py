from __future__ import annotations

from pathlib import Path
import numpy as np
from ..io.simulation.grid import GridFile

try:
    from scipy.ndimage import gaussian_filter, uniform_filter1d
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False


def smooth_1d(y, method="None", window=5):
    y = np.asarray(y)
    if method in (None, "None") or window <= 1:
        return y
    if method == "Moving average":
        if _HAVE_SCIPY: return uniform_filter1d(y, size=int(window), mode="nearest")
        return np.convolve(y, np.ones(int(window))/int(window), mode="same")
    if method == "Gaussian":
        if _HAVE_SCIPY: return gaussian_filter(y, sigma=float(window)/2.0, mode="nearest")
        sigma=max(float(window)/2.0, 1e-6); radius=max(int(3*sigma),1); x=np.arange(-radius,radius+1); k=np.exp(-0.5*(x/sigma)**2); k/=k.sum(); return np.convolve(y,k,mode="same")
    raise ValueError(f"Unknown smoothing method: {method}")


def smooth_2d(data, method="None", window=5):
    data=np.asarray(data)
    if method in (None,"None") or window<=1: return data
    if method == "Moving average":
        if _HAVE_SCIPY: from scipy.ndimage import uniform_filter; return uniform_filter(data,size=int(window),mode="nearest")
        k=np.ones((int(window),int(window)))/(window*window); pad=int(window)//2; p=np.pad(data,pad,mode="edge"); out=np.empty_like(data,dtype=float)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]): out[i,j]=np.sum(p[i:i+window,j:j+window]*k)
        return out
    if method == "Gaussian":
        if _HAVE_SCIPY: return gaussian_filter(data,sigma=float(window)/2.0,mode="nearest")
        return data
    raise ValueError(f"Unknown smoothing method: {method}")


def reduce_grid_series(files, reduction="mean", smoothing=None):
    reducers={"mean":np.mean,"sum":np.sum,"max":np.max,"min":np.min,"rms":lambda a:np.sqrt(np.mean(np.asarray(a)**2)),"integral":lambda a:np.sum(np.asarray(a))}
    if reduction not in reducers: raise ValueError(f"Unknown reduction: {reduction}")
    times=[]; iters=[]; vals=[]; meta={}
    for path in sorted(files):
        g=GridFile.load(path); times.append(g.time); iters.append(g.iteration); vals.append(float(reducers[reduction](g.data))); meta.update(label=g.label or g.name,units=g.units,ndim=g.ndim)
    vals=np.asarray(vals)
    if smoothing: vals=smooth_1d(vals,smoothing.get("method","None"),smoothing.get("window",5))
    return np.asarray(times),np.asarray(iters),vals,meta
