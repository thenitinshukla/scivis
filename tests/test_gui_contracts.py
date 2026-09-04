from pathlib import Path

from scientific_visualization.io.grid import GridFile

DATA = Path(__file__).parent / "sample_data" / "e1-000200.h5"

def test_grid_metadata_is_safe_without_loading_field():
    grid = GridFile.info(DATA)
    assert grid.data is None
    assert grid.shape == (64, 128)
    assert grid.name
    # The shared model requires data, so conversion is intentionally deferred.
    try:
        grid.to_dataset()
    except ValueError as exc:
        assert "data not loaded" in str(exc)
    else:
        raise AssertionError("metadata-only GridFile unexpectedly converted to Dataset")
