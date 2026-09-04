from __future__ import annotations

from pathlib import Path
import json
import numpy as np

from ..core.data import Dataset


def export_dataset(dataset: Dataset, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".npz":
        np.savez_compressed(path, data=dataset.data, **{f"coord_{i}": c.values for i,c in enumerate(dataset.coordinates)})
        return
    if path.suffix.lower() == ".json":
        payload = {"name": dataset.name, "shape": dataset.shape, "axes": dataset.axes, "units": dataset.units, "time": dataset.time, "source": dataset.source, "metadata": dict(dataset.metadata)}
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return
    raise ValueError("Supported dataset exports are .npz and .json")
