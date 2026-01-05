"""Insertion scan operation - insert a sequence at scanning positions."""
from numbers import Integral, Real

from ..types import Union, ModeType, Optional, PositionsType, beartype
from ..seq_utils import validate_positions
from ..pool import Pool


@beartype
def insertion_scan(
    bg_pool: Union[Pool, str],
    ins_pool: Union[Pool, str],
    positions: PositionsType = None,
    min_spacing: Optional[Integral] = None,
    max_spacing: Optional[Integral] = None,
    seq_name_prefix: Optional[str] = None,
    mode: ModeType = 'random',
    num_hybrid_states: Optional[Integral] = None,
    spacer_str: str = '',
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool:
    """
    Insert a sequence into a background sequence at specified scanning positions.

    Parameters
    ----------
    bg_pool : Pool or str
        The background Pool or sequence string in which to insert.
    ins_pool : Pool or str
        The insert Pool or sequence string to be inserted.
    positions : PositionsType, default=None
        Positions to consider for the start of the insertion (0-based, inclusive).
        If None, all valid positions are considered.
    min_spacing : Optional[Integral], default=None
        Not supported. Raises ValueError if provided.
    max_spacing : Optional[Integral], default=None
        Not supported. Raises ValueError if provided.
    mode : ModeType, default='random'
        Selection mode for insert positions: 'random', 'sequential', or 'hybrid'.
    num_hybrid_states : Optional[Integral], default=None
        Number of pool states when using 'hybrid' mode (ignored by other modes).
    spacer_str : str, default=''
        String to insert as a spacer between pool segments.
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
        A Pool yielding sequences where the insert is placed at the selected position(s)
        in the background.
    """
    from ..fixed_ops.from_seq import from_seq
    from ..fixed_ops.join import join
    from ..marker_ops import marker_scan, replace_marker_content

    # Validate min_spacing/max_spacing not supported
    if min_spacing is not None or max_spacing is not None:
        raise ValueError(
            "min_spacing and max_spacing are not supported in the marker-based "
            "implementation of insertion_scan. Use breakpoint_scan directly if needed."
        )

    # Convert string inputs to pools if needed
    bg_pool = from_seq(bg_pool) if isinstance(bg_pool, str) else bg_pool
    ins_pool = from_seq(ins_pool) if isinstance(ins_pool, str) else ins_pool

    # Validate bg_pool has defined seq_length
    bg_length = bg_pool.seq_length
    if bg_length is None:
        raise ValueError("bg_pool must have a defined seq_length")

    # Validate ins_pool has defined seq_length
    ins_length = ins_pool.seq_length
    if ins_length is None:
        raise ValueError("ins_pool must have a defined seq_length")

    # For insertion: marker_length=0, can insert at any position including after last char
    marker_name = '_ins'
    marker_length = 0
    max_position = bg_length

    # Validate positions
    validated_positions = validate_positions(positions, max_position, min_position=0)

    # 1. Insert marker at scanning positions
    marked = marker_scan(
        bg_pool,
        marker=marker_name,
        marker_length=marker_length,
        positions=validated_positions,
        seq_name_prefix=seq_name_prefix,
        mode=mode,
        num_hybrid_states=num_hybrid_states,
        op_name=op_name,
        op_iter_order=op_iter_order,
    )

    # 2. Build replacement content (ins_pool with optional spacers)
    content = ins_pool
    if spacer_str:
        content = join([from_seq(spacer_str), content, from_seq(spacer_str)])

    # 3. Replace marker with content
    result = replace_marker_content(
        marked,
        content,
        marker_name,
        name=name,
        op_name=op_name,
        iter_order=iter_order,
        op_iter_order=op_iter_order,
    )
    return result
