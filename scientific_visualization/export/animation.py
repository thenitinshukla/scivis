"""Animation export for time-resolved scientific grid data."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

from matplotlib.animation import FFMpegWriter, PillowWriter
from matplotlib.colors import LogNorm, Normalize
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np


def _configure_ffmpeg() -> bool:
    """Use system ffmpeg or the optional imageio-ffmpeg bundled executable."""
    try:
        writer = FFMpegWriter(fps=1)
        if writer.isAvailable():
            return True
    except Exception:
        pass
    try:
        import matplotlib as mpl
        from imageio_ffmpeg import get_ffmpeg_exe
        mpl.rcParams["animation.ffmpeg_path"] = get_ffmpeg_exe()
        return bool(FFMpegWriter(fps=1).isAvailable())
    except Exception:
        return False


def ffmpeg_available() -> bool:
    return _configure_ffmpeg()


def _normalization(data: np.ndarray, normalization: str, vmin: float | None, vmax: float | None):
    finite = np.asarray(data)[np.isfinite(data)]
    if finite.size == 0:
        raise ValueError("The selected frame contains no finite values.")
    lo = float(np.min(finite)) if vmin is None else float(vmin)
    hi = float(np.max(finite)) if vmax is None else float(vmax)
    if lo == hi:
        pad = max(abs(lo) * 1e-6, 1e-12)
        lo, hi = lo - pad, hi + pad
    elif not lo < hi:
        raise ValueError(f"Invalid movie color range: minimum {lo:g} must be less than maximum {hi:g}.")
    if normalization == "log":
        if lo <= 0 or hi <= 0:
            raise ValueError("Logarithmic normalization requires positive color limits.")
        return LogNorm(vmin=lo, vmax=hi)
    return Normalize(vmin=lo, vmax=hi)


def export_grid_movie(
    files: Iterable[str],
    output_path: str | os.PathLike,
    *,
    frame_start: int = 0,
    frame_end: int | None = None,
    frame_step: int = 1,
    fps: float = 10.0,
    cmap: str = "viridis",
    normalization: str = "linear",
    vmin: float | None = None,
    vmax: float | None = None,
    symmetric: bool = False,
    clip_percentile: float = 0.0,
    aspect: str = "auto",
    interpolation: str = "nearest",
    title_prefix: str = "",
    figsize: tuple[float, float] = (7.0, 5.5),
    dpi: int = 150,
    loader: Callable[[str], object] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
    verbose: bool = True,
) -> int:
    """Render a sequence of 2D grid files to GIF or MP4.

    The source HDF5 files are read one frame at a time. No expanded 3D array
    is created. A fixed color range is recommended for quantitative movies.
    Returns the number of rendered frames.

    If `verbose` (default True), each frame's progress is printed to
    stdout as it is rendered -- useful when running from a terminal,
    since encoding a long movie can otherwise look like the application
    has stalled. `progress_callback(frame_index, total_frames, path)` is
    also invoked per frame, e.g. for a GUI status bar.
    """
    paths = [str(p) for p in files]
    if not paths:
        raise ValueError("No frames were provided for movie export.")
    if frame_step <= 0:
        raise ValueError("Frame step must be positive.")
    if fps <= 0:
        raise ValueError("FPS must be positive.")
    frame_end = len(paths) - 1 if frame_end is None else min(int(frame_end), len(paths) - 1)
    frame_start = max(0, int(frame_start))
    if frame_start > frame_end:
        raise ValueError("Movie start frame must not be after the end frame.")

    if loader is None:
        from ..io.grid import GridFile
        loader = GridFile.load

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    suffix = out.suffix.lower()
    if suffix not in {".gif", ".mp4"}:
        raise ValueError("Movie output must use .gif or .mp4 extension.")

    selected = paths[frame_start : frame_end + 1 : frame_step]
    first = loader(selected[0])
    if getattr(first, "ndim", 0) != 2:
        raise ValueError("Movie export currently supports 2D scalar grid datasets.")

    # Compute a fixed range when the caller does not provide one and requested
    # clipping/symmetry. This scans each selected frame once, without keeping
    # all arrays in memory simultaneously.
    effective_vmin, effective_vmax = vmin, vmax
    if clip_percentile > 0 or symmetric or vmin is None or vmax is None:
        if clip_percentile > 0 or symmetric:
            values = []
            for path in selected:
                g = loader(path)
                arr = np.asarray(g.data)
                finite = arr[np.isfinite(arr)]
                if finite.size:
                    values.append(finite)
            if values:
                finite = np.concatenate(values)
                lo, hi = np.percentile(finite, [clip_percentile, 100.0 - clip_percentile]) if clip_percentile > 0 else (float(finite.min()), float(finite.max()))
                if symmetric and not (vmin is not None or vmax is not None):
                    m = max(abs(float(lo)), abs(float(hi)))
                    lo, hi = -m, m
                effective_vmin = float(lo) if effective_vmin is None else effective_vmin
                effective_vmax = float(hi) if effective_vmax is None else effective_vmax
            else:
                raise ValueError("No finite values were found in the selected movie frames.")

    # Build a bare Agg-backed Figure instead of going through `pyplot`.
    # `pyplot` keeps a global current-figure/backend state that is not safe
    # to touch from a worker thread while the Qt GUI thread may simultaneously
    # be drawing its own embedded Matplotlib canvas; a plain `Figure` +
    # `FigureCanvasAgg` has no such shared state and is safe for background
    # rendering (Pillow/FFMpeg writers only need `fig.canvas.draw()`).
    fig = Figure(figsize=figsize, dpi=dpi)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    first_data = np.asarray(first.data)
    extent = first.extent()
    norm = _normalization(first_data, normalization, effective_vmin, effective_vmax)
    im = ax.imshow(first_data, origin="lower", extent=extent, aspect=aspect, cmap=cmap, norm=norm, interpolation=interpolation)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"{getattr(first, 'label', getattr(first, 'name', 'quantity'))} [{first.units}]" if getattr(first, "units", "") else getattr(first, "label", getattr(first, "name", "quantity")))
    ax.set_xlabel(first.axes[0].label if first.axes else "x1")
    ax.set_ylabel(first.axes[1].label if len(first.axes) > 1 else "x2")

    def draw(path: str):
        grid = loader(path)
        data = np.asarray(grid.data)
        if data.ndim != 2:
            raise ValueError(f"Frame '{path}' is not 2D.")
        if data.shape != first_data.shape:
            raise ValueError(f"Frame '{path}' has shape {data.shape}, expected {first_data.shape}.")
        im.set_data(data)
        im.set_extent(grid.extent())
        title = title_prefix.strip() or f"{getattr(grid, 'label', getattr(grid, 'name', 'quantity'))}"
        im.axes.set_title(f"{title}    t = {getattr(grid, 'time', 0.0):g} {getattr(grid, 'time_units', '')}    (iter {getattr(grid, 'iteration', 0)})")
        return im

    writer = PillowWriter(fps=fps) if suffix == ".gif" else FFMpegWriter(fps=fps, metadata={"title": "Scientific simulation"})
    if suffix == ".mp4" and not _configure_ffmpeg():
        pass  # non-pyplot Figure: no global state to close/leak
        raise RuntimeError("MP4 export requires ffmpeg. Install ffmpeg or use GIF export.")

    total = len(selected)
    if verbose:
        print(f"[movie export] starting: {total} frame(s) -> {out}", flush=True)
    with writer.saving(fig, str(out), dpi=dpi):
        for i, path in enumerate(selected, start=1):
            if verbose:
                print(f"[movie export] frame {i}/{total}: {Path(path).name}", flush=True)
            if progress_callback is not None:
                progress_callback(i, total, path)
            draw(path)
            fig.canvas.draw()
            writer.grab_frame()
    if verbose:
        print(f"[movie export] done: {total} frame(s) written to {out}", flush=True)
    pass  # non-pyplot Figure: no global state to close/leak
    return len(selected)
