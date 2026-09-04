"""Region-of-interest (ROI) definitions and statistics.

Pure, GUI-independent logic per this project's architecture rule ("the
GUI must not contain scientific algorithms"): `gui/grid_tab.py` only
handles drawing the ROI shape with the mouse and displaying the results
computed here.

Scope note: this implements rectangle and ellipse ROIs with full
statistics, multiple simultaneous ROIs, JSON export, and time-evolution
across a file series (see `roi_time_series`). Polygon/freehand ROIs are
not implemented -- the shapes here cover the large majority of practical
"measure this region" use cases while keeping the mask math simple and
exactly verifiable; freehand/polygon support would need canvas-based
point collection that belongs in the GUI layer and can build on the same
`RegionOfInterest.mask()`/`roi_statistics()` functions when added.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field, asdict
from typing import Sequence

import numpy as np

from .statistics import statistics

_id_counter = itertools.count(1)


@dataclass
class RegionOfInterest:
    """A rectangle or ellipse region, defined in *physical* coordinates
    (the same units as the dataset's axes), not pixel/array indices --
    this is what makes a ROI meaningful across frames whose array
    resolution can differ but whose physical domain matches.
    """
    shape: str  # "rectangle" or "ellipse"
    x0: float
    y0: float
    x1: float
    y1: float
    label: str = ""
    id: int = field(default_factory=lambda: next(_id_counter))

    def __post_init__(self):
        if self.shape not in ("rectangle", "ellipse"):
            raise ValueError(f"shape must be 'rectangle' or 'ellipse', got {self.shape!r}")
        if self.x0 == self.x1 or self.y0 == self.y1:
            raise ValueError("ROI must have non-zero width and height")
        # Normalize so x0<x1, y0<y1 regardless of drag direction.
        if self.x0 > self.x1:
            self.x0, self.x1 = self.x1, self.x0
        if self.y0 > self.y1:
            self.y0, self.y1 = self.y1, self.y0
        if not self.label:
            self.label = f"ROI {self.id}"

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        """Physical area: exact for a rectangle, pi/4 of the bounding-box
        area for an ellipse."""
        base = self.width * self.height
        return base if self.shape == "rectangle" else base * (np.pi / 4.0)

    def mask(self, x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
        """Boolean mask of shape (len(y_coords), len(x_coords)) -- matching
        this project's `data.shape == (n_axis2, n_axis1)` convention --
        True where a grid point falls inside this ROI."""
        x_coords = np.asarray(x_coords, dtype=float)
        y_coords = np.asarray(y_coords, dtype=float)
        X, Y = np.meshgrid(x_coords, y_coords)  # shape (len(y), len(x))
        if self.shape == "rectangle":
            return (X >= self.x0) & (X <= self.x1) & (Y >= self.y0) & (Y <= self.y1)
        cx, cy = (self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0
        rx, ry = self.width / 2.0, self.height / 2.0
        return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RegionOfInterest":
        d = dict(d)
        d.pop("id", None)  # always assign a fresh id on reconstruction
        return cls(**d)


def roi_statistics(data: np.ndarray, x_coords: np.ndarray, y_coords: np.ndarray, roi: RegionOfInterest) -> dict:
    """Statistics for the portion of `data` (shape (len(y), len(x))) that
    falls inside `roi`, plus physical-coordinate-aware area/integral.

    Raises ValueError if the ROI doesn't overlap the data at all, rather
    than silently returning empty/NaN statistics.
    """
    data = np.asarray(data, dtype=float)
    x_coords = np.asarray(x_coords, dtype=float)
    y_coords = np.asarray(y_coords, dtype=float)
    if data.shape != (y_coords.size, x_coords.size):
        raise ValueError(
            f"data.shape {data.shape} does not match (len(y_coords), len(x_coords)) "
            f"= ({y_coords.size}, {x_coords.size})"
        )
    mask = roi.mask(x_coords, y_coords)
    selected = data[mask]
    finite = selected[np.isfinite(selected)]
    if finite.size == 0:
        raise ValueError(
            f"ROI '{roi.label}' ({roi.shape}, x=[{roi.x0:.6g},{roi.x1:.6g}], "
            f"y=[{roi.y0:.6g},{roi.y1:.6g}]) contains no finite data points -- "
            f"check it overlaps the plotted domain."
        )
    stats = statistics(finite, finite_only=False)
    quantiles = {f"p{p}": float(np.percentile(finite, p)) for p in (5, 25, 50, 75, 95)}

    # Area-weighted integral: each selected grid point contributes
    # value * (per-point physical cell area), approximated from the local
    # coordinate spacing so non-uniform axes are still handled reasonably.
    dx = np.gradient(x_coords) if x_coords.size > 1 else np.ones_like(x_coords)
    dy = np.gradient(y_coords) if y_coords.size > 1 else np.ones_like(y_coords)
    cell_area = np.outer(np.abs(dy), np.abs(dx))  # shape (len(y), len(x)), matches `data`
    integral = float(np.sum(np.where(mask & np.isfinite(data), data * cell_area, 0.0)))
    covered_area = float(np.sum(np.where(mask & np.isfinite(data), cell_area, 0.0)))

    return {
        "roi": roi.to_dict(),
        "n_points": int(finite.size),
        **stats,
        **quantiles,
        "roi_area_nominal": roi.area,
        "roi_area_covered": covered_area,
        "integral": integral,
    }


def roi_time_series(
    files: Sequence[str],
    loader,
    roi: RegionOfInterest,
    progress_callback=None,
) -> list[dict]:
    """Evaluate `roi_statistics` for the same ROI across a series of grid
    files (e.g. every frame of a simulation run), returning one result
    dict per file plus its source path/time/iteration -- the "time
    evolution of ROI statistics" capability. `loader(path)` must return an
    object with `.data`, `.axes[0].values()`, `.axes[1].values()`,
    `.time`, `.time_units`, `.iteration` (i.e. a loaded GridFile).

    Files that fail to load or whose ROI doesn't overlap them are skipped
    with a recorded error rather than aborting the whole series, since a
    single bad/empty frame shouldn't discard every other frame's result.
    """
    results = []
    total = len(files)
    for i, path in enumerate(files, start=1):
        if progress_callback is not None:
            progress_callback(i, total, path)
        try:
            grid = loader(path)
            x = np.asarray(grid.axes[0].values(), dtype=float)
            y = np.asarray(grid.axes[1].values(), dtype=float)
            stats = roi_statistics(grid.data, x, y, roi)
            stats["source_file"] = path
            stats["time"] = float(grid.time)
            stats["time_units"] = grid.time_units
            stats["iteration"] = int(grid.iteration)
        except Exception as exc:
            stats = {"source_file": path, "error": str(exc)}
        results.append(stats)
    return results


def export_roi_results(results, path: str) -> str:
    """Write ROI statistics (a single roi_statistics() dict, or a list from
    roi_time_series()) to a JSON file. Returns the path written."""
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=float)
    return path
