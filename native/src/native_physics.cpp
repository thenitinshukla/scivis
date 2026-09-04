// Optional, OpenMP-parallelized C++ backend for the physics differential
// operators (gradient/divergence/curl/laplacian) and particle-field
// trilinear sampling.
//
// Design constraints this file must satisfy (see project docs):
//   * The Python application must work perfectly without this extension
//     being compiled at all -- see scientific_visualization/physics/native_backend.py
//     for the pure-NumPy fallback that mirrors every function here.
//   * Every formula here must exactly match the pre-existing NumPy
//     implementation in scientific_visualization/physics/engine.py (which is
//     built on np.gradient) for *uniform* grid spacing, so switching backends
//     never silently changes a scientific result. Non-uniform coordinate
//     spacing is intentionally NOT supported here -- the Python layer must
//     check CoordinateAxis.is_uniform before calling into this module and
//     fall back to np.gradient (which does support non-uniform spacing)
//     otherwise.
//
// Why this helps performance:
//   * np.gradient() re-derives edge handling and validates its inputs in
//     Python/C on every call, and divergence()/laplacian() in engine.py sum
//     several full-size temporary NumPy arrays (one per axis / per pass).
//     The kernels below fuse those passes into a single set of tight loops
//     over contiguous memory, parallelized across the outer (non-derivative)
//     axes with OpenMP so they scale with the number of CPU cores available
//     at runtime (see omp_get_max_threads()/omp_set_num_threads() below).

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <stdexcept>
#include <algorithm>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

using Array = py::array_t<double, py::array::c_style | py::array::forcecast>;

namespace {

// Decompose shape/strides (in elements) for a C-contiguous array.
struct Layout {
    std::vector<ssize_t> shape;
    std::vector<ssize_t> strides_elems; // per-dimension stride, in elements
    ssize_t total = 1;
    int ndim = 0;

    explicit Layout(const py::buffer_info& buf) {
        ndim = buf.ndim;
        shape.assign(buf.shape.begin(), buf.shape.end());
        strides_elems.resize(ndim);
        ssize_t acc = 1;
        for (int d = ndim - 1; d >= 0; --d) {
            strides_elems[d] = acc;
            acc *= shape[d];
        }
        total = acc;
    }
};

// One-dimensional finite-difference derivative along `axis` of an N-D
// C-contiguous array, using the same formulas as numpy.gradient for
// *uniform* spacing `h`:
//   interior:  (f[i+1] - f[i-1]) / (2h)                         (2nd order)
//   edge_order 2 boundary: 3-point one-sided formula             (2nd order)
//   edge_order 1 boundary (or n == 2): simple forward/backward   (1st order)
//
// `accumulate` selects whether results are written (`false`) or added
// in-place (`true`) into `out` -- the latter is what lets divergence()
// and laplacian() fuse multiple axis-passes without allocating a fresh
// full-size temporary array for every axis.
void gradient_pass(const double* in, double* out, const Layout& layout,
                    int axis, double h, int edge_order, bool accumulate) {
    if (axis < 0 || axis >= layout.ndim)
        throw std::invalid_argument("axis out of range");
    const ssize_t n = layout.shape[axis];
    if (n < 2)
        throw std::invalid_argument("need at least 2 points along the differentiated axis");
    const ssize_t axis_stride = layout.strides_elems[axis];
    const ssize_t outer_size = layout.total / n;

    std::vector<ssize_t> other_shape, other_stride;
    other_shape.reserve(layout.ndim - 1);
    other_stride.reserve(layout.ndim - 1);
    for (int d = 0; d < layout.ndim; ++d) {
        if (d != axis) {
            other_shape.push_back(layout.shape[d]);
            other_stride.push_back(layout.strides_elems[d]);
        }
    }
    const int n_other = static_cast<int>(other_shape.size());
    const bool two_point = (n == 2);
    const bool second_order_edges = (edge_order >= 2) && !two_point;

    #pragma omp parallel for schedule(static)
    for (ssize_t o = 0; o < outer_size; ++o) {
        ssize_t rem = o, base = 0;
        for (int d = n_other - 1; d >= 0; --d) {
            const ssize_t s = other_shape[d];
            const ssize_t idx = rem % s;
            rem /= s;
            base += idx * other_stride[d];
        }
        const double* col_in = in + base;
        double* col_out = out + base;

        if (two_point) {
            const double d0 = (col_in[axis_stride] - col_in[0]) / h;
            if (accumulate) { col_out[0] += d0; col_out[axis_stride] += d0; }
            else { col_out[0] = d0; col_out[axis_stride] = d0; }
            continue;
        }

        for (ssize_t i = 1; i < n - 1; ++i) {
            const double val = (col_in[(i + 1) * axis_stride] - col_in[(i - 1) * axis_stride]) / (2.0 * h);
            if (accumulate) col_out[i * axis_stride] += val;
            else col_out[i * axis_stride] = val;
        }

        double left, right;
        if (second_order_edges) {
            left  = (-3.0 * col_in[0] + 4.0 * col_in[axis_stride] - col_in[2 * axis_stride]) / (2.0 * h);
            right = (3.0 * col_in[(n - 1) * axis_stride] - 4.0 * col_in[(n - 2) * axis_stride] + col_in[(n - 3) * axis_stride]) / (2.0 * h);
        } else {
            left  = (col_in[axis_stride] - col_in[0]) / h;
            right = (col_in[(n - 1) * axis_stride] - col_in[(n - 2) * axis_stride]) / h;
        }
        if (accumulate) { col_out[0] += left; col_out[(n - 1) * axis_stride] += right; }
        else { col_out[0] = left; col_out[(n - 1) * axis_stride] = right; }
    }
}

} // namespace

// ---------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------

Array gradient_uniform(Array input, double h, int axis, int edge_order) {
    auto buf = input.request();
    Layout layout(buf);
    Array result(layout.shape);
    auto out_buf = result.request();
    std::fill(static_cast<double*>(out_buf.ptr), static_cast<double*>(out_buf.ptr) + layout.total, 0.0);
    gradient_pass(static_cast<const double*>(buf.ptr), static_cast<double*>(out_buf.ptr),
                  layout, axis, h, edge_order, /*accumulate=*/false);
    return result;
}

Array divergence_uniform(std::vector<Array> components, std::vector<double> spacings, int edge_order) {
    if (components.empty())
        throw std::invalid_argument("divergence_uniform requires at least one component");
    if (components.size() != spacings.size())
        throw std::invalid_argument("components and spacings must have the same length");

    auto buf0 = components[0].request();
    Layout layout(buf0);
    if (static_cast<int>(components.size()) != layout.ndim)
        throw std::invalid_argument("number of components must equal the array dimensionality");

    Array result(layout.shape);
    auto out_buf = result.request();
    double* out = static_cast<double*>(out_buf.ptr);
    std::fill(out, out + layout.total, 0.0);

    for (int axis = 0; axis < layout.ndim; ++axis) {
        auto buf = components[axis].request();
        Layout comp_layout(buf);
        if (comp_layout.shape != layout.shape)
            throw std::invalid_argument("all components must share the same shape");
        gradient_pass(static_cast<const double*>(buf.ptr), out, layout, axis,
                      spacings[axis], edge_order, /*accumulate=*/true);
    }
    return result;
}

Array laplacian_uniform(Array input, std::vector<double> spacings, int edge_order) {
    auto buf = input.request();
    Layout layout(buf);
    if (static_cast<int>(spacings.size()) != layout.ndim)
        throw std::invalid_argument("spacings must have one entry per dimension");

    Array result(layout.shape);
    auto out_buf = result.request();
    double* out = static_cast<double*>(out_buf.ptr);
    std::fill(out, out + layout.total, 0.0);

    // Matches physics.engine.PhysicsEngine.laplacian(): apply the first
    // derivative, then differentiate that result again along the same axis
    // (a wider, still-second-order stencil), summed over every axis.
    std::vector<double> scratch(layout.total);
    for (int axis = 0; axis < layout.ndim; ++axis) {
        std::fill(scratch.begin(), scratch.end(), 0.0);
        gradient_pass(static_cast<const double*>(buf.ptr), scratch.data(), layout, axis,
                      spacings[axis], edge_order, /*accumulate=*/false);
        gradient_pass(scratch.data(), out, layout, axis,
                      spacings[axis], edge_order, /*accumulate=*/true);
    }
    return result;
}

py::tuple curl_uniform_3d(Array c1, Array c2, Array c3, double h1, double h2, double h3, int edge_order) {
    auto buf1 = c1.request();
    Layout layout(buf1);
    if (layout.ndim != 3)
        throw std::invalid_argument("curl_uniform_3d requires 3D arrays");
    auto buf2 = c2.request();
    auto buf3 = c3.request();
    Layout layout2(buf2), layout3(buf3);
    if (layout2.shape != layout.shape || layout3.shape != layout.shape)
        throw std::invalid_argument("all three components must share the same shape");

    const double* d1 = static_cast<const double*>(buf1.ptr);
    const double* d2 = static_cast<const double*>(buf2.ptr);
    const double* d3 = static_cast<const double*>(buf3.ptr);

    // out_a = d(c3)/dx2 - d(c2)/dx3
    // out_b = d(c1)/dx3 - d(c3)/dx1
    // out_c = d(c2)/dx1 - d(c1)/dx2
    std::vector<double> d3_dx2(layout.total), d2_dx3(layout.total);
    std::vector<double> d1_dx3(layout.total), d3_dx1(layout.total);
    std::vector<double> d2_dx1(layout.total), d1_dx2(layout.total);

    gradient_pass(d3, d3_dx2.data(), layout, 1, h2, edge_order, false);
    gradient_pass(d2, d2_dx3.data(), layout, 2, h3, edge_order, false);
    gradient_pass(d1, d1_dx3.data(), layout, 2, h3, edge_order, false);
    gradient_pass(d3, d3_dx1.data(), layout, 0, h1, edge_order, false);
    gradient_pass(d2, d2_dx1.data(), layout, 0, h1, edge_order, false);
    gradient_pass(d1, d1_dx2.data(), layout, 1, h2, edge_order, false);

    Array out_a(layout.shape), out_b(layout.shape), out_c(layout.shape);
    double* pa = static_cast<double*>(out_a.request().ptr);
    double* pb = static_cast<double*>(out_b.request().ptr);
    double* pc = static_cast<double*>(out_c.request().ptr);

    #pragma omp parallel for schedule(static)
    for (ssize_t i = 0; i < layout.total; ++i) {
        pa[i] = d3_dx2[i] - d2_dx3[i];
        pb[i] = d1_dx3[i] - d3_dx1[i];
        pc[i] = d2_dx1[i] - d1_dx2[i];
    }
    return py::make_tuple(out_a, out_b, out_c);
}

// Trilinear sampling of a scalar 3D field at arbitrary physical points,
// parallelized across the (typically large and independent) set of
// sample points -- the natural use case being "sample E(x(t), y(t), z(t))
// along a particle trajectory" for many particles/timesteps at once.
// Points outside the grid are clamped to the boundary (matching how
// lineouts/interpolation already behave elsewhere in this codebase)
// rather than raising, since a slightly-out-of-bounds particle position
// due to floating point error is expected, not exceptional.
py::array_t<double> sample_field_trilinear(
    Array field,
    std::array<double, 3> origin,
    std::array<double, 3> spacing,
    Array points // (N, 3)
) {
    auto fbuf = field.request();
    if (fbuf.ndim != 3)
        throw std::invalid_argument("sample_field_trilinear requires a 3D field");
    const ssize_t n0 = fbuf.shape[0], n1 = fbuf.shape[1], n2 = fbuf.shape[2];
    const ssize_t s0 = n1 * n2, s1 = n2, s2 = 1;
    const double* f = static_cast<const double*>(fbuf.ptr);

    auto pbuf = points.request();
    if (pbuf.ndim != 2 || pbuf.shape[1] != 3)
        throw std::invalid_argument("points must have shape (N, 3)");
    const ssize_t npts = pbuf.shape[0];
    const double* pts = static_cast<const double*>(pbuf.ptr);

    for (double h : spacing)
        if (h == 0.0) throw std::invalid_argument("grid spacing must be non-zero");

    auto result = py::array_t<double>(npts);
    double* out = static_cast<double*>(result.request().ptr);

    #pragma omp parallel for schedule(static)
    for (ssize_t k = 0; k < npts; ++k) {
        double gx = (pts[k * 3 + 0] - origin[0]) / spacing[0];
        double gy = (pts[k * 3 + 1] - origin[1]) / spacing[1];
        double gz = (pts[k * 3 + 2] - origin[2]) / spacing[2];

        gx = std::min(std::max(gx, 0.0), static_cast<double>(n0 - 1));
        gy = std::min(std::max(gy, 0.0), static_cast<double>(n1 - 1));
        gz = std::min(std::max(gz, 0.0), static_cast<double>(n2 - 1));

        ssize_t i0 = static_cast<ssize_t>(std::floor(gx));
        ssize_t j0 = static_cast<ssize_t>(std::floor(gy));
        ssize_t k0 = static_cast<ssize_t>(std::floor(gz));
        ssize_t i1 = std::min(i0 + 1, n0 - 1);
        ssize_t j1 = std::min(j0 + 1, n1 - 1);
        ssize_t k1 = std::min(k0 + 1, n2 - 1);

        const double tx = gx - i0, ty = gy - j0, tz = gz - k0;

        auto at = [&](ssize_t i, ssize_t j, ssize_t kk) { return f[i * s0 + j * s1 + kk * s2]; };

        const double c00 = at(i0, j0, k0) * (1 - tx) + at(i1, j0, k0) * tx;
        const double c01 = at(i0, j0, k1) * (1 - tx) + at(i1, j0, k1) * tx;
        const double c10 = at(i0, j1, k0) * (1 - tx) + at(i1, j1, k0) * tx;
        const double c11 = at(i0, j1, k1) * (1 - tx) + at(i1, j1, k1) * tx;
        const double c0 = c00 * (1 - ty) + c10 * ty;
        const double c1 = c01 * (1 - ty) + c11 * ty;
        out[k] = c0 * (1 - tz) + c1 * tz;
    }
    return result;
}

int omp_max_threads() {
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}

bool openmp_enabled() {
#ifdef _OPENMP
    return true;
#else
    return false;
#endif
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Optional OpenMP-parallelized C++ kernels for uniform-grid physics "
              "operators and particle-field trilinear sampling. Pure-NumPy "
              "fallbacks with identical numerics live in "
              "scientific_visualization.physics.native_backend and are used "
              "automatically whenever this extension is not compiled.";
    m.def("gradient_uniform", &gradient_uniform, py::arg("data"), py::arg("h"), py::arg("axis"), py::arg("edge_order") = 2);
    m.def("divergence_uniform", &divergence_uniform, py::arg("components"), py::arg("spacings"), py::arg("edge_order") = 2);
    m.def("laplacian_uniform", &laplacian_uniform, py::arg("data"), py::arg("spacings"), py::arg("edge_order") = 2);
    m.def("curl_uniform_3d", &curl_uniform_3d, py::arg("c1"), py::arg("c2"), py::arg("c3"),
          py::arg("h1"), py::arg("h2"), py::arg("h3"), py::arg("edge_order") = 2);
    m.def("sample_field_trilinear", &sample_field_trilinear, py::arg("field"), py::arg("origin"),
          py::arg("spacing"), py::arg("points"));
    m.def("omp_max_threads", &omp_max_threads);
    m.def("openmp_enabled", &openmp_enabled);
}
