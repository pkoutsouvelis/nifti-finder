"""Concrete implementation of file explorers."""

from __future__ import annotations

__all__ = [
    "RecursiveFileExplorer",
    "NestedFileExplorer",
    "FileFinder",
    "BasicFileExplorer",
    "TwoStageFileExplorer",
    "AllPurposeFileExplorer",
    "NeuroExplorer",
]

import warnings
from pathlib import Path
from typing import Iterator
from collections.abc import Sequence

from nifti_finder.explorers.base import FileExplorer
from nifti_finder.explorers.mixins import MaterializeMixin
from nifti_finder.filters import Filter, Logic, FilterableMixin
from nifti_finder.utils import (
    resolve_path,
    ensure_seq,
    deprecated_class,
    deprecated_alias,
)


class RecursiveFileExplorer(FileExplorer):
    """
    Recursive file explorer with pattern-based file discovery.

    Performs a recursive glob from the root directory and yields matching files.
    Use :class:`NestedFileExplorer` when directory-level traversal and progress
    tracking are needed.

    Examples:
    --------
    A) Find all nifti files ('.nii.gz' or '.nii') in any dataset, regardless the structure:
       - Specify `patterns` to match nifti files

    ```python
    >>> explorer = RecursiveFileExplorer(patterns="*.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    B) Find all raw T1w MR images ('.nii.gz' or '.nii') in the `anat` directory of a BIDS-style dataset:
       - Specify `patterns` to match BIDS-style T1w MR images

    ```python
    >>> explorer = RecursiveFileExplorer(patterns="sub-*/**/anat/*T1w.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```
    """

    @deprecated_alias(old="pattern", new="patterns", since="2.0.0", remove_in="2.2.0")
    def __init__(self, patterns: str | Sequence[str] = "*.nii*"):
        """
        Args:
            patterns (str | Sequence[str]): Filename patterns to match.
                Defaults to ``'*.nii*'``.
        """
        self._patterns = ensure_seq(patterns)

    def scan(self, root_dir: Path | str, /) -> Iterator[Path]:
        """Scan the directory for files matching the patterns.

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


class NestedFileExplorer(FileExplorer):
    """
    Nested file explorer with support for multi-level directory traversal and progress tracking.

    Each key in ``levels`` names a traversal stage whose value is a glob pattern matching
    **directories** at that depth. After all levels are resolved, ``patterns`` is applied
    recursively within each leaf directory via :class:`RecursiveFileExplorer`.

    When ``levels`` is ``None``, only ``patterns`` is used for a flat recursive
    scan (no progress bar). Pass ``levels`` when you want hierarchical traversal
    and optional progress tracking over the first level.

    Examples:
    --------
    A) BIDS dataset exploration with progress tracking:

    ```python
    >>> explorer = NestedFileExplorer(
    ...     levels={"subjects": "sub-*"},
    ...     patterns="**/anat/*T1w.nii*",
    ... )
    >>> for path in explorer.scan("/path/to/dataset", progress=True, desc="Subjects"):
    ...     preprocess(path)
    >>> Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
    ```

    B) Explore multiple datasets with nested directory levels:

    ```python
    >>> explorer = NestedFileExplorer(
    ...     levels={
    ...         "datasets": "OpenNeuro-ds*",
    ...         "subjects": "sub-*",
    ...     },
    ...     patterns=["*_T1w.nii*", "*_FLAIR.nii*"],
    ... )
    >>> for path in explorer.scan("/path/to/datasets", progress=True, desc="Datasets"):
    ...     preprocess(path)
    ```

    C) Flat recursive scan without nested levels (no progress bar):

    ```python
    >>> explorer = NestedFileExplorer(patterns="*.nii*")
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    D) Track progress automatically only when a top level exists:
       - Default ``progress="auto"`` shows a bar when ``levels`` is set, and
         silently does nothing otherwise.

    ```python
    >>> explorer = NestedFileExplorer(levels={"subjects": "sub-*"})
    >>> for path in explorer.scan("/path/to/dataset"):  # progress="auto"
    ...     preprocess(path)
    ```
    """

    @deprecated_alias(old="pattern", new="patterns", since="2.0.0", remove_in="2.2.0")
    def __init__(
        self,
        *,
        levels: dict[str, str | Sequence[str]] | None = None,
        patterns: str | Sequence[str] = "*.nii*",
    ):
        """
        Args:
            levels (dict[str, str | Sequence[str]] | None): Named directory traversal
                levels. Each value is a glob pattern matching directories at that
                stage. When ``None``, only ``patterns`` is used for a flat recursive
                scan.
            patterns (str | Sequence[str]): File patterns searched recursively within
                each directory reached by ``levels``. Also used alone for a flat
                recursive scan when ``levels`` is ``None``. Defaults to ``'*.nii*'``.
        """
        self._levels = levels
        self._recursive = RecursiveFileExplorer(patterns=patterns)
        if levels is not None:
            if not levels:
                raise ValueError(
                    "levels must not be empty; omit levels for flat recursive search."
                )
            self._dir_levels = levels
        else:
            self._dir_levels = {}

    def scan(
        self,
        root_dir: Path | str,
        /,
        *,
        progress: bool | str = "auto",
        **tqdm_kw,
    ) -> Iterator[Path]:
        """Scan a dataset with optional nested directory traversal.

        Args:
            root_dir (Path | str): The root directory to scan.
            progress (bool | str): Whether to track progress over the first
                directory level. ``"auto"`` (default) tracks progress at the top
                level if it exists, and silently does nothing when ``levels`` is
                ``None``. ``True`` forces a progress bar (and warns if ``levels``
                is ``None``); ``False`` disables it.
            **tqdm_kw: Additional keyword arguments to pass to ``tqdm``. Most
                common are ``total`` and ``desc``.
        """
        root = resolve_path(root_dir)
        if not root.is_dir():
            raise NotADirectoryError(f"{root} is not a valid directory")

        auto_progress = progress == "auto"
        if isinstance(progress, str) and not auto_progress:
            raise ValueError(
                f"Invalid progress value {progress!r}; expected a bool or 'auto'."
            )

        if self._levels is None:
            if progress is True:
                warnings.warn(
                    "progress is ignored when levels is None; provide levels "
                    "with at least one directory stage to enable progress tracking.",
                    UserWarning,
                    stacklevel=2,
                )
            yield from self._recursive.scan(root)
            return

        first_name, first_patterns = next(iter(self._dir_levels.items()))
        remaining_dir_levels = list(self._dir_levels.items())[1:]

        first_level_dirs = [
            p
            for ptrn in ensure_seq(first_patterns)
            for p in root.glob(ptrn)
            if p.is_dir()
        ]

        show_progress = progress is True or auto_progress
        if show_progress:
            try:
                from tqdm.auto import tqdm

                first_level_it = tqdm(
                    first_level_dirs,
                    total=len(first_level_dirs),
                    desc=tqdm_kw.pop("desc", first_name),
                    **tqdm_kw,
                )
            except ImportError:
                first_level_it = first_level_dirs
        else:
            first_level_it = first_level_dirs

        for first_dir in first_level_it:
            current_dirs = [first_dir]
            for _, dir_patterns in remaining_dir_levels:
                next_dirs: list[Path] = []
                for current in current_dirs:
                    for ptrn in ensure_seq(dir_patterns):
                        for path in current.glob(ptrn):
                            if path.is_dir():
                                next_dirs.append(path)
                current_dirs = next_dirs

            for directory in current_dirs:
                yield from self._recursive.scan(directory)


@deprecated_class("RecursiveFileExplorer", remove_in="2.2.0")
class BasicFileExplorer(RecursiveFileExplorer):
    """
    .. deprecated:: 2.0.0
        Use :class:`RecursiveFileExplorer` instead.
    """

    @deprecated_alias(old="pattern", new="patterns", since="2.0.0", remove_in="2.2.0")
    def __init__(self, patterns: str | Sequence[str] = "*"):
        super().__init__(patterns=patterns)


@deprecated_class("NestedFileExplorer", remove_in="2.2.0")
class TwoStageFileExplorer(NestedFileExplorer):
    """
    .. deprecated:: 2.0.0
        Use :class:`NestedFileExplorer` instead.
    """

    def __init__(
        self,
        stage_1_pattern: str | Sequence[str] = "*",
        stage_2_pattern: str | Sequence[str] = "*",
    ):
        super().__init__(
            levels={"stage_1": stage_1_pattern},
            patterns=stage_2_pattern,
        )


class FileFinder(NestedFileExplorer, FilterableMixin, MaterializeMixin):
    """
    General-purpose file finder with neuroimaging-friendly defaults.

    Combines nested directory traversal, optional progress tracking, composable
    filters, and convenience methods for materializing results. Developed with
    neuroimaging workflows in mind (e.g. BIDS-style datasets), but works for
    any file type via ``patterns`` and ``levels``.

    Note:
        For faster exploration, prioritize ``levels`` for filtering by name;
        apply subsequent filters only to the narrowed down results. Supports
        multiple patterns per level, but will traverse the directory once per
        pattern, which can be slow on large datasets. The best performance is
        expected with a single pattern per level plus filters.

    Examples:
    --------
    A) Find all nifti files ('.nii.gz' or '.nii') in any dataset, regardless the structure:
       - Default behavior; no need to specify anything

    ```python
    >>> finder = FileFinder()
    >>> for path in finder.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    B) Find all T1w MR images ('.nii.gz' or '.nii') in a BIDS-style dataset that are
       not yet preprocessed:
       - Set ``levels`` to match subject-level directories and T1w files
       - Set ``filters`` to exclude ``T1w_preprocessed.nii.*`` files
       - Set ``progress`` and ``desc`` to track progress

    ```python
    >>> finder = FileFinder(
    ...     levels={"subjects": "sub-*"},
    ...     patterns="**/anat/*T1w.nii*",
    ...     filters=[ExcludeFileSuffix(suffix="preprocessed")],
    ... )
    >>> for path in finder.scan("/path/to/dataset", progress=True, desc="Subjects"):
    ...     preprocess(path)
    >>> Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
    ```

    C) Same as B, but skip files without a segmentation mask in a dedicated labels directory:

    ```python
    >>> finder = FileFinder(
    ...     levels={"subjects": "sub-*"},
    ...     patterns="**/anat/*T1w.nii*",
    ...     filters=[IncludeIfFileExists(filename_pattern="*seg*", search_in="/labels",
    ...                                  mirror_relative_to="/path/to/dataset")],
    ... )
    >>> for path in finder.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    D) Get materialized results:

    ```python
    >>> all_paths = finder.list("/path/to/dataset")
    >>> any_path = finder.first("/path/to/dataset")
    >>> n_paths = finder.count("/path/to/dataset")
    >>> batched_paths = finder.batched("/path/to/dataset", size=100)
    ```
    """

    @deprecated_alias(old="pattern", new="patterns", since="2.0.0", remove_in="2.2.0")
    def __init__(
        self,
        *,
        levels: dict[str, str | Sequence[str]] | None = None,
        patterns: str | Sequence[str] = "*.nii*",
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND,
    ):
        """
        Args:
            levels (dict[str, str | Sequence[str]] | None): Named directory traversal
                levels. Each value is a glob pattern matching directories at that
                stage. When ``None``, only ``patterns`` is used for a flat recursive
                scan.
            patterns (str | Sequence[str]): File patterns searched recursively within
                each directory reached by ``levels``. Also used alone for a flat
                recursive scan when ``levels`` is ``None``. Defaults to ``'*.nii*'``.
            filters (Filter | Sequence[Filter], optional): Filters to refine the
                discovered paths. Defaults to None.
            logic (Logic | str): Logical operator to combine multiple filters.
                Defaults to ``'AND'``.
        """
        super().__init__(levels=levels, patterns=patterns)
        FilterableMixin.__init__(self, filters=filters, logic=logic)

    def scan(
        self,
        root_dir: Path | str,
        /,
        *,
        progress: bool | str = "auto",
        **tqdm_kw,
    ) -> Iterator[Path]:
        """Scan a directory tree and yield paths matching the configured patterns.

        Args:
            root_dir (Path | str): The root directory to scan.
            progress (bool | str): Whether to track progress over the first
                directory level. ``"auto"`` (default) tracks progress at the top
                level if it exists, and silently does nothing when ``levels`` is
                ``None``. ``True`` forces a progress bar (and warns if ``levels``
                is ``None``); ``False`` disables it.
            **tqdm_kw: Additional keyword arguments to pass to ``tqdm``. Most
                common are ``total`` and ``desc``.
        """
        for path in super().scan(root_dir, progress=progress, **tqdm_kw):
            if self.apply_filters(path):
                yield path


@deprecated_class("FileFinder", remove_in="2.2.0")
class AllPurposeFileExplorer(FileFinder):
    """
    .. deprecated:: 2.0.0
        Use :class:`FileFinder` instead.

    Legacy flat file explorer with ``patterns`` and filters, retained for
    backward compatibility.
    """

    @deprecated_alias(old="pattern", new="patterns", since="2.0.0", remove_in="2.2.0")
    def __init__(
        self,
        patterns: str | Sequence[str] = "*",
        *,
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND,
    ):
        """
        Args:
            patterns (str | Sequence[str]): Filename patterns to match.
                Defaults to ``'*'``.
            filters (Filter | Sequence[Filter], optional): Filters to refine the
                discovered paths. Defaults to None.
            logic (Logic | str): Logical operator to combine multiple filters.
                Defaults to ``'AND'``.
        """
        super().__init__(patterns=patterns, filters=filters, logic=logic)


@deprecated_class("FileFinder", remove_in="2.2.0")
class NeuroExplorer(FileFinder):
    """
    .. deprecated:: 2.0.0
        Use :class:`FileFinder` instead.

    Legacy two-stage file explorer with ``outer`` / ``inner`` patterns, retained
    for backward compatibility.

    Examples:
    --------
    A) Find all nifti files with the default two-stage scan:

    ```python
    >>> explorer = NeuroExplorer()
    >>> for path in explorer.scan("/path/to/dataset"):
    ...     preprocess(path)
    ```

    B) BIDS-style subject-level progress tracking:

    ```python
    >>> explorer = NeuroExplorer(outer="sub-*", inner="**/anat/*T1w.nii*")
    >>> for path in explorer.scan("/path/to/dataset", progress=True, desc="Subjects"):
    ...     preprocess(path)
    ```
    """

    def __init__(
        self,
        outer: str = "*",
        inner: str = "*.nii*",
        *,
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND,
    ):
        """
        Args:
            outer (str): Glob pattern for the first directory level. Also
                determines the units over which progress is tracked.
                Defaults to ``'*'``.
            inner (str): File patterns applied recursively within each outer
                match. Defaults to ``'*.nii*'``.
            filters (Filter | Sequence[Filter], optional): Filters to refine the
                discovered paths. Defaults to None.
            logic (Logic | str): Logical operator to combine multiple filters.
                Defaults to ``'AND'``.
        """
        super().__init__(
            levels={"outer": outer},
            patterns=inner,
            filters=filters,
            logic=logic,
        )
