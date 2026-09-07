from __future__ import annotations

from pathlib import Path

import h5py

from ..hdf5.base import DataReader, DatasetDescriptor
from ..grid import GridFile, is_grid_file, open_h5
from ..particles import ParticleFile, is_particle_file
from ..tracks import TracksFile, is_tracks_file


class SimulationReader(DataReader):
    """Simulation-aware HDF5 reader that converts native readers to shared models."""

    def can_read(self, path: str | Path) -> bool:
        path = str(path)
        return is_grid_file(path) or is_tracks_file(path) or is_particle_file(path)

    def discover(self, path: str | Path) -> list[DatasetDescriptor]:
        # Open the file once and classify+read metadata off the same handle,
        # instead of opening it up to 4 times (once per is_*_file probe, plus
        # once more for the metadata read) -- see `open_h5` for why this
        # matters when browsing many simulation files.
        with open_h5(str(path)) as f:
            if is_grid_file(f):
                info = GridFile.info(f)
                return [DatasetDescriptor(info.dataset_name, info.shape, info.units)]
            if is_tracks_file(f):
                info = TracksFile.info(f)
                return [DatasetDescriptor(q, (sum(info._counts) if info._counts is not None else 0,), info.unit(q)) for q in info.quants]
            if is_particle_file(f):
                info = ParticleFile.info(f)
                return [DatasetDescriptor(q, (info.npar,), info.unit(q)) for q in info.quants]
            raise ValueError(f"Unsupported Simulation HDF5 structure: '{path}'")

    def load(self, path: str | Path, quantity: str | None = None):
        with open_h5(str(path)) as f:
            if is_grid_file(f):
                return GridFile.load(f).to_dataset()
            if is_tracks_file(f):
                tf = TracksFile.info(f)
                q = quantity or (tf.quants[0] if tf.quants else None)
                if q is None:
                    raise ValueError(f"No track quantities found in '{path}'")
                return tf.to_dataset(q)
            if is_particle_file(f):
                pf = ParticleFile.info(f)
                q = quantity or (pf.quants[0] if pf.quants else None)
                if q is None:
                    raise ValueError(f"No particle quantities found in '{path}'")
                return pf.to_dataset(q)
            raise ValueError(f"Unsupported Simulation HDF5 structure: '{path}'")
