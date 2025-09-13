"""Test mixins for file explorers"""

from __future__ import annotations

import pytest

from nifti_finder.explorers import MaterializeMixin

class MatObj(MaterializeMixin):
    def __init__(self, dummy_file_paths):
        super().__init__()
        self.file_paths = dummy_file_paths

    def scan(self, root_dir):
        for f in self.file_paths:
            yield f

class TestMaterializeMixin:
    @pytest.fixture
    def mat_obj(self, file_paths):
        return MatObj(file_paths)

    def test_list(self, mat_obj, file_paths):
        files = mat_obj.list("/a/root/dir")
        assert isinstance(files, list)
        assert len(files) == len(file_paths)

    def test_sort(self, mat_obj, file_paths):
        files = mat_obj.list("/a/root/dir", sort=True)
        print(files)
        assert files == sorted(file_paths)

    def test_unique(self, file_paths):
        inputs = file_paths + file_paths
        mat_obj = MatObj(inputs)
        files = mat_obj.list("/a/root/dir", unique=True, sort=True)
        assert files == sorted(file_paths)

    @pytest.mark.parametrize("limit", [2, 3, 4])
    def test_limit(self, mat_obj, limit):
        files = mat_obj.list("/a/root/dir", limit=limit)
        assert len(files) == limit

    def test_first(self, mat_obj, file_paths):
        file = mat_obj.first("/a/root/dir")
        assert file == file_paths[0]

    def test_any(self, mat_obj):
        assert mat_obj.any("/a/root/dir") == True
        assert MatObj([]).any("/a/root/dir") == False

    @pytest.mark.parametrize("n", [2, 3, 4])
    def test_count(self, file_paths, n):
        mat_obj = MatObj(file_paths * n)
        assert mat_obj.count("/a/root/dir") == len(file_paths) * n

    @pytest.mark.parametrize("size", [5, 10, 15])
    def test_batched(self, file_paths, size):
        mat_obj = MatObj(file_paths * 3)
        batches = mat_obj.batched("/a/root/dir", size=size)
        len_expected = (len(file_paths) * 3 // size) + ((len(file_paths) * 3 % size) > 0)
        len_actual = len(list(batches))
        assert len_expected == len_actual
        for i, batch in enumerate(batches):
            assert batch == file_paths[i * size:(i + 1) * size]
    