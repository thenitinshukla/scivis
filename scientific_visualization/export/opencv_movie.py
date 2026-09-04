from __future__ import annotations
from pathlib import Path
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except Exception:
    cv2 = None
    OPENCV_AVAILABLE = False


def _limits(arr, vmin=None, vmax=None, symmetric=False, clip_percentile=0.0):
    finite = np.asarray(arr)[np.isfinite(arr)]
    if finite.size == 0:
        raise ValueError('Frame contains no finite values.')
    lo = float(np.min(finite)) if vmin is None else float(vmin)
    hi = float(np.max(finite)) if vmax is None else float(vmax)
    if clip_percentile:
        lo, hi = np.percentile(finite, [clip_percentile, 100 - clip_percentile])
    if symmetric:
        m = max(abs(lo), abs(hi)); lo, hi = -m, m
    if lo == hi:
        pad = max(abs(lo) * 1e-6, 1e-12); lo -= pad; hi += pad
    if lo >= hi:
        raise ValueError(f'Invalid limits: {lo} >= {hi}')
    return float(lo), float(hi)


def export_grid_movie_opencv(files, output_path, *, fps=10, cmap='viridis', vmin=None, vmax=None,
                              symmetric=False, clip_percentile=0.0, frame_start=0, frame_end=None,
                              frame_step=1, title_prefix='', size=None, loader=None,
                              progress_callback=None, verbose=True):
    """Encode scientific 2D field frames directly with OpenCV VideoWriter.

    Rendering uses a Matplotlib colormap lookup to preserve scientific color
    maps, while OpenCV handles image assembly and MP4/AVI encoding.

    If `verbose` (default True), each frame's progress is printed to
    stdout as it is encoded, so running this from a terminal shows which
    frame is currently being processed instead of appearing to hang.
    `progress_callback(frame_index, total_frames, path)` is also invoked
    per frame for GUI use.
    """
    if not OPENCV_AVAILABLE:
        raise RuntimeError('OpenCV is not installed. Install opencv-python.')
    from matplotlib import colormaps
    from ..io.grid import GridFile
    loader = loader or GridFile.load
    paths = [str(p) for p in files]
    if not paths:
        raise ValueError('No frames supplied.')
    end = len(paths) - 1 if frame_end is None else min(int(frame_end), len(paths)-1)
    start = max(0, int(frame_start))
    selected = paths[start:end+1:int(frame_step)]
    if not selected:
        raise ValueError('No frames selected.')
    first = loader(selected[0])
    if first.ndim != 2:
        raise ValueError('OpenCV movie export supports 2D scalar grid fields.')
    lo, hi = _limits(first.data, vmin=vmin, vmax=vmax, symmetric=symmetric, clip_percentile=clip_percentile)
    lut = colormaps.get_cmap(cmap)(np.linspace(0, 1, 256))[:, :3]
    if size is None:
        width = int(first.shape[1] if len(first.shape) > 1 else first.shape[0])
        height = int(first.shape[0] if first.shape else 1)
    else:
        width, height = int(size[0]), int(size[1])
    out = str(Path(output_path))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*('mp4v' if Path(out).suffix.lower() == '.mp4' else 'MJPG'))
    writer = cv2.VideoWriter(out, fourcc, float(fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError('OpenCV could not open the video encoder. Try an .avi output or install a codec-enabled OpenCV build.')
    count = 0
    total = len(selected)
    if verbose:
        print(f"[movie export] starting: {total} frame(s) -> {out}", flush=True)
    try:
        for i, path in enumerate(selected, start=1):
            if verbose:
                print(f"[movie export] frame {i}/{total}: {Path(path).name}", flush=True)
            if progress_callback is not None:
                progress_callback(i, total, path)
            grid = loader(path)
            arr = np.asarray(grid.data, dtype=float)
            if arr.shape != tuple(first.shape):
                raise ValueError(f"Frame '{path}' has shape {arr.shape}, expected {first.shape}.")
            scaled = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
            idx = np.nan_to_num(scaled * 255.0, nan=0.0).astype(np.uint8)
            rgb = (lut[idx] * 255.0).astype(np.uint8)
            frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            if (frame.shape[1], frame.shape[0]) != (width, height):
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            label = title_prefix.strip() or getattr(grid, 'label', getattr(grid, 'name', 'field'))
            text = f'{label}  t={getattr(grid, "time", 0.0):g}  iter={getattr(grid, "iteration", 0)}'
            cv2.putText(frame, text, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame, text, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0,0,0), 1, cv2.LINE_AA)
            writer.write(frame)
            count += 1
    finally:
        writer.release()
    if verbose:
        print(f"[movie export] done: {count} frame(s) written to {out}", flush=True)
    return count
