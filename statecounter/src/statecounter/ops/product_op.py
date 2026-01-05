"""ProductOp - Cartesian product of N counters."""
from ..imports import beartype, Sequence, Optional, math, Integral, Counter_type, Literal
from ..operation import Operation

# Module-level flag for product ordering mode
_product_order_mode: str = 'first_counter_slowest'

def set_product_order_mode(mode: Literal['first_counter_fastest', 'first_counter_slowest']) -> None:
    """Set the global ordering mode for ordered_product()."""
    global _product_order_mode
    if mode not in ('first_counter_fastest', 'first_counter_slowest'):
        raise ValueError(f"mode must be 'first_counter_fastest' or 'first_counter_slowest', got {mode!r}")
    _product_order_mode = mode

def get_product_order_mode() -> str:
    """Get the current global ordering mode for ordered_product()."""
    return _product_order_mode


def _collect_product_bases(counter: Counter_type) -> list:
    """
    Recursively collect base counters, flattening through ProductOp only.
    
    This enables proper deduplication when the same counter appears at different
    levels of a nested product hierarchy (diamond pattern).
    
    Parameters
    ----------
    counter : Counter_type
        A counter to collect bases from.
    
    Returns
    -------
    list
        List of base counters. For ProductOp counters, this recursively collects
        from parents. For leaf counters or non-product operations, returns [counter].
    """
    if not counter._parents:
        # Leaf counter (no parents)
        return [counter]
    elif isinstance(counter._op, ProductOp):
        # Product counter - recurse into parents
        bases = []
        for parent in counter._parents:
            bases.extend(_collect_product_bases(parent))
        return bases
    else:
        # Other operation (stack, slice, etc.) - treat as atomic
        return [counter]


def ordered_product(counters:Sequence[Counter_type], name:Optional[str]=None):
    """
    Create a product Counter from the provided counters, removing duplicates and 
    automatically imposing an order based on counter.iter_order and counter.id.
    
    This function recursively flattens nested product counters before deduplication,
    which handles diamond patterns where the same counter appears both as a direct
    parent and as an ancestor through another parent.

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
    
    Notes
    -----
    Product is associative, so nested products are flattened:
    ``ordered_product([A*B, C, D*A])`` becomes ``ordered_product([A, B, C, D])``
    
    Non-product operations (like stack, slice) are NOT flattened:
    ``ordered_product([stack(A,B), C])`` keeps ``stack(A,B)`` as an atomic unit.
    """
    from ..counter import Counter
    if len(counters) == 0:
        return Counter(1, name=name)
    
    # Recursively collect bases, flattening through ProductOp only
    base_counters = []
    for c in counters:
        base_counters.extend(_collect_product_bases(c))
    
    # Deduplicate and order
    unique_counters = list(set(base_counters))
    id_sign = -1 if _product_order_mode == 'first_counter_slowest' else 1
    ordered_counters = sorted(unique_counters, key=lambda c: (c._iter_order, id_sign * c._id))
    
    return Counter(_parents=ordered_counters, _op=ProductOp(), name=name)

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