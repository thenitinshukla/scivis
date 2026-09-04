from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import numpy as np


@dataclass
class DatasetTable:
    path: str
    columns: list[str]
    values: np.ndarray
    delimiter: str
    has_header: bool
    skipped_comments: int = 0
    skipped_rows: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def row_count(self) -> int:
        return int(self.values.shape[0])

    @property
    def column_count(self) -> int:
        return int(self.values.shape[1])

    def column_values(self, index: int) -> np.ndarray:
        if index < 0 or index >= self.column_count:
            raise IndexError(f"column index {index} is out of range")
        return self.values[:, index]

    def set_value(self, row: int, column: int, value: float) -> None:
        """Update one numeric cell in the editable in-memory dataset.

        Source files are never modified by this operation. The caller can
        explicitly export the edited table when persistence is desired.
        """
        if not (0 <= row < self.row_count and 0 <= column < self.column_count):
            raise IndexError("cell index is out of range")
        self.values[row, column] = float(value)

    def statistics(self, index: int) -> dict[str, float]:
        values = self.column_values(index)
        mask = np.isfinite(values)
        count = int(np.count_nonzero(mask))
        if count == 0:
            return {"count": 0, "min": np.nan, "max": np.nan, "mean": np.nan, "std": np.nan}
        finite = values[mask]
        return {
            "count": count,
            "min": float(np.min(finite)),
            "max": float(np.max(finite)),
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite)),
        }


@dataclass
class DatasetPlotConfig:
    x: int = 0
    y: int = 1
    label: str = ""
    color: str = "#0072B2"
    enabled: bool = True
    line_style: str = "-"
    marker: str = "None"
    line_width: float = 1.8
    marker_size: float = 4.0
