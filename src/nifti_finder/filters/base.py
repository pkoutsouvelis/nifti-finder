"""Interface for filter"""

from __future__ import annotations

__all__ = [
    "Filter",
]
from abc import ABC, abstractmethod
from pathlib import Path

class Filter(ABC):
    """Interface for filter"""
    @abstractmethod
    def __call__(self, filepath: Path, /) -> bool: ...

    def filter(self, filepath: Path) -> bool:  # pragma: no cover
        return self(filepath)