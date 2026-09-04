from __future__ import annotations

from pathlib import Path



class DataService:
    """GUI-independent application service for browsing and loading scientific data."""

    def __init__(self, reader=None):
        from ...io.simulation import SimulationReader
        self.reader = reader or SimulationReader()

    def discover(self, path: str | Path):
        return self.reader.discover(path)

    def load(self, path: str | Path, quantity: str | None = None):
        return self.reader.load(path, quantity=quantity)

    def generic_discover(self, path: str | Path):
        from ...io.hdf5.generic import discover_hdf5_datasets
        return discover_hdf5_datasets(path)
