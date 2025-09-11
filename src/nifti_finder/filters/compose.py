"""Compose multiple filters"""

from __future__ import annotations

__all__ = [
    "ComposeFilter",
]

from collections.abc import Sequence
from pathlib import Path
from dataclasses import dataclass, field

from nifti_finder.filters.base import Filter, Logic


@dataclass(frozen=True, slots=True, init=False)
class ComposeFilter(Filter):
    """
    Compose multiple filters with `AND` or `OR` logic.
    
    Example use-case to support both `.nii.gz` and `.nii` files:
    ```
    >>> filter = ComposeFilter([IncludeExtension("nii.gz"), IncludeExtension("nii")], logic="OR")
    >>> filter(Path("path/to/file.nii.gz"))
    True
    ```

    Args:
        filters: Filters to compose.
        logic: Logic to use to compose the filters.
    """
    filters: tuple[Filter, ...] = field()
    logic: Logic = field()
    
    def __init__(
        self, 
        filters: Filter | Sequence[Filter], 
        logic: Logic | str = Logic.AND
    ):
        if isinstance(filters, Filter):
            filters = (filters,)
        elif isinstance(filters, Sequence):
            filters = tuple(filters)
        else:
            raise TypeError("filters must be Filter or Sequence[Filter]")

        if not all(isinstance(f, Filter) for f in filters):
            bad = [type(f).__name__ for f in filters if not isinstance(f, Filter)]
            raise TypeError(f"All items must be Filter; got: {bad}")

        if isinstance(logic, str):
            try:
                logic = Logic[logic.upper()]
            except KeyError as e:
                raise ValueError("logic must be 'AND' or 'OR'") from e
        elif not isinstance(logic, Logic):
            raise TypeError(f"logic must be Logic or str, got {type(logic).__name__}")

        object.__setattr__(self, "filters", filters)
        object.__setattr__(self, "logic", logic)

    @property
    def _op(self):
        return all if self.logic is Logic.AND else any

    @property
    def _identity(self):
        return True if self.logic is Logic.AND else False
    
    def __call__(self, filepath: Path) -> bool:
        if not self.filters:
            return self._identity
        return self._op(flt(filepath) for flt in self.filters)
    
    def flatten(self) -> ComposeFilter:
        """Return a new ComposeFilter with one-level, same-logic children flattened."""
        flat: list[Filter] = []
        stack: list[Filter] = list(self.filters)
        while stack:
            f = stack.pop()
            if isinstance(f, ComposeFilter) and f.logic is self.logic:
                stack.extend(f.filters)
            else:
                flat.append(f)
        flat.reverse()
        return ComposeFilter(flat, self.logic)
    
    def __len__(self) -> int:
        return len(self.flatten().filters)