"""Miscellaneous utilities"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")

def ensure_seq(obj: T | Sequence[T]) -> Sequence[T]:
    return obj if isinstance(obj, Sequence) else [obj]