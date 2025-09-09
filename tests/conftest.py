"""Pytest configuration"""

from __future__ import annotations

from pathlib import Path

import pytest

@pytest.fixture(scope="session")
def file_paths() -> list[Path]:
    return [
        Path(__file__).parent / "data" / "file0.txt",
        Path(__file__).parent / "data" / "file1.nii.gz",
        Path(__file__).parent / "data" / "file2_suffix.nii.gz",
        Path(__file__).parent / "data" / "prefix_file3.nii.gz",
        Path(__file__).parent / "data" / "ignore_suffix_file5.nii.gz",
        Path(__file__).parent / "data_suffix" / "ignore_suffix_file5.nii.gz",
        Path(__file__).parent / "prefix_data" / "prefix_file6.nii.gz",
    ]