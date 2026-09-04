import numpy as np
from scientific_visualization.io.grid import GridFile, AxisInfo


def make_grid():
    # Stored HDF5 layout is reversed physical axis order: shape=(x3,x2,x1).
    arr=np.zeros((3,4,5),dtype=float)
    for k in range(3):
        for j in range(4):
            for i in range(5):
                arr[k,j,i]=i + 10*j + 100*k
    return GridFile(filename='synthetic', name='f', label='f', ndim=3, shape=arr.shape,
                    axes=[AxisInfo('x1','x1','',0,5,5), AxisInfo('x2','x2','',0,4,4), AxisInfo('x3','x3','',0,3,3)], data=arr, dataset_name='f')


def test_3d_index_lineout_uses_physical_axis_indices():
    gf=make_grid(); coord, values=gf.lineout(axis=0,index=(1,2,0))
    np.testing.assert_allclose(values, gf.data[1,2,:])
    assert len(coord)==5
