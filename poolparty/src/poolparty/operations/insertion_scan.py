"""InsertionScan - insert sequences into background at scanning positions."""
from ..types import Union, ModeType, Optional, Integral, Real, PositionsType, beartype
from ..seq_utils import validate_positions
from ..pool import Pool


@beartype
def insertion_scan(
    bg_pool: Union[Pool, str],
    ins_pool: Union[Pool, str],
    positions: PositionsType = None,
    min_spacing: Optional[Integral] = None,
    max_spacing: Optional[Integral] = None,
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
        Positions to consider for the start of the insertion (0-based, inclusive). If None, all valid positions are considered.
    min_spacing : Optional[Integral], default=None
        Minimum spacing required between breakpoints (not commonly used for single insertions).
    max_spacing : Optional[Integral], default=None
        Maximum spacing allowed between breakpoints (not commonly used for single insertions).
    mode : ModeType, default='random'
        Selection mode for insert positions: 'random', 'sequential', or 'hybrid'.
    num_hybrid_states : Optional[Integral], default=None
        Number of pool states when using 'hybrid' mode (ignored by other modes).
    spacer_str : str, default=''
        String to insert as a spacer between pool segments (optional, placed between left, insert, and right).
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
        A Pool yielding sequences where the insert is placed at the selected position(s) in the background.
    """
    from .from_seq import from_seq
    from .join import join
    from .breakpoint_scan import breakpoint_scan

    # Convert string inputs to pools if needed
    bg_pool = from_seq(bg_pool) if isinstance(bg_pool, str) else bg_pool
    ins_pool = from_seq(ins_pool) if isinstance(ins_pool, str) else ins_pool

    # Validate that both pools have defined seq_length
    bg_length = bg_pool.seq_length
    ins_length = ins_pool.seq_length
    if bg_length is None:
        raise ValueError("bg_pool must have a defined seq_length")
    if ins_length is None:
        raise ValueError("ins_pool must have a defined seq_length")

    # Validate positions (valid range: 0 to bg_length inclusive)
    validated_positions = validate_positions(positions, max_position=bg_length, min_position=0)

    # Split background at breakpoint positions
    left, right = breakpoint_scan(
        pool=bg_pool,
        num_breakpoints=1,
        positions=validated_positions,
        min_spacing=min_spacing,
        max_spacing=max_spacing,
        mode=mode,
        num_hybrid_states=num_hybrid_states,
        op_iter_order=op_iter_order,
    )

    # Join left, insert, and right (no clipping - insert is added)
    result = join(
        [left, ins_pool, right],
        spacer_str=spacer_str,
        name=name,
        op_name=op_name,
        iter_order=iter_order,
        op_iter_order=op_iter_order,
    )
    return result
