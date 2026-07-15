"""Integration tests for file explorers"""

from __future__ import annotations

import warnings

import pytest

from nifti_finder.explorers import (
    RecursiveFileExplorer,
    NestedFileExplorer,
    FileFinder,
    BasicFileExplorer,
    TwoStageFileExplorer,
    AllPurposeFileExplorer,
    NeuroExplorer,
)
from nifti_finder.filters import ExcludeDirectoryPrefix


class TestRecursiveFileExplorer:
    """
    Test `RecursiveFileExplorer`

    Tests:
    A) All files: general traversal of the dataset
    B) All nifti files: specific pattern matching
    C) All T1w files in BIDS-style dataset: Checks flexibility
        to lack of 'ses-*' in several subjects
    D) All nifti files in multiple datasets: checks tranversal
        invariance to dataset structure.
    E) All nifti files and 'participants.tsv': Check multiple patterns compatibility.
    F) Deprecated `pattern` argument still works.
    """

    def test_all_files(self, mock_datasets):
        explorer = RecursiveFileExplorer(patterns="*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 11
        assert all(path.is_file() for path in paths)

    def test_default_finds_nifti(self, mock_datasets):
        explorer = RecursiveFileExplorer()
        paths = list(explorer.scan(mock_datasets["bids_root"]))
        assert len(paths) == 5

    def test_all_nifti_files(self, mock_datasets):
        explorer = RecursiveFileExplorer(patterns="*.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_all_nifti_files_bids(self, mock_datasets):
        explorer = RecursiveFileExplorer(patterns="sub-*/**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_all_nifti_files_multi_datasets(self, mock_datasets):
        explorer = RecursiveFileExplorer(patterns="*.nii*")
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_multiple_patterns(self, mock_datasets):
        explorer = RecursiveFileExplorer(patterns=["*.nii*", "*.tsv"])
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 6

    def test_deprecated_pattern_arg(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = RecursiveFileExplorer(pattern="*.nii*")
        paths = list(explorer.scan(mock_datasets["bids_root"]))
        assert len(paths) == 5


class TestNestedFileExplorer:
    """
    Test `NestedFileExplorer`

    Tests:
    A) All T1w files in BIDS-style dataset: Checks nested traversal,
        first for subjects, then for files. Also checks progress tracking.
    B) All T1w files in multiple datasets: Checks nested traversal,
        first for datasets, then for subjects-files. Also disables progress tracking.
    C) Get single dataset from multiple datasets: Ensures pattern matching works
        for the first level; i.e., get single dataset.
    D) All nifti files and 'participants.tsv': Check it ignores 'participants.tsv.'
        as it is not a directory.
    E) Same as D, but with multiple patterns in the last level as well for .json files.
    F) Flat scan when levels is None.
    G) Three-level nested traversal with multiple file patterns.
    H) Progress ignored when levels is None.
    """

    def test_all_nifti_files_bids(self, mock_datasets):
        explorer = NestedFileExplorer(
            levels={"subjects": "sub-*"},
            patterns="**/anat/*T1w.nii*",
        )
        paths = explorer.scan(
            mock_datasets["bids_root"], progress=True, desc="Subjects"
        )
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_all_nifti_multi_datasets(self, mock_datasets):
        explorer = NestedFileExplorer(
            levels={"datasets": "OpenNeuro-ds*"},
            patterns="**/anat/*T1w.nii*",
        )
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_three_level_nested(self, mock_datasets):
        explorer = NestedFileExplorer(
            levels={
                "datasets": "OpenNeuro-ds*",
                "subjects": "sub-*",
                "sessions": "ses-*",
                "anat": "anat",
            },
            patterns="*T1w.nii*",
        )
        paths = list(explorer.scan(mock_datasets["multi_root"]))
        assert len(paths) == 5

    def test_all_nifti_multi_datasets_single(self, mock_datasets):
        explorer = NestedFileExplorer(
            levels={"datasets": "OpenNeuro-ds00001"},
            patterns="**/anat/*T1w.nii*",
        )
        paths = explorer.scan(mock_datasets["multi_root"])
        paths = list(paths)
        assert len(paths) == 1
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_dirs_only(self, mock_datasets):
        explorer = NestedFileExplorer(
            levels={"subjects": ["sub-*", "*.tsv"]},
            patterns="*.nii*",
        )
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5

    def test_multiple_patterns(self, mock_datasets):
        explorer = NestedFileExplorer(
            levels={"subjects": ["sub-*", "*.tsv"]},
            patterns=["*.nii*", "*.json"],
        )
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 10

    def test_flat_scan_without_levels(self, mock_datasets):
        explorer = NestedFileExplorer(patterns="*.nii*")
        paths = list(explorer.scan(mock_datasets["bids_root"]))
        assert len(paths) == 5

    def test_progress_ignored_without_levels(self, mock_datasets):
        explorer = NestedFileExplorer(patterns="*.nii*")
        with pytest.warns(UserWarning, match="progress is ignored"):
            list(explorer.scan(mock_datasets["bids_root"], progress=True))

    def test_levels_must_not_be_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            NestedFileExplorer(levels={})


class TestFileFinder:
    """Integration tests for `FileFinder`."""

    def test_all_nifti_files(self, mock_datasets):
        finder = FileFinder()
        paths = list(finder.scan(mock_datasets["bids_root"]))
        assert len(paths) == 5
        assert all(
            path.name.endswith(".nii") or path.name.endswith(".nii.gz")
            for path in paths
        )

    def test_all_nifti_files_bids_w_progress(self, mock_datasets):
        finder = FileFinder(
            levels={"subjects": "sub-*"},
            patterns="**/anat/*T1w.nii*",
        )
        paths = list(
            finder.scan(mock_datasets["bids_root"], progress=True, desc="Subjects")
        )
        assert len(paths) == 5

    def test_all_nifti_files_multi_datasets(self, mock_datasets):
        finder = FileFinder(
            levels={"datasets": "OpenNeuro-ds*"},
            patterns="*.nii*",
        )
        paths = list(finder.scan(mock_datasets["multi_root"]))
        assert len(paths) == 5

    def test_all_nifti_files_multi_datasets_filter(self, mock_datasets):
        finder = FileFinder(
            levels={"datasets": "OpenNeuro-ds*"},
            patterns="*.nii*",
            filters=[ExcludeDirectoryPrefix("ses-")],
        )
        paths = list(finder.scan(mock_datasets["multi_root"]))
        assert len(paths) == 0
        finder.remove_filters(ExcludeDirectoryPrefix("ses-"))
        paths = list(finder.scan(mock_datasets["multi_root"]))
        assert len(paths) == 5

    def test_materialization(self, mock_datasets):
        finder = FileFinder(patterns="sub-*/**/anat/*T1w.nii*")
        paths = finder.list(mock_datasets["bids_root"])
        assert len(paths) == 5
        batched = finder.batched(mock_datasets["bids_root"], size=2)
        assert len(list(batched)) == 3


class TestBasicFileExplorer:
    """Deprecated shim remains compatible."""

    def test_deprecated_warning(self):
        with pytest.warns(DeprecationWarning, match="BasicFileExplorer"):
            BasicFileExplorer()


class TestTwoStageFileExplorer:
    """Deprecated shim remains compatible."""

    def test_all_nifti_files_bids(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = TwoStageFileExplorer(
                stage_1_pattern="sub-*", stage_2_pattern="**/anat/*T1w.nii*"
            )
        paths = list(explorer.scan(mock_datasets["bids_root"]))
        assert len(paths) == 5


class TestAllPurposeFileExplorer:
    """
    Integration tests for deprecated `AllPurposeFileExplorer`.
    """

    def test_all_nifti_files_bids(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = AllPurposeFileExplorer(patterns="sub-*/**/anat/*T1w.nii*")
        paths = explorer.scan(mock_datasets["bids_root"])
        paths = list(paths)
        assert len(paths) == 5

    def test_all_nifti_files_bids_materialization(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = AllPurposeFileExplorer(patterns="sub-*/**/anat/*T1w.nii*")
        paths = explorer.list(mock_datasets["bids_root"])
        assert len(paths) == 5
        batched = explorer.batched(mock_datasets["bids_root"], size=2)
        assert len(list(batched)) == 3

    def test_all_nifti_files_bids_filter(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = AllPurposeFileExplorer(
                patterns="sub-*/**/anat/*T1w.nii*",
                filters=[ExcludeDirectoryPrefix("ses-")],
            )
        paths = explorer.list(mock_datasets["bids_root"])
        assert len(paths) == 3
        explorer.remove_filters(ExcludeDirectoryPrefix("ses-"))
        paths = explorer.list(mock_datasets["bids_root"])
        assert len(paths) == 5


class TestNeuroExplorer:
    """Integration tests for deprecated `NeuroExplorer` (outer/inner API)."""

    def test_deprecated_warning(self):
        with pytest.warns(DeprecationWarning, match="NeuroExplorer"):
            NeuroExplorer()

    def test_all_nifti_files_two_stage_default(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = NeuroExplorer()
        paths = list(explorer.scan(mock_datasets["bids_root"]))
        assert len(paths) == 5

    def test_all_nifti_files_bids_w_progress(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = NeuroExplorer(outer="sub-*", inner="**/anat/*T1w.nii*")
        paths = list(
            explorer.scan(mock_datasets["bids_root"], progress=True, desc="Subjects")
        )
        assert len(paths) == 5

    def test_all_nifti_files_multi_datasets_w_progress(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = NeuroExplorer(outer="OpenNeuro-ds*", inner="*.nii*")
        paths = list(explorer.scan(mock_datasets["multi_root"]))
        assert len(paths) == 5

    def test_all_nifti_files_multi_datasets_filter(self, mock_datasets):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            explorer = NeuroExplorer(
                outer="OpenNeuro-ds*",
                inner="*.nii*",
                filters=[ExcludeDirectoryPrefix("ses-")],
            )
        paths = list(explorer.scan(mock_datasets["multi_root"]))
        assert len(paths) == 0
        explorer.remove_filters(ExcludeDirectoryPrefix("ses-"))
        paths = list(explorer.scan(mock_datasets["multi_root"]))
        assert len(paths) == 5
