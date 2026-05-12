"""Filters for selecting a given filepath based on predefined membership criteria.

Includes:
- Base classes for filters:
    - `Filter`
- Mixin classes for filterable objects:
    - `FilterableMixin`
- Concrete filters:
    - `IncludeExtension`
    - `IncludeFileSuffix`
    - `IncludeFilePrefix`
    - `IncludeFileRegex`
    - `IncludeDirectorySuffix`
    - `IncludeDirectoryPrefix`
    - `IncludeDirectoryRegex`
    - `IncludeIfFileExists`
    - `IncludeFromTable`
    - `IncludeFromLogs`
    - `ExcludeExtension`
    - `ExcludeFileSuffix`
    - `ExcludeFilePrefix`
    - `ExcludeFileRegex`
    - `ExcludeDirectorySuffix`
    - `ExcludeDirectoryPrefix`
    - `ExcludeDirectoryRegex`
    - `ExcludeIfFileExists`
    - `ExcludeFromTable`
    - `ExcludeFromLogs`
"""

from __future__ import annotations

__all__ = [
    "FilterableMixin",
    "ComposeFilter",
    "IncludeExtension",
    "IncludeFileSuffix",
    "IncludeFilePrefix",
    "IncludeFileRegex",
    "IncludeDirectorySuffix",
    "IncludeDirectoryPrefix",
    "IncludeDirectoryRegex",
    "IncludeIfFileExists",
    "IncludeFromTable",
    "IncludeFromLogs",
    "ExcludeExtension",
    "ExcludeFileSuffix",
    "ExcludeFilePrefix",
    "ExcludeFileRegex",
    "ExcludeDirectorySuffix",
    "ExcludeDirectoryPrefix",
    "ExcludeDirectoryRegex",
    "ExcludeIfFileExists",
    "ExcludeFromTable",
    "ExcludeFromLogs",
]

from nifti_finder.filters.base import *
from nifti_finder.filters.filterable import *
from nifti_finder.filters.compose import *
from nifti_finder.filters.basic_filters import *
from nifti_finder.filters.extra_filters import *
from nifti_finder.filters.utils import *
