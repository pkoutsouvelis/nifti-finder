"""Concrete implementation of file explorers"""

from __future__ import annotations

__all__ = [
    "GenericFilterableFileExplorer",
    "NiftiExplorer",
]

from pathlib import Path
from typing import Iterator
from collections.abc import Sequence

from nifti_finder.explorers.base import FilterableFileExplorer
from nifti_finder.explorers.mixins import MaterializeMixin
from nifti_finder.filters import Filter, Logic
from nifti_finder.utils import resolve_path, ensure_seq


class GenericFilterableFileExplorer(FilterableFileExplorer, MaterializeMixin):
    """
    Concrete file explorer with filtering support and convenience methods for materializing `scan()`.

    Finds all files in a directory and applies a cached composed filter to each filepath.
    
    Note:
        For faster exploration, prioritize `patterns` for filtering by name; apply subsequent filters
        only to the narrowed down results. Suppports multiple `patterns`, but will traverse the
        directory once per pattern, which can be slow on large datasets. 
        The best performance is expected with a single pattern + filters.
    
    Example use-cases: 
    A. Find all nifti files ('.nii.gz' or '.nii') in any dataset, regardless the structure:
    ```
    >>> explorer = GenericFilterableFileExplorer(pattern="*.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```
    B. Find T1w files ('.nii.gz' or '.nii') in the `anat` directory of a BIDS-style dataset:
    ```
    >>> explorer = GenericFilterableFileExplorer(pattern="/sub-*/**/anat/*T1w.nii*",)
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```
    C. Same as B, but skip files without a segmentation mask:
    ```
    >>> explorer = GenericFilterableFileExplorer(
    ...     pattern="/sub-*/**/anat/*T1w.nii*",
    ...     filters=[IncludeIfFileExists(filename_pattern="*seg*")],
    ...     logic="AND",
    ... )
    ```
    D. Get materialized results:
    ```
    >>> all_paths = explorer.list("/path/to/dataset")
    >>> any_path = explorer.first("/path/to/dataset")
    >>> n_paths = explorer.count("/path/to/dataset")
    >>> batched_paths = explorer.batched("/path/to/dataset", size=100)
    ```
    """
    def __init__(self, *, pattern: str | Sequence[str] = "*", **filter_kw):
        super().__init__(**filter_kw)
        self._patterns = ensure_seq(pattern)

    def scan(self, root_dir: Path | str, /) -> Iterator[Path]:
        root = resolve_path(root_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a valid directory")

        for pattern in self._patterns:
            for path in root.rglob(pattern):
                if path.is_file():
                    if self.apply_filters(path):
                        yield path



class NiftiExplorer(GenericFilterableFileExplorer):
    """
    Out-of-the-box file explorer defaulted to find all nifti files in a directory.

    Assumes a patient-level structure with separate subject and file patterns, as well
    as optional patient-level progress tracking.

    Example use-cases:
    ```
    >>> explorer = NiftiExplorer()
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```
    """
    def __init__(
        self,
        *,
        sub_pattern: str = "*",
        file_pattern: str | Sequence[str] = "*.nii*",
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND,
    ):
        super().__init__(
            filters=filters,
            logic=logic,
            pattern=file_pattern,
        )
        self._sub_pattern = sub_pattern

    def scan(
        self,
        root_dir: Path | str,
        /,
        progress: bool = False,
    ) -> Iterator[Path]:
        """Scan dataset with subject-level directories and file patterns."""
        root = resolve_path(root_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a valid directory")

        subjects = [p for p in root.glob(self._sub_pattern) if p.is_dir()]

        if progress:
            try:
                from tqdm.auto import tqdm
                it = tqdm(subjects, desc="Subjects", total=len(subjects))
            except ImportError:
                it = subjects
        else:
            it = subjects

        for subj in it:
            for file_pat in self._patterns:
                for path in subj.rglob(file_pat):
                    if path.is_file() and self.apply_filters(path):
                        yield path