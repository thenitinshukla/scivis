import numpy as np
import pandas as pd
import pytest

from scientific_visualization.workspace.types import (
    ColumnType, classify_dataframe, detect_column_type, suggest_conversion, to_object_str,
)


def test_numeric_column_detected():
    s = pd.Series([1, 2, 3, 4.5])
    assert detect_column_type(s) == ColumnType.NUMERIC


def test_boolean_column_detected_from_yes_no_strings():
    s = pd.Series(["yes", "no", "yes", "no"])
    assert detect_column_type(s) == ColumnType.BOOLEAN


def test_boolean_column_detected_from_bool_dtype():
    s = pd.Series([True, False, True])
    assert detect_column_type(s) == ColumnType.BOOLEAN


def test_datetime_stored_as_string_detected():
    s = pd.Series(["2020-01-01", "2020-02-15", "2020-03-30"])
    assert detect_column_type(s) == ColumnType.DATETIME


def test_datetime_dtype_detected():
    s = pd.Series(pd.to_datetime(["2020-01-01", "2020-02-15"]))
    assert detect_column_type(s) == ColumnType.DATETIME


def test_currency_column_detected():
    s = pd.Series(["$1,000", "$2,500.50", "$999"])
    assert detect_column_type(s) == ColumnType.CURRENCY


def test_currency_with_euro_symbol_detected():
    s = pd.Series(["\u20ac1.000", "\u20ac2.500,50"])
    assert detect_column_type(s) == ColumnType.CURRENCY


def test_percentage_column_detected():
    s = pd.Series(["12%", "5.5%", "100%"])
    assert detect_column_type(s) == ColumnType.PERCENTAGE


def test_geographic_column_detected_by_name():
    s = pd.Series(["France", "Spain", "France", "Spain"])
    assert detect_column_type(s, name="country") == ColumnType.GEOGRAPHIC


def test_identifier_detected_for_fully_unique_short_values():
    s = pd.Series([f"ID-{i}" for i in range(20)])
    assert detect_column_type(s, name="record_id") == ColumnType.IDENTIFIER


def test_free_text_not_misclassified_as_identifier():
    s = pd.Series([f"This is a fairly long free-text note number {i} about something" for i in range(20)])
    assert detect_column_type(s, name="notes") == ColumnType.TEXT


def test_categorical_detected_for_small_repeated_set():
    s = pd.Series(["red", "green", "blue"] * 20)
    assert detect_column_type(s) == ColumnType.CATEGORICAL


def test_empty_column_detected():
    s = pd.Series([None, None, np.nan])
    assert detect_column_type(s) == ColumnType.EMPTY


def test_numeric_identifier_detected_by_name_hint():
    s = pd.Series(range(1, 21))
    assert detect_column_type(s, name="customer_id") == ColumnType.IDENTIFIER


def test_numeric_not_misclassified_as_identifier_without_name_hint():
    s = pd.Series(range(1, 21))
    assert detect_column_type(s, name="age") == ColumnType.NUMERIC


def test_classify_dataframe_returns_all_columns():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    result = classify_dataframe(df)
    assert set(result) == {"a", "b"}


# --- suggest_conversion ---

def test_suggest_conversion_for_string_dates():
    s = pd.Series(["2020-01-01", "2020-02-02"])
    suggestion = suggest_conversion(s, ColumnType.DATETIME)
    assert suggestion is not None
    assert suggestion.to_dtype == "datetime64[ns]"


def test_suggest_conversion_none_when_already_correct_dtype():
    s = pd.Series(pd.to_datetime(["2020-01-01", "2020-02-02"]))
    assert suggest_conversion(s, ColumnType.DATETIME) is None


def test_suggest_conversion_for_currency_text():
    s = pd.Series(["$100", "$200"])
    suggestion = suggest_conversion(s, ColumnType.CURRENCY)
    assert suggestion is not None
    assert suggestion.to_dtype == "float64"


# --- to_object_str (regression guard for the pandas 3.0 string-dtype pitfall) ---

def test_to_object_str_preserves_missing_values():
    s = pd.Series(["a", None, "b"])
    result = to_object_str(s)
    assert result.iloc[1] is None or pd.isna(result.iloc[1])
    assert result.iloc[0] == "a"


def test_to_object_str_supports_unicode_regex_without_pyarrow_error():
    # This exact pattern (a \u escape) crashes pandas' PyArrow-backed
    # ".str.match" engine; to_object_str exists specifically so downstream
    # regex operations don't hit that.
    s = pd.Series(["\u20ac100", "\u20ac200"])
    result = to_object_str(s).str.match(r"^\u20ac\d+$")
    assert result.all()
