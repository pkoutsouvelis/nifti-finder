"""Interfaces and base classes for filepath filtering"""

from __future__ import annotations

__all__ = [
    "Filter",
    "Logic",
]
from enum import Enum
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Logic(str, Enum):
    AND = "AND"
    OR = "OR"


class Filter(ABC):
    """Interface for any filepath filter"""
    @abstractmethod
    def __call__(self, filepath: Path | str, /) -> bool: ...

    def filter(self, filepath: Path | str, /) -> bool:
        return self(filepath)