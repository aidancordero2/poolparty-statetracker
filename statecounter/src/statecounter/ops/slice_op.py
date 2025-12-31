"""SliceOp - Slice a counter to select a subset of states."""
from ..imports import beartype, Optional, Integral, Counter_type
from ..operation import Operation
import builtins


@beartype
def slice(counter: Counter_type, start: Optional[Integral] = None, stop: Optional[Integral] = None, step: Optional[Integral] = None, name: Optional[str] = None):
    """
    Create a Counter whose states correspond to a slice of the parent Counter.

    Parameters
    ----------
    counter : Counter_type
        The Counter to be sliced.
    start : Optional[Integral], default=None
        Start index of the slice (inclusive).
    stop : Optional[Integral], default=None
        Stop index of the slice (exclusive).
    step : Optional[Integral], default=None
        Step size for the slice.
    name : Optional[str], default=None
        Name for the resulting sliced Counter.

    Returns
    -------
    Counter_type
        A Counter whose states correspond to the specified slice of the parent Counter's states.
    """
    from ..counter import Counter
    s = builtins.slice(start, stop, step)
    start_norm, stop_norm, step_norm = s.indices(counter.num_states)
    result = Counter(_parents=(counter,), _op=SliceOp(start_norm, stop_norm, step_norm), name=name)
    return result


@beartype
class SliceOp(Operation):
    """Slice a counter to select a subset of states."""
    
    def __init__(self, start: Integral, stop: Integral, step: Integral):
        self.start = start
        self.stop = stop
        self.step = step
    
    def compute_num_states(self, parent_num_states):
        return len(range(self.start, self.stop, self.step))
    
    def decompose(self, state, parent_num_states):
        if state is None:
            return (None,)
        parent_state = self.start + (state * self.step)
        return (parent_state,)
