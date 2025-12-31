"""InterleaveOp - Interleave states from N counters."""
from ..imports import beartype, Sequence, Optional, Counter_type
from ..operation import Operation


@beartype
def interleave(counters: Sequence[Counter_type], name: Optional[str] = None):
    """
    Create a Counter that interleaves the states from multiple Counter objects.

    Parameters
    ----------
    counters : Sequence[Counter_type]
        Sequence of Counter instances to interleave, each with equal num_states.
    name : Optional[str], default=None
        Optional name for the resulting interleaved Counter.

    Returns
    -------
    Counter_type
        A Counter whose states interleave across the provided counters.
    """
    from ..counter import Counter
    if len(counters) < 2:
        raise ValueError("interleave() requires at least 2 counters")
    return Counter(_parents=counters, _op=InterleaveOp(), name=name)


@beartype
class InterleaveOp(Operation):
    """Interleave states from N counters with equal num_states."""
    
    def compute_num_states(self, parent_num_states):
        if len(set(parent_num_states)) != 1:
            raise ValueError(
                f"Cannot interleave counters with different num_states: {parent_num_states}"
            )
        return parent_num_states[0] * len(parent_num_states)
    
    def decompose(self, state, parent_num_states):
        if state is None:
            return tuple(None for _ in parent_num_states)
        k = len(parent_num_states)
        active_idx = state % k
        parent_state = state // k
        return tuple(parent_state if i == active_idx else None for i in range(k))
