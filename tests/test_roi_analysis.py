"""Tests for scientific_visualization.analysis.roi (plan.md section 4.4:
ROI and measurement tools).
"""
import json

import numpy as np
import pytest

from scientific_visualization.analysis.roi import (
    RegionOfInterest, roi_statistics, roi_time_series, export_roi_results,
)


def test_roi_normalizes_reversed_coordinates():
    roi = RegionOfInterest("rectangle", x0=1.0, y0=1.0, x1=0.0, y1=0.5)
    assert roi.x0 == 0.0 and roi.x1 == 1.0
    assert roi.y0 == 0.5 and roi.y1 == 1.0


def test_roi_rejects_invalid_shape():
    with pytest.raises(ValueError, match="rectangle"):
        RegionOfInterest("triangle", 0, 0, 1, 1)


def test_roi_rejects_zero_size():
    with pytest.raises(ValueError):
        RegionOfInterest("rectangle", 0, 0, 0, 1)
    with pytest.raises(ValueError):
        RegionOfInterest("rectangle", 0, 0, 1, 0)


def test_roi_gets_a_default_label():
    roi = RegionOfInterest("rectangle", 0, 0, 1, 1)
    assert roi.label == f"ROI {roi.id}"


def test_roi_ids_are_unique():
    roi1 = RegionOfInterest("rectangle", 0, 0, 1, 1)
    roi2 = RegionOfInterest("rectangle", 0, 0, 1, 1)
    assert roi1.id != roi2.id


def test_rectangle_mask_matches_exact_bounding_box():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 4, 5)
    roi = RegionOfInterest("rectangle", x0=2.5, y0=1.5, x1=6.5, y1=3.5)
    mask = roi.mask(x, y)
    assert mask.shape == (5, 10)
    expected = np.zeros((5, 10), dtype=bool)
    expected[2:4, 3:7] = True  # y in {2,3}, x in {3,4,5,6}
    np.testing.assert_array_equal(mask, expected)


def test_ellipse_mask_contains_center_and_excludes_far_corner():
    x = np.linspace(-5, 5, 11)
    y = np.linspace(-5, 5, 11)
    roi = RegionOfInterest("ellipse", x0=-4, y0=-4, x1=4, y1=4)
    mask = roi.mask(x, y)
    cx = cy = 5  # index of coordinate 0.0
    assert mask[cy, cx]  # center is inside
    assert not mask[0, 0]  # far corner (-5,-5) is outside the ellipse
    assert not mask[10, 10]


def test_rectangle_area_is_exact():
    roi = RegionOfInterest("rectangle", 0, 0, 2, 3)
    assert roi.area == pytest.approx(6.0)


def test_ellipse_area_matches_pi_r1_r2():
    roi = RegionOfInterest("ellipse", -2, -3, 2, 3)  # semi-axes 2, 3
    assert roi.area == pytest.approx(np.pi * 2 * 3, rel=1e-9)


def test_roi_statistics_on_known_constant_region():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 9, 10)
    data = np.zeros((10, 10))
    data[2:5, 2:5] = 3.0  # a known 3x3 block of constant value 3
    roi = RegionOfInterest("rectangle", x0=2, y0=2, x1=4, y1=4)
    result = roi_statistics(data, x, y, roi)
    assert result["n_points"] == 9
    assert result["mean"] == pytest.approx(3.0)
    assert result["min"] == pytest.approx(3.0)
    assert result["max"] == pytest.approx(3.0)
    assert result["std"] == pytest.approx(0.0)
    assert result["p50"] == pytest.approx(3.0)


def test_roi_statistics_integral_matches_value_times_area_for_uniform_region():
    x = np.linspace(0, 10, 11)  # spacing 1.0
    y = np.linspace(0, 10, 11)
    data = np.full((11, 11), 2.0)
    roi = RegionOfInterest("rectangle", x0=2, y0=2, x1=6, y1=6)
    result = roi_statistics(data, x, y, roi)
    # 5x5 grid points at spacing 1 => covered area ~16 (4x4 cells), integral ~= 2*area
    assert result["integral"] == pytest.approx(result["roi_area_covered"] * 2.0, rel=0.2)


def test_roi_statistics_rejects_shape_mismatch():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 4, 5)
    data = np.zeros((5, 11))  # wrong x length
    roi = RegionOfInterest("rectangle", 0, 0, 1, 1)
    with pytest.raises(ValueError, match="shape"):
        roi_statistics(data, x, y, roi)


def test_roi_statistics_rejects_roi_with_no_overlap():
    x = np.linspace(0, 9, 10)
    y = np.linspace(0, 9, 10)
    data = np.zeros((10, 10))
    roi = RegionOfInterest("rectangle", x0=100, y0=100, x1=101, y1=101)
    with pytest.raises(ValueError, match="no finite data"):
        roi_statistics(data, x, y, roi)


def test_roi_statistics_ignores_nan_but_counts_only_finite():
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    data = np.ones((5, 5))
    data[2, 2] = np.nan
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)
    result = roi_statistics(data, x, y, roi)
    assert result["n_points"] == 8  # 3x3 block minus the one NaN


def test_roi_to_dict_and_from_dict_round_trip():
    roi = RegionOfInterest("ellipse", 0, 0, 2, 2, label="my region")
    d = roi.to_dict()
    restored = RegionOfInterest.from_dict(d)
    assert restored.shape == roi.shape
    assert restored.x0 == roi.x0 and restored.x1 == roi.x1
    assert restored.label == roi.label
    assert restored.id != roi.id  # fresh id on reconstruction, by design


class _FakeAxis:
    def __init__(self, values):
        self._values = np.asarray(values, dtype=float)
    def values(self):
        return self._values


class _FakeGrid:
    def __init__(self, data, x, y, time, iteration):
        self.data = data
        self.axes = [_FakeAxis(x), _FakeAxis(y)]
        self.time = time
        self.time_units = "s"
        self.iteration = iteration


def test_roi_time_series_computes_stats_for_every_frame():
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    grids = {f"frame{i}.h5": _FakeGrid(np.full((5, 5), float(i)), x, y, float(i), i) for i in range(4)}
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)

    progress = []
    results = roi_time_series(
        list(grids.keys()), loader=lambda p: grids[p], roi=roi,
        progress_callback=lambda i, total, p: progress.append((i, total, p)),
    )
    assert len(results) == 4
    for i, r in enumerate(results):
        assert r["mean"] == pytest.approx(float(i))
        assert r["iteration"] == i
    assert progress == [(1, 4, "frame0.h5"), (2, 4, "frame1.h5"), (3, 4, "frame2.h5"), (4, 4, "frame3.h5")]


def test_roi_time_series_records_error_for_bad_frame_without_aborting_others():
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    good = _FakeGrid(np.full((5, 5), 7.0), x, y, 0.0, 0)
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)

    def loader(path):
        if path == "bad.h5":
            raise RuntimeError("corrupt file")
        return good

    results = roi_time_series(["good1.h5", "bad.h5", "good2.h5"], loader=loader, roi=roi)
    assert results[0]["mean"] == pytest.approx(7.0)
    assert "error" in results[1] and "corrupt" in results[1]["error"]
    assert results[2]["mean"] == pytest.approx(7.0)


def test_export_roi_results_writes_valid_json(tmp_path):
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    data = np.full((5, 5), 3.0)
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3, label="test region")
    result = roi_statistics(data, x, y, roi)

    out = tmp_path / "roi.json"
    export_roi_results(result, str(out))
    loaded = json.loads(out.read_text())
    assert loaded["mean"] == pytest.approx(3.0)
    assert loaded["roi"]["label"] == "test region"


def test_export_roi_results_handles_list_of_results(tmp_path):
    x = np.linspace(0, 4, 5)
    y = np.linspace(0, 4, 5)
    grids = [_FakeGrid(np.full((5, 5), float(i)), x, y, float(i), i) for i in range(3)]
    roi = RegionOfInterest("rectangle", x0=1, y0=1, x1=3, y1=3)
    results = roi_time_series([f"f{i}" for i in range(3)], loader=lambda p: grids[int(p[1:])], roi=roi)

    out = tmp_path / "roi_series.json"
    export_roi_results(results, str(out))
    loaded = json.loads(out.read_text())
    assert len(loaded) == 3
    assert [r["mean"] for r in loaded] == [0.0, 1.0, 2.0]
