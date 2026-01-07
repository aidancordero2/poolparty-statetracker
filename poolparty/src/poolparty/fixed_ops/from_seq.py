"""FromSeq operation - create a pool from a single sequence."""
from numbers import Real
from ..types import Pool_type, Union, Optional, RegionType, beartype
from ..pool import Pool


@beartype
def from_seq(
    seq: str,
    bg_pool: Optional[Union[Pool, str]] = None,
    region: RegionType = None,
    remove_marker: Optional[bool] = None,
    op_name: Optional[str] = None,
    name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool_type:
    """
    Create a Pool containing a single, fixed sequence.

    If bg_pool and region are provided, the sequence replaces the region content
    in bg_pool. Otherwise, creates a standalone pool with the sequence.

    Parameters
    ----------
    seq : str
        The sequence to include in the pool (or to insert at region).
    bg_pool : Optional[Union[Pool, str]], default=None
        Background pool or sequence. If provided with region, seq replaces the region.
    region : RegionType, default=None
        Region to replace in bg_pool. Can be marker name (str) or [start, stop].
    remove_marker : Optional[bool], default=None
        If True and region is a marker name, remove marker tags from output.

    Returns
    -------
    Pool_type
        A Pool object yielding the provided sequence (or bg_pool with region replaced).
    """
    from ..party import get_active_party
    from ..marker_ops.parsing import _validate_markers
    from .fixed import fixed_operation
    
    party = get_active_party()
    if party is None:
        raise RuntimeError(
            "from_seq requires an active Party context. "
            "Use 'with pp.Party() as party:' to create one."
        )
    
    # Validate and register any markers in the sequence
    markers = _validate_markers(seq)
    seq_length = party._alphabet.get_length_without_markers(seq)
    
    # If bg_pool and region provided, replace region content with seq
    if bg_pool is not None:
        if region is None:
            raise ValueError("region is required when bg_pool is provided")
        
        pool = fixed_operation(
            parent_pools=[bg_pool],
            seq_from_seqs_fn=lambda _: seq,
            seq_length_from_pool_lengths_fn=lambda _: seq_length,
            region=region,
            remove_marker=remove_marker,
            name=name,
            op_name=op_name,
            iter_order=iter_order,
            op_iter_order=op_iter_order,
            _factory_name='from_seq',
        )
    else:
        # Standalone pool with just the sequence
        pool = fixed_operation(
            parent_pools=[],
            seq_from_seqs_fn=lambda _: seq,
            seq_length_from_pool_lengths_fn=lambda _: seq_length,
            name=name,
            op_name=op_name,
            iter_order=iter_order,
            op_iter_order=op_iter_order,
            _factory_name='from_seq',
        )
    
    # Add validated markers to the pool
    for marker in markers:
        pool.add_marker(marker)
    
    return pool