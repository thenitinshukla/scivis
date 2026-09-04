from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .. import style


class PlotCanvas(QWidget):
    """A matplotlib Figure embedded in a Qt widget, with the standard
    pan/zoom/save toolbar plus a one-click high-resolution export button.

    Rendering API (backend-independent for GUI callers):
        draw()         – schedule a redraw; applies theme if dirty.
        draw_idle()    – same as draw(); coalesces rapid UI updates.
        flush_events() – process pending Matplotlib/Qt draw events.
        clear()        – clear the figure and schedule a redraw.

    Callers must use these methods on the PlotCanvas instance rather than
    reaching into ``self.canvas`` (the FigureCanvasQTAgg) for draw calls.
    """

    def __init__(self, parent=None, figsize=(6, 5)):
        super().__init__(parent)
        self.figure = Figure(figsize=figsize, tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.theme = "Light"
        # Reapplying the theme walks every Axes/tick/spine/label in the
        # figure (including the colorbar's own axes) -- real cost on a
        # large figure. Most redraws (dragging a gamma/contrast slider,
        # nudging a colorbar limit) don't add or restyle any new artist,
        # so there is nothing for a theme re-application to actually
        # change. Track "dirty" explicitly instead of reapplying on every
        # draw: only style changes and events that create fresh artists
        # (a new colorbar, a mode change that rebuilds the axes) need to
        # mark this again -- see grid_tab.py's refresh_plot().
        self._theme_dirty = True

        export_btn = QPushButton("Export HQ…")
        export_btn.setToolTip("Save this figure at publication resolution (300 dpi, PNG/PDF/SVG)")
        export_btn.clicked.connect(self.export_hq)

        toolbar_row = QHBoxLayout()
        toolbar_row.addWidget(self.toolbar)
        toolbar_row.addStretch(1)
        toolbar_row.addWidget(export_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar_row)
        layout.addWidget(self.canvas)

    def clear(self):
        self.figure.clear()
        self.mark_theme_dirty()  # a cleared figure's fresh axes need re-theming on next draw
        self.draw_idle()

    def deactivate_navigation(self):
        """Disable the Matplotlib toolbar interaction mode before custom mouse tools."""
        try:
            active = getattr(self.toolbar, "_active", None)
            if active == "ZOOM":
                self.toolbar.zoom()
            elif active == "PAN":
                self.toolbar.pan()
        except Exception:
            pass

    def mark_theme_dirty(self):
        """Call this whenever new artists were added/recreated (a fresh
        colorbar, a mode change that rebuilt the axes, new contour lines,
        annotations, ...) so the next draw() actually restyles them.
        Routine data-only updates don't need this."""
        self._theme_dirty = True

    def _apply_theme_if_needed(self, apply_theme=None):
        if apply_theme is None:
            apply_theme = self._theme_dirty
        if apply_theme:
            style.apply_theme(self.figure, self.theme)
            self._theme_dirty = False

    def draw(self, apply_theme=None):
        """Schedule a redraw (via draw_idle). Applies theme when dirty.

        Prefer this or draw_idle() from GUI code. Using draw_idle avoids
        forcing synchronous rasterization on every slider/control event
        so Qt can coalesce rapid updates.
        """
        self._apply_theme_if_needed(apply_theme)
        self.canvas.draw_idle()

    def draw_idle(self, apply_theme=None):
        """Schedule a coalesced redraw on the Qt event loop.

        This is the preferred entry point for interactive updates
        (slider moves, mode toggles, repeated refresh). Equivalent to
        draw() for this backend; provided so callers can use the same
        Matplotlib-style name without reaching into the FigureCanvas.
        """
        self._apply_theme_if_needed(apply_theme)
        self.canvas.draw_idle()

    def flush_events(self):
        """Process pending Matplotlib canvas events (for export / tests)."""
        self.canvas.flush_events()

    def set_theme(self, theme_name: str):
        if theme_name != self.theme:
            self.theme = theme_name
            self._theme_dirty = True

    def export_hq(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export figure", "figure.png",
            "PNG image (*.png);;PDF document (*.pdf);;SVG vector (*.svg)"
        )
        if not path:
            return
        t = style.THEMES.get(self.theme, style.LIGHT)
        self.figure.savefig(
            path, dpi=300, facecolor=t["figure_facecolor"], bbox_inches="tight"
        )
