"""Centralized type definitions for poolparty."""
from typing import TypeAlias, Literal, Union, Optional
from collections.abc import Sequence, Callable
from beartype import beartype
from numbers import Real, Integral
from beartype.roar import BeartypeCallHintParamViolation

import math
import numpy
import pandas

Counter_type: TypeAlias = "statecounter.counter.Counter"
Operation_type: TypeAlias = "statecounter.operation.Operation"

__all__ = [
    'beartype',
    'Union',
    'Optional', 
    'Sequence',
    'Callable',
    'Literal',
    'Real',
    'Integral',
    'Counter_type',
    'Operation_type',
    'math',
]
