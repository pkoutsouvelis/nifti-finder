"""Interfaces for file explorer and handler"""

from __future__ import annotations

__all__ = [
    "Filter", 
    "FileExplorer",
]

from abc import ABC, abstractmethod
from pathlib import Path

class Filter(ABC):
    """Protocol for filter"""
    @abstractmethod
    def filter(self, filepath: Path) -> bool:
        """Filter a file; return True if the file should be included, False otherwise"""
        pass

class FileExplorer(ABC):
    """Interface for file explorer"""
    @property
    @abstractmethod
    def root(self) -> Path:
        """Root dir the explorer is anchored at."""

    @abstractmethod
    def list(self, path: str) -> list[Path]:
        """Get all files in a directory"""
        pass
