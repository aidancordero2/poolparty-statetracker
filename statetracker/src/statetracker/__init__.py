"""StateTracker - Composable states with unidirectional value propagation."""

import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from .manager import Manager
from .operation import Operation
from .ops import (
    InterleaveOp,
    ProductOp,
    RepeatOp,
    SampleOp,
    ShuffleOp,
    SliceOp,
    StackOp,
    get_product_order_mode,
    interleave,
    ordered_product,
    product,
    repeat,
    sample,
    set_product_order_mode,
    shuffle,
    slice,
    split,
    stack,
    sync,
    synced_to,
)
from .state import ConflictingValueAssignmentError, State

__version__ = "0.1.0"

__all__ = [
    "State",
    "Manager",
    "Operation",
    "ConflictingValueAssignmentError",
    "ProductOp",
    "StackOp",
    "SliceOp",
    "RepeatOp",
    "ShuffleOp",
    "SampleOp",
    "InterleaveOp",
    "product",
    "ordered_product",
    "set_product_order_mode",
    "get_product_order_mode",
    "stack",
    "sync",
    "slice",
    "repeat",
    "shuffle",
    "sample",
    "split",
    "interleave",
    "synced_to",
]
