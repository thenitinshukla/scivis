#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

extern "C" void smooth_field(const float* in, float* out, std::size_t n, int radius) {
    if (!in || !out || n == 0) return;
    if (radius <= 0) { std::copy(in, in+n, out); return; }
#pragma omp parallel for if(n > 4096)
    for (long long i=0; i<static_cast<long long>(n); ++i) {
        const std::size_t lo = (i < radius) ? 0 : static_cast<std::size_t>(i-radius);
        const std::size_t hi = std::min<std::size_t>(n-1, static_cast<std::size_t>(i+radius));
        double s=0.0; for (std::size_t j=lo;j<=hi;++j) s += in[j];
        out[i]=static_cast<float>(s/static_cast<double>(hi-lo+1));
    }
}
