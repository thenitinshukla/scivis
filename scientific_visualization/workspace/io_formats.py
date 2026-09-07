"""Multi-format dataset import.

`load_any` is the single entry point: it dispatches on file extension to
the right pandas reader, with clear, actionable error messages when an
optional dependency (openpyxl for .xlsx, pyarrow/fastparquet for
.parquet) isn't installed, rather than letting a raw ImportError surface.

CSV/TSV/TXT reuse the existing delimiter/header sniffing already built for
the Data Plotter (`data_plotter.parser`) so behavior stays consistent
between the two rather than having two independent, possibly-diverging
sniffers.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".tsv", ".txt", ".json", ".xlsx", ".xls", ".parquet")


def _read_delimited(path: Path) -> pd.DataFrame:
    from ..data_plotter.parser import Delimiter, detect_delimiter, _data_lines

    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    lines, _comments = _data_lines(text)
    if not lines:
        raise ValueError(f"'{path.name}' is empty or contains only comments")
    delimiter = "\t" if path.suffix.lower() == ".tsv" else detect_delimiter(lines)
    sep = r"\s+" if delimiter is None else delimiter
    try:
        return pd.read_csv(path, sep=sep, engine="python" if delimiter is None else "c",
                          comment="#", skip_blank_lines=True)
    except Exception as exc:
        raise ValueError(f"Could not parse '{path.name}' as delimited text: {exc}") from exc


def _read_json(path: Path) -> pd.DataFrame:
    try:
        return pd.read_json(path)
    except ValueError:
        # Common alternate shape: newline-delimited JSON records.
        try:
            return pd.read_json(path, lines=True)
        except Exception as exc:
            raise ValueError(
                f"Could not parse '{path.name}' as JSON. Expected either a JSON array of "
                f"objects, a {{column: {{index: value}}}} mapping, or newline-delimited JSON records."
            ) from exc


def _read_excel(path: Path, sheet_name=0) -> pd.DataFrame:
    try:
        import openpyxl  # noqa: F401
    except ImportError as exc:
        raise ValueError("Reading .xlsx files needs the optional 'openpyxl' package (pip install openpyxl)") from exc
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as exc:
        raise ValueError(f"Could not read '{path.name}': {exc}") from exc


def _read_parquet(path: Path) -> pd.DataFrame:
    try:
        return pd.read_parquet(path)
    except ImportError as exc:
        raise ValueError(
            "Reading .parquet files needs the optional 'pyarrow' (or 'fastparquet') package "
            "(pip install pyarrow)"
        ) from exc
    except Exception as exc:
        raise ValueError(f"Could not read '{path.name}': {exc}") from exc


def list_excel_sheets(path: str | Path) -> list[str]:
    """Sheet names for an .xlsx/.xls file, for a sheet-picker UI."""
    import openpyxl
    path = Path(path)
    if path.suffix.lower() == ".xls":
        return list(pd.ExcelFile(path).sheet_names)
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def load_any(path: str | Path, *, sheet_name=0) -> pd.DataFrame:
    """Load any supported tabular file into a DataFrame.

    Raises ValueError (safe to show directly to the user) for unsupported
    extensions, missing optional dependencies, or parse failures.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if not path.exists():
        raise ValueError(f"File not found: {path}")
    if suffix in (".csv", ".tsv", ".txt"):
        df = _read_delimited(path)
    elif suffix == ".json":
        df = _read_json(path)
    elif suffix in (".xlsx", ".xls"):
        df = _read_excel(path, sheet_name=sheet_name)
    elif suffix == ".parquet":
        df = _read_parquet(path)
    else:
        raise ValueError(
            f"Unsupported file type '{suffix or path.name}'. Supported: "
            f"{', '.join(SUPPORTED_EXTENSIONS)}"
        )
    if df.shape[1] == 0:
        raise ValueError(f"'{path.name}' has no columns")
    # Normalize column labels to plain strings -- some readers (esp. Excel/
    # JSON) can hand back ints, tuples (MultiIndex), or NaN as column names.
    df.columns = [str(c) for c in df.columns]
    return df
