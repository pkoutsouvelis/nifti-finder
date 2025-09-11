"""Unit tests for compose filter"""

from __future__ import annotations

import pytest

from nifti_finder.filters import (
    ComposeFilter, 
    IncludeExtension, 
    IncludeFilePrefix, 
    IncludeFileSuffix, 
    ExcludeFilePrefix,
    IncludeDirectorySuffix,
)
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

class TestComposeFilter:
    """Test compose filter"""
    def test_identity(self, file_paths):
        filter = ComposeFilter([])
        assert_filter(filter, file_paths, [True, True, True, True, True, True, True])

    def test_single_filter_compose(self, file_paths):
        filter = ComposeFilter(IncludeExtension("nii.gz"))
        single_filter_ref = IncludeExtension("nii.gz")
        for f in file_paths:
            assert filter(f) == single_filter_ref(f)
    
    def test_and(self, file_paths):
        filter = ComposeFilter([IncludeExtension("nii.gz"), IncludeFilePrefix("file")], logic="AND")
        assert_filter(filter, file_paths, [False, True, True, False, False, False, False])

    def test_and_w_exclude(self, file_paths):
        filter = ComposeFilter([IncludeExtension("nii.gz"), ExcludeFilePrefix("file")], logic="AND")
        assert_filter(filter, file_paths, [False, False, False, True, True, True, True])
    
    def test_or(self, file_paths):
        filter = ComposeFilter([IncludeExtension("nii.gz"), IncludeFilePrefix("file")], logic="OR")
        assert_filter(filter, file_paths, [True, True, True, True, True, True, True])

    def test_or_w_exclude(self, file_paths):
        filter = ComposeFilter([IncludeExtension("nii.gz"), ExcludeFilePrefix("file")], logic="OR")
        assert_filter(filter, file_paths, [False, True, True, True, True, True, True])

    def test_nested_compose(self, file_paths):
        filter = ComposeFilter(
            [IncludeExtension("nii.gz"), ComposeFilter([IncludeFilePrefix("prefix"), IncludeFileSuffix("suffix")], logic="OR")], 
            logic="AND"
        )
        assert_filter(filter, file_paths, [False, False, True, True, False, False, True])
    
    def test_flatten(self, file_paths):
        filter_wo_flatten = ComposeFilter([
            IncludeExtension("nii.gz"), 
            ComposeFilter([
                ComposeFilter([IncludeFilePrefix("prefix"), IncludeFileSuffix("suffix")], logic="OR"), 
                IncludeDirectorySuffix("suffix")], logic="OR")], 
            logic="AND",
        )
        filter_flatten_ref = ComposeFilter([
            IncludeExtension("nii.gz"), 
            ComposeFilter([
                IncludeFilePrefix("prefix"), 
                IncludeFileSuffix("suffix"),
                IncludeDirectorySuffix("suffix"),
            ], logic="OR")], 
            logic="AND",
        )
        filter_w_flatten = filter_wo_flatten.flatten()
        gnd_truth = [False, False, True, True, False, True, True]

        assert_filter(filter_wo_flatten, file_paths, gnd_truth)
        assert_filter(filter_flatten_ref, file_paths, gnd_truth)
        assert_filter(filter_w_flatten, file_paths, gnd_truth)

    def test_wrong_filters(self):
        def _an_invalid_filter(x): return x
        invalid_combs = [
            _an_invalid_filter,
            [IncludeExtension("nii.gz"), _an_invalid_filter],
            5,
            [IncludeExtension("nii.gz"), 5],
            "NOT_VALID",
            [IncludeExtension("nii.gz"), "NOT_VALID"],
        ]
        for comb in invalid_combs:
            with pytest.raises(TypeError):
                ComposeFilter(comb)
    
    def test_wrong_logic(self):
        with pytest.raises(ValueError):
            ComposeFilter([IncludeExtension("nii.gz")], logic="NOT_VALID")
        with pytest.raises(TypeError):
            ComposeFilter([IncludeExtension("nii.gz")], logic=5) # type: ignore
        