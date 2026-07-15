"""File explorers for traversing datasets and retrieving files.

Includes:
- Base classes for file exploration:
    - `FileExplorer`
    - `RecursiveFileExplorer`
    - `NestedFileExplorer`
- Mixin classes for materializing results:
    - `MaterializeMixin`
- Recommended entry point:
    - `FileFinder`
- Deprecated explorers (scheduled for removal in v2.2.0):
    - `NeuroExplorer`
    - `BasicFileExplorer`
    - `TwoStageFileExplorer`
    - `AllPurposeFileExplorer`
"""

from __future__ import annotations

__all__ = [
    "FileExplorer",
    "MaterializeMixin",
    "RecursiveFileExplorer",
    "NestedFileExplorer",
    "FileFinder",
    "NeuroExplorer",
    "BasicFileExplorer",
    "TwoStageFileExplorer",
    "AllPurposeFileExplorer",
]

from .base import *
from .core import *
from .mixins import *
