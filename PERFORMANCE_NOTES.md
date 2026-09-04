# Performance Assessment

The main interactive slowdown was not a lack of C++ for ordinary plotting. The dominant avoidable costs were in the Qt/rendering path:

1. **Synchronous Matplotlib redraws**: `GridTab.refresh_plot()` called `canvas.draw()` after many control changes. This forced immediate rasterization on every UI event. It is now `draw_idle()`, allowing Qt/Matplotlib to coalesce repeated changes.
2. **Full-array temporary allocation for color limits**: `_plot_2d()` used `data[np.isfinite(data)]` even when only minimum and maximum values were required. That creates a second large array. The common no-clipping path now uses `np.nanmin()`/`np.nanmax()` directly.
3. **Repeated frame loading**: the Fields / Grid path already had `LazyGridSeries`, but the 3D tab loaded each selected HDF5 file directly. The 3D tab now uses a bounded `LazyGridSeries` cache for multi-frame navigation.
4. **3D rebuild cost**: the renderer already caches VTK grids and contains safeguards against expensive smoothing and normal computation. The new camera movement controls translate the camera/focal point directly and therefore do not rebuild the scene just to move the image.

## Why C++ was not used for these particular fixes

NumPy reductions and Matplotlib/VTK rendering already execute their heavy loops in compiled native code. Replacing `np.mean`, `np.nanmin`, or plotting calls with a C++ extension would introduce data-conversion and extension-call overhead while duplicating functionality that is already optimized.

The repository's existing C++/OpenMP backend remains appropriate for compute-heavy physics kernels such as gradients, divergence, Laplacian, curl, and particle-field sampling. New C++ kernels should be added only after profiling demonstrates that one of those computational kernels is the bottleneck.

## Microbenchmark

On a 2048 x 2048 float64 NumPy array in the current environment, replacing the temporary finite-value array with `np.nanmin`/`np.nanmax` reduced the local extrema operation from about 33.6 ms median in the allocation-based path to about 6.6 ms median in the direct reduction path, roughly a 5x improvement in this benchmark. Exact timings depend strongly on hardware and NumPy build, so this benchmark is intended as a regression check rather than a hardware claim.
