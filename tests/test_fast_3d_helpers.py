import numpy as np
from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.core.configuration import RenderingConfig

def _ds(shape=(12, 10, 8)):
    coords = tuple(CoordinateAxis(f"x{i+1}", np.linspace(0, 1, n)) for i, n in enumerate(shape))
    x = np.linspace(0, 1, shape[0])[:,None,None]
    y = np.linspace(0, 1, shape[1])[None,:,None]
    z = np.linspace(0, 1, shape[2])[None,None,:]
    data = (x + 2*y + 3*z).astype(np.float32)
    return Dataset("f", data, ("x1","x2","x3"), coords)

def test_rendering_config_accepts_scalar_bar_size_and_fast_resolution():
    cfg = RenderingConfig(colorbar_width=.22, colorbar_height=.65, render_decimation=.5)
    cfg.validate()

def test_rendering_config_rejects_invalid_scalar_bar_size():
    import pytest
    with pytest.raises(ValueError): RenderingConfig(colorbar_width=1.1).validate()

def test_renderer_grid_cache_reuses_regular_grid():
    import pytest
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None: pytest.skip("pyvista not installed")
    p = pv.Plotter(off_screen=True)
    try:
        r=ThreeDRenderer(p); ds=_ds()
        a=r._build_3d_grid(ds); b=r._build_3d_grid(ds)
        assert a is b
        assert isinstance(a, pv.ImageData)
    finally: p.close()

def test_threshold_produces_mesh_for_in_range_values():
    import pytest
    from scientific_visualization.visualization.three_d.pyvista_renderer import ThreeDRenderer, pv
    if pv is None: pytest.skip("pyvista not installed")
    p=pv.Plotter(off_screen=True)
    try:
        r=ThreeDRenderer(p); ds=_ds(); a=r.add_threshold(ds, lower=1.0, upper=3.0)
        assert a is not None
    finally: p.close()
