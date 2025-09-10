"""Path and filesystem helpers"""

from __future__ import annotations

from typing import TypeAlias
from pathlib import Path

FilePath: TypeAlias = str | Path

def resolve_path(path: FilePath) -> Path:
    """Expand user and resolve path."""
    return Path(path).expanduser().resolve()

def get_ext(path: FilePath) -> str:
    """Get file extension from filepath with leading dot."""
    p = Path(path)
    suffixes = p.suffixes                    
    full_ext = ''.join(suffixes)              
    return full_ext