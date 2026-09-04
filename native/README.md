# Native C++20 + Qt6 high-performance path

This directory is the native rendering/core path. It is deliberately separate from the Python scientific workflow so the application can be migrated incrementally without changing HDF5 semantics.

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/scientific_simulation_native
```

The build uses Qt6 Widgets + OpenGLWidgets, C++20, `-O3`, `-march=native`, optional OpenMP, and a static native core. The intended production integration is HDF5 -> zero-copy/typed field buffers -> VTK/PyVista or native OpenGL GPU buffers -> Qt, with long operations kept off the GUI thread.
