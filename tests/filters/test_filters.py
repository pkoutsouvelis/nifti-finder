"""Unit tests for filters"""

from __future__ import annotations

import pytest

from nifti_finder.filters import *
from tests.utils import assert_filter

@pytest.fixture(autouse=True)
def mock_iterdir(monkeypatch, file_paths):
    def _dummy_call(self, *args, **kwargs):
        out_paths = []
        for f in file_paths:
            if f.parent == self:
                out_paths.append(f.parent / "prefix_file6.nii.gz")
        return out_paths
    monkeypatch.setattr("pathlib.Path.iterdir", _dummy_call)


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
    def test_include_if_file_exists(self, file_paths):
        filter = IncludeIfFileExists("prefix_file6.nii.gz")
        assert_filter(filter, file_paths, [True, True, True, True, True, True, True])
    
    def test_exclude_if_file_exists(self, file_paths):
        filter = ExcludeIfFileExists("file6.nii.gz")
        assert_filter(filter, file_paths, [True, True, True, True, True, True, True])