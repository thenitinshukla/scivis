from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from .vispy_renderer import VISPY_AVAILABLE, VisPyFieldRenderer

class GPUFieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.renderer = None
        if VISPY_AVAILABLE:
            self.renderer = VisPyFieldRenderer(self)
            self.layout.addWidget(self.renderer.widget())
        else:
            self.layout.addWidget(QLabel('GPU rendering is unavailable. Install VisPy and an OpenGL-capable Qt environment.'))

    def set_data(self, data, extent=None, cmap='viridis'):
        if self.renderer:
            self.renderer.set_data(data, extent=extent, cmap=cmap)

    def set_clim(self, vmin, vmax):
        if self.renderer:
            self.renderer.set_clim(vmin, vmax)

    def reset_view(self):
        if self.renderer:
            self.renderer.reset_view()
