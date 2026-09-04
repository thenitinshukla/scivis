from __future__ import annotations

import numpy as np

from ..core.data import Dataset


class LineoutAnalyzer:
    def lineout(self, dataset: Dataset, axis: str | int = 0, position=None, indices=None):
        if dataset.ndim < 1:
            raise ValueError("Lineouts require at least a 1D dataset")
        axis_i = dataset.axis_index(axis)
        if dataset.ndim == 1:
            return dataset.coordinates[0].values, dataset.data

        selectors = [slice(None)] * dataset.ndim
        if indices is not None:
            if len(indices) != dataset.ndim:
                raise ValueError("indices must have one entry per dataset dimension")
            selectors = list(indices)
        else:
            for i in range(dataset.ndim):
                if i != axis_i:
                    selectors[i] = dataset.shape[i] // 2

        if position is not None:
            fixed = [i for i in range(dataset.ndim) if i != axis_i]
            if len(fixed) != 1:
                raise ValueError("coordinate-based position requires exactly one fixed dimension for ndim > 2")
            fixed_i = fixed[0]
            coords = dataset.coordinates[fixed_i].values
            if not np.isfinite(position) or position < coords.min() or position > coords.max():
                raise ValueError(f"Lineout position {position} is outside [{coords.min()}, {coords.max()}]")
            idx = float(np.interp(position, coords, np.arange(coords.size)))
            i0, i1 = int(np.floor(idx)), min(int(np.floor(idx)) + 1, coords.size - 1)
            w = idx - i0
            s0, s1 = list(selectors), list(selectors)
            s0[fixed_i], s1[fixed_i] = i0, i1
            values = dataset.data[tuple(s0)] * (1 - w) + dataset.data[tuple(s1)] * w
        else:
            values = dataset.data[tuple(selectors)]
        return dataset.coordinates[axis_i].values, np.asarray(values)

    def along_x1(self, dataset, position=None, indices=None):
        return self.lineout(dataset, axis="x1", position=position, indices=indices)

    def along_x2(self, dataset, position=None, indices=None):
        return self.lineout(dataset, axis="x2", position=position, indices=indices)

    def along_x3(self, dataset, position=None, indices=None):
        return self.lineout(dataset, axis="x3", position=position, indices=indices)
