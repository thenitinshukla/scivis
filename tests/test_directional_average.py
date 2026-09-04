import numpy as np
from scientific_visualization.core.data import CoordinateAxis, Dataset
from scientific_visualization.analysis.derived import DerivedQuantityEngine, parse_average_direction
from scientific_visualization.analysis import reduce_grid_series


def make_dataset():
    a = np.arange(24, dtype=float).reshape(2,3,4)
    coords = tuple(CoordinateAxis(f'x{i+1}', np.arange(n, dtype=float)) for i,n in enumerate(a.shape))
    return Dataset('f', a, ('x1','x2','x3'), coords, units='u')


def test_parse_directions():
    assert parse_average_direction('average,dir=x') == ('x',)
    assert parse_average_direction('(x,y,z)') == ('x','y','z')


def test_directional_average_shapes_and_values():
    ds=make_dataset(); eng=DerivedQuantityEngine()
    ax=eng.directional_average(ds,'x')
    assert ax.shape==(3,4); np.testing.assert_allclose(ax.data, ds.data.mean(axis=0))
    all_=eng.directional_average(ds,'average,dir=(x,y,z)')
    assert all_.data.shape==(); np.testing.assert_allclose(all_.data, ds.data.mean())
