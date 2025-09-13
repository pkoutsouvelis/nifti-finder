"""Implementations of file explorer filters"""

from __future__ import annotations

__all__ = [
    "IncludeExtension",
    "IncludeFileSuffix",
    "IncludeFilePrefix",
    "IncludeFileRegex",
    "IncludeDirectorySuffix",
    "IncludeDirectoryPrefix",
    "IncludeDirectoryRegex",
    "IncludeIfFileExists",
    "ExcludeExtension",
    "ExcludeFileSuffix",
    "ExcludeFilePrefix",
    "ExcludeFileRegex",
    "ExcludeDirectorySuffix",
    "ExcludeDirectoryPrefix",
    "ExcludeDirectoryRegex",
    "ExcludeIfFileExists",
]

from pathlib import Path
from dataclasses import dataclass
import re

from nifti_finder.filters.base import Filter
from nifti_finder.utils import get_ext, resolve_path


@dataclass(frozen=True, slots=True)
class IncludeExtension(Filter):
    """
    Include files with a specific extension.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeExtension("nii.gz")
    >>> filter("path/to/file.nii.gz")
    True
    ```

    Args:
        extension (str): Target file extension.
    """
    extension: str
    
    def __post_init__(self):
        if not self.extension.startswith("."):
            object.__setattr__(self, "extension", f".{self.extension}")

    def __call__(self, filepath: Path | str, /) -> bool:
        return get_ext(filepath) == self.extension


@dataclass(frozen=True, slots=True)
class IncludeFileSuffix(Filter):
    """
    Include files with a specific suffix.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeFileSuffix("preprocessed")
    >>> filter("path/to/file_preprocessed.nii.gz")
    True
    ```

    Args:
        suffix (str): Target file suffix.
    """
    suffix: str

    def __call__(self, filepath: Path | str, /) -> bool:
        name_only = Path(filepath).name.removesuffix(get_ext(filepath))
        return name_only.endswith(self.suffix)


@dataclass(frozen=True, slots=True)
class IncludeFilePrefix(Filter):
    """
    Include files with a specific prefix.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeFilePrefix("bad")
    >>> filter("path/to/bad_file.nii.gz")
    True
    ```

    Args:
        prefix (str): Target file prefix.
    """
    prefix: str

    def __call__(self, filepath: Path | str, /) -> bool:
        return Path(filepath).name.startswith(self.prefix)


@dataclass(frozen=True, slots=True)
class IncludeFileRegex(Filter):
    """Include files with a specific regex.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeFileRegex(".*seg.*")
    >>> filter("path/to/file_seg_mask.nii.gz")
    True
    ```

    Args:
        regex (str): Target file regex.
    """
    regex: str

    def __call__(self, filepath: Path | str, /) -> bool:
        return re.match(self.regex, Path(filepath).name) is not None


@dataclass(frozen=True, slots=True)
class IncludeDirectorySuffix(Filter):
    """
    Include directories with a specific suffix.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeDirectorySuffix("derivatives")
    >>> filter("path/to/derivatives/sub-1/ses-1/file.nii.gz")
    True
    ```

    Args:
        suffix (str): Target directory suffix.
    """
    suffix: str

    def __call__(self, filepath: Path | str, /) -> bool:
        dirs = list(Path(filepath).parents)
        if len(dirs) == 0:
            return False
        return any(d.name.endswith(self.suffix) for d in dirs)


@dataclass(frozen=True, slots=True)
class IncludeDirectoryPrefix(Filter):
    """
    Include directories with a specific prefix.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeDirectoryPrefix("bad")
    >>> filter("path/to/sub-1/ses-1/bad_dir/file.nii.gz")
    True
    ```

    Args:
        prefix (str): Target directory prefix.
    """
    prefix: str

    def __call__(self, filepath: Path | str, /) -> bool:
        dirs = list(Path(filepath).parents)
        if len(dirs) == 0:
            return False
        return any(d.name.startswith(self.prefix) for d in dirs)


@dataclass(frozen=True, slots=True)
class IncludeDirectoryRegex(Filter):
    """Include directories with a specific regex.

    Example use-case to include all nifti files:
    ```python
    >>> filter = IncludeDirectoryRegex(".*seg.*")
    >>> filter("path/to/sub-1/ses-1/seg_dir/file.nii.gz")
    True
    ```

    Args:
        regex (str): Target directory regex.
    """
    regex: str

    def __call__(self, filepath: Path | str, /) -> bool:
        dirs = list(Path(filepath).parents)
        if len(dirs) == 0:
            return False
        return any(re.match(self.regex, str(d)) is not None for d in dirs)


@dataclass(frozen=True, slots=True)
class IncludeIfFileExists(Filter):
    """
    Include files if a glob-matching file exists in a related directory.

    Can support multiple use-cases:
    - Screening in a fixed absolute directory
    - Screening in the same directory (see Example A)
    - Screening in a relative directory (see Example B)
    - Screening in a different directory that mirrors the source directory (see Example C)

    Examples:
    --------
    A) Include a file that contains a brain mask in the same directory:
    ```python
    >>> IncludeIfFileExists(filename_pattern="*mask*")
    >>> filter("/data/sub-1/ses-1/t1.nii.gz")
    True
    ```

    B) Include file only if it contains a segmentation mask in a relative directory; 
       e.g., assume an input file '/data/sub-1/ses-1/t1.nii.gz' with segmentation mask 
             in 'data/sub-1/ses-1/labels/seg.nii.gz':
    ```python
    >>> filter = IncludeIfFileExists(filename_pattern="labels/*seg*", search_in="--")
    >>> filter("/data/sub-1/ses-1/t1.nii.gz")
    True
    ```

    C) Include file only if it contains a segmentation mask in a different directory; 
       e.g., assume an input file '/data/sub-1/ses-1/t1.nii.gz' with segmentation mask 
             in '/labels/sub-1/ses-1/seg.nii.gz':
    ```python
    >>> filter = IncludeIfFileExists(filename_pattern="*seg*", search_in="/labels", mirror_relative_to="/data")
    >>> filter("/data/sub-1/ses-1/t1.nii.gz")
    True
    ```

    Args:
        filename_pattern (str):
            Glob applied to filenames in the target dir (e.g., '*seg*', '*.json').
            Special: '--' = use the current file's name.

        search_in (str):
            Target directory to search in.
            Special (default): '--' = use same directory as the file

        mirror_relative_to (str):
            Replace this root with `search_in` (e.g., '/data') and mirror the directory structure.

            Note: Default `FileExplorer` implementations assume no fixed source root. Use this mode only
                when sure that the source root will always contain the `mirror_relative_to` directory.
                Otherwise the filter will keep silently failing and returning False.
    
    """
    filename_pattern: str
    search_in: str = "--"
    mirror_relative_to: Path | str | None = None

    def __call__(self, filepath: Path | str, /) -> bool:
        filepath = resolve_path(filepath)
        if self.search_in == "--":
            target_dir = filepath.parent
        elif self.mirror_relative_to is not None:
            mirror_root = resolve_path(self.search_in)
            src_root = resolve_path(self.mirror_relative_to)
            try:
                rel = filepath.parent.relative_to(src_root)
            except ValueError:
                return False
            target_dir = (mirror_root / rel)
        else:
            p = Path(self.search_in)
            target_dir = resolve_path(p) if p.is_absolute() else filepath.parent / p

        pattern = filepath.name if self.filename_pattern == "--" else self.filename_pattern

        try:
            return any(p.is_file() for p in target_dir.glob(pattern))
        except FileNotFoundError:
            return False


@dataclass(frozen=True, init=False)
class ExcludeExtension(IncludeExtension):
    """
    Exclude files with a specific extension

    Opposite of `IncludeExtension`. See `IncludeExtension` for examples.
    
    Args:
        extension (str): Target file extension.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeFileSuffix(IncludeFileSuffix):
    """
    Exclude files with a specific suffix

    Opposite of `IncludeFileSuffix`. See `IncludeFileSuffix` for examples.

    Args:
        suffix (str): Target file suffix.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeFilePrefix(IncludeFilePrefix):
    """
    Exclude files with a specific prefix

    Opposite of `IncludeFilePrefix`. See `IncludeFilePrefix` for examples.

    Args:
        prefix (str): Target file prefix.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeFileRegex(IncludeFileRegex):
    """
    Exclude files with a specific regex

    Opposite of `IncludeFileRegex`. See `IncludeFileRegex` for examples.

    Args:
        regex (str): Target file regex.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeDirectorySuffix(IncludeDirectorySuffix):
    """
    Exclude directories with a specific suffix

    Opposite of `IncludeDirectorySuffix`. See `IncludeDirectorySuffix` for examples.

    Args:
        suffix (str): Target directory suffix.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeDirectoryPrefix(IncludeDirectoryPrefix):
    """
    Exclude directories with a specific prefix

    Opposite of `IncludeDirectoryPrefix`. See `IncludeDirectoryPrefix` for examples.

    Args:
        prefix (str): Target directory prefix.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeDirectoryRegex(IncludeDirectoryRegex):
    """
    Exclude directories with a specific regex

    Opposite of `IncludeDirectoryRegex`. See `IncludeDirectoryRegex` for examples.

    Args:
        regex (str): Target directory regex.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeIfFileExists(IncludeIfFileExists):
    """
    Exclude files if they are in the same directory as a specific file

    Opposite of `IncludeIfFileExists`. See `IncludeIfFileExists` for examples.

    Args:
        filename_pattern (str): Target file pattern.
    """
    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)