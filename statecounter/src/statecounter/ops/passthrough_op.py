"""PassthroughOp - Pass through a single parent counter unchanged."""
from ..imports import beartype, Optional, Counter_type
from ..operation import Operation


@beartype
def passthrough(counter: Counter_type, name: Optional[str] = None):
    """
    Create a Counter that passes through its parent's states unchanged.

    Parameters
    ----------
    counter : Counter_type
        Parent Counter whose states will be tracked.
    name : Optional[str], default=None
        Optional name for the resulting passthrough Counter.

    Returns
    -------
    Counter_type
        A Counter that mirrors the states of its parent.
    """
    from ..counter import Counter
    result = Counter(_parents=(counter,), _op=PassthroughOp(), name=name)
    return result


@beartype
class PassthroughOp(Operation):
    """Pass through a single parent counter unchanged."""
    
    def compute_num_states(self, parent_num_states):
        return parent_num_states[0]
    
    def decompose(self, state, parent_num_states):
        return (state,)
