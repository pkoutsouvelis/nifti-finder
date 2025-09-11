"""Interfaces and base classes for file explorers"""

from __future__ import annotations

__all__ = [
    "FileExplorer",
]

from abc import ABC, abstractmethod
from typing import Iterator, TYPE_CHECKING

from nifti_finder.filters import FilterableMixin

if TYPE_CHECKING:
    from pathlib import Path

class FileExplorer(ABC):
    """Interface for file explorer"""
    @abstractmethod
    def scan(self, root_dir: Path | str, /) -> Iterator[Path]:
        """Get all files in a directory"""
        ...


class FilterableFileExplorer(FileExplorer, FilterableMixin):
    """Abstract file explorer with filtering support."""
    ...