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
from nifti_finder.utils import get_ext


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
    """Include files if they are in the same directory as a specific file"""
    filename: str
    search_in: Path | None = None

    def __call__(self, filepath: Path, /) -> bool:
        if self.search_in is None:
            search_in = filepath.parent
        else:
            search_in = self.search_in
        return any(f.name == self.filename for f in search_in.iterdir())


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