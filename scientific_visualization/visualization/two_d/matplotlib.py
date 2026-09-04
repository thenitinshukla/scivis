from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize, SymLogNorm
from matplotlib.axes import Axes

from ...core.configuration import RenderingConfig
from ...core.data import Dataset
from ...core.coordinates import coordinate_edges


def _norm_and_limits(data, config):
    finite = np.asarray(data)[np.isfinite(data)]
    if finite.size == 0:
        raise ValueError("Dataset contains no finite values")
    vmin = config.vmin if config.vmin is not None else float(np.min(finite))
    vmax = config.vmax if config.vmax is not None else float(np.max(finite))
    if config.symmetric_limits:
        m = max(abs(vmin), abs(vmax))
        vmin, vmax = -m, m
    if config.normalization == "log":
        positive = finite[finite > 0]
        if positive.size == 0:
            raise ValueError("Log normalization requires at least one positive value")
        vmin = vmin if vmin is not None and vmin > 0 else float(np.min(positive))
        vmax = vmax if vmax is not None and vmax > vmin else float(np.max(positive))
        return LogNorm(vmin=vmin, vmax=vmax), vmin, vmax
    return Normalize(vmin=vmin, vmax=vmax), vmin, vmax


def plot_2d(dataset: Dataset, ax: Axes | None = None, config: RenderingConfig | None = None):
    config = config or RenderingConfig()
    config.validate()
    if dataset.ndim != 2:
        raise ValueError("plot_2d expects a 2D dataset")
    ax = ax or plt.subplots(figsize=(config.figure_width, config.figure_height))[1]
    norm, _, _ = _norm_and_limits(dataset.data, config)
    x = dataset.coordinates[0].values
    y = dataset.coordinates[1].values
    im = ax.pcolormesh(coordinate_edges(x), coordinate_edges(y), dataset.data.T, cmap=config.colormap, norm=norm, shading="auto")
    if config.show_colorbar:
        orientation = "vertical" if config.colorbar_position in ("left", "right") else "horizontal"
        cbar = ax.figure.colorbar(im, ax=ax, orientation=orientation, location=config.colorbar_position,
                                  fraction=min(max(config.colorbar_width or 0.10, 0.02), 0.5))
        cbar.set_label(label_with_units(dataset.name, dataset.units), rotation=config.colorbar_label_rotation,
                       labelpad=config.colorbar_label_pad)
        if config.colorbar_label_position != "auto":
            if orientation == "vertical":
                cbar.ax.yaxis.set_label_position(config.colorbar_label_position)
            else:
                cbar.ax.xaxis.set_label_position(config.colorbar_label_position)
        cbar.outline.set_visible(bool(config.colorbar_box))
    ax.set_aspect(config.aspect)
    ax.set_xlabel(config.xlabel or label_with_units(dataset.coordinates[0].label or dataset.axes[0], dataset.coordinates[0].units))
    ax.set_ylabel(config.ylabel or label_with_units(dataset.coordinates[1].label or dataset.axes[1], dataset.coordinates[1].units))
    ax.set_title(config.title or dataset.name)
    return ax


def label_with_units(label, units):
    return f"{label} [{units}]" if units else label
