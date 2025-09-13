"""Miscellaneous utilities"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar, cast

T = TypeVar("T")

def ensure_seq(obj: T | Sequence[T]) -> Sequence[T]:
    if isinstance(obj, str):
        return cast(Sequence[T], [obj])
    if isinstance(obj, Sequence):
        return obj
    return cast(Sequence[T], [obj])