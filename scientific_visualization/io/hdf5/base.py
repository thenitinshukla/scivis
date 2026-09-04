from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DatasetDescriptor:
    name: str
    shape: tuple[int, ...]
    units: str = ""
    kind: str = "scalar"


class DataReader(ABC):
    @abstractmethod
    def can_read(self, path: str | Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def discover(self, path: str | Path) -> list[DatasetDescriptor]:
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str | Path, quantity: str | None = None):
        raise NotImplementedError


class HDF5ReaderRegistry:
    """Format-neutral entry point. Concrete readers are selected by file inspection."""

    def __init__(self, readers: Iterable[DataReader] = ()):
        self.readers = list(readers)

    def register(self, reader: DataReader):
        self.readers.append(reader)

    def reader_for(self, path: str | Path) -> DataReader:
        for reader in self.readers:
            if reader.can_read(path):
                return reader
        raise ValueError(f"No supported HDF5 reader recognized '{path}'")

    def load(self, path: str | Path, quantity: str | None = None):
        return self.reader_for(path).load(path, quantity=quantity)
