"""Generic implementation of filterable file explorer"""

from __future__ import annotations

__all__ = [
    "GenericFilterableFileExplorer",
]

from pathlib import Path

from nifti_finder.explorers.base import FilterableFileExplorer
from nifti_finder.filters import Filter
from nifti_finder.utils import resolve_path

class GenericFilterableFileExplorer(FilterableFileExplorer):
    """Generic implementation of filterable file explorer"""
    def __init__(self, root_dir: str | Path):
        self._root = resolve_path(root_dir)
        self._filters: list[Filter] = []

    def root(self) -> Path:
        """Get the root directory"""
        return self._root

    def filters(self) -> list[Filter]:
        """Get the filters"""
        return self._filters

    def add_filters(self, filters: Filter | list[Filter]):
        """Add filter(s)"""
        if isinstance(filters, list):
            for f in filters:
                self.add_filters(f)
            return

        if not isinstance(filters, Filter):
            raise ValueError("Filter(s) must be an instance of nifti_finder.Filter or a list "
                             "of nifti_finder.Filter objects")
        self._filters.append(filters)

    def remove_filters(self, filters: Filter | list[Filter]):
        """Remove filter(s)"""
        if isinstance(filters, list):
            for f in filters:
                self.remove_filters(f)
            return

        if not isinstance(filters, Filter):
            raise ValueError("Filter(s) must be an instance of nifti_finder.Filter or a list "
                             "of nifti_finder.Filter objects")
        self._filters.remove(filters)

    def clear_filters(self):
        """Clear all filters"""
        self._filters = []
    
    def apply_filters(self, files: Path) -> bool:
        """Apply the filters to a list of files"""
        return all(filter.filter(files) for filter in self._filters)