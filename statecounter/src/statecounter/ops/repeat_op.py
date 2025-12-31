"""RepeatOp - Repeat a single counter N times."""
from ..imports import beartype, Optional, Integral, Counter_type
from ..operation import Operation


@beartype
def repeat(counter: Counter_type, times: Integral, name: Optional[str] = None):
    """
    Create a Counter that repeats the states of another Counter a specified number of times.

    Parameters
    ----------
    counter : Counter_type
        The Counter to repeat.
    times : Integral
        Number of times to repeat the entire sequence of the parent's states.
    name : Optional[str], default=None
        Name for the resulting repeated Counter.

    Returns
    -------
    Counter_type
        A Counter whose states iterate through the parent's states, repeated the specified number of times.
    """
    from ..counter import Counter
    if times < 1:
        raise ValueError("times must be at least 1")    
    result = Counter(_parents=(counter,), _op=RepeatOp(times), name=name)
    return result


@beartype
class RepeatOp(Operation):
    """Repeat a single counter N times."""
    
    def __init__(self, times: Integral):
        self.times = times
    
    def compute_num_states(self, parent_num_states):
        return parent_num_states[0] * self.times
    
    def decompose(self, state, parent_num_states):
        if state is None:
            return (None,)
        return (state % parent_num_states[0],)
