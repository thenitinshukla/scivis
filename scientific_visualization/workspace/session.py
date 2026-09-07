"""WorkspaceSession: the object a whole Import -> Profile -> Clean ->
Transform -> Analyze -> Visualize workflow revolves around.

Design choices that matter:

- `original` is never mutated after `load()`. Every other view of the data
  (`current`) is *recomputed* from it by replaying `pipeline`, so nothing
  is ever silently lost -- switching to Profile after Clean always still
  shows you where you started, if you ask for it.
- The pipeline is a plain, ordered list of `cleaning.PipelineStep`, each
  just an operation name and a parameter dict. This is what makes undo,
  reordering, and toggling steps on/off possible without a separate
  snapshot-per-step history stack: "undo" is "remove the last step and
  recompute `current`", "reorder" is "move a list entry and recompute".
  Recomputing from scratch on every edit is deliberately simple rather
  than incrementally patching a cached frame -- correct-by-construction
  matters more here than micro-optimizing pipeline replay, and replay
  time is dominated by I/O-bound steps like parsing dates, not by list
  bookkeeping.
- Recompute never raises: a broken step's error is attached to the
  session (`self.errors`) and that step's *effect* is skipped, so one bad
  step can't strand the user with no data on screen at all.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .cleaning import PipelineStep, apply_pipeline
from .io_formats import load_any
from .profiling import DatasetProfile, profile_dataframe
from .types import ColumnType, classify_dataframe


@dataclass
class WorkspaceSession:
    name: str = ""
    original: pd.DataFrame | None = field(default=None, repr=False)
    current: pd.DataFrame | None = field(default=None, repr=False)
    pipeline: list[PipelineStep] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # -- Import --------------------------------------------------------
    def load(self, path: str | Path, *, sheet_name=0) -> None:
        path = Path(path)
        df = load_any(path, sheet_name=sheet_name)
        self.name = path.name
        self.original = df
        self.pipeline = []
        self.recompute()

    def load_dataframe(self, name: str, df: pd.DataFrame) -> None:
        """Load an already-in-memory DataFrame (e.g. the result of a SQL
        query run elsewhere) instead of a file."""
        self.name = name
        self.original = df.copy()
        self.pipeline = []
        self.recompute()

    @property
    def loaded(self) -> bool:
        return self.original is not None

    # -- Pipeline editing ------------------------------------------------
    def add_step(self, op: str, params: dict, note: str = "") -> None:
        self.pipeline.append(PipelineStep(op=op, params=params, enabled=True, note=note))
        self.recompute()

    def remove_step(self, index: int) -> None:
        if 0 <= index < len(self.pipeline):
            del self.pipeline[index]
            self.recompute()

    def move_step(self, index: int, new_index: int) -> None:
        if not (0 <= index < len(self.pipeline)) or not (0 <= new_index < len(self.pipeline)):
            return
        step = self.pipeline.pop(index)
        self.pipeline.insert(new_index, step)
        self.recompute()

    def toggle_step(self, index: int, enabled: bool | None = None) -> None:
        if 0 <= index < len(self.pipeline):
            step = self.pipeline[index]
            step.enabled = (not step.enabled) if enabled is None else enabled
            self.recompute()

    def undo(self) -> None:
        """Drop the most recent step. Since `current` is always a replay
        of `original` + `pipeline`, this is a real undo, not a "hide the
        result but keep the step" toggle."""
        if self.pipeline:
            self.pipeline.pop()
            self.recompute()

    def clear_pipeline(self) -> None:
        self.pipeline = []
        self.recompute()

    def recompute(self) -> None:
        if self.original is None:
            self.current = None
            self.errors = []
            return
        self.current, self.errors = apply_pipeline(self.original, self.pipeline)

    # -- Profiling / types ------------------------------------------------
    def profile(self, *, use_original: bool = False) -> DatasetProfile | None:
        df = self.original if use_original else self.current
        return profile_dataframe(df) if df is not None else None

    def column_types(self) -> dict[str, ColumnType]:
        return classify_dataframe(self.current) if self.current is not None else {}

    # -- Bridge to the Data Plotter's numeric-only rendering --------------
    def to_numeric_dataset(self, columns: list[str] | None = None):
        """Build a `data_plotter.model.DatasetTable` from the numeric
        columns of `current` -- the hand-off point for any chart that
        wants the Data Plotter's richer rendering (curve fits, change
        annotations, paper scaling, ...) instead of the workspace's own
        simpler chart step. Non-numeric columns are coerced with
        `pd.to_numeric(errors="coerce")` and silently dropped only if the
        result is entirely NaN (i.e. genuinely not numeric).
        """
        from ..data_plotter.model import DatasetTable
        import numpy as np

        if self.current is None:
            raise ValueError("No dataset loaded")
        cols = columns if columns is not None else list(self.current.columns)
        kept, arrays = [], []
        for c in cols:
            numeric = pd.to_numeric(self.current[c], errors="coerce")
            if numeric.notna().any():
                kept.append(c)
                arrays.append(numeric.to_numpy(dtype=float))
        if not kept:
            raise ValueError("No numeric columns available to plot")
        values = np.column_stack(arrays)
        return DatasetTable(path=self.name, columns=kept, values=values, delimiter=",", has_header=True)
