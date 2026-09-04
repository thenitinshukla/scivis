"""
Reader for Simulation particle-diagnostic HDF5 files.

Layout (mirrors hdf5_partfileinfo.pro / hdf5_partfiledata.pro):

    /                      (root group)
        attrs: NAME, TIME, ITER, QUANTS (list of quantity names, e.g.
               ['x1','x2','p1','p2','p3','q','ene',...]), LABELS, UNITS
        <quant> dataset for each entry in QUANTS, each a 1D array of length
        NPAR (one value per particle in this dump).

Older files don't have a QUANTS attribute; in that case every dataset in the
root group is itself a quantity, named after the dataset.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np

from .grid import _attr, _scalar_attr
from ..core.data import Dataset


@dataclass
class ParticleFile:
    filename: str
    name: str = ""
    time: float = 0.0
    iteration: int = 0
    npar: int = 0
    quants: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    _data: dict = field(default_factory=dict)

    @classmethod
    def info(cls, filename: str) -> "ParticleFile":
        pf = cls(filename=filename)
        with h5py.File(filename, "r") as f:
            root = f["/"]
            pf.name = _attr(root, "NAME", "")
            pf.time = _scalar_attr(root, "TIME", 0.0, float)
            pf.iteration = _scalar_attr(root, "ITER", 0, int)

            quants = _attr(root, "QUANTS", None)
            if not quants:
                quants = [k for k in root.keys() if isinstance(root[k], h5py.Dataset)]
            elif isinstance(quants, str):
                quants = [quants]
            else:
                quants = list(quants)

            labels = _attr(root, "LABELS", None)
            units = _attr(root, "UNITS", None)
            if isinstance(labels, str):
                labels = [labels]
            if isinstance(units, str):
                units = [units]

            pf.quants = quants
            for i, q in enumerate(quants):
                if q not in root:
                    continue
                pf.labels[q] = labels[i] if labels and i < len(labels) else q
                pf.units[q] = units[i] if units and i < len(units) else _attr(root[q], "UNITS", "")

            if quants and quants[0] in root:
                pf.npar = int(root[quants[0]].shape[-1]) if root[quants[0]].shape else 0
        return pf

    def get(self, quant: str) -> np.ndarray:
        """Load (and cache) one quantity array by name, e.g. 'x1', 'p1', 'ene'."""
        if quant in self._data:
            return self._data[quant]
        with h5py.File(self.filename, "r") as f:
            if quant not in f:
                raise KeyError(f"quantity '{quant}' not found in {self.filename}")
            arr = np.asarray(f[quant][()])
        self._data[quant] = arr
        return arr

    def label(self, quant: str) -> str:
        return self.labels.get(quant, quant)

    def unit(self, quant: str) -> str:
        return self.units.get(quant, "")

    def to_dataset(self, quant: str) -> Dataset:
        return Dataset(
            name=quant, data=self.get(quant), axes=("particle",), units=self.unit(quant),
            time=self.time, metadata={"label": self.label(quant), "iteration": self.iteration},
            source=self.filename, simulation_metadata={"format": "Simulation", "iteration": self.iteration},
        )


def is_particle_file(filename: str) -> bool:
    try:
        with h5py.File(filename, "r") as f:
            if "AXIS" in f:
                return False
            root = f["/"]
            quants = _attr(root, "QUANTS", None)
            if quants:
                return True
            # heuristic: several 1D datasets of equal length, no AXIS group
            datasets = [k for k in root.keys() if isinstance(root[k], h5py.Dataset)]
            if len(datasets) < 2:
                return False
            shapes = {root[k].shape for k in datasets}
            return len(shapes) == 1 and len(next(iter(shapes))) == 1
    except Exception:
        return False
