from __future__ import annotations

import argparse
from .io.simulation import SimulationReader
from .io.hdf5.generic import discover_hdf5_datasets


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect an HDF5 scientific dataset")
    parser.add_argument("path")
    args = parser.parse_args(argv)
    for item in discover_hdf5_datasets(args.path):
        print(f"{item.name}\tshape={item.shape}\tunits={item.units}")
    try:
        ds = SimulationReader().load(args.path)
        print(ds.summary())
    except Exception as exc:
        print(f"Simulation interpretation: {exc}")


if __name__ == "__main__":
    main()
