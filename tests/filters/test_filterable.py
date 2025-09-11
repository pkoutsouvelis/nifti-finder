"""Test filterable mixin"""

from __future__ import annotations

import pytest

from nifti_finder.filters import FilterableMixin, IncludeExtension

class TestFilterableMixin:
    """Test filterable mixin"""
    @pytest.fixture
    def filterable(self):
        return FilterableMixin()

    def test_filters_init(self):
        filterable = FilterableMixin(filters=[IncludeExtension("nii.gz")], logic="OR")
        assert filterable.filters() == (IncludeExtension("nii.gz"),)

    def test_filters_add_single(self, filterable):
        filterable.add_filters(IncludeExtension("nii.gz"))
        filterable.add_filters(IncludeExtension("txt"))
        assert filterable.filters() == (IncludeExtension("nii.gz"), IncludeExtension("txt"))

    def test_filters_add_multiple(self, filterable):
        filterable.add_filters([IncludeExtension("nii.gz"), IncludeExtension("txt")])
        assert filterable.filters() == (IncludeExtension("nii.gz"), IncludeExtension("txt"))
    
    def test_filters_remove_by_instance(self, filterable):
        filterable.add_filters(IncludeExtension("nii.gz"))
        filterable.remove_filters(IncludeExtension("nii.gz"))
        assert filterable.filters() == ()

    def test_filters_remove_by_index(self, filterable):
        filterable.add_filters([IncludeExtension("nii.gz"), IncludeExtension("txt")])
        filterable.remove_filters(-1)
        assert filterable.filters() == (IncludeExtension("nii.gz"),)
    
    def test_filters_clear(self, filterable):
        filterable.add_filters([IncludeExtension("nii.gz"), IncludeExtension("txt")])
        filterable.clear_filters()
        assert filterable.filters() == ()
    
    def test_filters_apply(self, filterable, file_paths):
        filterable.add_filters(IncludeExtension("nii.gz"))
        gnd_truth = [False, True, True, True, True, True, True]
        for f, g in zip(file_paths, gnd_truth):
            assert filterable.apply_filters(f) == g
    
    def test_filters_wrong_input(self, filterable):
        with pytest.raises(TypeError):
            filterable.add_filters(5)
        with pytest.raises(TypeError):
            filterable.add_filters([5])
        with pytest.raises(TypeError):
            filterable.add_filters('invalid')
        with pytest.raises(TypeError):
            filterable.add_filters(['invalid'])
        with pytest.raises(TypeError):
            filterable.add_filters([IncludeExtension("nii.gz"), 5])
        with pytest.raises(TypeError):
            filterable.add_filters([IncludeExtension("nii.gz"), 'invalid'])
        with pytest.raises(TypeError):
            filterable.remove_filters("invalid")
        with pytest.raises(TypeError):
            filterable.remove_filters(['invalid'])