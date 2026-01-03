"""Subsequence scan operation - extract subsequences at scanning positions."""
from numbers import Integral, Real

from ..types import Union, Literal, ModeType, Optional, PositionsType, beartype
from ..seq_utils import validate_positions
from ..pool import Pool


@beartype
def subseq_scan(
    pool: Union[Pool, str],
    seq_length: Integral,
    positions: PositionsType = None,
    strand: Literal['+', '-', 'both'] = '+',
    mode: ModeType = 'random',
    num_hybrid_states: Optional[Integral] = None,
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool:
    """
    Extract subsequences of a specified length at scanning positions.

    Scans a marker across the pool and extracts the marked content,
    returning subsequences at each valid position.

    Parameters
    ----------
    pool : Pool or str
        Source pool or sequence string to extract subsequences from.
    seq_length : Integral
        Length of subsequence to extract at each position.
    positions : PositionsType, default=None
        Positions to consider for the start of extraction (0-based).
        If None, all valid positions are used.
    strand : Literal['+', '-', 'both'], default='+'
        Strand for extraction: '+', '-', or 'both'.
        If '-', content is reverse-complemented.
        If 'both', creates 2x states scanning both strands.
    mode : ModeType, default='random'
        Position selection mode: 'random', 'sequential', or 'hybrid'.
    num_hybrid_states : Optional[Integral], default=None
        Number of pool states when using 'hybrid' mode (ignored by other modes).
    name : Optional[str], default=None
        Name for the resulting Pool.
    op_name : Optional[str], default=None
        Name for the underlying Operation.
    iter_order : Optional[Real], default=None
        Iteration order priority for the resulting Pool.
    op_iter_order : Optional[Real], default=None
        Iteration order priority for the underlying Operation.

    Returns
    -------
    Pool
        A Pool yielding subsequences extracted at each allowed position.
    """
    from ..fixed_ops.from_seq import from_seq
    from ..marker_ops import marker_scan, extract_marker_content

    # Convert string input to pool if needed
    pool = from_seq(pool) if isinstance(pool, str) else pool

    # Validate pool has defined seq_length
    pool_length = pool.seq_length
    if pool_length is None:
        raise ValueError("pool must have a defined seq_length")

    # Validate seq_length
    if seq_length <= 0:
        raise ValueError(f"seq_length must be > 0, got {seq_length}")
    if seq_length > pool_length:
        raise ValueError(
            f"seq_length ({seq_length}) must be <= pool.seq_length ({pool_length})"
        )

    # Calculate max position for marker placement
    marker_name = '_subseq'
    marker_length = int(seq_length)
    max_position = pool_length - seq_length

    # Validate positions
    validated_positions = validate_positions(positions, max_position, min_position=0)

    # 1. Scan marker across pool at specified positions
    marked = marker_scan(
        pool,
        marker=marker_name,
        marker_length=marker_length,
        positions=validated_positions,
        strand=strand,
        mode=mode,
        num_hybrid_states=num_hybrid_states,
        op_name=op_name,
        op_iter_order=op_iter_order,
    )

    # 2. Extract marker content as the result
    result = extract_marker_content(
        marked,
        marker_name,
        name=name,
        op_name=op_name,
        iter_order=iter_order,
        op_iter_order=op_iter_order,
    )

    return result
