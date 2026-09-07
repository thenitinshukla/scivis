"""Regression tests for scientific_visualization.io.simulation.reader.SimulationReader.

Covers two fixes:
  1. A tracks file (which, like a particle file, has a QUANTS attribute and
     no AXIS group) must not be misidentified as a particle file -- it has
     its own 'data'+'itermap'/'NTRACKS' shape that takes priority.
  2. discover()/load() open the underlying HDF5 file from disk exactly
     once, instead of once per is_*_file probe plus once more to read
     metadata.
"""
import h5py
import numpy as np
import pytest

from scientific_visualization.io.simulation.reader import SimulationReader


@pytest.fixture
def grid_file(tmp_path):
    path = tmp_path / "grid.h5"
    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "e1"
        f.attrs["TIME"] = 1.0
        f.attrs["ITER"] = 1
        f.create_dataset("e1", data=np.random.rand(10, 10))
        ax = f.create_group("AXIS")
        ax.create_dataset("AXIS1", data=[0.0, 1.0])
        ax.create_dataset("AXIS2", data=[0.0, 1.0])
    return path


@pytest.fixture
def particle_file(tmp_path):
    path = tmp_path / "particles.h5"
    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "electrons"
        f.attrs["TIME"] = 1.0
        f.attrs["ITER"] = 1
        f.attrs["QUANTS"] = ["x1", "p1", "ene"]
        f.create_dataset("x1", data=np.random.rand(50))
        f.create_dataset("p1", data=np.random.rand(50))
        f.create_dataset("ene", data=np.random.rand(50))
    return path


@pytest.fixture
def tracks_file(tmp_path):
    path = tmp_path / "tracks.h5"
    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "tracks"
        f.attrs["NTRACKS"] = 2
        f.attrs["NDUMP"] = 1
        f.attrs["DT"] = 0.1
        # Tracks files have a QUANTS attribute too, same as particle files --
        # this is exactly what previously fooled is_particle_file.
        f.attrs["QUANTS"] = ["t", "x1"]
        f.create_dataset("data", data=np.random.rand(20, 2))
        f.create_dataset("itermap", data=np.array([[0, 10], [10, 10]]))
    return path


def test_tracks_file_not_misidentified_as_particle_file(tracks_file):
    reader = SimulationReader()
    ds = reader.load(str(tracks_file))
    # Before the fix this raised KeyError("quantity 't' not found in ..."),
    # because the tracks file was routed through ParticleFile.to_dataset,
    # which looks for a top-level 't' dataset that only exists as a column
    # of 'data' in the tracks format.
    assert ds.name == "t"
    assert ds.data.shape == (20,)


def test_particle_file_still_identified_correctly(particle_file):
    reader = SimulationReader()
    ds = reader.load(str(particle_file))
    assert ds.name == "x1"
    assert ds.data.shape == (50,)


def test_grid_file_still_identified_correctly(grid_file):
    reader = SimulationReader()
    ds = reader.load(str(grid_file))
    assert ds.name == "e1"
    assert ds.data.shape == (10, 10)


@pytest.mark.parametrize("method,args", [("load", ()), ("discover", ())])
def test_reader_opens_file_from_disk_exactly_once(grid_file, method, args):
    real_opens = []
    orig_init = h5py.File.__init__

    def counted_init(self, *a, **kw):
        if a and isinstance(a[0], (str, bytes)):
            real_opens.append(a[0])
        return orig_init(self, *a, **kw)

    h5py.File.__init__ = counted_init
    try:
        reader = SimulationReader()
        getattr(reader, method)(str(grid_file), *args)
    finally:
        h5py.File.__init__ = orig_init

    assert len(real_opens) == 1
