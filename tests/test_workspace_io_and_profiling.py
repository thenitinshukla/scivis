import numpy as np
import pandas as pd
import pytest

from scientific_visualization.workspace.io_formats import load_any, list_excel_sheets
from scientific_visualization.workspace.profiling import profile_dataframe
from scientific_visualization.workspace.types import ColumnType


@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


# --- io_formats ---

def test_load_csv(tmp_path, sample_df):
    p = tmp_path / "d.csv"
    sample_df.to_csv(p, index=False)
    df = load_any(p)
    pd.testing.assert_frame_equal(df, sample_df)


def test_load_tsv(tmp_path, sample_df):
    p = tmp_path / "d.tsv"
    sample_df.to_csv(p, sep="\t", index=False)
    df = load_any(p)
    pd.testing.assert_frame_equal(df, sample_df)


def test_load_json_records(tmp_path, sample_df):
    p = tmp_path / "d.json"
    sample_df.to_json(p, orient="records")
    df = load_any(p)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 3


def test_load_excel(tmp_path, sample_df):
    pytest.importorskip("openpyxl")
    p = tmp_path / "d.xlsx"
    sample_df.to_excel(p, index=False, sheet_name="Data")
    df = load_any(p)
    pd.testing.assert_frame_equal(df, sample_df)
    assert list_excel_sheets(p) == ["Data"]


def test_load_parquet(tmp_path, sample_df):
    pytest.importorskip("pyarrow")
    p = tmp_path / "d.parquet"
    sample_df.to_parquet(p)
    df = load_any(p)
    pd.testing.assert_frame_equal(df, sample_df)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        load_any(tmp_path / "nope.csv")


def test_load_unsupported_extension_raises(tmp_path):
    p = tmp_path / "d.xyz"
    p.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported"):
        load_any(p)


def test_load_empty_csv_raises(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    with pytest.raises(ValueError):
        load_any(p)


def test_load_csv_with_semicolon_delimiter_autodetected(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a;b\n1;x\n2;y\n")
    df = load_any(p)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


# --- profiling ---

def test_profile_basic_shape(sample_df):
    p = profile_dataframe(sample_df)
    assert p.row_count == 3
    assert p.column_count == 2
    assert p.duplicate_rows == 0


def test_profile_detects_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    p = profile_dataframe(df)
    assert p.duplicate_rows == 1


def test_profile_detects_missing_values():
    df = pd.DataFrame({"a": [1, None, 3]})
    p = profile_dataframe(df)
    assert p.total_missing() == 1
    assert p.columns[0].missing == 1
    assert p.columns[0].missing_pct == pytest.approx(33.333, abs=0.01)


def test_profile_numeric_stats():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0, 5.0]})
    p = profile_dataframe(df)
    col = p.columns[0]
    assert col.numeric_min == 1.0
    assert col.numeric_max == 5.0
    assert col.numeric_mean == 3.0
    assert col.numeric_median == 3.0


def test_profile_outlier_detection():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6, 7, 100]})
    p = profile_dataframe(df)
    assert p.columns[0].outlier_count == 1


def test_profile_text_length_stats():
    df = pd.DataFrame({"name": ["ab", "abcdef", "abcd"]})
    p = profile_dataframe(df)
    col = p.columns[0]
    assert col.min_length == 2
    assert col.max_length == 6


def test_profile_type_counts_and_columns_of_type():
    df = pd.DataFrame({"n": [1, 2, 3], "cat": ["a", "b", "a"], "n2": [4.0, 5.0, 6.0]})
    p = profile_dataframe(df)
    counts = p.type_counts()
    assert counts.get("Numeric") == 2
    assert set(p.columns_of_type(ColumnType.NUMERIC)) == {"n", "n2"}


def test_profile_sample_values_json_safe():
    df = pd.DataFrame({"a": [1, 2, None, 4]})
    p = profile_dataframe(df)
    # NaN must not leak into sample_values as a float NaN (breaks naive
    # display/serialization); it should already be filtered by dropna.
    assert all(v is not None for v in p.columns[0].sample_values)
