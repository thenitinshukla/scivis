from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ...core.configuration import RenderingConfig
from ...core.data import Dataset


def label_with_units(label: str, units: str) -> str:
    return f"{label} [{units}]" if units else label


def plot_dataset(dataset: Dataset, ax: Axes | None = None, x_axis: str | int = 0, config: RenderingConfig | None = None, label: str | None = None):
    config = config or RenderingConfig()
    config.validate()
    if dataset.ndim != 1:
        raise ValueError("plot_dataset expects a 1D dataset")
    ax = ax or plt.subplots(figsize=(config.figure_width, config.figure_height))[1]
    x = dataset.coordinates[dataset.axis_index(x_axis)].values
    ax.plot(x, dataset.data, label=label or dataset.name)
    ax.set_xlabel(label_with_units(dataset.coordinates[0].label or dataset.axes[0], dataset.coordinates[0].units))
    ax.set_ylabel(label_with_units(dataset.name, dataset.units))
    if config.title:
        ax.set_title(config.title)
    if label:
        ax.legend()
    return ax


def plot_time_series(times, values, *, ax=None, config=None, label="quantity", time_units=""):
    config = config or RenderingConfig()
    config.validate()
    if ax is None:
        _, ax = plt.subplots(figsize=(config.figure_width, config.figure_height))
    ax.plot(times, values, label=label)
    ax.set_xlabel(label_with_units("time", time_units))
    ax.set_ylabel(label)
    ax.legend()
    return ax
