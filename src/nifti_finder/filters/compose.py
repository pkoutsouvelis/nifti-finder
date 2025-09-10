"""Compose multiple filters"""

from __future__ import annotations

__all__ = [
    "ComposeFilter",
]

from typing import Callable, Iterable
from collections.abc import Sequence
from enum import Enum
from pathlib import Path

from nifti_finder.filters.base import Filter

class Logic(str, Enum):
    AND = "AND"
    OR = "OR"

class ComposeFilter(Filter):
    """Compose multiple filters with `AND` or `OR` logic."""
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
            raise TypeError(f"`filters` must be a Filter or a Sequence[Filter], got {type(filters).__name__}")
        
        if not all(isinstance(f, Filter) for f in filters):
            bad = [type(f).__name__ for f in filters if not isinstance(f, Filter)]
            raise TypeError(f"All items must be Filter; got: {bad}")
        
        if isinstance(logic, str):
            try:
                logic = Logic[logic.upper()]
            except KeyError as e:
                raise ValueError("logic must be 'AND' or 'OR'") from e
        elif not isinstance(logic, Logic):
            raise TypeError(f"`logic` must be Logic or str, got {type(logic).__name__}")
        
        self._filters: tuple[Filter, ...] = filters
        self._logic: Logic = logic

        self._op: Callable[[Iterable[bool]], bool] = all if self._logic is Logic.AND else any
        self._identity: bool = True

    def __call__(self, filepath: Path) -> bool:
        if not self._filters:
            return self._identity
        return self._op(flt(filepath) for flt in self._filters)

