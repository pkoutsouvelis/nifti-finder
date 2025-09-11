"""Generic file explorer implementations"""

from __future__ import annotations

__all__ = [
    "GenericFilterableFileExplorer",
]

from pathlib import Path
from typing import Iterator

from nifti_finder.explorers.base import FilterableFileExplorer
from nifti_finder.utils import resolve_path


class GenericFilterableFileExplorer(FilterableFileExplorer):
    """
    Concrete file explorer with filtering support.

    Finds all files in a directory and applies a cached composed filter to each filepath.

    Example use-cases: 
    A. Nifti-file ('.nii.gz' or '.nii') finder for a generic dataset:
    ```
    >>> explorer = GenericFilterableFileExplorer(
    ...     filters=[IncludeExtension("nii.gz"), IncludeExtension("nii")],
    ...     logic="OR",
    ... )
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```
    B. Find T1w files ('.nii.gz' or '.nii') in the `anat` directory of a BIDS-style dataset:
    ```
    >>> explorer = GenericFilterableFileExplorer(
    ...     filters=[IncludeDirectorySuffix("anat"), IncludeFileSuffix("T1w")],
    ...     logic="AND",
    ... )
    >>> explorer.add_filters(
    ...     ComposeFilter([IncludeExtension("nii.gz"), IncludeExtension("nii")], logic="OR")
    ... )
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```
    """
    def scan(self, root_dir: Path | str, /) -> Iterator[Path]:
        root = resolve_path(root_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a valid directory")

        for path in root.rglob("*"):
            if path.is_file():
                if self.apply_filters(path):
                    yield path