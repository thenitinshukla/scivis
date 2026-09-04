"""Generate small synthetic HDF5 files that mimic Simulation output, purely for
testing the Python readers/GUI (no real Simulation files needed)."""
import os
import h5py
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "sample_data")
os.makedirs(OUT, exist_ok=True)


def make_grid_file(path, nx1=128, nx2=64, iteration=200, time=4.0):
    x1 = np.linspace(-10, 10, nx1, endpoint=False)
    x2 = np.linspace(-5, 5, nx2, endpoint=False)
    X2, X1 = np.meshgrid(x2, x1, indexing="ij")  # shape (nx2, nx1) -> matches HDF5 (slowest..fastest)
    data = np.sin(X1) * np.exp(-0.05 * X2 ** 2)

    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "e1"
        f.attrs["TYPE"] = "grid"
        f.attrs["TIME"] = time
        f.attrs["ITER"] = iteration
        f.attrs["UNITS"] = "m_e c omega_p e^-1"
        f.attrs["LABEL"] = "E_1"

        dset = f.create_dataset("e1", data=data.astype(np.float32))
        dset.attrs["UNITS"] = "m_e c omega_p e^-1"
        dset.attrs["LONG_NAME"] = "E_1"
        dset.attrs["TAG"] = "e1"

        axis = f.create_group("AXIS")
        a1 = axis.create_dataset("AXIS1", data=np.array([-10.0, 10.0]))
        a1.attrs["NAME"] = "x1"
        a1.attrs["UNITS"] = "c / omega_p"
        a1.attrs["LONG_NAME"] = "x_1"
        a2 = axis.create_dataset("AXIS2", data=np.array([-5.0, 5.0]))
        a2.attrs["NAME"] = "x2"
        a2.attrs["UNITS"] = "c / omega_p"
        a2.attrs["LONG_NAME"] = "x_2"


def make_particle_file(path, npar=5000, iteration=200, time=4.0):
    rng = np.random.default_rng(0)
    x1 = rng.normal(0, 2.0, npar)
    x2 = rng.normal(0, 1.0, npar)
    p1 = rng.normal(0, 0.5, npar) + 0.1 * x1
    p2 = rng.normal(0, 0.3, npar)
    ene = 0.5 * (p1 ** 2 + p2 ** 2)
    q = -np.ones(npar) / npar

    quants = ["x1", "x2", "p1", "p2", "ene", "q"]
    arrays = {"x1": x1, "x2": x2, "p1": p1, "p2": p2, "ene": ene, "q": q}
    labels = ["x_1", "x_2", "p_1", "p_2", "\\gamma - 1", "q"]
    units = ["c/\\omega_p", "c/\\omega_p", "m_e c", "m_e c", "m_e c^2", "e"]

    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "electrons"
        f.attrs["TIME"] = time
        f.attrs["ITER"] = iteration
        f.attrs["QUANTS"] = quants
        f.attrs["LABELS"] = labels
        f.attrs["UNITS"] = units
        for q_name in quants:
            f.create_dataset(q_name, data=arrays[q_name].astype(np.float32))


def make_tracks_file(path, ntracks=10, npoints=100):
    rng = np.random.default_rng(1)
    quants = ["t", "x1", "x2", "p1", "p2", "ene"]
    rows = []
    counts = []
    starts = []
    for i in range(ntracks):
        t = np.arange(npoints) * 0.5
        phase = rng.uniform(0, 2 * np.pi)
        x1 = 2.0 * np.sin(0.05 * t + phase) + rng.normal(0, 0.05, npoints).cumsum() * 0.02
        x2 = 0.1 * t + rng.normal(0, 0.2)
        p1 = 0.05 * np.cos(0.05 * t + phase)
        p2 = np.full(npoints, 0.1 * rng.normal())
        ene = 0.5 * (p1 ** 2 + p2 ** 2)
        block = np.stack([t, x1, x2, p1, p2, ene], axis=1)
        rows.append(block)
        counts.append(npoints)
        starts.append(0)

    data = np.concatenate(rows, axis=0).astype(np.float64)
    itermap = np.array([[s, c] for s, c in zip(starts, counts)], dtype=np.int32)

    with h5py.File(path, "w") as f:
        f.attrs["NAME"] = "electrons-tracks"
        f.attrs["NTRACKS"] = ntracks
        f.attrs["NDUMP"] = 1
        f.attrs["DT"] = 0.5
        f.attrs["QUANTS"] = quants
        f.attrs["LABELS"] = quants
        f.attrs["UNITS"] = ["1/\\omega_p", "c/\\omega_p", "c/\\omega_p", "m_ec", "m_ec", "m_ec^2"]
        f.create_dataset("data", data=data)
        f.create_dataset("itermap", data=itermap)


def make_grid_series(folder, n=10):
    """A short time series of grid files, with an amplitude that grows then
    decays, for testing the 'time series (reduced over space)' feature."""
    os.makedirs(folder, exist_ok=True)
    for i in range(n):
        it = i * 100
        t = i * 2.0
        amp = np.sin(np.pi * i / (n - 1)) * 2.0  # rises then falls
        nx1, nx2 = 128, 64
        x1 = np.linspace(-10, 10, nx1, endpoint=False)
        x2 = np.linspace(-5, 5, nx2, endpoint=False)
        X2, X1 = np.meshgrid(x2, x1, indexing="ij")
        data = amp * np.sin(X1) * np.exp(-0.05 * X2 ** 2)

        path = os.path.join(folder, f"b3-{it:06d}.h5")
        with h5py.File(path, "w") as f:
            f.attrs["NAME"] = "b3"
            f.attrs["TIME"] = t
            f.attrs["ITER"] = it
            f.attrs["UNITS"] = "m_e c omega_p e^-1"
            f.attrs["LABEL"] = "B_3"
            dset = f.create_dataset("b3", data=data.astype(np.float32))
            dset.attrs["UNITS"] = "m_e c omega_p e^-1"
            dset.attrs["LONG_NAME"] = "B_3"
            axis = f.create_group("AXIS")
            a1 = axis.create_dataset("AXIS1", data=np.array([-10.0, 10.0]))
            a1.attrs["NAME"] = "x1"; a1.attrs["UNITS"] = "c / omega_p"; a1.attrs["LONG_NAME"] = "x_1"
            a2 = axis.create_dataset("AXIS2", data=np.array([-5.0, 5.0]))
            a2.attrs["NAME"] = "x2"; a2.attrs["UNITS"] = "c / omega_p"; a2.attrs["LONG_NAME"] = "x_2"


if __name__ == "__main__":
    make_grid_file(os.path.join(OUT, "e1-000200.h5"))
    make_particle_file(os.path.join(OUT, "electrons-000200.h5"))
    make_tracks_file(os.path.join(OUT, "electrons-tracks.h5"))
    make_grid_series(os.path.join(OUT, "b3_series"))
    print("Sample files written to", OUT)
