"""
Reader for Simulation particle-tracking HDF5 files ("*-tracks.h5").

Standard Simulation tracks file layout:

    /                     (root group)
        attrs: NAME, NTRACKS, NDUMP, DT, QUANTS (e.g. ['t','x1','x2','p1',
               'p2','p3','ene','q']), LABELS, UNITS
        data       -- float array, shape (total_points, n_quants); the
                      per-track records concatenated one after another
        itermap    -- integer array, shape (n_tracks, 2); column 0 is the
                      starting iteration of the track, column 1 is the
                      number of saved points (dumps) for that track

This mirrors the structure written by z_data_tracks::Save in the original
Scientific Visualization IDL package.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np

from .grid import _attr, _scalar_attr
from ..core.data import Dataset


@dataclass
class TracksFile:
    filename: str
    name: str = ""
    ntracks: int = 0
    ndump: int = 0
    dt: float = 0.0
    quants: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    _offsets: Optional[np.ndarray] = None   # (ntracks,) start row into `data`
    _counts: Optional[np.ndarray] = None    # (ntracks,) number of points
    _data: Optional[np.ndarray] = None      # cached full data array

    @classmethod
    def info(cls, filename: str) -> "TracksFile":
        tf = cls(filename=filename)
        with h5py.File(filename, "r") as f:
            root = f["/"]
            tf.name = _attr(root, "NAME", "")
            tf.ndump = _scalar_attr(root, "NDUMP", 0, int)
            tf.dt = _scalar_attr(root, "DT", 0.0, float)

            quants = _attr(root, "QUANTS", None)
            if isinstance(quants, str):
                quants = [quants]
            tf.quants = list(quants) if quants else []

            labels = _attr(root, "LABELS", None)
            units = _attr(root, "UNITS", None)
            if isinstance(labels, str):
                labels = [labels]
            if isinstance(units, str):
                units = [units]
            for i, q in enumerate(tf.quants):
                tf.labels[q] = labels[i] if labels and i < len(labels) else q
                tf.units[q] = units[i] if units and i < len(units) else ""

            if "itermap" in root:
                itermap = np.asarray(root["itermap"][()])
                tf._offsets = np.concatenate(([0], np.cumsum(itermap[:, 1])[:-1])).astype(int)
                tf._counts = itermap[:, 1].astype(int)
                tf.ntracks = _scalar_attr(root, "NTRACKS", itermap.shape[0], int)
            else:
                tf.ntracks = _scalar_attr(root, "NTRACKS", 0, int)

            if not tf.quants and "data" in root:
                ncol = root["data"].shape[1] if root["data"].ndim > 1 else 1
                tf.quants = [f"q{i}" for i in range(ncol)]
        return tf

    def _load_data(self) -> np.ndarray:
        if self._data is None:
            with h5py.File(self.filename, "r") as f:
                self._data = np.asarray(f["data"][()])
        return self._data

    def get_track(self, index: int) -> dict:
        """Return {quant_name: 1D array} for a single track (0-based index)."""
        data = self._load_data()
        if self._offsets is not None:
            start = self._offsets[index]
            count = self._counts[index]
            rows = data[start:start + count]
        else:
            # Fallback: assume equal-length tracks, data is (ntracks, npoints, nquants)
            rows = data[index]
        return {q: rows[:, i] for i, q in enumerate(self.quants)}

    def get_all(self, quant_x: str, quant_y: str, max_tracks: Optional[int] = None):
        """Return a list of (x_array, y_array) tuples, one per track."""
        n = self.ntracks if max_tracks is None else min(self.ntracks, max_tracks)
        ix = self.quants.index(quant_x)
        iy = self.quants.index(quant_y)
        out = []
        for i in range(n):
            trk = self.get_track(i)
            out.append((trk[quant_x] if quant_x in trk else None,
                        trk[quant_y] if quant_y in trk else None))
        return out

    def label(self, quant: str) -> str:
        return self.labels.get(quant, quant)

    def unit(self, quant: str) -> str:
        return self.units.get(quant, "")

    def to_dataset(self, quant: str) -> Dataset:
        if quant not in self.quants:
            raise KeyError(quant)
        col = self.quants.index(quant)
        data = self._load_data()[:, col]
        return Dataset(
            name=quant, data=data, axes=("point",), units=self.unit(quant),
            metadata={"label": self.label(quant), "ntracks": self.ntracks}, source=self.filename,
            simulation_metadata={"format": "Simulation tracks", "ntracks": self.ntracks},
        )


def is_tracks_file(filename: str) -> bool:
    try:
        with h5py.File(filename, "r") as f:
            root = f["/"]
            return "data" in root and ("itermap" in root or "NTRACKS" in root.attrs)
    except Exception:
        return False
