from __future__ import annotations

from collections import OrderedDict

import numpy as np

try:
    import pyvista as pv
except Exception:
    pv = None

from ...core.configuration import RenderingConfig
from ...core.data import Dataset


class ThreeDRenderer:
    """Fast PyVista renderer for native 3D data and 2D data promoted to geometry."""

    def __init__(self, plotter=None):
        if pv is None:
            raise ImportError("3D visualization requires optional dependency 'pyvista'")
        self.plotter = plotter or pv.Plotter()
        self._grid_cache = OrderedDict()
        self._grid_cache_size = 4

    @staticmethod
    def _require_2d(dataset):
        if dataset.ndim != 2:
            raise ValueError("2D-to-3D modes require a 2D dataset")
        if len(dataset.coordinates) != 2:
            raise ValueError("2D dataset must provide two coordinate axes")

    @staticmethod
    def _world_axes(dataset):
        names = tuple(a.name.lower() for a in dataset.coordinates)
        out = []
        for i, name in enumerate(names):
            out.append(name if name in {"x1", "x2", "x3"} else f"x{i+1}")
        if len(set(out)) != 2:
            raise ValueError("2D dataset coordinates must map to two distinct spatial axes")
        return tuple(out)

    @staticmethod
    def _make_plane_coordinates(dataset, normal_axis, position):
        axes = ThreeDRenderer._world_axes(dataset)
        if normal_axis in axes:
            raise ValueError(f"Plane normal {normal_axis} must be the axis absent from the 2D dataset ({axes})")
        coords = {axes[0]: np.asarray(dataset.coordinates[0].values), axes[1]: np.asarray(dataset.coordinates[1].values)}
        u_axis, v_axis = axes
        uu, vv = np.meshgrid(coords[u_axis], coords[v_axis], indexing="ij")
        mapping = {
            u_axis: uu.astype(np.float32, copy=False),
            v_axis: vv.astype(np.float32, copy=False),
            normal_axis: np.full(uu.shape, float(position), dtype=np.float32),
        }
        return mapping["x1"], mapping["x2"], mapping["x3"]

    @staticmethod
    def _mesh_options(config):
        return dict(
            smooth_shading=bool(getattr(config, "smooth_shading", True)),
            show_edges=bool(getattr(config, "show_edges", False)),
            edge_color=getattr(config, "edge_color", "black"),
        )

    def _add_mesh(self, grid, dataset, config, name, *, volume=False):
        # These are optional VTK features. Missing support on an older VTK build
        # never prevents normal scientific rendering.
        try:
            if getattr(config, "depth_peeling", False):
                self.plotter.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
        except Exception:
            pass
        try:
            if getattr(config, "ssao", False):
                self.plotter.enable_ssao(radius=0.5, bias=0.0)
        except Exception:
            pass
        try:
            if getattr(config, "stereo", False):
                self.plotter.enable_stereo_render()
        except Exception:
            pass
        try:
            if getattr(config, "hidden_line_removal", False) and not volume:
                grid = grid.extract_geometry() if hasattr(grid, "extract_geometry") else grid
        except Exception:
            pass
        if getattr(config, "antialiasing", True):
            try: self.plotter.enable_anti_aliasing()
            except Exception: pass
        if getattr(config, "eye_dome_lighting", False):
            try: self.plotter.enable_eye_dome_lighting()
            except Exception: pass
        common = dict(
            scalars=dataset.name,
            cmap=config.colormap,
            clim=self._clim(dataset, config),
            opacity=config.opacity,
            name=name,
            show_scalar_bar=False,
        )
        if volume:
            actor = self.plotter.add_volume(grid, opacity="sigmoid", **{k: v for k, v in common.items() if k != "opacity"})
        else:
            common.update(self._mesh_options(config))
            n_points = int(getattr(grid, "n_points", 0) or 0)
            if common.get("smooth_shading") and n_points > 300_000:
                # smooth_shading triggers VTK's compute_normals pass, whose
                # cost scales with mesh size and can dominate rendering time
                # on its own for a very dense/complex mesh (measured: ~11s
                # for a 6.2M-point isosurface) for a visually negligible
                # difference at that triangle density. Auto-downgrade to
                # flat shading rather than silently stalling; the checkbox
                # still forces it on for meshes under the threshold.
                common["smooth_shading"] = False
                print(f"[3D] Using flat shading for a large mesh ({n_points:,} points) to avoid a slow normal-computation pass.", flush=True)
            common["lighting"] = bool(getattr(config, "lighting", True))
            actor = self.plotter.add_mesh(grid, **common)
        self._add_scalar_bar(actor, dataset, config)
        return actor

    def add_2d_plane(self, dataset: Dataset, plane_axis="x3", position=0.0, config=None, name=None):
        self._require_2d(dataset); config = config or RenderingConfig()
        X, Y, Z = self._make_plane_coordinates(dataset, plane_axis, position)
        grid = pv.StructuredGrid(X, Y, Z)
        grid[dataset.name] = np.asarray(dataset.data).ravel(order="F")
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_plane")

    def add_2d_surface(self, dataset: Dataset, z_scale=1.0, height_axis="x3", base_position=0.0, config=None, name=None):
        self._require_2d(dataset); config = config or RenderingConfig()
        X, Y, Z = self._make_plane_coordinates(dataset, height_axis, base_position)
        values = np.asarray(dataset.data, dtype=np.float32)
        height = values * float(z_scale)
        if height_axis == "x1": X = X + height
        elif height_axis == "x2": Y = Y + height
        elif height_axis == "x3": Z = Z + height
        else: raise ValueError("height_axis must be x1, x2, or x3")
        grid = pv.StructuredGrid(X, Y, Z)
        grid[dataset.name] = values.ravel(order="F")
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_surface")

    def add_2d_extrusion(self, dataset: Dataset, depth=1.0, extrusion_axis="x3", start_position=0.0, config=None, name=None):
        self._require_2d(dataset); config = config or RenderingConfig()
        axes = self._world_axes(dataset)
        if extrusion_axis in axes:
            raise ValueError(f"Extrusion axis {extrusion_axis} must be the axis absent from the 2D dataset ({axes})")
        X0, Y0, Z0 = self._make_plane_coordinates(dataset, extrusion_axis, start_position)
        X1, Y1, Z1 = X0.copy(), Y0.copy(), Z0.copy()
        if extrusion_axis == "x1": X1 += float(depth)
        elif extrusion_axis == "x2": Y1 += float(depth)
        else: Z1 += float(depth)
        nx, ny = X0.shape
        n = nx * ny
        p0 = np.column_stack((X0.ravel(), Y0.ravel(), Z0.ravel()))
        p1 = np.column_stack((X1.ravel(), Y1.ravel(), Z1.ravel()))
        points = np.vstack((p0, p1))
        grid = pv.PolyData(points)
        # Vectorized quad generation, replacing the old Python loop over every cell.
        ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
        base = (ii * ny + jj).ravel()
        quads0 = np.column_stack((np.full(base.size, 4), base, base + ny, base + ny + 1, base + 1))
        quads1 = quads0.copy(); quads1[:, 1:] += n
        grid.faces = np.vstack((quads0, quads1)).astype(np.int64, copy=False).ravel()
        grid[dataset.name] = np.tile(np.asarray(dataset.data, dtype=np.float32).ravel(order="C"), 2)
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_extrusion")

    @staticmethod
    def _grid_cache_key(dataset):
        coords_key = tuple((c.name, c.size, float(c.values[0]) if c.size else 0.0,
                            float(c.values[-1]) if c.size else 0.0,
                            bool(c.is_uniform)) for c in dataset.coordinates)
        arr = np.asarray(dataset.data)
        return (id(dataset), id(arr), arr.shape, str(arr.dtype), coords_key)

    def clear_grid_cache(self):
        self._grid_cache.clear()

    def _build_3d_grid(self, dataset: Dataset):
        """Build a VTK grid without allocating coordinate meshes for uniform grids."""
        if dataset.ndim != 3:
            raise ValueError("A native 3D VTK grid requires a 3D dataset")
        key = self._grid_cache_key(dataset)
        cached = self._grid_cache.get(key)
        if cached is not None:
            return cached
        coords = dataset.coordinates
        if all(c.is_uniform for c in coords):
            dims = tuple(int(c.size) for c in coords)
            origin = tuple(float(c.values[0]) if c.size else 0.0 for c in coords)
            spacing = tuple(float(c.spacing) if c.size > 1 else 1.0 for c in coords)
            grid = pv.ImageData(dimensions=dims, origin=origin, spacing=spacing)
        else:
            x, y, z = (np.asarray(c.values, dtype=np.float32) for c in coords)
            xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
            grid = pv.StructuredGrid(xx, yy, zz)
        grid[dataset.name] = np.asarray(dataset.data, dtype=np.float32).ravel(order="F")
        self._grid_cache[key] = grid
        self._grid_cache.move_to_end(key)
        while len(self._grid_cache) > self._grid_cache_size:
            self._grid_cache.popitem(last=False)
        return grid

    def _render_grid(self, dataset: Dataset, config: RenderingConfig):
        grid = self._build_3d_grid(dataset)
        factor = float(getattr(config, "render_decimation", 1.0) or 1.0)
        if factor >= 0.999:
            return grid
        if isinstance(grid, pv.ImageData):
            dims = tuple(int(v) for v in grid.dimensions)
            extents = []
            for dim in dims:
                step = max(1, int(round(1.0 / factor)))
                extents.extend([0, max(0, dim - 1), step])
            try:
                return grid.extract_subset(extents)
            except Exception:
                return grid
        return grid

    def add_native_3d_slices(self, dataset: Dataset, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Native 3D slicing requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        slices = grid.slice_orthogonal()
        return self._add_mesh(slices, dataset, config, name or f"{dataset.name}_slices")

    def add_native_3d(self, dataset: Dataset, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Native 3D rendering requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        return self._add_mesh(grid, dataset, config, name or f"{dataset.name}_volume", volume=True)

    @staticmethod
    def suggest_isovalues(dataset: Dataset, n: int = 3) -> list[float]:
        if n < 1: raise ValueError("n must be at least 1")
        data = np.asarray(dataset.data, dtype=float); finite = data[np.isfinite(data)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values to derive isovalues from")
        percentiles = np.linspace(100.0 / (n + 1), 100.0 * n / (n + 1), n)
        return [float(v) for v in np.percentile(finite, percentiles)]

    def add_isosurfaces(self, dataset: Dataset, isovalues, config=None, name=None, smooth=True,
                         max_smooth_points=60_000, smooth_iterations=20):
        if dataset.ndim != 3: raise ValueError("Isosurfaces require a 3D dataset")
        isovalues = sorted({float(v) for v in isovalues})
        if not isovalues: raise ValueError("Provide at least one isovalue")
        data = np.asarray(dataset.data, dtype=float); finite = data[np.isfinite(data)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values")
        lo, hi = float(finite.min()), float(finite.max())
        bad = [v for v in isovalues if v < lo or v > hi]
        if bad:
            raise ValueError(f"Isovalue(s) {bad} are outside the field '{dataset.name}' range {lo:.6g} to {hi:.6g}.")
        contours = self._render_grid(dataset, config or RenderingConfig()).contour(isosurfaces=isovalues, scalars=dataset.name)
        if contours.n_points == 0:
            raise ValueError(f"No isosurface exists at value(s) {isovalues}; the field ranges from {lo:.6g} to {hi:.6g}.")
        if smooth and contours.n_points > 20:
            if contours.n_points > max_smooth_points:
                # Laplacian smoothing cost scales with n_iter * n_points;
                # a noisy or high-resolution field can produce an
                # isosurface with hundreds of thousands of points, which
                # made this an unbounded, silent multi-second-to-minutes
                # stall (measured: 23s alone for a 3.4M-point volume,
                # dwarfing the ~2.5s isosurface extraction itself, which
                # is already VTK/C++). Skip rather than hang, and say why,
                # instead of leaving the user thinking the app has frozen.
                print(
                    f"[3D] Skipping isosurface smoothing: this isosurface has {contours.n_points:,} "
                    f"points (> {max_smooth_points:,}), which would make smoothing very slow. "
                    f"Showing the unsmoothed surface. Reduce the source grid resolution or the "
                    f"number of isosurfaces to enable smoothing.", flush=True,
                )
            else:
                try: contours = contours.smooth(n_iter=smooth_iterations, relaxation_factor=0.01, feature_smoothing=False)
                except Exception: pass
        return self._add_mesh(contours, dataset, config or RenderingConfig(), name or f"{dataset.name}_isosurfaces")

    def add_threshold(self, dataset: Dataset, lower=None, upper=None, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Threshold rendering requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        finite = np.asarray(dataset.data, dtype=float); finite = finite[np.isfinite(finite)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values")
        lo = float(finite.min()) if lower is None else float(lower); hi = float(finite.max()) if upper is None else float(upper)
        if lo >= hi: raise ValueError("Threshold lower bound must be smaller than upper bound")
        mesh = grid.threshold(value=(lo, hi), scalars=dataset.name)
        return self._add_mesh(mesh, dataset, config, name or f"{dataset.name}_threshold")

    def add_clipped_volume(self, dataset: Dataset, config=None, name=None, normal="x", interactive=True):
        if dataset.ndim != 3: raise ValueError("Clipping requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        common = dict(scalars=dataset.name, cmap=config.colormap, clim=self._clim(dataset, config), opacity=config.opacity, show_scalar_bar=False)
        if interactive:
            actor = self.plotter.add_mesh_clip_plane(grid, normal=normal, name=name or f"{dataset.name}_clip", **common)
        else:
            actor = self.plotter.add_mesh(grid.clip(normal=normal), name=name or f"{dataset.name}_clip", **common)
        self._add_scalar_bar(actor, dataset, config); return actor

    def move_camera_screen(self, dx: float = 0.0, dy: float = 0.0, scale: float = 0.02):
        """Translate camera and focal point in the camera's screen plane."""
        cam = self.plotter.camera
        pos = np.asarray(cam.position, dtype=float)
        focal = np.asarray(cam.focal_point, dtype=float)
        direction = focal - pos
        distance = max(float(np.linalg.norm(direction)), 1e-9)
        forward = direction / distance
        up = np.asarray(cam.up, dtype=float)
        up /= max(float(np.linalg.norm(up)), 1e-9)
        right = np.cross(forward, up)
        right /= max(float(np.linalg.norm(right)), 1e-9)
        step = distance * float(scale)
        shift = right * float(dx) * step + up * float(dy) * step
        cam.position = tuple(pos + shift)
        cam.focal_point = tuple(focal + shift)
        self.plotter.render()

    def set_show_bounding_box(self, show: bool):
        try: self.plotter.remove_bounds_axes()
        except Exception: pass
        if show: self.plotter.show_bounds(grid=True, location="outer", all_edges=True)

    def set_show_orientation_axes(self, show: bool):
        if show: self.plotter.show_axes()
        else: self.plotter.hide_axes()

    def set_background(self, color):
        self.plotter.set_background(color)
        self.plotter.render()

    def save_screenshot(self, filepath: str):
        self.plotter.screenshot(filepath); return filepath

    @staticmethod
    def scalar_bar_geometry(position: str):
        geometries = {
            "right":  (True, 0.87, 0.10, 0.10, 0.80),
            "left":   (True, 0.03, 0.10, 0.10, 0.80),
            "top":    (False, 0.15, 0.90, 0.70, 0.08),
            "bottom": (False, 0.15, 0.02, 0.70, 0.08),
        }
        if position not in geometries: raise ValueError(f"Invalid colorbar position: {position!r}")
        return geometries[position]

    def set_render_quality(self, quality: str):
        quality = quality.lower()
        try:
            if quality == "high": self.plotter.enable_anti_aliasing()
            elif quality == "balanced": self.plotter.enable_anti_aliasing(aa_type="ssaa")
            elif quality == "fast": self.plotter.disable_anti_aliasing()
        except Exception: pass
        try: self.plotter.render()
        except Exception: pass

    def add_box_clip(self, dataset: Dataset, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Box clipping requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        clipped = grid.clip_box(invert=False)
        return self._add_mesh(clipped, dataset, config, name or f"{dataset.name}_boxclip")

    def add_slice(self, dataset: Dataset, axis: str = "x3", value=None, config=None, name=None):
        if dataset.ndim != 3: raise ValueError("Slice requires a 3D dataset")
        config = config or RenderingConfig(); grid = self._render_grid(dataset, config)
        bounds = grid.bounds
        idx = {"x1":0,"x2":1,"x3":2}[axis]
        v = [0.5*(bounds[0]+bounds[1]), 0.5*(bounds[2]+bounds[3]), 0.5*(bounds[4]+bounds[5])][idx] if value is None else float(value)
        normal = [0,0,0]; normal[idx]=1
        sl = grid.slice(normal=normal, origin=[0,0,0] if value is None else [v if idx==0 else 0, v if idx==1 else 0, v if idx==2 else 0])
        return self._add_mesh(sl, dataset, config, name or f"{dataset.name}_{axis}_slice")

    def _add_scalar_bar(self, actor, dataset: Dataset, config):
        if not config.show_colorbar: return None
        vertical, x, y, w, h = self.scalar_bar_geometry(getattr(config, "colorbar_position", "right"))
        title = f"{dataset.name} [{dataset.units}]" if dataset.units else dataset.name
        width = getattr(config, "colorbar_width", None) or w
        height = getattr(config, "colorbar_height", None) or h
        kwargs = dict(title=title, vertical=vertical, position_x=x, position_y=y, width=float(width), height=float(height), outline=bool(getattr(config, "colorbar_box", False)), interactive=bool(getattr(config, "colorbar_interactive", True)))
        mapper = getattr(actor, "mapper", None)
        if mapper is not None: kwargs["mapper"] = mapper
        try: return self.plotter.add_scalar_bar(**kwargs)
        except TypeError:
            kwargs.pop("interactive", None)
            return self.plotter.add_scalar_bar(**kwargs)

    @staticmethod
    def _clim(dataset, config):
        finite = np.asarray(dataset.data)[np.isfinite(dataset.data)]
        if finite.size == 0: raise ValueError("Dataset contains no finite values")
        vmin = config.vmin if config.vmin is not None else float(finite.min())
        vmax = config.vmax if config.vmax is not None else float(finite.max())
        if config.symmetric_limits:
            m = max(abs(vmin), abs(vmax)); vmin, vmax = -m, m
        return (vmin, vmax)
