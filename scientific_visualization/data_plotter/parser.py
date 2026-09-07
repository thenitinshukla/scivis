from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

import numpy as np


class Delimiter(str, Enum):
    AUTO = "Automatic"
    COMMA = "Comma (,)"
    TAB = "Tab"
    SPACE = "Space"
    SEMICOLON = "Semicolon (;)"

    @property
    def char(self) -> str | None:
        return {
            Delimiter.AUTO: None,
            Delimiter.COMMA: ",",
            Delimiter.TAB: "\t",
            Delimiter.SPACE: None,
            Delimiter.SEMICOLON: ";",
        }[self]


@dataclass
class ParseResult:
    path: str
    columns: list[str]
    values: np.ndarray
    delimiter: str
    has_header: bool
    skipped_comments: int
    skipped_rows: int


def _data_lines(text: str) -> tuple[list[str], int]:
    lines, comments = [], 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments += 1
            continue
        lines.append(line)
    return lines, comments


def _split(line: str, delimiter: str | None) -> list[str]:
    if delimiter == " ":
        return re.split(r"\s+", line.strip())
    if delimiter is None:
        return re.split(r"\s+", line.strip())
    return [part.strip() for part in line.split(delimiter)]


def detect_delimiter(lines: list[str]) -> str:
    candidates = [",", "\t", ";", " "]
    sample = lines[: min(8, len(lines))]
    scores = {}
    for candidate in candidates:
        counts = [len(_split(line, candidate)) for line in sample]
        if counts and min(counts) >= 2 and len(set(counts)) == 1:
            scores[candidate] = (counts[0], -sum(len(x) for x in sample))
    if scores:
        return max(scores, key=scores.get)
    return " "


def _is_numeric_row(parts: list[str]) -> bool:
    try:
        [float(x) for x in parts]
        return True
    except ValueError:
        return False


def _fast_numeric_parse(data_rows: list[str], width: int, delimiter: str | None) -> np.ndarray | None:
    """Vectorized fallback-free parse for the common case: every row has
    exactly `width` whitespace/comma/tab/semicolon-separated numeric fields.

    ``np.fromstring`` parses the whole text blob in C, which is roughly
    20x faster than building Python floats one cell at a time (the
    original per-row ``float(x)`` loop below). It cannot express this
    module's per-cell NaN-on-bad-value behavior or tolerate ragged rows,
    so it is only used as a fast path: any row-count/shape mismatch
    (ragged rows, stray non-numeric tokens, missing values, ...) makes it
    return None and the caller transparently falls back to the exact,
    fully general row-by-row parser further down.

    ``data_rows`` must already have been verified (by the caller) to all
    contain exactly ``width`` fields -- this function only does the bulk
    numeric conversion, not field-count validation.
    """
    if not data_rows:
        return None
    sep = " " if delimiter in (None, " ") else delimiter
    blob = "\n".join(data_rows)
    try:
        flat = np.fromstring(blob, dtype=float, sep=sep)
    except (ValueError, TypeError):
        return None
    if flat.size != len(data_rows) * width:
        # A row had an unexpected number of fields, a token numpy couldn't
        # parse (e.g. "nan" with stray characters, "N/A", empty fields from
        # doubled delimiters), or similar -- bail out to the robust path
        # rather than risk silently misaligning columns.
        return None
    return flat.reshape(len(data_rows), width)


def _verify_uniform_width(data_rows: list[str], delimiter: str | None, width: int, sample: int = 200) -> bool:
    """Cheaply check that rows look like they all split into `width` fields.

    Checking every row would cost as much as just parsing them, so this
    samples up to `sample` rows spread across the file (most real-world
    ragged/corrupt data shows up either near the top or is scattered
    throughout, and a spread-out sample catches both far better than only
    checking the first few lines). The fast path is only attempted when
    the sample passes; the final size check in `_fast_numeric_parse`
    still guards against anything the sample missed.
    """
    n = len(data_rows)
    if n <= sample:
        indices = range(n)
    else:
        step = n / sample
        indices = (int(i * step) for i in range(sample))
    return all(len(_split(data_rows[i], delimiter)) == width for i in indices)


def _detect_header(lines: list[str], detected: str | None) -> tuple[bool, list[str], list[str], list[str]]:
    """Inspect just the first two lines to decide on a header and column
    names. Returns (has_header, header_candidates, row0, row1) where row0
    and row1 are the split first/second lines -- the only rows this
    function needs to split, so callers with thousands of data rows never
    pay for splitting rows they don't need yet.
    """
    row0 = _split(lines[0], detected)
    row1 = _split(lines[1], detected) if len(lines) > 1 else []

    has_header = False
    header_candidates = row0
    if detected == " " and len(lines) > 1 and not _is_numeric_row(row0):
        raw_header = lines[0].strip()
        candidate = [part.strip() for part in re.split(r"\s{2,}|\t+", raw_header) if part.strip()]
        numeric_width = len(row1)
        if len(candidate) == numeric_width and numeric_width >= 1:
            header_candidates = candidate
    if len(lines) > 1 and not _is_numeric_row(row0):
        if len(row1) == len(header_candidates) and any(
            not re.fullmatch(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", x) for x in header_candidates
        ):
            has_header = True
    return has_header, header_candidates, row0, row1


def parse_text_file(path: str | Path, delimiter: Delimiter = Delimiter.AUTO) -> ParseResult:
    path = Path(path)
    if path.suffix.lower() not in {".csv", ".txt"}:
        raise ValueError(f"Unsupported data file type: {path.suffix or '<none>'}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    except OSError as exc:
        raise ValueError(f"Could not read '{path}': {exc}") from exc

    lines, comments = _data_lines(text)
    if not lines:
        raise ValueError(f"'{path.name}' is empty or contains only comments")

    detected = delimiter.char if delimiter != Delimiter.AUTO else detect_delimiter(lines)

    # Only split the first two lines up front (needed for header detection).
    # Splitting every line is the expensive step on large files, so it is
    # deferred until we know we actually need it (the slow-path fallback
    # below), rather than done unconditionally like the rest of the rows.
    has_header, header_candidates, row0, row1 = _detect_header(lines, detected)
    data_row_strings = lines[1:] if has_header else lines
    guess_width = len(row1) if has_header else len(row0)

    skipped = 0
    array = None
    columns: list[str] | None = None

    # Fast path: most scientific data files are perfectly rectangular, so
    # try a single vectorized parse of the raw lines first (no per-row
    # Python splitting/float() calls at all) and only fall back to the
    # fully general per-cell loop when that assumption doesn't hold.
    if guess_width >= 1 and _verify_uniform_width(data_row_strings, detected, guess_width):
        fast_array = _fast_numeric_parse(data_row_strings, guess_width, detected)
        if fast_array is not None:
            array = fast_array
            columns = (
                [x or f"Column {i+1}" for i, x in enumerate(header_candidates)]
                if has_header
                else [f"Column {i+1}" for i in range(guess_width)]
            )

    if array is None:
        # Robust path: split every line and convert cell-by-cell, tolerating
        # ragged rows and bad/missing values exactly as before.
        rows = [_split(line, detected) for line in lines]
        width = max((len(r) for r in rows), default=0)
        if width < 1:
            raise ValueError(f"Could not detect columns in '{path.name}'")

        if has_header:
            columns = [x or f"Column {i+1}" for i, x in enumerate(header_candidates)]
            data_rows = rows[1:]
        else:
            columns = [f"Column {i+1}" for i in range(width)]
            data_rows = rows
        width = len(columns)

        parsed: list[list[float]] = []
        for row in data_rows:
            if len(row) != width:
                skipped += 1
                continue
            try:
                values = [float(x) for x in row]
            except ValueError:
                # Allow missing/invalid entries while keeping the row shape.
                values = []
                for x in row:
                    try:
                        values.append(float(x))
                    except ValueError:
                        values.append(np.nan)
            parsed.append(values)

        if not parsed:
            raise ValueError(f"No numeric data rows could be read from '{path.name}'")
        array = np.asarray(parsed, dtype=float)

    if array.ndim != 2 or array.shape[1] == 0:
        raise ValueError(f"No numeric columns could be read from '{path.name}'")
    return ParseResult(str(path), columns, array, detected, has_header, comments, skipped)
