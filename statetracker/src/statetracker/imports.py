"""Centralized type definitions for poolparty."""

import math
from collections.abc import Callable, Sequence
from numbers import Integral, Real
from typing import Literal, Optional, TypeAlias, Union

from beartype import beartype

State_type: TypeAlias = "statetracker.state.State"
Operation_type: TypeAlias = "statetracker.operation.Operation"

__all__ = [
    "beartype",
    "Union",
    "Optional",
    "Sequence",
    "Callable",
    "Literal",
    "Real",
    "Integral",
    "State_type",
    "Operation_type",
    "math",
]
