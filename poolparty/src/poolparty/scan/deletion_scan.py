"""Deletion scan operation - delete a segment at scanning positions."""
from numbers import Integral, Real

from ..types import Union, ModeType, Optional, PositionsType, beartype
from ..seq_utils import validate_positions
from ..pool import Pool


@beartype
def deletion_scan(
    bg_pool: Union[Pool, str],
    deletion_length: Integral,
    deletion_marker: Optional[str] = '-',
    spacer_str: str = '',
    positions: PositionsType = None,
    min_spacing: Optional[Integral] = None,
    max_spacing: Optional[Integral] = None,
    mode: ModeType = 'random',
    num_hybrid_states: Optional[Integral] = None,
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool:
    """
    Scan a pool for all possible single deletions of a fixed length.

    Parameters
    ----------
    bg_pool : Pool or str
        Source pool or sequence string to delete from.
    deletion_length : Integral
        Number of characters to delete at each valid position.
    deletion_marker : Optional[str], default='-'
        String to insert at the deletion site (i.e., a gap marker). If None, deleted
        segment is removed with no marker.
    spacer_str : str, default=''
        String to insert as a spacer between pool segments after deletion.
    positions : PositionsType, default=None
        Positions to consider for the start of the deletion (0-based).
        If None, all valid positions are used.
    min_spacing : Optional[Integral], default=None
        Not supported. Raises ValueError if provided.
    max_spacing : Optional[Integral], default=None
        Not supported. Raises ValueError if provided.
    mode : ModeType, default='random'
        Deletion mode: 'random', 'sequential', or 'hybrid'.
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
        A Pool yielding sequences where a segment of the specified length is removed
        from the source at each allowed position, optionally with a marker inserted.
    """
    from ..operations.from_seq import from_seq
    from ..operations.join import join
    from ..markers import marker_scan, replace_marker_content

    # Validate min_spacing/max_spacing not supported
    if min_spacing is not None or max_spacing is not None:
        raise ValueError(
            "min_spacing and max_spacing are not supported in the marker-based "
            "implementation of deletion_scan. Use breakpoint_scan directly if needed."
        )

    # Convert string inputs to pools if needed
    bg_pool = from_seq(bg_pool) if isinstance(bg_pool, str) else bg_pool

    # Validate bg_pool has defined seq_length
    bg_length = bg_pool.seq_length
    if bg_length is None:
        raise ValueError("bg_pool must have a defined seq_length")

    # Validate deletion_length
    if deletion_length <= 0:
        raise ValueError(f"del_length must be > 0, got {deletion_length}")
    if deletion_length >= bg_length:
        raise ValueError(
            f"del_length ({deletion_length}) must be < bg_pool.seq_length ({bg_length})"
        )

    # Map old API: deletion_marker='-' -> mark_changes=True, del_char='-'
    #              deletion_marker=None -> mark_changes=False
    mark_changes = deletion_marker is not None
    del_char = deletion_marker if deletion_marker else '-'

    # For deletion: marker_length=del_length, max_position=bg_length - del_length
    marker_name = '_del'
    marker_length = int(deletion_length)
    max_position = bg_length - deletion_length

    # Validate positions
    validated_positions = validate_positions(positions, max_position, min_position=0)

    # 1. Insert marker at scanning positions
    marked = marker_scan(
        bg_pool,
        marker=marker_name,
        marker_length=marker_length,
        positions=validated_positions,
        mode=mode,
        num_hybrid_states=num_hybrid_states,
        op_name=op_name,
        op_iter_order=op_iter_order,
    )

    # 2. Build replacement content based on mark_changes
    if mark_changes:
        # Fill gap with del_char * del_length
        marker_str = del_char * marker_length
        content = from_seq(marker_str)
        # Wrap with spacers if needed
        if spacer_str:
            content = join([from_seq(spacer_str), content, from_seq(spacer_str)])
    else:
        # Simply remove the segment - just use spacer_str once (or empty)
        content = from_seq(spacer_str)

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
