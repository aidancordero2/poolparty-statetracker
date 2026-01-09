"""Color operation - color regions of text."""
from numbers import Real
from ..types import Pool_type, Union, Optional, RegionType, Literal, beartype
from ..pool import Pool
from ..marker_ops.parsing import transform_nonmarker_chars

code_dict = {
    'red':      '\033[91m',
    'green':    '\033[92m',
    'yellow':   '\033[93m',
    'blue':     '\033[94m',
    'magenta':  '\033[95m',
    'cyan':     '\033[96m',
    'bold':     '\033[1m',
    'underline':'\033[4m',
    'reset':    '\033[0m',
}

@beartype
def color_chars(
    pool: Union[Pool_type, str],
    region: RegionType = None,
    remove_marker: Optional[bool] = None,
    spacer_str: str = '',
    color: Literal['red','green','yellow','blue','magenta','cyan','bold','underline']='red',
    which: Literal['upper','lower','molecular','gap','tag','all']='all',
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
    _factory_name: Optional[str] = None,
) -> Pool:
    """
    Create a Pool containing case-swapped sequences from the input pool.

    Preserves XML marker tags exactly as they appear (only transforms
    non-marker characters).

    Parameters
    ----------
    pool : Union[Pool_type, str]
        Parent pool or sequence to swap case.
    region : RegionType, default=None
        Region to apply transformation to. Can be marker name (str), [start, stop], or None.
    remove_marker : Optional[bool], default=None
        If True and region is a marker name, remove marker tags from output.
    spacer_str:
    color:
    case:
    name : Optional[str], default=None
        Name for the resulting Pool.
    op_name : Optional[str], default=None
        Name for the underlying Operation.
    iter_order : Optional[Real], default=None
        Iteration order priority for the resulting Pool.
    op_iter_order : Optional[Real], default=None
        Iteration order priority for the underlying Operation.
    _factory_name: Optional[str], default=None
        Sets default name of the resulting operation
    Returns
    -------
    Pool
        A Pool containing case-swapped sequences.
    """
    from .fixed import fixed_operation

    code_str = code_dict[color]
    reset_str = code_dict['reset']
    match which:
        case 'all':
            seq_from_seqs_fn = lambda seqs: code_str+seqs[0]+reset_str
        case 'lower':
            seq_from_seqs_fn = lambda seqs: ''.join([code_str+c+reset_str if c!=c.upper() else c for c in seqs[0]]) 
        case 'upper':
            seq_from_seqs_fn = lambda seqs: ''.join([code_str+c+reset_str if c!=c.lower() else c for c in seqs[0]]) 

    return fixed_operation(
        parent_pools=[pool],
        seq_from_seqs_fn=seq_from_seqs_fn,
        seq_length_from_pool_lengths_fn=lambda lengths: lengths[0],
        region=region,
        remove_marker=remove_marker,
        spacer_str=spacer_str,
        name=name,
        op_name=op_name,
        iter_order=iter_order,
        op_iter_order=op_iter_order,
        _factory_name=_factory_name if _factory_name is not None else 'color',
    )
