"""Unit tests for extra filters."""

from __future__ import annotations

import pytest
from pathlib import Path
import csv

from nifti_finder.filters.extra_filters import *


class TestFromTable:
    """Test include/exclude from table filter."""

    @pytest.fixture
    def include_from_table_path(self, tmp_path: Path) -> Path:
        """Create a temporary participants-like TSV table for IncludeFromTable tests."""
        table_path = tmp_path / "participants.tsv"

        rows = [
            {"sub_id": "sub-01", "meta_1": "A", "meta_2": "1", "meta_3": "true"},
            {"sub_id": "sub-02", "meta_1": "B", "meta_2": "2", "meta_3": "false"},
            {"sub_id": "01", "meta_1": "A", "meta_2": "3", "meta_3": "true"},
            {"sub_id": "patient-003", "meta_1": "C", "meta_2": "4", "meta_3": "false"},
            {"sub_id": "control_04", "meta_1": "B", "meta_2": "5", "meta_3": "true"},
        ]

        with table_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["sub_id", "meta_1", "meta_2", "meta_3"],
                delimiter="\t",
            )
            writer.writeheader()
            writer.writerows(rows)

        return table_path

    def test_include_strict_id_matching(self, include_from_table_path):
        filter = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
        )
        assert filter("sub-01")
        assert filter("sub-02")
        assert filter("01")
        assert filter("patient-003")
        assert filter("control_04")
        assert not filter("/data/sub-02_T1w.nii.gz")
        assert not filter("/data/01_T1w.nii.gz")
        assert not filter("/data/patient-003_T1w.nii.gz")
        assert not filter("/data/control_04_T1w.nii.gz")

    def test_include_loose_id_matching(self, include_from_table_path):
        filter = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="/{id}_",
        )
        assert filter("/data/sub-01_T1w.nii.gz")
        assert filter("/data/sub-02_T1w.nii.gz")
        assert filter("/data/01_T1w.nii.gz")
        assert filter("/data/patient-003_T1w.nii.gz")
        assert filter("/data/control_04_T1w.nii.gz")

    def test_exclude_id_matching(self, include_from_table_path):
        filter = ExcludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="/{id}_",
        )
        assert not filter("/data/sub-01_T1w.nii.gz")
        assert not filter("/data/sub-02_T1w.nii.gz")
        assert not filter("/data/01_T1w.nii.gz")
        assert not filter("/data/patient-003_T1w.nii.gz")
        assert not filter("/data/control_04_T1w.nii.gz")

    def test_include_multiple_id_matches(self, include_from_table_path):
        filter = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="{id}_",
        )
        with pytest.warns(UserWarning):
            assert filter("sub-01_T1w.nii.gz")

    def test_include_criteria_matching_single(self, include_from_table_path):
        filter = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="/{id}_",
            criteria_column="meta_1",
            criteria_value="A",
        )
        assert filter("/data/sub-01_T1w.nii.gz")
        assert not filter("/data/sub-02_T1w.nii.gz")
        assert filter("/data/01_T1w.nii.gz")
        assert not filter("/data/patient-003_T1w.nii.gz")
        assert not filter("/data/control_04_T1w.nii.gz")

    def test_include_criteria_matching_multiple(self, include_from_table_path):
        filter = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="/{id}_",
            criteria_column="meta_1",
            criteria_value=["A", "B"],
        )
        assert filter("/data/sub-01_T1w.nii.gz")
        assert filter("/data/sub-02_T1w.nii.gz")
        assert filter("/data/01_T1w.nii.gz")
        assert not filter("/data/patient-003_T1w.nii.gz")
        assert filter("/data/control_04_T1w.nii.gz")

    def test_include_criteria_matching_normalized(self, include_from_table_path):
        filter = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="/{id}_",
            criteria_column="meta_1",
            criteria_value=["a", "b"],
        )
        assert filter("/data/sub-01_T1w.nii.gz")
        assert filter("/data/sub-02_T1w.nii.gz")
        assert filter("/data/01_T1w.nii.gz")
        assert not filter("/data/patient-003_T1w.nii.gz")
        assert filter("/data/control_04_T1w.nii.gz")

    def test_exclude_criteria_matching(self, include_from_table_path):
        filter = ExcludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            id_pattern="/{id}_",
            criteria_column="meta_1",
            criteria_value=["A", "B"],
        )
        assert not filter("/data/sub-01_T1w.nii.gz")
        assert not filter("/data/sub-02_T1w.nii.gz")
        assert not filter("/data/01_T1w.nii.gz")
        assert filter("/data/patient-003_T1w.nii.gz")
        assert not filter("/data/control_04_T1w.nii.gz")

    def test_handle_missing(self, include_from_table_path):
        # Include if missing
        filter_inc = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            skip_if_missing=False,
        )
        filter_exc = ExcludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            skip_if_missing=True,
        )
        assert filter_inc("sub-xyz")
        assert filter_exc("sub-xyz")

        # Exclude if missing
        filter_inc = IncludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            skip_if_missing=True,
        )
        filter_exc = ExcludeFromTable(
            table_path=include_from_table_path,
            id_column="sub_id",
            skip_if_missing=False,
        )
        assert not filter_inc("sub-xyz")
        assert not filter_exc("sub-xyz")

    def test_missing_criteria_column(self, include_from_table_path):
        with pytest.raises(ValueError):
            IncludeFromTable(
                table_path=include_from_table_path,
                id_column="sub_id",
                criteria_column="meta_4",
                criteria_value=["A", "B"],
            )

    def test_missing_criteria_value(self, include_from_table_path):
        with pytest.raises(ValueError):
            IncludeFromTable(
                table_path=include_from_table_path,
                id_column="sub_id",
                criteria_column="meta_4",
            )

    def test_missing_criteria_column_but_value(self, include_from_table_path):
        with pytest.raises(ValueError):
            IncludeFromTable(
                table_path=include_from_table_path,
                id_column="sub_id",
                criteria_value=["A", "B"],
            )

    def test_invalid_id_pattern(self, include_from_table_path):
        with pytest.raises(ValueError):
            IncludeFromTable(
                table_path=include_from_table_path,
                id_column="sub_id",
                id_pattern="sub_id",
            )

    def test_missing_table(self):
        with pytest.raises(FileNotFoundError):
            IncludeFromTable(
                table_path="non_existent.tsv",
                id_column="sub_id",
            )


class TestFromLogs:
    """Test include/exclude from logs filter."""

    @pytest.fixture
    def logs_file_path(self, tmp_path: Path) -> Path:
        """Create a temporary logs file for IncludeFromLogs tests."""
        logs_path = tmp_path / "logs.txt"

        lines = [
            "sub-01_T1w.nii.gz: SUCCESS",
            "sub-02_T1w.nii.gz: FAILED",
            "patient-003_T1w.nii.gz: FAILED",
            "control_04_T1w.nii.gz: SUCCESS",
            "orphan_file.nii.gz",
        ]

        logs_path.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

        return logs_path

    def test_include_filepath_matching(self, logs_file_path):
        filter = IncludeFromLogs(
            logs_path=logs_file_path,
        )
        assert filter("/data/sub-01_T1w.nii.gz")  # full path
        assert filter("sub-01_T1w.nii.gz")
        assert filter("sub-02_T1w.nii.gz")
        assert filter("patient-003_T1w.nii.gz")
        assert filter("control_04_T1w.nii.gz")
        assert not filter("sub-01_T1w")  # no match; partial match
        assert not filter("sub-01")  # no match; partial match

    def test_exclude_filepath_matching(self, logs_file_path):
        filter = ExcludeFromLogs(
            logs_path=logs_file_path,
        )
        assert not filter("sub-01_T1w.nii.gz")
        assert not filter("sub-02_T1w.nii.gz")
        assert not filter("patient-003_T1w.nii.gz")
        assert not filter("control_04_T1w.nii.gz")
        assert not filter("orphan_file.nii.gz")

    def test_include_message_matching(self, logs_file_path):
        filter = IncludeFromLogs(
            logs_path=logs_file_path,
            message="FAILED",
        )
        assert not filter("sub-01_T1w.nii.gz")
        assert filter("sub-02_T1w.nii.gz")
        assert filter("patient-003_T1w.nii.gz")
        assert not filter("control_04_T1w.nii.gz")
        assert not filter("orphan_file.nii.gz")

    def test_exclude_message_missing(self, logs_file_path):
        filter = ExcludeFromLogs(
            logs_path=logs_file_path,
            message="SUCCESS",
        )
        assert not filter("sub-01_T1w.nii.gz")
        assert filter("sub-02_T1w.nii.gz")
        assert filter("patient-003_T1w.nii.gz")
        assert not filter("control_04_T1w.nii.gz")
        assert filter("orphan_file.nii.gz")

    def test_handle_missing(self, logs_file_path):
        # Include if missing
        filter_inc = IncludeFromLogs(
            logs_path=logs_file_path,
            skip_if_missing=False,
        )
        filter_exc = ExcludeFromLogs(
            logs_path=logs_file_path,
            skip_if_missing=True,
        )
        assert filter_inc("sub-xyz")
        assert filter_exc("sub-xyz")

        # Exclude if missing
        filter_inc = IncludeFromLogs(
            logs_path=logs_file_path,
            skip_if_missing=True,
        )
        filter_exc = ExcludeFromLogs(
            logs_path=logs_file_path,
            skip_if_missing=False,
        )
        assert not filter_inc("sub-xyz")
        assert not filter_exc("sub-xyz")

    def test_missing_logs_file(self):
        with pytest.raises(FileNotFoundError):
            IncludeFromLogs(
                logs_path="non_existent.txt",
            )
