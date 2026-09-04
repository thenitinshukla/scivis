from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.configuration import RenderingConfig
from ..core.data import Dataset


class Renderer(ABC):
    @abstractmethod
    def render(self, dataset: Dataset, config: RenderingConfig):
        raise NotImplementedError
