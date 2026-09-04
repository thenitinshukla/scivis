from __future__ import annotations

from pathlib import Path

import h5py

from .base import DatasetDescriptor


def discover_hdf5_datasets(path: str | Path) -> list[DatasetDescriptor]:
    """Discover datasets without reading their array payloads."""
    path = str(path)
    try:
        with h5py.File(path, "r") as f:
            out: list[DatasetDescriptor] = []
            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    units = obj.attrs.get("UNITS", "")
                    if isinstance(units, bytes):
                        units = units.decode("utf-8", "replace")
                    out.append(DatasetDescriptor(name=name, shape=tuple(obj.shape), units=str(units), kind="scalar"))
            f.visititems(visitor)
            return out
    except OSError as exc:
        raise ValueError(f"Invalid or truncated HDF5 file '{path}': {exc}") from exc


def validate_file(path: str | Path) -> None:
    try:
        with h5py.File(path, "r"):
            pass
    except OSError as exc:
        raise ValueError(f"Invalid or truncated HDF5 file '{path}': {exc}") from exc
