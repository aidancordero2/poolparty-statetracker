"""ProductOp - Cartesian product of N counters."""
from ..imports import beartype, Sequence, Optional, math, Integral, Counter_type
from ..operation import Operation


def ordered_product(counters:Sequence[Counter_type], name:Optional[str]=None):
    """
    Create a product Counter from the provided counters, removing duplicates and 
    automatically imposing an order based on counter.iter_order and counter.id.

    Parameters
    ----------
    counters : Sequence[Counter_type]
        Sequence of parent Counters to combine into the product. Duplicates are removed 
        and order is determined by (iter_order, id).
    name : Optional[str], default=None
        Name for the resulting product Counter.

    Returns
    -------
    Counter_type
        A Counter representing the ordered, uniquified cartesian product of the input counters.
    """
    from ..counter import Counter
    if len(counters) == 0:
        result = Counter(1, name=name)
    else:
        unique_counters = list(set(counters))
        ordered_counters = sorted(unique_counters,key=lambda c: (c._iter_order, c._id))
        result = Counter(_parents=ordered_counters, _op=ProductOp(), name=name)
    return result

@beartype
def product(counters:Sequence[Counter_type], name:Optional[str]=None):
    """
    Create a Counter representing the cartesian product of the provided Counters.

    Parameters
    ----------
    counters : Sequence[Counter_type]
        Sequence of parent Counters to combine into a product Counter. No duplicates allowed.
    name : Optional[str], default=None
        Optional name for the resulting product Counter.

    Returns
    -------
    Counter_type
        A Counter whose states index the cartesian product of the input counters' states.
    """
    from ..counter import Counter
    if len(counters) != len(set(counters)):
        raise ValueError(f"product() does not allow duplicate counters")
    if len(counters) == 0:
        result = Counter(1, name=name)
    else:
        result = Counter(_parents=counters, _op=ProductOp(), name=name)
    return result


@beartype
class ProductOp(Operation):
    """Cartesian product of N counters."""
    def compute_num_states(self, parent_num_states:Sequence[Integral]):
        return math.prod(parent_num_states)
    
    def decompose(self, state, parent_num_states):
        if state is None:
            return tuple(None for _ in parent_num_states)
        result = []
        for n in parent_num_states:
            result.append(state % n)
            state //= n
        return tuple(result)