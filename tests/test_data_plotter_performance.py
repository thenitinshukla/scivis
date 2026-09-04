import numpy as np
from scientific_visualization.data_plotter.batch import parse_many
from scientific_visualization.data_plotter.model import DatasetTable


def test_large_dataset_statistics_without_mask_copy_explosion():
    values = np.linspace(0.0, 1.0, 1_000_000)
    ds = DatasetTable("large.txt", ["x"], values.reshape(-1, 1), " ", False)
    stats = ds.statistics(0)
    assert stats["count"] == values.size
    assert stats["min"] == 0.0
    assert stats["max"] == 1.0
