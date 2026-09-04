from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .model import DatasetTable
from .parser import Delimiter, parse_text_file


@dataclass
class BatchParseResult:
    datasets: list[DatasetTable]
    errors: list[str]


def parse_one(path: str, delimiter: Delimiter) -> DatasetTable:
    result = parse_text_file(path, delimiter)
    return DatasetTable(result.path, result.columns, result.values, result.delimiter,
                        result.has_header, result.skipped_comments, result.skipped_rows)


def parse_many(paths: list[str], delimiter: Delimiter = Delimiter.AUTO, max_workers: int | None = None) -> BatchParseResult:
    clean = [str(Path(p)) for p in paths if Path(p).suffix.lower() in {".csv", ".txt"}]
    if not clean:
        return BatchParseResult([], [])
    datasets: list[DatasetTable] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max_workers or min(8, len(clean))) as pool:
        futures = [(p, pool.submit(parse_one, p, delimiter)) for p in clean]
        for path, future in futures:
            try:
                datasets.append(future.result())
            except ValueError as exc:
                errors.append(str(exc))
            except Exception as exc:
                errors.append(f"{Path(path).name}: {exc}")
    return BatchParseResult(datasets, errors)
