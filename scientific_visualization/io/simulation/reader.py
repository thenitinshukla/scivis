from __future__ import annotations

from pathlib import Path

from ..hdf5.base import DataReader, DatasetDescriptor
from ..grid import GridFile, is_grid_file
from ..particles import ParticleFile, is_particle_file
from ..tracks import TracksFile, is_tracks_file


class SimulationReader(DataReader):
    """Simulation-aware HDF5 reader that converts native readers to shared models."""

    def can_read(self, path: str | Path) -> bool:
        path = str(path)
        return is_grid_file(path) or is_particle_file(path) or is_tracks_file(path)

    def discover(self, path: str | Path) -> list[DatasetDescriptor]:
        if is_grid_file(path):
            info = GridFile.info(str(path))
            return [DatasetDescriptor(info.dataset_name, info.shape, info.units)]
        if is_particle_file(path):
            info = ParticleFile.info(str(path))
            return [DatasetDescriptor(q, (info.npar,), info.unit(q)) for q in info.quants]
        if is_tracks_file(path):
            info = TracksFile.info(str(path))
            return [DatasetDescriptor(q, (sum(info._counts) if info._counts is not None else 0,), info.unit(q)) for q in info.quants]
        raise ValueError(f"Unsupported Simulation HDF5 structure: '{path}'")

    def load(self, path: str | Path, quantity: str | None = None):
        if is_grid_file(path):
            return GridFile.load(str(path)).to_dataset()
        if is_particle_file(path):
            pf = ParticleFile.info(str(path))
            q = quantity or (pf.quants[0] if pf.quants else None)
            if q is None:
                raise ValueError(f"No particle quantities found in '{path}'")
            return pf.to_dataset(q)
        if is_tracks_file(path):
            tf = TracksFile.info(str(path))
            q = quantity or (tf.quants[0] if tf.quants else None)
            if q is None:
                raise ValueError(f"No track quantities found in '{path}'")
            return tf.to_dataset(q)
        raise ValueError(f"Unsupported Simulation HDF5 structure: '{path}'")
