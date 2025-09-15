"""Miscellaneous utilities"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar, Callable, Any, cast
import functools
import warnings

T = TypeVar("T")

def ensure_seq(obj: T | Sequence[T]) -> Sequence[T]:
    if isinstance(obj, str):
        return cast(Sequence[T], [obj])
    if isinstance(obj, Sequence):
        return obj
    return cast(Sequence[T], [obj])

def deprecated_class(
    new_name: str, 
    remove_in: str | None = None,
) -> Callable[[type[T]], type[T]]:
    """
    Mark a class as deprecated. Emits a DeprecationWarning on instantiation.
    """
    def decorator(cls: type[T]) -> type[T]:
        orig_init = cls.__init__

        @functools.wraps(orig_init)
        def new_init(self, *args: Any, **kwargs: Any):
            msg = f"Class '{cls.__name__}' is deprecated; use '{new_name}' instead."
            if remove_in:
                msg += f" Support will be removed in v{remove_in}."
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return orig_init(self, *args, **kwargs)

        cls.__init__ = cast(Any, new_init)
        return cls
    return decorator

def deprecated_alias(
    *, 
    old: str, 
    new: str, 
    since: str, 
    remove_in: str,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Shim a deprecated keyword argument to a new name.
    - Warns if `old` is used.
    - Does NOT overwrite `new` if both are provided.
    """
    def deco(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if old in kwargs:
                if new in kwargs:
                    warnings.warn(
                        f"Ignoring deprecated '{old}' because '{new}' is also provided. "
                        f"'{old}' has been deprecated since {since} and will be removed in {remove_in}.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    kwargs.pop(old, None)
                else:
                    warnings.warn(
                        f"Argument '{old}' is deprecated since {since}; use '{new}'. "
                        f"Will be removed in {remove_in}.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    kwargs[new] = kwargs.pop(old)
            return fn(*args, **kwargs)
        return wrapper
    return deco