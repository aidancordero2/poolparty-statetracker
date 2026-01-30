"""synced_to - Create or pair synced states."""

from ..imports import Integral, Optional, State_type, beartype


@beartype
def synced_to(
    child_state: State_type, name: Optional[str] = None, num_values: Optional[Integral] = None
) -> State_type:
    """Create a new state synchronized with child_state.

    Args:
        child_state: The state to synchronize with.
        name: Optional name for the new state.
        num_values: Optional number of values for the new state.
            If not provided, uses child_state.num_values.
            Can be different from child_state.num_values - the group
            will track the max and states receive None when out of range.

    Returns:
        A new State synchronized with child_state.
    """
    from ..state import State

    nv = num_values if num_values is not None else child_state.num_values
    synced = State(num_values=nv, name=name)
    synced.sync_with(child_state)
    # Set iter_order to minimum in the sync group (ensures earliest iteration priority)
    min_iter_order = min(s.iter_order for s in synced._synced_group._states)
    synced.iter_order = min_iter_order
    return synced


@beartype
def sync(a: State_type, b: State_type) -> None:
    """Synchronize two existing states (bidirectional)."""
    a.sync_with(b)
