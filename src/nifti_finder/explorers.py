"""File explorer implementations"""

from __future__ import annotations

from pathlib import Path

from nifti_finder.interfaces import FileExplorer, Filter
from nifti_finder.utils import get_ext, resolve_path

class GenericNiftiExplorer(FileExplorer):
    """File explorer for nifti files"""
    def __init__(self, root_dir: str | Path):
        self._root = resolve_path(root_dir)
        self._filters: list[Filter] = []

    def root(self) -> Path:
        """Get the root directory"""
        return self._root
    
    def filters(self) -> list[Filter]:
        """Get the filters"""
        return self._filters

    def add_filter(self, filter: Filter):
        """Add a filter"""
        if not isinstance(filter, Filter):
            raise ValueError("Filter must be an instance of nifti_finder.Filter")
        self._filters.append(filter)