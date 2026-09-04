from __future__ import annotations

from pathlib import Path


def export_figure(figure, path, *, dpi=300, transparent=False, background=None, bbox_inches="tight"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = dict(dpi=dpi, transparent=transparent, bbox_inches=bbox_inches)
    if background is not None:
        kwargs["facecolor"] = background
    figure.savefig(path, **kwargs)
