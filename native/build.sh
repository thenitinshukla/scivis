#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel "${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"
echo "Native Qt executable: $PWD/build/scientific_simulation_native"
