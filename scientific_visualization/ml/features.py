from __future__ import annotations

import numpy as np

from ..core.data import Dataset
from .core import FeatureSet


def dataset_to_features(dataset: Dataset, *, flatten: bool = True, include_coordinates: bool = True) -> FeatureSet:
    if dataset.is_vector:
        raise ValueError("dataset_to_features currently expects a scalar Dataset")
    data = np.asarray(dataset.data)
    if data.ndim == 0:
        values = data.reshape(1, 1).astype(float)
        coords = None
    else:
        values = data.reshape(-1, 1).astype(float) if flatten else data.astype(float)
        coords = None
        if include_coordinates and dataset.coordinates:
            meshes = np.meshgrid(*[c.values for c in dataset.coordinates], indexing="ij")
            coords = np.column_stack([m.reshape(-1) for m in meshes])
    names = [dataset.name]
    if include_coordinates:
        names.extend(c.name for c in dataset.coordinates)
        if coords is not None:
            values = np.column_stack([values, coords])
    return FeatureSet(values, tuple(names), coords, {"source": dataset.source, "dataset": dataset.name, "sample_indices": np.arange(values.shape[0], dtype=int)})


def sample_grid_features(dataset: Dataset, max_samples: int = 10000, seed: int = 0) -> FeatureSet:
    """Draw a bounded random subsample of grid points as ML features.

    For grids larger than ``max_samples`` this selects the sample indices
    *first* and only computes values/coordinates at those indices, instead
    of materializing a full coordinate meshgrid and flattened value array
    for every point in the grid and then discarding almost all of it. This
    matters in practice: for a 200^3 PIC field (8,000,000 points) sampling
    10,000 points previously built and discarded 7,990,000 rows of a
    (N, 1+ndim) array plus a full meshgrid, which dominates runtime and
    memory for large 3D simulations.
    """
    if dataset.is_vector:
        raise ValueError("sample_grid_features currently expects a scalar Dataset")
    data = np.asarray(dataset.data)
    n = data.size if data.ndim else 1
    if n <= max_samples:
        return dataset_to_features(dataset)

    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(n, size=max_samples, replace=False))

    flat_values = data.reshape(-1)[idx].astype(float).reshape(-1, 1)
    names = [dataset.name]
    coords = None
    values = flat_values
    if dataset.coordinates:
        # `data` is stored in the same axis order as `dataset.coordinates`
        # (see GridFile.to_dataset), so unravel_index against data.shape
        # gives the per-axis index for each sampled flat index directly,
        # with no need to build the full per-point coordinate mesh.
        unravel = np.unravel_index(idx, data.shape)
        coord_cols = [np.asarray(c.values, dtype=float)[u] for c, u in zip(dataset.coordinates, unravel)]
        coords = np.column_stack(coord_cols)
        names.extend(c.name for c in dataset.coordinates)
        values = np.column_stack([flat_values, coords])

    return FeatureSet(
        values,
        tuple(names),
        coords,
        {
            "source": dataset.source,
            "dataset": dataset.name,
            "sample_count": max_samples,
            "sample_indices": idx,
        },
    )

# Backward-compatible public name used by earlier GUI/test integrations.
def feature_matrix_from_dataset(dataset: Dataset, *, flatten: bool = True, include_coordinates: bool = True) -> FeatureSet:
    return dataset_to_features(dataset, flatten=flatten, include_coordinates=include_coordinates)
