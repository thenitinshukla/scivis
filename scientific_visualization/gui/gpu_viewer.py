from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
try:
    from ..visualization.gpu.vispy_renderer import VISPY_AVAILABLE, VisPyFieldRenderer
except Exception:
    VISPY_AVAILABLE = False
    VisPyFieldRenderer = None

class GPUViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('GPU 2D Viewer (VisPy)')
        self.resize(900, 700)
        lay = QVBoxLayout(self)
        self._renderer = None
        if not VISPY_AVAILABLE:
            lay.addWidget(QLabel('VisPy is not installed or OpenGL is unavailable. Install vispy and restart the application.'))
        else:
            self._renderer = VisPyFieldRenderer(self)
            lay.addWidget(self._renderer.widget())

    def set_field(self, data, extent, cmap):
        if self._renderer is None:
            return
        self._renderer.set_data(data, extent=extent, cmap=cmap)
