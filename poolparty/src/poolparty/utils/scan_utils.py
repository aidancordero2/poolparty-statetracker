"""Scan operation utilities."""
from ..types import PositionsType, Optional
from .seq_utils import validate_positions


def build_scan_cache(
    seq_length: Optional[int],
    item_length: int,
    positions: PositionsType,
    error_context: str = "scan",
) -> int:
    """Build cache and return number of states for a scan operation.
    
    Parameters
    ----------
    seq_length
        Length of the sequence to scan. If None, uses positions directly.
    item_length
        Length of the item being scanned (e.g., deletion length, region length).
    positions
        User-specified positions to scan, or None for all positions.
    error_context
        Context string for error messages (e.g., "deletion", "region tag insertion").
    
    Returns
    -------
    int
        Number of valid positions (states) for the scan operation.
    
    Raises
    ------
    ValueError
        If no valid positions exist for the scan.
    """
    if seq_length is None:
        if positions is not None:
            positions_list = validate_positions(
                positions,
                max_position=1000000,
                min_position=0,
            )
            return max(1, len(positions_list))
        return 1
    
    # Calculate maximum valid starting position
    max_start = seq_length - item_length
    if max_start < 0:
        max_start = 0
    
    num_all_positions = max_start + 1
    if positions is not None:
        indices = validate_positions(
            positions,
            max_position=num_all_positions - 1,
            min_position=0,
        )
        num_states = len(indices)
    else:
        num_states = num_all_positions
    
    if num_states == 0:
        raise ValueError(f"No valid positions for {error_context}")
    return num_states
