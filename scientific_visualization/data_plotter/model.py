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

    # -- In-memory editing -------------------------------------------------
    # None of these touch the source file; they mutate this table's own
    # in-memory arrays only. Every method keeps `values` a 2D float array
    # shaped (row_count, column_count) in sync with `columns`, so the rest
    # of the app (plotting, the data table widget, statistics) never needs
    # to know editing happened.

    def add_column(self, name: str, values) -> int:
        """Append a new column and return its index."""
        values = np.asarray(values, dtype=float).reshape(-1)
        if values.size != self.row_count:
            raise ValueError(f"New column has {values.size} values but the table has {self.row_count} rows")
        name = name.strip() or f"Column {self.column_count + 1}"
        self.columns = [*self.columns, name]
        self.values = np.column_stack([self.values, values])
        return self.column_count - 1

    def remove_column(self, index: int) -> None:
        if not (0 <= index < self.column_count):
            raise IndexError(f"column index {index} is out of range")
        if self.column_count <= 1:
            raise ValueError("Cannot remove the last remaining column")
        self.columns = [c for i, c in enumerate(self.columns) if i != index]
        self.values = np.delete(self.values, index, axis=1)

    def rename_column(self, index: int, name: str) -> None:
        if not (0 <= index < self.column_count):
            raise IndexError(f"column index {index} is out of range")
        name = name.strip()
        if not name:
            raise ValueError("Column name cannot be empty")
        self.columns = [name if i == index else c for i, c in enumerate(self.columns)]

    def add_row(self, values=None) -> int:
        """Append a new row (defaulting to NaN) and return its index."""
        if values is None:
            row = np.full(self.column_count, np.nan)
        else:
            row = np.asarray(values, dtype=float).reshape(-1)
            if row.size != self.column_count:
                raise ValueError(f"New row has {row.size} values but the table has {self.column_count} columns")
        self.values = np.vstack([self.values, row]) if self.row_count else row.reshape(1, -1)
        return self.row_count - 1

    def remove_rows(self, indices) -> None:
        indices = sorted({int(i) for i in indices})
        if not indices:
            return
        if any(i < 0 or i >= self.row_count for i in indices):
            raise IndexError("row index is out of range")
        if len(indices) >= self.row_count:
            raise ValueError("Cannot remove every row from the table")
        self.values = np.delete(self.values, indices, axis=0)

    def sort_by(self, index: int, ascending: bool = True) -> None:
        if not (0 <= index < self.column_count):
            raise IndexError(f"column index {index} is out of range")
        column = self.values[:, index]
        # NaNs sort last regardless of direction, rather than interleaving
        # unpredictably with real values under a plain descending argsort.
        order = np.argsort(column, kind="stable")
        if not ascending:
            finite_order = order[np.isfinite(column[order])][::-1]
            nan_order = order[~np.isfinite(column[order])]
            order = np.concatenate([finite_order, nan_order])
        self.values = self.values[order]

    def add_computed_column(self, name: str, expression: str) -> int:
        """Add a column computed from existing ones, e.g. ``"c/b"`` or
        ``"log(a) + 2*b"``, where column names are referenced by their
        exact header text (spaces and all). Evaluated in a restricted
        namespace exposing only NumPy math functions and this table's own
        columns -- no builtins, no attribute access, nothing file-related.
        """
        from .expressions import evaluate_column_expression
        values = evaluate_column_expression(expression, self.columns, self.values)
        return self.add_column(name, values)


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
    workload_factor: float = 1.0
    # Relative problem size for this dataset, used by weak-scaling figure
    # modes. Must be set explicitly by the user (see scaling.weak_scaling) --
    # it cannot be safely inferred from a filename.
    extra_y: list[int] = field(default_factory=list)
    # Additional Y columns (beyond `y`) plotted as their own series against
    # the same X column, from the same file. This is what lets one CSV with
    # several measurement columns (e.g. "year, house_price, salary") be
    # plotted as multiple lines on one chart without splitting it into
    # separate files -- the common general-purpose-data-analysis case.
