"""Multiscan operations - operations that use marker_multiscan() to operate on multiple positions."""

from .deletion_multiscan import deletion_multiscan
from .replacement_multiscan import replacement_multiscan

__all__ = [
    'deletion_multiscan',
    'replacement_multiscan',
]
