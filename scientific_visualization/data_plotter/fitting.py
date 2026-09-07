"""User-defined curve fitting for the Data Plotter's Line/Scatter mode.

Every fit kind returns a `FitResult` with a ready-to-plot dense curve, a
human-readable equation string, and the R^2 of the fit against the actual
data points -- so the GUI layer only has to plot `x_fit`/`y_fit` and show
`equation`/`r_squared`, without knowing anything about the underlying math.

Linear/Polynomial/Exponential/Power-law/Logarithmic all reduce to an
ordinary least-squares polynomial fit (linearizing the nonlinear ones the
standard way: take logs of x and/or y), so none of them need SciPy. Custom
fits are arbitrary user-supplied formulas with free parameters (e.g.
``"a*sin(b*x)+c"``) fit by nonlinear least squares, which does need SciPy;
this is checked explicitly with a clear message rather than a confusing
ImportError if it's missing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .expressions import SAFE_FUNCTIONS

FIT_KINDS = ("Linear", "Polynomial", "Exponential", "Power law", "Logarithmic", "Custom")


@dataclass
class FitResult:
    kind: str
    params: dict[str, float]
    equation: str
    r_squared: float
    x_fit: np.ndarray
    y_fit: np.ndarray
    predict: Callable[[np.ndarray], np.ndarray] = field(repr=False)


def _clean_xy(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


def _finish(x: np.ndarray, y: np.ndarray, predict, equation: str, kind: str, params: dict, n_points: int = 200) -> FitResult:
    y_pred = predict(x)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else (1.0 if ss_res == 0 else 0.0)
    xs = np.linspace(float(np.min(x)), float(np.max(x)), n_points)
    return FitResult(kind=kind, params=params, equation=equation, r_squared=r_squared,
                      x_fit=xs, y_fit=predict(xs), predict=predict)


def _format_number(v: float) -> str:
    return f"{v:.4g}"


def _poly_fit(x: np.ndarray, y: np.ndarray, degree: int) -> FitResult:
    coeffs = np.polyfit(x, y, degree)
    predict = np.poly1d(coeffs)
    terms = []
    for i, c in enumerate(coeffs):
        power = degree - i
        magnitude = _format_number(abs(c))
        sign = "-" if c < 0 else "+"
        if power == 0:
            term = magnitude
        elif power == 1:
            term = f"{magnitude}\u00b7x"
        else:
            term = f"{magnitude}\u00b7x^{power}"
        terms.append((sign, term))
    equation = "y = " + terms[0][1] if terms[0][0] == "+" else "y = -" + terms[0][1]
    for sign, term in terms[1:]:
        equation += f" {sign} {term}"
    kind = "Linear" if degree == 1 else f"Polynomial (degree {degree})"
    params = {f"c{degree - i}": float(c) for i, c in enumerate(coeffs)}
    return _finish(x, y, predict, equation, kind, params)


def _exponential_fit(x: np.ndarray, y: np.ndarray) -> FitResult:
    if np.any(y <= 0):
        raise ValueError("Exponential fit (y = a\u00b7exp(b\u00b7x)) requires every Y value to be positive")
    b, ln_a = np.polyfit(x, np.log(y), 1)
    a = float(np.exp(ln_a))
    predict = lambda xx: a * np.exp(b * np.asarray(xx, dtype=float))
    equation = f"y = {_format_number(a)}\u00b7exp({_format_number(b)}\u00b7x)"
    return _finish(x, y, predict, equation, "Exponential", {"a": a, "b": float(b)})


def _power_law_fit(x: np.ndarray, y: np.ndarray) -> FitResult:
    if np.any(x <= 0) or np.any(y <= 0):
        raise ValueError("Power-law fit (y = a\u00b7x^b) requires every X and Y value to be positive")
    b, ln_a = np.polyfit(np.log(x), np.log(y), 1)
    a = float(np.exp(ln_a))
    predict = lambda xx: a * np.power(np.asarray(xx, dtype=float), b)
    equation = f"y = {_format_number(a)}\u00b7x^{_format_number(b)}"
    return _finish(x, y, predict, equation, "Power law", {"a": a, "b": float(b)})


def _logarithmic_fit(x: np.ndarray, y: np.ndarray) -> FitResult:
    if np.any(x <= 0):
        raise ValueError("Logarithmic fit (y = a\u00b7ln(x) + b) requires every X value to be positive")
    a, b = np.polyfit(np.log(x), y, 1)
    predict = lambda xx: a * np.log(np.asarray(xx, dtype=float)) + b
    equation = f"y = {_format_number(a)}\u00b7ln(x) + {_format_number(b)}"
    return _finish(x, y, predict, equation, "Logarithmic", {"a": float(a), "b": float(b)})


_RESERVED_NAMES = {"x", *SAFE_FUNCTIONS}
_DISALLOWED_PATTERN = re.compile(r"__|\.\s*\w|\[|\]|;|:=|\bimport\b|\blambda\b")


def _infer_custom_params(expression: str) -> list[str]:
    tokens = re.findall(r"\b[A-Za-z_]\w*\b", expression)
    seen = []
    for t in tokens:
        if t not in _RESERVED_NAMES and t not in seen:
            seen.append(t)
    return seen


def _custom_fit(x: np.ndarray, y: np.ndarray, expression: str) -> FitResult:
    expression = (expression or "").strip()
    if not expression:
        raise ValueError('Enter a custom formula in terms of x and free parameters, e.g. "a*exp(b*x)+c"')
    if _DISALLOWED_PATTERN.search(expression):
        raise ValueError("Formula contains characters that aren't allowed (only x, parameter names, numbers, and math functions/operators)")
    try:
        from scipy.optimize import curve_fit
    except ImportError as exc:
        raise ValueError("Custom fits need the optional 'scipy' package (pip install scipy) for nonlinear least squares") from exc

    param_names = _infer_custom_params(expression)
    if not param_names:
        raise ValueError('No free parameters found -- use letters like "a", "b" for the values to fit, e.g. "a*x+b"')
    try:
        code = compile(expression, "<fit expression>", "eval")
    except SyntaxError as exc:
        raise ValueError(f"Could not parse formula: {exc.msg}") from exc

    def func(xx, *params):
        namespace = dict(SAFE_FUNCTIONS)
        namespace["x"] = xx
        namespace.update(zip(param_names, params))
        return eval(code, {"__builtins__": {}}, namespace)  # noqa: S307 -- restricted namespace above

    try:
        popt, _ = curve_fit(func, x, y, p0=np.ones(len(param_names)), maxfev=10000)
    except Exception as exc:
        raise ValueError(f"Custom fit did not converge: {exc}") from exc

    predict = lambda xx: func(np.asarray(xx, dtype=float), *popt)
    params = dict(zip(param_names, (float(v) for v in popt)))
    param_text = ", ".join(f"{k}={_format_number(v)}" for k, v in params.items())
    equation = f"y = {expression}  ({param_text})"
    return _finish(x, y, predict, equation, "Custom", params)


def fit_curve(x, y, kind: str, *, order: int = 2, custom_expression: str = "") -> FitResult:
    """Fit `kind` to (x, y), ignoring any non-finite pairs.

    Raises ValueError (with a message safe to show the user directly) if
    there isn't enough data, the data's sign doesn't support the requested
    fit (e.g. negative Y for an exponential fit), or a custom formula fails
    to parse/converge.
    """
    x, y = _clean_xy(x, y)
    if x.size < 2:
        raise ValueError("Need at least 2 finite (X, Y) points to fit a curve")

    if kind == "Linear":
        return _poly_fit(x, y, 1)
    if kind == "Polynomial":
        degree = max(1, int(order))
        if x.size <= degree:
            raise ValueError(f"Need more than {degree} points for a degree-{degree} polynomial fit")
        return _poly_fit(x, y, degree)
    if kind == "Exponential":
        return _exponential_fit(x, y)
    if kind == "Power law":
        return _power_law_fit(x, y)
    if kind == "Logarithmic":
        return _logarithmic_fit(x, y)
    if kind == "Custom":
        return _custom_fit(x, y, custom_expression)
    raise ValueError(f"Unknown fit kind: {kind!r}")
