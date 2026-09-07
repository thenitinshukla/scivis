import numpy as np
import pandas as pd
import pytest

from scientific_visualization.workspace.cleaning import PipelineStep, apply_pipeline, OPERATIONS
import scientific_visualization.workspace.transforms  # noqa: F401 -- registers ops


def run(df, op, **params):
    result, errors = apply_pipeline(df, [PipelineStep(op, params)])
    assert errors == [], errors
    return result


# --- cleaning.py ---

def test_remove_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    out = run(df, "remove_duplicates")
    assert len(out) == 2


def test_remove_duplicates_with_subset():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "y", "z"]})
    out = run(df, "remove_duplicates", subset=["a"])
    assert len(out) == 2


def test_drop_rows_with_missing():
    df = pd.DataFrame({"a": [1, None, 3]})
    out = run(df, "drop_rows_with_missing")
    assert len(out) == 2


def test_fill_missing_mean():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    out = run(df, "fill_missing", columns=["a"], method="mean")
    assert out["a"].iloc[1] == 2.0


def test_fill_missing_median():
    df = pd.DataFrame({"a": [1.0, None, 3.0, 100.0]})
    out = run(df, "fill_missing", columns=["a"], method="median")
    assert not out["a"].isna().any()


def test_fill_missing_mode():
    df = pd.DataFrame({"a": ["x", "x", None, "y"]})
    out = run(df, "fill_missing", columns=["a"], method="mode")
    assert out["a"].iloc[2] == "x"


def test_fill_missing_constant():
    df = pd.DataFrame({"a": [1.0, None]})
    out = run(df, "fill_missing", columns=["a"], method="constant", value=0.0)
    assert out["a"].iloc[1] == 0.0


def test_fill_missing_ffill_bfill():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    assert run(df, "fill_missing", columns=["a"], method="ffill")["a"].iloc[1] == 1.0
    assert run(df, "fill_missing", columns=["a"], method="bfill")["a"].iloc[1] == 3.0


def test_replace_values():
    df = pd.DataFrame({"a": ["yes", "no", "yes"]})
    out = run(df, "replace_values", column="a", mapping={"yes": True, "no": False})
    assert out["a"].tolist() == [True, False, True]


def test_rename_column():
    df = pd.DataFrame({"old": [1, 2]})
    out = run(df, "rename_column", column="old", new_name="new")
    assert list(out.columns) == ["new"]


def test_rename_column_rejects_duplicate_name():
    df = pd.DataFrame({"a": [1], "b": [2]})
    _, errors = apply_pipeline(df, [PipelineStep("rename_column", {"column": "a", "new_name": "b"})])
    assert errors


def test_change_dtype_numeric_strips_currency():
    df = pd.DataFrame({"a": ["$1,000", "$2,500.50"]})
    out = run(df, "change_dtype", column="a", dtype="numeric")
    assert out["a"].tolist() == pytest.approx([1000.0, 2500.5])


def test_change_dtype_datetime():
    df = pd.DataFrame({"a": ["2020-01-01", "2020-02-01"]})
    out = run(df, "change_dtype", column="a", dtype="datetime")
    assert pd.api.types.is_datetime64_any_dtype(out["a"])


def test_change_dtype_boolean():
    df = pd.DataFrame({"a": ["yes", "no", "TRUE", "0"]})
    out = run(df, "change_dtype", column="a", dtype="boolean")
    assert out["a"].tolist() == [True, False, True, False]


def test_change_dtype_category():
    df = pd.DataFrame({"a": ["x", "y", "x"]})
    out = run(df, "change_dtype", column="a", dtype="category")
    assert isinstance(out["a"].dtype, pd.CategoricalDtype)


def test_trim_whitespace():
    df = pd.DataFrame({"a": [" x ", "y  ", None]})
    out = run(df, "trim_whitespace", columns=["a"])
    assert out["a"].iloc[0] == "x"
    assert out["a"].iloc[1] == "y"
    assert pd.isna(out["a"].iloc[2])


def test_standardize_text_lower_upper_title():
    df = pd.DataFrame({"a": ["Hello World"]})
    assert run(df, "standardize_text", columns=["a"], case="lower")["a"].iloc[0] == "hello world"
    assert run(df, "standardize_text", columns=["a"], case="upper")["a"].iloc[0] == "HELLO WORLD"


def test_remove_empty_columns():
    df = pd.DataFrame({"a": [1, 2], "b": [None, None]})
    out = run(df, "remove_empty_columns")
    assert list(out.columns) == ["a"]


def test_remove_constant_columns():
    df = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
    out = run(df, "remove_constant_columns")
    assert list(out.columns) == ["b"]


def test_handle_outliers_clip():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 100]})
    out = run(df, "handle_outliers", column="a", method="clip")
    assert out["a"].max() < 100


def test_handle_outliers_remove():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 100]})
    out = run(df, "handle_outliers", column="a", method="remove")
    assert 100 not in out["a"].tolist()


def test_parse_dates():
    df = pd.DataFrame({"a": ["01/15/2020"]})
    out = run(df, "parse_dates", column="a", date_format="%m/%d/%Y")
    assert out["a"].iloc[0] == pd.Timestamp("2020-01-15")


def test_extract_date_component():
    df = pd.DataFrame({"a": pd.to_datetime(["2020-03-15"])})
    out = run(df, "extract_date_component", column="a", component="year")
    assert out["a_year"].iloc[0] == 2020
    out2 = run(df, "extract_date_component", column="a", component="weekday")
    assert out2["a_weekday"].iloc[0] == "Sunday"


def test_split_column():
    df = pd.DataFrame({"full": ["John Smith", "Jane Doe"]})
    out = run(df, "split_column", column="full", delimiter=" ", new_names=["first", "last"])
    assert out["first"].tolist() == ["John", "Jane"]
    assert out["last"].tolist() == ["Smith", "Doe"]


def test_combine_columns():
    df = pd.DataFrame({"first": ["John"], "last": ["Smith"]})
    out = run(df, "combine_columns", columns=["first", "last"], new_name="full", separator=" ")
    assert out["full"].iloc[0] == "John Smith"


def test_pipeline_step_error_does_not_abort_remaining_steps():
    df = pd.DataFrame({"a": [1, 2]})
    steps = [
        PipelineStep("rename_column", {"column": "nonexistent", "new_name": "x"}),
        PipelineStep("remove_duplicates", {}),
    ]
    result, errors = apply_pipeline(df, steps)
    assert len(errors) == 1
    assert len(result) == 2  # second step still ran


def test_disabled_step_is_skipped():
    df = pd.DataFrame({"a": [1, 1, 2]})
    steps = [PipelineStep("remove_duplicates", {}, enabled=False)]
    result, errors = apply_pipeline(df, steps)
    assert len(result) == 3


# --- transforms.py ---

def test_filter_rows_numeric_comparator():
    df = pd.DataFrame({"a": [1, 5, 10]})
    out = run(df, "filter_rows", column="a", comparator=">", value=4)
    assert out["a"].tolist() == [5, 10]


def test_filter_rows_contains():
    df = pd.DataFrame({"a": ["apple pie", "banana", "apple tart"]})
    out = run(df, "filter_rows", column="a", comparator="contains", value="apple")
    assert len(out) == 2


def test_filter_rows_is_null():
    df = pd.DataFrame({"a": [1, None, 3]})
    out = run(df, "filter_rows", column="a", comparator="is null", value=None)
    assert len(out) == 1


def test_sort_rows():
    df = pd.DataFrame({"a": [3, 1, 2]})
    out = run(df, "sort_rows", columns=["a"], ascending=True)
    assert out["a"].tolist() == [1, 2, 3]


def test_select_and_drop_columns():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    assert list(run(df, "select_columns", columns=["a", "c"]).columns) == ["a", "c"]
    assert list(run(df, "drop_columns", columns=["b"]).columns) == ["a", "c"]


def test_select_columns_missing_raises():
    df = pd.DataFrame({"a": [1]})
    _, errors = apply_pipeline(df, [PipelineStep("select_columns", {"columns": ["nope"]})])
    assert errors


def test_calculated_column():
    df = pd.DataFrame({"revenue": [100.0, 200.0], "units": [10.0, 20.0]})
    out = run(df, "calculated_column", new_name="price", expression="revenue / units")
    assert out["price"].tolist() == [10.0, 10.0]


def test_calculated_column_rejects_unsafe_expression():
    df = pd.DataFrame({"a": [1]})
    _, errors = apply_pipeline(df, [PipelineStep("calculated_column", {
        "new_name": "bad", "expression": "__import__('os').system('echo hi')",
    })])
    assert errors


def test_group_aggregate():
    df = pd.DataFrame({"region": ["E", "E", "W"], "rev": [10.0, 20.0, 30.0]})
    out = run(df, "group_aggregate", group_by=["region"], aggregations={"rev": "sum"})
    assert dict(zip(out["region"], out["rev"])) == {"E": 30.0, "W": 30.0}


def test_pivot_and_unpivot_roundtrip_shape():
    df = pd.DataFrame({"r": ["E", "E", "W", "W"], "p": ["A", "B", "A", "B"], "v": [1.0, 2.0, 3.0, 4.0]})
    pivoted = run(df, "pivot", index="r", columns="p", values="v", aggfunc="sum")
    assert set(pivoted.columns) == {"r", "A", "B"}
    unpivoted = run(df, "unpivot", id_vars=["r", "p"], value_vars=["v"])
    assert set(unpivoted.columns) == {"r", "p", "variable", "value"}


def test_normalize_minmax():
    df = pd.DataFrame({"a": [0.0, 5.0, 10.0]})
    out = run(df, "normalize", columns=["a"], method="minmax")
    assert out["a"].tolist() == [0.0, 0.5, 1.0]


def test_normalize_zscore():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    out = run(df, "normalize", columns=["a"], method="zscore")
    assert out["a"].mean() == pytest.approx(0.0, abs=1e-9)


def test_encode_categorical_onehot():
    df = pd.DataFrame({"c": ["a", "b", "a"]})
    out = run(df, "encode_categorical", column="c", method="onehot")
    assert "c_a" in out.columns and "c_b" in out.columns
    assert "c" not in out.columns


def test_encode_categorical_label():
    df = pd.DataFrame({"c": ["b", "a", "b"]})
    out = run(df, "encode_categorical", column="c", method="label")
    assert out["c_code"].tolist() == [1, 0, 1]


def test_bin_column():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0, 5.0]})
    out = run(df, "bin_column", column="a", bins=2)
    assert out["a_bin"].notna().all()
    assert out["a_bin"].nunique() == 2
