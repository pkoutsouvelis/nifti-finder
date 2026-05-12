"""Utility functions for creating filters."""

from __future__ import annotations

from typing import Any
import re

__all__ = [
    "parse_scalar",
]


def parse_scalar(v: Any) -> Any:
    """Parse a scalar value from a table cell into a boolean, integer, float, or string.

    Args:
        v: The value to parse.

    Returns:
        The parsed value.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v
    if v is None:
        return None
    s = str(v).strip()
    low = s.lower()
    # booleans
    if low in {"true", "yes", "y", "1"}:
        return True
    if low in {"false", "no", "n", "0"}:
        return False
    # ints
    if re.fullmatch(r"[+-]?\d+", s):
        try:
            return int(s)
        except Exception:
            pass
    # floats
    if re.fullmatch(r"[+-]?\d*\.\d+(e[+-]?\d+)?", s, re.IGNORECASE) or re.fullmatch(
        r"[+-]?\d+e[+-]?\d+", s, re.IGNORECASE
    ):
        try:
            return float(s)
        except Exception:
            pass
    # fallback: case-insensitive string
    return low
