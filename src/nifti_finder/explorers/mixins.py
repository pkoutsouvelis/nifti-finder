"""Mixins for file explorers"""

from __future__ import annotations

__all__ = [
    "Materializable",
    "MaterializeMixin",
]

from typing import Protocol, Iterator, TYPE_CHECKING, runtime_checkable

from nifti_finder.utils import resolve_path

if TYPE_CHECKING:
    from pathlib import Path


@runtime_checkable
class Materializable(Protocol):
    """Any object with convenience methods that materialize `scan()`."""
    def list(self, root_dir: Path | str, /) -> list[Path]: ...
    def first(self, root_dir: Path | str, /) -> Path | None: ...
    def any(self, root_dir: Path | str, /) -> bool: ...
    def count(self, root_dir: Path | str, /) -> int: ...
    def batched(self, root_dir: Path | str, /, *, size: int) -> Iterator[list[Path]]: ...


class MaterializeMixin:
    """Concrete implementation of the `Materializable` protocol."""
    def list(self, root_dir: Path | str, /, *, sort: bool=False,
             unique: bool=False, limit: int | None=None, **scan_kw) -> list[Path]:
        root = resolve_path(root_dir)
        it = self.scan(root, **scan_kw)  # type: ignore[attr-defined]
        items: list[Path] = []
        for p in it:
            items.append(p)
            if limit is not None and len(items) >= limit:
                break
        if unique:
            seen: set[Path] = set()
            items = [p for p in items if not (p in seen or seen.add(p))]
        if sort:
            items.sort()
        return items

    def first(self, root_dir: Path | str, /, **scan_kw) -> Path | None:
        return next(self.scan(resolve_path(root_dir), **scan_kw), None)  # type: ignore[attr-defined]

    def any(self, root_dir: Path | str, /) -> bool:
        return self.first(root_dir) is not None

    def count(self, root_dir: Path | str, /, *, limit: int | None=None, **scan_kw) -> int:
        n = 0
        for _ in self.scan(resolve_path(root_dir), **scan_kw):  # type: ignore[attr-defined]
            n += 1
            if limit is not None and n >= limit:
                break
        return n

    def batched(self, root_dir: Path | str, /, *, size: int, **scan_kw) -> Iterator[list[Path]]:
        batch: list[Path] = []
        for p in self.scan(resolve_path(root_dir), **scan_kw):  # type: ignore[attr-defined]
            batch.append(p)
            if len(batch) >= size:
                yield batch
                batch = []
        if batch:
            yield batch 