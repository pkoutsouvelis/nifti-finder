"""Integration tests for file explorers"""

from __future__ import annotations

from nifti_finder.explorers import (
    BasicFileExplorer,
    TwoStageFileExplorer,
    AllPurposeFileExplorer,
    NiftiExplorer,
)
from nifti_finder.filters import ExcludeDirectoryPrefix

class TestBasicFileExplorer:
    """
    Test `BasicFileExplorer`

    Tests: 
    A) All files: general traversal of the dataset
    B) All nifti files: specific pattern matching
    C) All T1w files in BIDS-style dataset: Checks flexibility 
        to lack of 'ses-*' in several subjects
    D) All nifti files in multiple datasets: checks tranversal 
        invariance to dataset structure.
    E) All nifti files and 'participants.tsv': Check multiple patterns compatibility.
    """
    def test_all_files(self, mock_datasets):
        explorer = BasicFileExplorer()
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 11
        assert all(path.is_file() for path in paths)

    def test_all_nifti_files(self, mock_datasets):
        explorer = BasicFileExplorer(pattern="*.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )
    
    def test_all_nifti_files_bids(self, mock_datasets):
        explorer = BasicFileExplorer(pattern="sub-*/**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )

    def test_all_nifti_files_multi_datasets(self, mock_datasets):
        explorer = BasicFileExplorer(pattern="*.nii*")
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )

    def test_multiple_patterns(self, mock_datasets):
        explorer = BasicFileExplorer(pattern=["*.nii*", "*.tsv"])
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 6


class TestTwoStageFileExplorer:
    """
    Test `TwoStageFileExplorer`

    Tests: 
    A) All T1w files in BIDS-style dataset: Checks two-stage traversal,
        first for subjects, then for files. Also checks progress tracking.
    B) All T1w files in multiple datasets: Checks two-stage traversal,
        first for datasets, then for subjects-files. Also disables progress tracking.
    C) Get single dataset from multiple datasets: Ensures pattern matching works 
        for stage 1; i.e., get single dataset.
    D) All nifti files and 'participants.tsv': Check it ignores 'participants.tsv.'
        as it is not a directory.
    E) Same as D, but with multiple patterns in stage 2 as well for .json files.
        Should be equivalent to the '*' pattern without the 'participants.tsv'.
    """
    def test_all_nifti_files_bids(self, mock_datasets):
        explorer = TwoStageFileExplorer(stage_1_pattern="sub-*", 
                                        stage_2_pattern="**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["bids_root"], progress=True, desc="Subjects")
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )
    
    def test_all_nifti_multi_datasets(self, mock_datasets):
        explorer = TwoStageFileExplorer(stage_1_pattern="OpenNeuro-ds*", 
                                        stage_2_pattern="sub-*/**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )

    def test_all_nifti_multi_datasets_single(self, mock_datasets):
        explorer = TwoStageFileExplorer(stage_1_pattern="OpenNeuro-ds00001", 
                                        stage_2_pattern="sub-*/**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 1
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )
    
    def test_dirs_only(self, mock_datasets):
        explorer = TwoStageFileExplorer(stage_1_pattern=["sub-*", "*.tsv"], 
                                        stage_2_pattern="*.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
    
    def test_multiple_patterns_stage_2(self, mock_datasets):
        explorer = TwoStageFileExplorer(stage_1_pattern=["sub-*", "*.tsv"], 
                                        stage_2_pattern=["*.nii*", "*.json"])
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 10


class TestAllPurposeFileExplorer:
    """
    Integration tests for `AllPurposeFileExplorer`. 

    Checks compatibility with `Filterable` and `Materializable` mixins, as well
    as with the `scan()` method of the `BasicFileExplorer`.

    Tests: 
    A) All T1w files in BIDS-style dataset: Check 'BasicFileExplorer' works as expected.
    B) Same as A, but check materialization methods work as expected.
    C) Same as A, but check filtering compatibility by excluding 2 subjects
        that have a 'ses-*' directory. Also checks `remove_filters()` method.
    """
    def test_all_nifti_files_bids(self, mock_datasets):
        explorer = AllPurposeFileExplorer(pattern="sub-*/**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )

    def test_all_nifti_files_bids_materialization(self, mock_datasets):
        explorer = AllPurposeFileExplorer(pattern="sub-*/**/anat/*T1w.nii*")
        paths = explorer.list(mock_datasets["bids_root"])
        assert len(paths) == 5
        batched = explorer.batched(mock_datasets["bids_root"], size=2)
        assert len(list(batched)) == 3
    
    def test_all_nifti_files_bids_filter(self, mock_datasets):
        explorer = AllPurposeFileExplorer(pattern="sub-*/**/anat/*T1w.nii*",
                                            filters=[ExcludeDirectoryPrefix("ses-")])
        paths = explorer.list(mock_datasets["bids_root"])
        assert len(paths) == 3
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )
        explorer.remove_filters(ExcludeDirectoryPrefix("ses-"))
        paths = explorer.list(mock_datasets["bids_root"])
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )


class TestNiftiExplorer:
    """
    Integration tests for `NiftiExplorer`.

    Tests: 
    A) All nifti files: Check default behavior.
    B) All T1w files in BIDS-style dataset: Check two-stage traversal
        with progress works as expected.
    C) All nifti files in multiple datasets: Check two-stage traversal
        without progress works as expected.
    D) Same as C, but check filtering compatibility by excluding 2 subjects
        that have a 'ses-*' directory. Also checks `remove_filters()` method.
    """
    def test_all_nifti_files(self, mock_datasets):
        explorer = NiftiExplorer()
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )
    
    def test_all_nifti_files_bids_w_progress(self, mock_datasets):
        explorer = NiftiExplorer(stage_1_pattern="sub-*", 
                                stage_2_pattern="**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["bids_root"], progress=True, desc="Subjects")
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )

    def test_all_nifti_files_multi_datasets_w_progress(self, mock_datasets):
        explorer = NiftiExplorer(stage_1_pattern="OpenNeuro-ds*", 
                                stage_2_pattern="*.nii*")
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )

    def test_all_nifti_files_multi_datasets_filter(self, mock_datasets):
        explorer = NiftiExplorer(stage_1_pattern="OpenNeuro-ds*", 
                                stage_2_pattern="*.nii*",
                                filters=[ExcludeDirectoryPrefix("ses-")])
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 0
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )
        explorer.remove_filters(ExcludeDirectoryPrefix("ses-"))
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz") 
            for path in paths
        )