from __future__ import annotations

try:
    from vispy import scene
    from vispy.scene import visuals
    VISPY_AVAILABLE = True
except Exception:
    scene = None
    visuals = None
    VISPY_AVAILABLE = False

class VisPyFieldRenderer:
    """GPU-backed 2D field renderer. Imports VisPy lazily and is optional."""
    def __init__(self, parent=None):
        if not VISPY_AVAILABLE:
            raise RuntimeError('VisPy is not installed. Install vispy and a working OpenGL driver.')
        self.canvas = scene.SceneCanvas(keys='interactive', show=False, bgcolor='white', parent=parent)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.image = None
        self._extent = None

    def widget(self):
        return self.canvas.native

    def set_data(self, data, extent=None, cmap='viridis'):
        import numpy as np
        arr = np.asarray(data, dtype=np.float32)
        if arr.ndim != 2:
            raise ValueError('VisPy 2D field rendering requires a 2D array.')
        if self.image is None:
            self.image = visuals.Image(arr, cmap=cmap, interpolation='nearest', parent=self.view.scene)
        else:
            self.image.set_data(arr)
            try:
                self.image.cmap = cmap
            except Exception:
                pass
        if extent is not None:
            self._extent = tuple(extent)
        self.view.camera.set_range(x=(0, arr.shape[1]), y=(0, arr.shape[0]), margin=0.02)
        self.canvas.update()

    def set_clim(self, vmin, vmax):
        if self.image is not None:
            try:
                self.image.clim = (float(vmin), float(vmax))
            except Exception:
                pass
            self.canvas.update()

    def set_opacity(self, value):
        if self.image is not None:
            self.image.opacity = float(value)
            self.canvas.update()

    def reset_view(self):
        if self.image is not None:
            shape = self.image.size
            self.view.camera.set_range(x=(0, shape[1]), y=(0, shape[0]), margin=0.02)
