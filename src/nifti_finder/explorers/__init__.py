from __future__ import annotations

__all__ = [
    "FileExplorer",
    "MaterializeMixin",
    "BasicFileExplorer",
    "TwoStageFileExplorer",
    "AllPurposeFileExplorer",
    "NeuroExplorer",
    # Backward compatibility
    "NiftiExplorer",
]

from .base import *
from .core import *
from .mixins import *

from nifti_finder.utils.misc import deprecated_class, deprecated_alias


@deprecated_class("NeuroExplorer", "1.2.0")
class NiftiExplorer(NeuroExplorer):
    """
    Deprecated alias for NeuroExplorer.
    """
    @deprecated_alias(old="stage_1_pattern", new="outer", since="1.1.0", remove_in="1.2.0")
    @deprecated_alias(old="stage_2_pattern", new="inner", since="1.1.0", remove_in="1.2.0")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)