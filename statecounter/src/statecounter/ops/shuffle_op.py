"""ShuffleOp - Randomly shuffle counter states given a seed."""
from ..imports import beartype, Optional, Integral, Sequence, Counter_type
from ..operation import Operation
import random


@beartype
def shuffle(
    counter: Counter_type,
    seed: Optional[Integral] = None,
    permutation: Optional[Sequence[Integral]] = None,
    name: Optional[str] = None,
):
    """
    Create a Counter with the states of a parent Counter randomly shuffled.

    Parameters
    ----------
    counter : Counter_type
        The Counter whose states will be shuffled.
    seed : Optional[Integral], default=None
        Random seed to generate the shuffle permutation. Cannot be provided with 'permutation'.
    permutation : Optional[Sequence[Integral]], default=None
        Explicit permutation of parent state indices, as a sequence of length parent.num_states. Cannot be provided with 'seed'.
    name : Optional[str], default=None
        Name for the resulting shuffled Counter.

    Returns
    -------
    Counter_type
        A Counter whose state order corresponds to a permutation of the parent's states.
    """
    from ..counter import Counter
    result = Counter(
        _parents=(counter,),
        _op=ShuffleOp(counter.num_states, seed=seed, permutation=permutation),
        name=name,
    )
    return result


@beartype
class ShuffleOp(Operation):
    """Randomly shuffle counter states using a deterministic seed."""
    
    def __init__(
        self,
        num_parent_states: Integral,
        seed: Optional[Integral] = None,
        permutation: Optional[Sequence[Integral]] = None,
    ):
        match (seed, permutation):
            case (None, None):
                self.seed = random.randint(0, 2**32 - 1)
                indices = list(range(num_parent_states))
                random.Random(self.seed).shuffle(indices)
                self.permutation = tuple(indices)
            case (_, None):
                self.seed = seed
                indices = list(range(num_parent_states))
                random.Random(seed).shuffle(indices)
                self.permutation = tuple(indices)
            case (None, _):
                if len(permutation) != num_parent_states:
                    raise ValueError(
                        f"permutation has length {len(permutation)}, expected {num_parent_states}."
                    )
                if set(permutation) != set(range(num_parent_states)):
                    raise ValueError(
                        f"permutation must contain exactly the integers 0 to {num_parent_states - 1}."
                    )
                self.seed = None
                self.permutation = tuple(permutation)
            case (_, _):
                raise ValueError("Cannot specify both 'seed' and 'permutation'; they are mutually exclusive.")
    
    def compute_num_states(self, parent_num_states):
        return parent_num_states[0]
    
    def decompose(self, state, parent_num_states):
        if state is None:
            return (None,)
        return (self.permutation[state],)
