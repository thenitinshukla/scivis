from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class LazyFrame:
    path: str
    index: int
    time: float | None = None
    iteration: int | None = None
    name: str = ""
    shape: tuple[int, ...] = ()


class LazyGridSeries:
    """Metadata-lazy sequence for scientific grid frames.

    Construction performs no HDF5 opens. Metadata for a frame is read only
    when that frame is selected, loaded, or when a consumer explicitly asks
    for the complete time/iteration arrays.
    """

    def __init__(self, paths, info_loader: Callable | None = None, cache_size: int = 2):
        from .grid import GridFile
        self.paths = [str(Path(p)) for p in paths]
        self._info_loader = info_loader or GridFile.info
        self._loader = GridFile.load
        self._cache_size = max(0, int(cache_size))
        self._cache = {}
        self.frames = [LazyFrame(path=p, index=i) for i, p in enumerate(self.paths)]

    def _ensure_metadata(self, index: int) -> LazyFrame:
        frame = self.frames[index]
        if frame.time is None or not frame.shape:
            info = self._info_loader(frame.path)
            frame.time = float(info.time)
            frame.iteration = int(info.iteration)
            frame.name = info.name
            frame.shape = tuple(info.shape)
        return frame

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, index):
        if index < 0:
            index += len(self.frames)
        return self._ensure_metadata(index)

    def load(self, index: int, use_cache: bool = True):
        if not self.frames:
            raise IndexError("No simulation frames are available.")
        index = int(index)
        if index < 0:
            index += len(self.frames)
        if not 0 <= index < len(self.frames):
            raise IndexError(index)
        frame = self._ensure_metadata(index)
        if use_cache and index in self._cache:
            return self._cache[index]
        grid = self._loader(frame.path)
        if use_cache and self._cache_size:
            self._cache[index] = grid
            while len(self._cache) > self._cache_size:
                self._cache.pop(next(iter(self._cache)))
        return grid

    def metadata(self, index: int) -> LazyFrame:
        return self._ensure_metadata(int(index))

    def discover_metadata(self) -> list[LazyFrame]:
        for i in range(len(self.frames)):
            self._ensure_metadata(i)
        return self.frames

    def clear_cache(self):
        self._cache.clear()

    @property
    def times(self):
        import numpy as np
        self.discover_metadata()
        return np.asarray([f.time for f in self.frames], dtype=float)

    @property
    def iterations(self):
        import numpy as np
        self.discover_metadata()
        return np.asarray([f.iteration for f in self.frames], dtype=int)
