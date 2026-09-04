from __future__ import annotations

from pathlib import Path
import numpy as np

from ..io.grid import GridFile
from .spectral import temporal_spectrum, k_omega


class SimulationSeries:
    """Discover and analyze many Simulation grid frames without treating one frame as the simulation."""
    def __init__(self, files, quantity=None):
        self.files = [str(Path(f)) for f in files]
        self.quantity = quantity
        self._frames = []

    @classmethod
    def from_folder(cls, folder, quantity=None):
        files = sorted(str(p) for p in Path(folder).iterdir() if p.suffix.lower() in {".h5", ".hdf5"})
        if not files:
            raise ValueError(f"No HDF5 files found in '{folder}'")
        return cls(files, quantity=quantity)

    def discover(self):
        frames = []
        for path in self.files:
            try:
                info = GridFile.info(path)
                if self.quantity and info.dataset_name != self.quantity and info.name != self.quantity and info.label != self.quantity:
                    continue
                frames.append((path, info.time, info.iteration, info.dataset_name, info.shape, info.units, info.label))
            except Exception:
                continue
        frames.sort(key=lambda x: (x[1], x[2], x[0]))
        if not frames:
            raise ValueError("No compatible Simulation grid frames were found for the selected quantity")
        self._frames = frames
        if self.quantity is None:
            self.quantity = frames[0][3]
        return frames

    @property
    def frames(self):
        return self._frames or self.discover()

    def load(self, index):
        path = self.frames[index][0]
        return GridFile.load(path).to_dataset()

    def temporal_reduction(self, reduction="mean"):
        times, iterations, values = [], [], []
        for idx, (path, time, iteration, *_rest) in enumerate(self.frames):
            ds = self.load(idx)
            data = np.asarray(ds.data, dtype=float)
            finite = data[np.isfinite(data)]
            if not finite.size:
                value = np.nan
            elif reduction == "mean": value = np.mean(finite)
            elif reduction == "sum": value = np.sum(finite)
            elif reduction == "max": value = np.max(finite)
            elif reduction == "min": value = np.min(finite)
            elif reduction == "rms": value = np.sqrt(np.mean(finite**2))
            else: raise ValueError(f"Unsupported reduction '{reduction}'")
            times.append(time); iterations.append(iteration); values.append(value)
        return np.asarray(times), np.asarray(iterations), np.asarray(values)

    def temporal_frequency(self, reduction="mean"):
        times, iterations, values = self.temporal_reduction(reduction)
        result = temporal_spectrum(values, times)
        return times, iterations, values, result

    def k_omega(self, axis="x1", *, max_frames=None):
        frames = self.frames[:max_frames] if max_frames else self.frames
        stack = np.stack([np.asarray(self.load(i).data, dtype=float) for i in range(len(frames))], axis=0)
        reference = self.load(0)
        spatial_index = reference.axis_index(axis)
        # Dataset data axes are physical order, so stack is (time, x1, x2, ...).
        x = reference.coordinates[spatial_index].values
        times = np.asarray([f[1] for f in frames], dtype=float)
        if stack.ndim > 2:
            other_axes = tuple(i for i in range(1, stack.ndim) if i != spatial_index + 1)
            if other_axes:
                stack = np.mean(stack, axis=other_axes)
            spatial_index = 1
        omega, k, power = k_omega(stack, x, times, spatial_axis=spatial_index, time_axis=0)
        return omega, k, power
