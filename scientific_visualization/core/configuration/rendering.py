from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RenderingConfig:
    colormap: str = "viridis"
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    normalization: str = "linear"
    symmetric_limits: bool = False
    show_colorbar: bool = True
    opacity: float = 1.0
    aspect: str = "auto"
    interpolation: str = "nearest"
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    zlabel: Optional[str] = None
    figure_width: float = 7.0
    figure_height: float = 5.0
    dpi: int = 300
    background: Optional[str] = None
    transparent: bool = False
    font_family: str = "DejaVu Sans"
    font_size: float = 10.0
    bbox_inches: str = "tight"

    # Colorbar/scalar-bar placement (2D Matplotlib view and 3D PyVista view).
    # `colorbar_position` is one of "right", "left", "top", "bottom".
    colorbar_position: str = "right"
    # Draws a visible border (and, in the 3D view, an opaque background) box
    # around the colorbar/scalar bar instead of a borderless overlay.
    colorbar_box: bool = False
    # 3D view only: PyVista supports natively dragging/resizing a scalar bar
    # with the mouse at runtime when this is True.
    colorbar_interactive: bool = True
    colorbar_width: Optional[float] = None
    colorbar_height: Optional[float] = None
    colorbar_label_position: str = "auto"
    colorbar_label_rotation: float = 90.0
    colorbar_label_pad: float = 8.0
    contour_filled: bool = False
    hillshade: bool = False
    antialiasing: bool = True
    lighting: bool = True
    eye_dome_lighting: bool = False
    smooth_shading: bool = True
    show_edges: bool = False
    edge_color: str = "black"
    render_decimation: float = 1.0
    depth_peeling: bool = False
    ssao: bool = False
    stereo: bool = False
    hidden_line_removal: bool = False

    COLORBAR_POSITIONS = ("right", "left", "top", "bottom")

    def validate(self):
        if self.normalization not in {"linear", "log"}:
            raise ValueError("normalization must be 'linear' or 'log'")
        if self.vmin is not None and self.vmax is not None and self.vmin >= self.vmax:
            raise ValueError("vmin must be smaller than vmax")
        if self.normalization == "log":
            for value in (self.vmin, self.vmax):
                if value is not None and value <= 0:
                    raise ValueError("log normalization requires positive vmin/vmax")
        if not 0 < self.opacity <= 1:
            raise ValueError("opacity must be in (0, 1]")
        if self.colorbar_position not in self.COLORBAR_POSITIONS:
            raise ValueError(f"colorbar_position must be one of {self.COLORBAR_POSITIONS}")
        for name, value in (("colorbar_width", self.colorbar_width), ("colorbar_height", self.colorbar_height)):
            if value is not None and not 0 < value <= 1:
                raise ValueError(f"{name} must be in (0, 1] when specified")
        if self.colorbar_label_position not in {"auto", "left", "right", "top", "bottom"}:
            raise ValueError("invalid colorbar_label_position")
        if not -360 <= self.colorbar_label_rotation <= 360:
            raise ValueError("colorbar_label_rotation must be between -360 and 360 degrees")
        if self.colorbar_label_pad < 0:
            raise ValueError("colorbar_label_pad must be non-negative")
        if not 0 < self.render_decimation <= 1:
            raise ValueError("render_decimation must be in (0, 1]")
