from pathlib import Path

from scientific_visualization.io.lazy import LazyGridSeries
from scientific_visualization.export.opencv_movie import OPENCV_AVAILABLE, export_grid_movie_opencv


def test_lazy_grid_series_metadata_first():
    paths = sorted(str(p) for p in Path(__file__).parent.joinpath("sample_data/b3_series").glob("*.h5"))
    seq = LazyGridSeries(paths)
    assert len(seq) == 10
    assert seq[0].shape == (64, 128)
    assert seq._cache == {}
    grid = seq.load(0)
    assert grid.data is not None
    assert 0 in seq._cache


def test_opencv_movie_encoder(tmp_path):
    if not OPENCV_AVAILABLE:
        return
    paths = sorted(str(p) for p in Path(__file__).parent.joinpath("sample_data/b3_series").glob("*.h5"))
    out = tmp_path / "movie.mp4"
    n = export_grid_movie_opencv(paths, out, frame_end=2, fps=5)
    assert n == 3
    assert out.exists() and out.stat().st_size > 1000


def test_lazy_constructor_does_not_open_hdf5():
    paths = sorted(str(p) for p in Path(__file__).parent.joinpath("sample_data/b3_series").glob("*.h5"))
    calls = {"n": 0}
    from scientific_visualization.io.grid import GridFile
    def info(path):
        calls["n"] += 1
        return GridFile.info(path)
    seq = LazyGridSeries(paths, info_loader=info)
    assert calls["n"] == 0
    _ = seq[0]
    assert calls["n"] == 1
