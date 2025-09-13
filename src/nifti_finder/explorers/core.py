"""Concrete implementation of file explorers"""

from __future__ import annotations

__all__ = [
    "BasicFileExplorer",
    "TwoStageFileExplorer",
    "AllPurposeFileExplorer",
    "NiftiExplorer",
]

from pathlib import Path
from typing import Iterator
from collections.abc import Sequence

from nifti_finder.explorers.base import FileExplorer
from nifti_finder.explorers.mixins import MaterializeMixin
from nifti_finder.filters import Filter, Logic, FilterableMixin
from nifti_finder.utils import resolve_path, ensure_seq


class BasicFileExplorer(FileExplorer):
    """
    Basic file explorer implementation with support for pattern-based file discovery.

    Examples:
    --------
    A) Find all nifti files ('.nii.gz' or '.nii') in any dataset, regardless the structure:
       - Specify `pattern` to match nifti files

    ```python
    >>> explorer = BasicFileExplorer(pattern="*.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    B) Find all raw T1w MR images ('.nii.gz' or '.nii') in the `anat` directory of a BIDS-style dataset:
       - Specify `pattern` to match BIDS-style T1w MR images

    ```python
    >>> explorer = BasicFileExplorer(pattern="sub-*/**/anat/*T1w.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```
    """
    def __init__(self, *, pattern: str | Sequence[str] = "*"):
        """
        Args:
            pattern (str | Sequence[str]): Filename pattern to match. Defaults to '*'; i.e., 'any'.
        """
        self._patterns = ensure_seq(pattern)

    def scan(self, root_dir: Path | str, /) -> Iterator[Path]:
        """
        Scan the directory for files matching the pattern.

        Args:
            root_dir (Path | str): The root directory to scan.
        """
        root = resolve_path(root_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a valid directory")

        for pattern in self._patterns:
            for path in root.rglob(pattern):
                if path.is_file():
                    yield path


class TwoStageFileExplorer(FileExplorer):
    """
    Concrete file explorer with support for two-stage file discovery to track progress.

    Useful for progress tracking in subject-level dataset hierarchies (e.g., BIDS) or
    root with multiple datasets.

    Examples:
    --------
    A) BIDS dataset exploration with progress tracking:
       - Specify `stage_1_pattern` to match subject-level directories
       - Specify `stage_2_pattern` to match BIDS-style T1w MR images
       - Set `progress` and `desc` to track progress

    ```python
    >>> explorer = TwoStageFileExplorer(stage_1_pattern="sub-*", stage_2_pattern="**/anat/*.nii*")
    >>> for path in explorer.scan("/path/to/dataset", progress=True, desc="Subjects"):
    ...     preprocess(path)
    >>> Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
    ```
    
    B) Explore multiple datasets with progress tracking:
       - Specify `stage_1_pattern` to match dataset-level directories; e.g., `OpenNeuro-ds001`
       - Specify `stage_2_pattern` to match BIDS-style T1w MR images
       - Set `progress` and `desc` to track progress

    ```python
    >>> explorer = TwoStageFileExplorer(stage_1_pattern="OpenNeuro-ds*", stage_2_pattern="sub-*/**/anat/*.nii*")
    >>> for path in explorer.scan("/path/to/datasets", progress=True, desc="Datasets"):
    ...     preprocess(path)
    >>> Datasets:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
    ```
    """
    def __init__(
        self,
        *,
        stage_1_pattern: str | Sequence[str] = "*",
        stage_2_pattern: str | Sequence[str] = "*",
    ):
        """
        Args:
            stage_1_pattern (str | Sequence[str]): Pattern to match stage 1 directories. 
                Defaults to '*'; i.e., 'any'.
            stage_2_pattern (str | Sequence[str]): Pattern to match stage 2 files. 
                Defaults to '*'; i.e., 'any'.
        """
        self._stage_1_patterns = ensure_seq(stage_1_pattern)
        self._stage_2_patterns = ensure_seq(stage_2_pattern)

    def scan(
        self,
        root_dir: Path | str,
        /,
        *,
        progress: bool = False,
        **tqdm_kw,
    ) -> Iterator[Path]:
        """
        Scan dataset with two-stage file discovery to track progress.

        Args:
            root_dir (Path | str): The root directory to scan.
            progress (bool): Whether to track progress. Defaults to False.
            **tqdm_kw: Additional keyword arguments to pass to `tqdm`. Most common
                are `total`, and `desc`.
        """
        root = resolve_path(root_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a valid directory")

        stage_1_dirs = [p for ptrn in self._stage_1_patterns for p in root.glob(ptrn) if p.is_dir()]

        if progress:
            try:
                from tqdm.auto import tqdm
                it = tqdm(stage_1_dirs, total=len(stage_1_dirs), **tqdm_kw)
            except ImportError:
                it = stage_1_dirs
        else:
            it = stage_1_dirs

        for subj in it:
            for ptrn in self._stage_2_patterns:
                for path in subj.rglob(ptrn):
                    if path.is_file():
                        yield path


class AllPurposeFileExplorer(BasicFileExplorer, FilterableMixin, MaterializeMixin):
    """
    All-purpose file explorer with basic pattern-based file discovery, filtering support, 
    and convenience methods for materializing the results.

    Finds all files in a directory and applies a cached composed filter to each filepath.
    
    Note:
        For faster exploration, prioritize `patterns` for filtering by name; apply subsequent filters
        only to the narrowed down results. Supports multiple `patterns`, but will traverse the
        directory once per pattern, which can be slow on large datasets. 
        The best performance is expected with a single pattern + filters.
    
    Examples:
    --------
    A) Find all nifti files ('.nii.gz' or '.nii') in any dataset, regardless the structure:
       - Specify `pattern` to match nifti files

    ```python
    >>> explorer = AllPurposeFileExplorer(pattern="*.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```

    B) Find T1w MR images ('.nii.gz' or '.nii') in the `anat` directory of a BIDS-style dataset:
       - Specify `pattern` to match BIDS-style T1w MR images

    ```python
    >>> explorer = AllPurposeFileExplorer(pattern="/sub-*/**/anat/*T1w.nii*",)
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     print(path)
    ```

    C) Same as B, but skip files without a segmentation mask:
       - Specify `pattern` to match BIDS-style T1w MR images
       - Specify `filters` to exclude files without a segmentation mask

    ```python
    >>> explorer = AllPurposeFileExplorer(
    ...     pattern="/sub-*/**/anat/*T1w.nii*",
    ...     filters=[IncludeIfFileExists(filename_pattern="*seg*")],
    ...     logic="AND",
    ... )
    ```

    D) Get materialized results:

    ```python
    >>> all_paths = explorer.list("/path/to/dataset")
    >>> any_path = explorer.first("/path/to/dataset")
    >>> n_paths = explorer.count("/path/to/dataset")
    >>> batched_paths = explorer.batched("/path/to/dataset", size=100)
    ```
    """
    def __init__(
        self, 
        *, 
        pattern: str | Sequence[str] = "*", 
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND,
    ):
        """
        Args:
            pattern (str | Sequence[str]): Filename pattern to match. Defaults to '*'; i.e., 'any'.
            filters (Filter | Sequence[Filter], optional): Filters to apply. Defaults to None.
            logic (Logic | str): Logic to apply to the filters. Defaults to 'AND'.
        """
        super().__init__(pattern=pattern)
        FilterableMixin.__init__(self, filters=filters, logic=logic)

    def scan(self, root_dir: Path | str, /) -> Iterator[Path]:
        """
        Scan the directory for files matching the pattern and applying the filters.

        Args:
            root_dir (Path | str): The root directory to scan.
        """
        for path in super().scan(root_dir):
            if self.apply_filters(path):
                yield path


class NiftiExplorer(TwoStageFileExplorer, FilterableMixin, MaterializeMixin):
    """
    Out-of-the-box file explorer defaulted to find all nifti files in a directory.

    Assumes a two-stage structure with separate stage 1 and stage 2 patterns, as well
    as optional progress tracking. Supports filtering and convenience methods for 
    materializing the results.

    Note:
        For faster exploration, prioritize `patterns` for filtering by name; apply subsequent filters
        only to the narrowed down results. Suppports multiple `patterns`, but will traverse the
        directory once per pattern, which can be slow on large datasets. 
        The best performance is expected with a single pattern + filters.

    Examples:
    --------
    A) Find all nifti files ('.nii.gz' or '.nii') in any dataset, regardless the structure:
       - Default behavior; no need to specify anything

    ```python
    >>> explorer = NiftiExplorer()
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    B) Find all T1w MR images ('.nii.gz' or '.nii') in a BIDS-style dataset that are 
       not yet preprocessed:
       - Set `stage_1_pattern` to match subject-level directories
       - Set `stage_2_pattern` to match BIDS-style T1w MR images
       - Set `filters` to exclude `T1w_preprocessed.nii.*` files
       - Set `progress` and `desc` to track progress

    ```python
    >>> explorer = NiftiExplorer(stage_1_pattern="sub-*", stage_2_pattern="**/anat/*T1w.nii*", 
    ...                          filters=[ExcludeFileSuffix(suffix="preprocessed")])
    >>> for path in explorer.scan("/path/to/dataset", progress=True, desc="Subjects"):
    ...     preprocess(path)
    >>> Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
    ```

    C) Same as B, but skip files without a segmentation mask in a dedicated labels directory:

    ```python
    >>> explorer = NiftiExplorer(stage_1_pattern="sub-*", stage_2_pattern="**/anat/*T1w.nii*", 
    ...                          filters=[IncludeIfFileExists(filename_pattern="*seg*", search_in="/labels", 
    ...                                                       mirror_relative_to="/path/to/dataset")])
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    D) Get materialized results:

    ```python
    >>> all_paths = explorer.list("/path/to/dataset")
    >>> any_path = explorer.first("/path/to/dataset")
    >>> n_paths = explorer.count("/path/to/dataset")
    >>> batched_paths = explorer.batched("/path/to/dataset", size=100)
    ```
    """
    def __init__(
        self,
        *,
        stage_1_pattern: str = "*",
        stage_2_pattern: str = "*.nii*",
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND,
    ):
        """
        Args:
            stage_1_pattern (str): Pattern to match stage 1 directories. Defaults to '*'; 
                i.e., all directories.
            stage_2_pattern (str): Pattern to match stage 2 files. Defaults to '*.nii*'; 
                i.e., all nifti files.
            filters (Filter | Sequence[Filter], optional): Filters to apply. Defaults to None.
            logic (Logic | str): Logic to apply to the filters. Defaults to 'AND'.
        """
        super().__init__(
            stage_1_pattern=stage_1_pattern,
            stage_2_pattern=stage_2_pattern,
        )
        FilterableMixin.__init__(self, filters=filters, logic=logic)

    def scan(
        self, 
        root_dir: Path | str,
        /,
        *,
        progress: bool = False,
        **tqdm_kw,
    ) -> Iterator[Path]:
        """
        Scan dataset with two-stage file discovery to track progress.

        Args:
            root_dir (Path | str): The root directory to scan.
            progress (bool): Whether to track progress. Defaults to False.
            **tqdm_kw: Additional keyword arguments to pass to `tqdm`. Most common
                are `total`, and `desc`.
        """
        for path in super().scan(root_dir, progress=progress, **tqdm_kw):
            if self.apply_filters(path):
                yield path