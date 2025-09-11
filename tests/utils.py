"""Helper functions for tests"""

from __future__ import annotations

from pathlib import Path

from nifti_finder.filters import Filter


def assert_filter(filter: Filter, file_paths: list[Path], expected: list[bool]):
    outs = []
    for f in file_paths:
        outs.append(filter(f))
    assert outs == expected