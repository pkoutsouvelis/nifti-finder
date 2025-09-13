"""Pytest configuration"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

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

def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

def _make_subject(
    root: Path,
    sub: str,
    *,
    with_session: bool,
    t1_basename: str | None = None,
) -> Path:
    """
    Create a subject structure under `root` and return the subject directory.
    If `with_session` is True, creates `ses-01/anat/`; otherwise `anat/` directly.
    """
    if t1_basename is None:
        # BIDS-typical basename
        t1_basename = f"{sub}_T1w"

    if with_session:
        anat = root / sub / "ses-01" / "anat"
        nii = anat / f"{sub}_ses-01_T1w.nii"
        jsn = anat / f"{sub}_ses-01_T1w.json"
    else:
        anat = root / sub / "anat"
        nii = anat / f"{t1_basename}.nii.gz"
        jsn = anat / f"{t1_basename}.json"

    _touch(nii)
    _write_text(jsn, '{"Modality":"MR","Series":"T1w"}\n')
    return root / sub

def _make_bids_dataset(dst: Path) -> dict[str, Path]:
    """
    Build a BIDS-like dataset:
      - sub-01..sub-05
      - sub-02 and sub-04 have ses-01
      - participants.tsv at root
    """
    dst.mkdir(parents=True, exist_ok=True)

    subjects = [f"sub-{i:02d}" for i in range(1, 6)]
    session_subjects = {"sub-02", "sub-04"}

    sub_dirs: list[Path] = []
    for sub in subjects:
        sub_dir = _make_subject(dst, sub, with_session=(sub in session_subjects))
        sub_dirs.append(sub_dir)

    # participants.tsv
    _write_text(
        dst / "participants.tsv",
        "participant_id\tage\tsex\n"
        "sub-01\t25\tM\n"
        "sub-02\t31\tF\n"
        "sub-03\t29\tM\n"
        "sub-04\t40\tF\n"
        "sub-05\t35\tM\n",
    )
    return {
        "root": dst,
    }

def _make_multi_datasets(dst: Path) -> dict[str, Path]:
    """
    Build a container directory holding datasets:
      - OpenNeuro-ds00001 .. OpenNeuro-ds00005
      - each contains a single subject 'sub-01' with ses-01/anat/T1w.*
    """
    dst.mkdir(parents=True, exist_ok=True)
    made: dict[str, Path] = {"root": dst}

    for idx in range(1, 6):
        name = f"OpenNeuro-ds{idx:05d}"
        ds_root = dst / name
        ds_root.mkdir(parents=True, exist_ok=True)

        # Single subject with session
        _make_subject(ds_root, "sub-01", with_session=True)
        made[name] = ds_root

    return made

@pytest.fixture(scope="session")
def mock_datasets(tmp_path_factory) -> dict[str, Path]:
    """
    Create two mock datasets for explorer tests.

    Returns a dict with keys:
      - base:               base temporary directory
      - bids_root:          root of the BIDS-like dataset
      - multi_root:         container directory for multiple datasets
      - OpenNeuro-ds00001..OpenNeuro-ds00005: roots of each contained dataset
    """
    base = tmp_path_factory.mktemp("datasets")
    # Dataset A: BIDS-like
    bids_info = _make_bids_dataset(base / "bids_dataset")
    # Dataset B: multi-dataset
    multi_info = _make_multi_datasets(base / "multi_datasets")

    return {
        "base": base,
        "bids_root": bids_info["root"],
        "multi_root": multi_info["root"],
        **{k: v for k, v in multi_info.items() if k != "root"},
    }