"""Interfaces for file explorer and handler"""

from __future__ import annotations

__all__ = [
    "Filter", 
    "FileExplorer",
    "FilterableFileExplorer",
]

from abc import ABC, abstractmethod
from pathlib import Path

class Filter(ABC):
    """Interface for filter"""
    @abstractmethod
    def filter(self, filepath: Path) -> bool:
        """Filter a file; return True if the file should be included, False otherwise"""
        pass

    def __call__(self, filepath: Path) -> bool:
        return self.filter(filepath)

class FileExplorer(ABC):
    """Interface for file explorer"""
    @property
    @abstractmethod
    def root(self) -> Path:
        """Root dir the explorer is anchored at."""

    @abstractmethod
    def list(self, recursive: bool = False) -> list[Path]:
        """Get all files in a directory"""
        pass

class FilterableFileExplorer(FileExplorer):
    """File explorer that can be filtered"""
    @abstractmethod
    def filters(self) -> list[Filter]:
        """Get the filters"""
        pass

    @abstractmethod
    def add_filter(self, filter: Filter):
        """Add a filter"""
        pass

    @abstractmethod
    def remove_filter(self, filter: Filter):
        """Remove a filter"""
        pass

    @abstractmethod
    def clear_filters(self):
        """Clear all filters"""
        pass

    @abstractmethod
    def apply_filters(self, files: Path) -> bool:
        """Apply the filters to a given filepath"""
        pass