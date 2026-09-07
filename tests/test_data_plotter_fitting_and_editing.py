import numpy as np
import pytest

from scientific_visualization.data_plotter.expressions import evaluate_column_expression
from scientific_visualization.data_plotter.fitting import FIT_KINDS, fit_curve
from scientific_visualization.data_plotter.model import DatasetTable


# --- fitting.py ---

def test_linear_fit_recovers_known_coefficients():
    x = np.linspace(0, 10, 30)
    y = 2.0 * x + 3.0
    r = fit_curve(x, y, "Linear")
    assert r.r_squared == pytest.approx(1.0, abs=1e-9)
    assert r.params["c1"] == pytest.approx(2.0, abs=1e-6)
    assert r.params["c0"] == pytest.approx(3.0, abs=1e-6)


def test_polynomial_fit_recovers_known_coefficients():
    x = np.linspace(-5, 5, 40)
    y = 1.5 * x ** 2 - 2.0 * x + 1.0
    r = fit_curve(x, y, "Polynomial", order=2)
    assert r.r_squared == pytest.approx(1.0, abs=1e-9)
    assert "degree 2" in r.kind


def test_polynomial_fit_requires_enough_points():
    x = np.array([1.0, 2.0])
    y = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="more than"):
        fit_curve(x, y, "Polynomial", order=3)


def test_exponential_fit_recovers_known_parameters():
    x = np.linspace(0, 5, 25)
    y = 2.0 * np.exp(0.5 * x)
    r = fit_curve(x, y, "Exponential")
    assert r.params["a"] == pytest.approx(2.0, rel=1e-4)
    assert r.params["b"] == pytest.approx(0.5, rel=1e-4)
    assert r.r_squared > 0.999


def test_exponential_fit_rejects_nonpositive_y():
    x = np.linspace(0, 5, 10)
    y = np.linspace(-1, 1, 10)
    with pytest.raises(ValueError, match="positive"):
        fit_curve(x, y, "Exponential")


def test_power_law_fit_recovers_known_parameters():
    x = np.linspace(1, 10, 25)
    y = 3.0 * x ** 1.5
    r = fit_curve(x, y, "Power law")
    assert r.params["a"] == pytest.approx(3.0, rel=1e-4)
    assert r.params["b"] == pytest.approx(1.5, rel=1e-4)


def test_logarithmic_fit_recovers_known_parameters():
    x = np.linspace(1, 20, 25)
    y = 4.0 * np.log(x) + 1.0
    r = fit_curve(x, y, "Logarithmic")
    assert r.params["a"] == pytest.approx(4.0, rel=1e-4)
    assert r.params["b"] == pytest.approx(1.0, abs=1e-3)


def test_custom_fit_recovers_known_parameters():
    scipy = pytest.importorskip("scipy")
    x = np.linspace(0, 10, 40)
    y = 5.0 * x + 2.0
    r = fit_curve(x, y, "Custom", custom_expression="a*x+b")
    assert r.params["a"] == pytest.approx(5.0, rel=1e-3)
    assert r.params["b"] == pytest.approx(2.0, abs=1e-2)


def test_custom_fit_rejects_unsafe_expression():
    x = np.linspace(0, 10, 10)
    y = np.linspace(0, 10, 10)
    with pytest.raises(ValueError, match="allowed"):
        fit_curve(x, y, "Custom", custom_expression="__import__('os').system('echo hi')")


def test_custom_fit_rejects_expression_with_no_parameters():
    pytest.importorskip("scipy")
    x = np.linspace(0, 10, 10)
    y = np.linspace(0, 10, 10)
    with pytest.raises(ValueError, match="free parameter"):
        fit_curve(x, y, "Custom", custom_expression="x*2")


def test_fit_requires_at_least_two_finite_points():
    with pytest.raises(ValueError, match="at least 2"):
        fit_curve([1.0, np.nan], [1.0, np.nan], "Linear")


def test_fit_ignores_nonfinite_pairs():
    x = np.array([1.0, 2.0, 3.0, np.nan, 5.0])
    y = np.array([2.0, 4.0, 6.0, 99.0, 10.0])
    r = fit_curve(x, y, "Linear")
    assert r.r_squared == pytest.approx(1.0, abs=1e-9)


def test_unknown_fit_kind_raises():
    with pytest.raises(ValueError, match="Unknown fit kind"):
        fit_curve([1, 2, 3], [1, 2, 3], "Not a real fit")


def test_all_declared_fit_kinds_are_handled():
    x = np.linspace(1, 10, 20)
    y = 2 * x + 1
    for kind in FIT_KINDS:
        try:
            fit_curve(x, y, kind, custom_expression="a*x+b")
        except ValueError as exc:
            assert "scipy" in str(exc).lower() or kind == "Custom"


# --- expressions.py ---

def test_evaluate_column_expression_basic_arithmetic():
    cols = ["a", "b"]
    values = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    result = evaluate_column_expression("b / a", cols, values)
    np.testing.assert_allclose(result, [10.0, 10.0, 10.0])


def test_evaluate_column_expression_handles_multiword_column_names():
    cols = ["Total GPUs", "Node"]
    values = np.array([[8.0, 2.0], [16.0, 4.0]])
    result = evaluate_column_expression("Total GPUs / Node", cols, values)
    np.testing.assert_allclose(result, [4.0, 4.0])


def test_evaluate_column_expression_supports_math_functions():
    cols = ["a"]
    values = np.array([[1.0], [np.e], [np.e ** 2]])
    result = evaluate_column_expression("log(a)", cols, values)
    np.testing.assert_allclose(result, [0.0, 1.0, 2.0], atol=1e-9)


def test_evaluate_column_expression_rejects_unsafe_input():
    cols = ["a"]
    values = np.array([[1.0], [2.0]])
    with pytest.raises(ValueError, match="allowed"):
        evaluate_column_expression("__import__('os').system('echo hi')", cols, values)


def test_evaluate_column_expression_rejects_unknown_names():
    cols = ["a"]
    values = np.array([[1.0], [2.0]])
    with pytest.raises(ValueError, match="Unknown name"):
        evaluate_column_expression("a + b", cols, values)


def test_evaluate_column_expression_rejects_empty_formula():
    cols = ["a"]
    values = np.array([[1.0], [2.0]])
    with pytest.raises(ValueError):
        evaluate_column_expression("", cols, values)


# --- model.py editing methods ---

def _table():
    return DatasetTable("a.csv", ["x", "y"], np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]), ",", True)


def test_add_computed_column():
    ds = _table()
    idx = ds.add_computed_column("ratio", "y / x")
    assert ds.columns[idx] == "ratio"
    np.testing.assert_allclose(ds.column_values(idx), [10.0, 10.0, 10.0])


def test_rename_column():
    ds = _table()
    ds.rename_column(0, "time")
    assert ds.columns[0] == "time"


def test_rename_column_rejects_empty_name():
    ds = _table()
    with pytest.raises(ValueError):
        ds.rename_column(0, "   ")


def test_add_row_defaults_to_nan():
    ds = _table()
    idx = ds.add_row()
    assert ds.row_count == 4
    assert np.all(np.isnan(ds.values[idx]))


def test_add_row_with_explicit_values():
    ds = _table()
    ds.add_row([4.0, 40.0])
    assert ds.row_count == 4
    np.testing.assert_allclose(ds.values[-1], [4.0, 40.0])


def test_add_row_rejects_wrong_width():
    ds = _table()
    with pytest.raises(ValueError):
        ds.add_row([1.0, 2.0, 3.0])


def test_remove_rows():
    ds = _table()
    ds.remove_rows([0])
    assert ds.row_count == 2
    np.testing.assert_allclose(ds.values[:, 0], [2.0, 3.0])


def test_remove_rows_rejects_removing_everything():
    ds = _table()
    with pytest.raises(ValueError):
        ds.remove_rows([0, 1, 2])


def test_remove_column():
    ds = _table()
    ds.remove_column(0)
    assert ds.columns == ["y"]
    assert ds.column_count == 1


def test_remove_last_column_rejected():
    ds = DatasetTable("a.csv", ["x"], np.array([[1.0], [2.0]]), ",", True)
    with pytest.raises(ValueError):
        ds.remove_column(0)


def test_sort_by_ascending_and_descending():
    ds = DatasetTable("a.csv", ["x", "y"], np.array([[3.0, 30.0], [1.0, 10.0], [2.0, 20.0]]), ",", True)
    ds.sort_by(0, ascending=True)
    np.testing.assert_allclose(ds.values[:, 0], [1.0, 2.0, 3.0])
    ds.sort_by(0, ascending=False)
    np.testing.assert_allclose(ds.values[:, 0], [3.0, 2.0, 1.0])


def test_sort_by_puts_nan_last_in_both_directions():
    ds = DatasetTable("a.csv", ["x"], np.array([[3.0], [np.nan], [1.0]]), ",", True)
    ds.sort_by(0, ascending=True)
    assert np.isnan(ds.values[-1, 0])
    ds.sort_by(0, ascending=False)
    assert np.isnan(ds.values[-1, 0])
