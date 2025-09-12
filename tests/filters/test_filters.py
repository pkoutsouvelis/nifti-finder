"""Unit tests for filters"""

from __future__ import annotations

import pytest
from pathlib import Path

from nifti_finder.filters import *
from tests.utils import assert_filter


class TestExtensionFilter:
    """Test extension filter"""
    def test_include_extension(self, file_paths):
        filter = IncludeExtension("nii.gz")
        assert_filter(filter, file_paths, [False, True, True, True, True, True, True])

    def test_exclude_extension(self, file_paths):
        filter = ExcludeExtension("txt")
        assert_filter(filter, file_paths, [False, True, True, True, True, True, True])
            
            
class TestSuffixFilter:
    """Test suffix filter"""
    def test_include_suffix_file(self, file_paths):
        filter = IncludeFileSuffix("suffix")
        assert_filter(filter, file_paths, [False, False, True, False, False, False, False])
    
    def test_exclude_suffix_file(self, file_paths):
        filter = ExcludeFileSuffix("file0")
        assert_filter(filter, file_paths, [False, True, True, True, True, True, True])

    def test_include_suffix_dir(self, file_paths):
        filter = IncludeDirectorySuffix("suffix")
        assert_filter(filter, file_paths, [False, False, False, False, False, True, False])
    
    def test_exclude_suffix_dir(self, file_paths):
        filter = ExcludeDirectorySuffix("data")
        assert_filter(filter, file_paths, [False, False, False, False, False, True, False])
            

class TestPrefixFilter:
    """Test prefix filter"""
    def test_include_prefix(self, file_paths):
        filter = IncludeFilePrefix("prefix")
        assert_filter(filter, file_paths, [False, False, False, True, False, False, True])
    
    def test_exclude_prefix(self, file_paths):
        filter = ExcludeFilePrefix("prefix_file6")
        assert_filter(filter, file_paths, [True, True, True, True, True, True, False])
    
    def test_include_prefix_dir(self, file_paths):
        filter = IncludeDirectoryPrefix("prefix")
        assert_filter(filter, file_paths, [False, False, False, False, False, False, True])
    
    def test_exclude_prefix_dir(self, file_paths):
        filter = ExcludeDirectoryPrefix("data")
        assert_filter(filter, file_paths, [False, False, False, False, False, False, True])


class TestRegexFilter:
    """Test regex filter"""
    def test_include_regex(self, file_paths):
        filter = IncludeFileRegex(".*file*")
        assert_filter(filter, file_paths, [True, True, True, True, True, True, True])
    
    def test_exclude_regex(self, file_paths):
        filter = ExcludeFileRegex("prefix_.*")
        assert_filter(filter, file_paths, [True, True, True, False, True, True, False])

    def test_include_regex_dir(self, file_paths):
        filter = IncludeDirectoryRegex(".*suffix*")
        assert_filter(filter, file_paths, [False, False, False, False, False, True, False])
    
    def test_exclude_regex_dir(self, file_paths):
        filter = ExcludeDirectoryRegex(".*data*")
        assert_filter(filter, file_paths, [False, False, False, False, False, False, False])


class TestIfFileExistsFilter:
    """Test if file exists filter"""
    @pytest.fixture
    def fs(self, tmp_path: Path) -> dict[str, Path]:
        """
        Create a tiny BIDS-like tree:

        /data/sub-1/ses-1/t1.nii.gz
        /data/sub-1/ses-1/other.json
        /labels/sub-1/ses-1/t1_seg.nii.gz
        /data/sub-2/ses-1/t1.nii.gz            (no label)
        """
        data = tmp_path / "data"
        labels = tmp_path / "labels"

        (data / "sub-1" / "ses-1").mkdir(parents=True)
        (data / "sub-1" / "ses-1" / "labels").mkdir(parents=True)
        (data / "sub-2" / "ses-1").mkdir(parents=True)
        (labels / "sub-1" / "ses-1").mkdir(parents=True)
        (labels / "sub-2" / "ses-1").mkdir(parents=True)

        (data / "sub-1" / "ses-1" / "t1.nii.gz").touch()
        (data / "sub-1" / "ses-1" / "other.json").touch()
        (data / "sub-2" / "ses-1" / "t1.nii.gz").touch()
        (data / "sub-1" / "ses-1" / "labels" / "t1_seg.nii.gz").touch()
        (labels / "sub-2" / "ses-1" / "t1_seg.nii.gz").touch()

        return {
            "data_root": data,
            "labels_root": labels,
            "t1_sub1": data / "sub-1" / "ses-1" / "t1.nii.gz",
            "t1_sub2": data / "sub-2" / "ses-1" / "t1.nii.gz",
        }

    def test_no_op(self, fs):
        filter = IncludeIfFileExists(filename_pattern="--")
        assert_filter(filter, [fs["t1_sub1"], fs["t1_sub2"]], [True, True])
    
    def test_include_if_file_exists_in_same_dir(self, fs):
        filter = IncludeIfFileExists(filename_pattern="*.json")
        assert_filter(filter, [fs["t1_sub1"], fs["t1_sub2"]], [True, False])

    def test_include_if_file_exists_in_mirror_dir(self, fs):
        filter = IncludeIfFileExists(filename_pattern="*seg*", search_in=f"{fs['labels_root']}--", 
                                     mirror_relative_to=fs["data_root"])
        assert_filter(filter, [fs["t1_sub1"], fs["t1_sub2"]], [False, True])
    
    def test_include_if_file_exists_in_absolute_dir(self, fs):
        filter = IncludeIfFileExists(filename_pattern="--", search_in=f"{fs['labels_root'] / 'sub-2' / 'ses-1'}")
        assert_filter(filter, [fs["data_root"] / "sub-1" / "ses-1 / labels" / "t1_seg.nii.gz"], [True])

    def test_include_if_file_exists_in_relative_dir(self, fs):
        filter = IncludeIfFileExists(filename_pattern="*seg*", search_in=f"--labels/")
        assert_filter(filter, [fs["t1_sub1"], fs["t1_sub2"]], [True, False])

    def test_exclude_if_file_exists_in_same_dir(self, fs):
        filter = ExcludeIfFileExists(filename_pattern="*.json")
        assert_filter(filter, [fs["t1_sub1"], fs["t1_sub2"]], [False, True])
    
    def test_exclude_if_file_exists_in_mirror_dir(self, fs):
        filter = ExcludeIfFileExists(filename_pattern="*seg*", search_in=f"{fs['labels_root']}--", 
                                     mirror_relative_to=fs["data_root"])
        assert_filter(filter, [fs["t1_sub1"], fs["t1_sub2"]], [True, False])

    
