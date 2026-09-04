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
    rows = [_split(line, detected) for line in lines]
    width = max((len(r) for r in rows), default=0)
    if width < 1:
        raise ValueError(f"Could not detect columns in '{path.name}'")

    # Whitespace-delimited scientific files often align headers with multiple
    # spaces, while a logical field may itself contain a space, e.g.
    # ``Total GPUs``. Parse such headers independently from numeric rows.
    has_header = False
    first = rows[0]
    header_candidates = first
    if detected == " " and len(lines) > 1 and not _is_numeric_row(first):
        raw_header = lines[0].strip()
        candidate = [part.strip() for part in re.split(r"\s{2,}|\t+", raw_header) if part.strip()]
        numeric_width = len(rows[1]) if rows[1:] else 0
        if len(candidate) == numeric_width and numeric_width >= 1:
            header_candidates = candidate
    if len(lines) > 1 and not _is_numeric_row(first):
        if len(rows[1]) == len(header_candidates) and any(not re.fullmatch(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", x) for x in header_candidates):
            has_header = True

    if has_header:
        columns = [x or f"Column {i+1}" for i, x in enumerate(header_candidates)]
        data_rows = rows[1:]
    else:
        columns = [f"Column {i+1}" for i in range(width)]
        data_rows = rows

    parsed: list[list[float]] = []
    skipped = 0
    for row in data_rows:
        if len(row) != len(columns):
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
