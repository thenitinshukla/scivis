import numpy as np
import pandas as pd
import pytest

from scientific_visualization.workspace.session import WorkspaceSession
from scientific_visualization.workspace.recommend import suggest_for_dataset, suggest_for_pair
from scientific_visualization.workspace.types import ColumnType


@pytest.fixture
def session_with_data():
    df = pd.DataFrame({
        "year": [2016, 2017, 2018, 2019, 2020],
        "price": [100.0, 120.0, None, 160.0, 180.0],
        "city": [" Lisbon", " Lisbon ", "Porto", "Porto", "Porto"],
    })
    sess = WorkspaceSession()
    sess.load_dataframe("test.csv", df)
    return sess


# --- WorkspaceSession ---

def test_load_dataframe_populates_original_and_current(session_with_data):
    sess = session_with_data
    assert sess.loaded
    assert sess.current.shape == (5, 3)
    pd.testing.assert_frame_equal(sess.original, sess.current)


def test_load_from_file(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3]})
    p = tmp_path / "d.csv"
    df.to_csv(p, index=False)
    sess = WorkspaceSession()
    sess.load(p)
    assert sess.name == "d.csv"
    assert sess.current["a"].tolist() == [1, 2, 3]


def test_add_step_updates_current_not_original(session_with_data):
    sess = session_with_data
    sess.add_step("trim_whitespace", {"columns": ["city"]})
    assert sess.current["city"].iloc[0] == "Lisbon"
    assert sess.original["city"].iloc[0] == " Lisbon"  # untouched


def test_undo_removes_last_step_effect(session_with_data):
    sess = session_with_data
    sess.add_step("trim_whitespace", {"columns": ["city"]})
    sess.add_step("fill_missing", {"columns": ["price"], "method": "mean"})
    assert not sess.current["price"].isna().any()
    sess.undo()
    assert sess.current["price"].isna().any()
    assert sess.current["city"].iloc[0] == "Lisbon"  # first step still applied


def test_remove_step_by_index(session_with_data):
    sess = session_with_data
    sess.add_step("trim_whitespace", {"columns": ["city"]})
    sess.add_step("fill_missing", {"columns": ["price"], "method": "mean"})
    sess.remove_step(0)
    assert len(sess.pipeline) == 1
    assert sess.current["city"].iloc[0] == " Lisbon"  # trim was removed
    assert not sess.current["price"].isna().any()  # fill still applied


def test_move_step_reorders_pipeline(session_with_data):
    sess = session_with_data
    sess.add_step("fill_missing", {"columns": ["price"], "method": "mean"})
    sess.add_step("trim_whitespace", {"columns": ["city"]})
    sess.move_step(1, 0)
    assert [s.op for s in sess.pipeline] == ["trim_whitespace", "fill_missing"]


def test_toggle_step_disables_without_removing(session_with_data):
    sess = session_with_data
    sess.add_step("trim_whitespace", {"columns": ["city"]})
    sess.toggle_step(0, False)
    assert sess.current["city"].iloc[0] == " Lisbon"
    assert len(sess.pipeline) == 1
    assert sess.pipeline[0].enabled is False


def test_clear_pipeline_restores_original(session_with_data):
    sess = session_with_data
    sess.add_step("trim_whitespace", {"columns": ["city"]})
    sess.clear_pipeline()
    pd.testing.assert_frame_equal(sess.current, sess.original)


def test_bad_step_recorded_in_errors_but_does_not_crash(session_with_data):
    sess = session_with_data
    sess.add_step("rename_column", {"column": "does_not_exist", "new_name": "x"})
    assert sess.errors
    assert sess.current is not None


def test_profile_reflects_current_by_default(session_with_data):
    sess = session_with_data
    before = sess.profile()
    assert before.total_missing() == 1
    sess.add_step("fill_missing", {"columns": ["price"], "method": "mean"})
    after = sess.profile()
    assert after.total_missing() == 0


def test_profile_use_original_ignores_pipeline(session_with_data):
    sess = session_with_data
    sess.add_step("fill_missing", {"columns": ["price"], "method": "mean"})
    original_profile = sess.profile(use_original=True)
    assert original_profile.total_missing() == 1


def test_column_types(session_with_data):
    types = session_with_data.column_types()
    assert types["year"] == ColumnType.NUMERIC


def test_to_numeric_dataset_bridges_to_data_plotter(session_with_data):
    sess = session_with_data
    sess.add_step("fill_missing", {"columns": ["price"], "method": "mean"})
    ds = sess.to_numeric_dataset()
    assert "year" in ds.columns
    assert "price" in ds.columns
    assert "city" not in ds.columns  # non-numeric, dropped
    assert ds.values.shape[0] == 5


def test_to_numeric_dataset_raises_when_nothing_numeric():
    sess = WorkspaceSession()
    sess.load_dataframe("t.csv", pd.DataFrame({"a": ["x", "y", "z"]}))
    with pytest.raises(ValueError, match="No numeric"):
        sess.to_numeric_dataset()


def test_to_numeric_dataset_raises_when_nothing_loaded():
    sess = WorkspaceSession()
    with pytest.raises(ValueError):
        sess.to_numeric_dataset()


# --- recommend.py ---

def test_suggest_for_dataset_recommends_correlation_for_multiple_numeric():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
    suggestions = suggest_for_dataset(df)
    assert any(s.chart_type == "Correlation heatmap" for s in suggestions)


def test_suggest_for_dataset_recommends_line_chart_for_datetime_and_numeric():
    df = pd.DataFrame({"date": pd.to_datetime(["2020-01-01", "2020-02-01"]), "value": [1.0, 2.0]})
    suggestions = suggest_for_dataset(df)
    assert any(s.chart_type == "Line chart" for s in suggestions)


def test_suggest_for_pair_numeric_numeric_is_scatter():
    df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    suggestions = suggest_for_pair(df, "a", "b")
    assert suggestions[0].chart_type == "Scatter plot"


def test_suggest_for_pair_categorical_numeric_is_bar():
    df = pd.DataFrame({"cat": ["x", "y"], "val": [1.0, 2.0]})
    suggestions = suggest_for_pair(df, "cat", "val")
    assert suggestions[0].chart_type == "Bar chart"


def test_suggest_for_pair_single_numeric_column_is_histogram():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    suggestions = suggest_for_pair(df, "a", None)
    assert suggestions[0].chart_type == "Histogram"


def test_suggest_for_pair_two_categorical_is_crosstab():
    df = pd.DataFrame({"a": ["x", "y"], "b": ["p", "q"]})
    suggestions = suggest_for_pair(df, "a", "b")
    assert suggestions[0].chart_type == "Cross-tab heatmap"
