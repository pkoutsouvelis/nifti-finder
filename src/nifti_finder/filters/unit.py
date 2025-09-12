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
    """Include files with a specific extension"""
    extension: str
    
    def __post_init__(self):
        if not self.extension.startswith("."):
            object.__setattr__(self, "extension", f".{self.extension}")

    def __call__(self, filepath: Path, /) -> bool:
        """Filter for files with a specific extension"""
        return get_ext(filepath) == self.extension


@dataclass(frozen=True, slots=True)
class IncludeFileSuffix(Filter):
    """Include files with a specific suffix"""
    suffix: str

    def __call__(self, filepath: Path, /) -> bool:
        name_only = filepath.name.removesuffix(get_ext(filepath))
        return name_only.endswith(self.suffix)


@dataclass(frozen=True, slots=True)
class IncludeFilePrefix(Filter):
    """Include files with a specific prefix"""
    prefix: str

    def __call__(self, filepath: Path, /) -> bool:
        return filepath.name.startswith(self.prefix)


@dataclass(frozen=True, slots=True)
class IncludeFileRegex(Filter):
    """Include files with a specific regex"""
    regex: str

    def __call__(self, filepath: Path, /) -> bool:
        return re.match(self.regex, filepath.name) is not None


@dataclass(frozen=True, slots=True)
class IncludeDirectorySuffix(Filter):
    """Include directories with a specific suffix"""
    suffix: str

    def __call__(self, filepath: Path, /) -> bool:
        dirs = list(filepath.parents)
        if len(dirs) == 0:
            return False
        return any(d.name.endswith(self.suffix) for d in dirs)


@dataclass(frozen=True, slots=True)
class IncludeDirectoryPrefix(Filter):
    """Include directories with a specific prefix"""
    prefix: str

    def __call__(self, filepath: Path, /) -> bool:
        dirs = list(filepath.parents)
        if len(dirs) == 0:
            return False
        return any(d.name.startswith(self.prefix) for d in dirs)


@dataclass(frozen=True, slots=True)
class IncludeDirectoryRegex(Filter):
    """Include directories with a specific regex"""
    regex: str

    def __call__(self, filepath: Path, /) -> bool:
        dirs = list(filepath.parents)
        if len(dirs) == 0:
            return False
        return any(re.match(self.regex, str(d)) is not None for d in dirs)


@dataclass(frozen=True, slots=True)
class IncludeIfFileExists(Filter):
    """
    Include files if a glob-matching file exists in a related directory.

    Example use-cases:
    A. Include a file that contains a brain mask in the same directory:
    ```
    >>> IncludeIfFileExists(filename_pattern="*mask*")
    >>> filter("/data/sub-1/ses-1/t1.nii.gz")
    True
    ```
    B. Include file only if it contains a segmentation mask in a different directory; 
       e.g., assume an input file '/data/sub-1/ses-1/t1.nii.gz' with segmentation mask 
             in '/labels/sub-1/ses-1/seg.nii.gz':
    ```
    >>> filter = IncludeIfFileExists(filename_pattern="*seg*", search_in="/labels--", mirror_relative_to="/data")
    >>> filter("/data/sub-1/ses-1/t1.nii.gz")
    True
    ```

    Args:
        filename_pattern:
            Glob applied to filenames in the target dir (e.g., '*seg*', '*.json').
            Special: '--' = use the current file's name.

        search_in (mini-DSL):
            '--'            → same directory as the file
            '--<relpath>'   → (file.parent / <relpath>)            e.g. '--../labels'
            '<abs path>'    → fixed absolute directory              e.g. '/tmp/labels'
            '<mirror_root>--' → mirror under <mirror_root>; requires mirror_relative_to

        mirror_relative_to:
            The source root to strip when mirroring (e.g., Path('/data')).

            Example: file '/data/sub-1/ses-1/t1.nii.gz' + search_in=' /labels-- '
                    → target '/labels/sub-1/ses-1'

            Note: Default `FileExplorer` implementations assume no fixed source root. Use this mode only
                when sure that the source root will always contain the `mirror_relative_to` directory.
                Otherwise the filter will keep silently failing and returning False.
    
    """
    filename_pattern: str
    search_in: str = "--"
    mirror_relative_to: Path | str | None = None

    def __call__(self, filepath: Path, /) -> bool:
        fp = filepath.resolve()
        si = self.search_in

        if si == "--":
            target_dir = fp.parent
        elif si.startswith("--"):
            target_dir = resolve_path(fp.parent / si.removeprefix("--"))
        elif si.endswith("--"):
            mirror_root = resolve_path(si.removesuffix("--"))
            src_root = resolve_path(self.mirror_relative_to or Path("/"))
            try:
                rel = fp.parent.relative_to(src_root)
            except ValueError:
                return False
            target_dir = (mirror_root / rel)
        else:
            p = Path(si)
            target_dir = p if p.is_absolute() else resolve_path(fp.parent / p)

        pattern = fp.name if self.filename_pattern == "--" else self.filename_pattern

        try:
            return any(p.is_file() for p in target_dir.glob(pattern))
        except FileNotFoundError:
            return False


@dataclass(frozen=True, init=False)
class ExcludeExtension(IncludeExtension):
    """Exclude files with a specific extension"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeFileSuffix(IncludeFileSuffix):
    """Exclude files with a specific suffix"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeFilePrefix(IncludeFilePrefix):
    """Exclude files with a specific prefix"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeFileRegex(IncludeFileRegex):
    """Exclude files with a specific regex"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeDirectorySuffix(IncludeDirectorySuffix):
    """Exclude directories with a specific suffix"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeDirectoryPrefix(IncludeDirectoryPrefix):
    """Exclude directories with a specific prefix"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeDirectoryRegex(IncludeDirectoryRegex):
    """Exclude directories with a specific regex"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)


@dataclass(frozen=True, init=False)
class ExcludeIfFileExists(IncludeIfFileExists):
    """Exclude files if they are in the same directory as a specific file"""
    def __call__(self, filepath: Path, /) -> bool:
        return not super().__call__(filepath)