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
import re

from nifti_finder.interfaces import Filter
from nifti_finder.utils import get_ext


class IncludeExtension(Filter):
    """Include files with a specific extension"""
    def __init__(self, extension: str):
        if not extension.startswith("."):
            extension = f".{extension}"
        self._extension = extension

    def filter(self, filepath: Path) -> bool:
        """Filter for files with a specific extension"""
        return get_ext(filepath) == self._extension


class IncludeFileSuffix(Filter):
    """Include files with a specific suffix"""
    def __init__(self, suffix: str):
        self._suffix = suffix

    def filter(self, filepath: Path) -> bool:
        name_only = filepath.name.removesuffix(get_ext(filepath))
        return name_only.endswith(self._suffix)


class IncludeFilePrefix(Filter):
    """Include files with a specific prefix"""
    def __init__(self, prefix: str):
        self._prefix = prefix

    def filter(self, filepath: Path) -> bool:
        return filepath.name.startswith(self._prefix)


class IncludeFileRegex(Filter):
    """Include files with a specific regex"""
    def __init__(self, regex: str):
        self._regex = regex

    def filter(self, filepath: Path) -> bool:
        return re.match(self._regex, filepath.name) is not None


class IncludeDirectorySuffix(Filter):
    """Include directories with a specific suffix"""
    def __init__(self, suffix: str):
        self._suffix = suffix

    def filter(self, filepath: Path) -> bool:
        dirs = list(filepath.parents)
        if len(dirs) == 0:
            return False
        return any(d.name.endswith(self._suffix) for d in dirs)


class IncludeDirectoryPrefix(Filter):
    """Include directories with a specific prefix"""
    def __init__(self, prefix: str):
        self._prefix = prefix

    def filter(self, filepath: Path) -> bool:
        dirs = list(filepath.parents)
        if len(dirs) == 0:
            return False
        return any(d.name.startswith(self._prefix) for d in dirs)


class IncludeDirectoryRegex(Filter):
    """Include directories with a specific regex"""
    def __init__(self, regex: str):
        self._regex = regex

    def filter(self, filepath: Path) -> bool:
        dirs = list(filepath.parents)
        if len(dirs) == 0:
            return False
        return any(re.match(self._regex, str(d)) is not None for d in dirs)


class IncludeIfFileExists(Filter):
    """Include files if they are in the same directory as a specific file"""
    def __init__(self, filename: str, search_in: Path | None = None):
        self._filename = filename
        self._search_in = search_in

    def filter(self, filepath: Path) -> bool:
        if self._search_in is None:
            search_in = filepath.parent
        else:
            search_in = self._search_in
        return any(f.name == self._filename for f in search_in.iterdir())


class ExcludeExtension(IncludeExtension):
    """Exclude files with a specific extension"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeFileSuffix(IncludeFileSuffix):
    """Exclude files with a specific suffix"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeFilePrefix(IncludeFilePrefix):
    """Exclude files with a specific prefix"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeFileRegex(IncludeFileRegex):
    """Exclude files with a specific regex"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeDirectorySuffix(IncludeDirectorySuffix):
    """Exclude directories with a specific suffix"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeDirectoryPrefix(IncludeDirectoryPrefix):
    """Exclude directories with a specific prefix"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeDirectoryRegex(IncludeDirectoryRegex):
    """Exclude directories with a specific regex"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)


class ExcludeIfFileExists(IncludeIfFileExists):
    """Exclude files if they are in the same directory as a specific file"""
    def filter(self, filepath: Path) -> bool:
        return not super().filter(filepath)