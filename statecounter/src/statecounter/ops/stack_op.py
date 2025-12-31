"""StackOp - Disjoint union of N counters."""
from ..imports import beartype, Sequence, Optional, Counter_type
from ..operation import Operation


@beartype
def stack(counters: Sequence[Counter_type], name: Optional[str] = None):
    """
    Create a Counter representing the disjoint union of the provided Counters.

    Parameters
    ----------
    counters : Sequence[Counter_type]
        Sequence of parent Counters to combine into a disjoint union Counter.
    name : Optional[str], default=None
        Optional name for the resulting disjoint union Counter.

    Returns
    -------
    Counter_type
        A Counter whose states correspond to the disjoint union of the input Counters' states.
    """
    from ..counter import Counter
    if len(counters) == 0:
        result = Counter(0)
    else:
        result = Counter(_parents=counters, _op=StackOp(), name=name)
    return result


@beartype
class StackOp(Operation):    
    def compute_num_states(self, parent_num_states):
        return sum(parent_num_states)
    
    def decompose(self, state, parent_num_states):
        if state is None:
            return tuple(None for _ in parent_num_states)
        cumsum = 0
        for i, n in enumerate(parent_num_states):
            if state < cumsum + n:
                return tuple(
                    state - cumsum if j == i else None
                    for j in range(len(parent_num_states))
                )
            cumsum += n
        raise ValueError(f"Invalid state {state}")
