"""Interface-like mixin for any object that can apply filters to a filepath"""

from __future__ import annotations

__all__ = [
    "Filterable",
    "FilterableMixin",
]

from typing import Protocol, runtime_checkable
from collections.abc import Sequence
from pathlib import Path

from nifti_finder.filters.base import Filter, Logic
from nifti_finder.filters.compose import ComposeFilter
from nifti_finder.utils import ensure_seq


@runtime_checkable
class Filterable(Protocol):
    """Protocol for any object that can apply filters to a filepath."""
    def filters(self) -> tuple[Filter, ...]: ...
    def add_filters(self, filters: Filter | Sequence[Filter]) -> None: ...
    def remove_filters(self, filters: Filter | Sequence[Filter]) -> None: ...
    def clear_filters(self) -> None: ...
    def apply_filters(self, filepath: Path, /) -> bool: ...


class FilterableMixin:
    """
    Concrete implementation of the `Filterable` protocol.

    Drop-in mixin for any object that can apply filters to a filepath.

    Can pass a single filter, a sequence of filters, or a mix of both, which get
    applied as a cached composed filter, with 'AND' or 'OR' logic.

    Example use-case to make a class filterable with 'AND' combination logic:
    ```python
    >>> class MyObject(FilterableMixin):
    ...     def __init__(self, filters: Filter | Sequence[Filter] | None = None, logic: Logic | str = Logic.AND):
    ...         super().__init__(filters, logic)
    ...     def apply_filters(self, filepath: Path | str, /) -> bool:
    ...         return self._composed(filepath)

    >>> my_object = MyObject()
    >>> my_object.add_filters([IncludeExtension("nii.gz")])
    >>> my_object.apply_filters("path/to/file.nii.gz")
    True
    ```
    """
    __slots__ = ("_filters", "_logic", "_composed")

    def __init__(
        self, 
        filters: Filter | Sequence[Filter] | None = None,
        logic: Logic | str = Logic.AND
    ):
        """
        Args:
            filters (Filter | Sequence[Filter], optional): Filters to apply. Defaults to None.
            logic (Logic | str): Logic to apply to the filters. Defaults to 'AND'.
        """
        self._filters: list[Filter] = []
        self._logic = logic
        if filters is not None:
            self.add_filters(filters)
        self._rebuild_composed()

    @property
    def filters(self) -> tuple[Filter, ...]:
        return tuple(self._filters)

    def add_filters(self, filters: Filter | Sequence[Filter], /) -> None:
        seq = list(ensure_seq(filters))
        self._filters.extend(seq)
        self._rebuild_composed()
    
    def remove_filters(
        self, 
        which: Filter | int | Sequence[Filter | int],
        /
    ) -> None:
        """
        Remove filters from the object.

        Can remove a single filter, a sequence of filters, or a mix of both, either by index or instance.

        Args:
            which (Filter | int | Sequence[Filter | int]): Filters to remove.
        """
        seq = tuple(ensure_seq(which))
        for f in seq:
            if isinstance(f, int):
                self._filters.pop(f)
            elif isinstance(f, Filter):
                try:
                    self._filters.remove(f)
                except ValueError:
                    continue
            else:
                raise TypeError(f"Invalid entry in `which`: expected Filter or int, "
                                f"got {type(f).__name__}")
        self._rebuild_composed()

    def clear_filters(self) -> None:
        self._filters.clear()
        self._rebuild_composed()

    def apply_filters(self, filepath: Path | str, /) -> bool:
        return self._composed(filepath)

    def _rebuild_composed(self) -> None:
        self._composed = ComposeFilter(self._filters, self._logic)