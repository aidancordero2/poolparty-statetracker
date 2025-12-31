"""SynchronizeOp - Keep N counters in lockstep."""
from ..imports import beartype, Sequence, Optional, Counter_type
from ..operation import Operation


@beartype
def sync(counters: Sequence[Counter_type], name: Optional[str] = None):
    """
    Create a Counter that synchronizes the states of multiple parent Counters.

    Parameters
    ----------
    counters : Sequence[Counter_type]
        Sequence of parent Counters to synchronize.
    name : Optional[str], default=None
        Optional name for the resulting synchronized Counter.

    Returns
    -------
    Counter_type
        A Counter whose states are the same as all parent Counters' states.
    """
    from ..counter import Counter
    if len(counters) == 0:
        result = Counter(1)
    else:
        result = Counter(_parents=counters, _op=SyncOp(), name=name)
    return result


@beartype
class SyncOp(Operation):
    """Keep N counters in lockstep."""
    
    def compute_num_states(self, parent_num_states):
        if len(parent_num_states) == 0:
            return 1
        if len(set(parent_num_states)) != 1:
            raise ValueError(
                f"Cannot sync counters with different num_states: {parent_num_states}"
            )
        return parent_num_states[0]
    
    def decompose(self, state, parent_num_states):
        return tuple(state for _ in parent_num_states)
