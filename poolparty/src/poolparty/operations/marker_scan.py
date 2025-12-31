"""MarkerScan operation - insert markers at scanning positions."""
from ..types import Union, ModeType, Optional, Integral, Real, PositionsType, Marker_type, beartype
from ..seq_utils import validate_positions
from ..operation import Operation
from ..pool import Pool
from ..marker import Marker
import numpy as np


@beartype
def marker_scan(
    pool: Union[Pool, str],
    marker: Union[None, str, Marker] = None,
    positions: PositionsType = None,
    mode: ModeType = 'random',
    num_hybrid_states: Optional[Integral] = None,
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool:
    """
    Insert a marker at specified positions in a sequence.

    Parameters
    ----------
    pool : Pool or str
        Input Pool or sequence string to insert marker into.
    marker : None, str, or Marker
        The marker to insert. If None, creates a new Marker with default name.
        If str, creates a new Marker with that name.
    positions : PositionsType, default=None
        Valid insertion positions (0-based). If None, all positions are valid.
    mode : ModeType, default='random'
        Position selection mode: 'random', 'sequential', or 'hybrid'.
    num_hybrid_states : Optional[Integral], default=None
        Number of pool states when using 'hybrid' mode.
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
        A Pool yielding sequences with the marker inserted at selected positions.
    """
    from .from_seq import from_seq
    
    # Convert string input to pool if needed
    pool = from_seq(pool) if isinstance(pool, str) else pool
    
    # Handle marker argument
    if marker is None:
        marker = Marker()
    elif isinstance(marker, str):
        marker = Marker(name=marker)
    # else: marker is already a Marker object
    
    op = MarkerScanOp(
        parent_pool=pool,
        marker=marker,
        positions=positions,
        mode=mode,
        num_hybrid_states=num_hybrid_states,
        name=op_name,
        iter_order=op_iter_order,
    )
    result_pool = Pool(operation=op, name=name, iter_order=iter_order)
    return result_pool


@beartype
class MarkerScanOp(Operation):
    """Insert a marker at scanning positions."""
    factory_name = "marker_scan"
    design_card_keys = ['position', 'marker_tag']
    
    def __init__(
        self,
        parent_pool: Pool,
        marker: Marker,
        positions: PositionsType = None,
        mode: ModeType = 'random',
        num_hybrid_states: Optional[Integral] = None,
        name: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> None:
        """Initialize MarkerScanOp."""
        if mode == 'hybrid' and num_hybrid_states is None:
            raise ValueError("num_hybrid_states is required when mode='hybrid'")
        
        self.marker = marker
        self._positions = positions
        self._mode = mode
        self._seq_length = parent_pool.seq_length
        self._valid_positions = None
        self._sequential_cache = None
        
        if mode == 'sequential':
            if self._seq_length is not None:
                num_states = self._build_caches()
            else:
                num_states = 1
        elif mode == 'hybrid':
            num_states = num_hybrid_states
        else:
            num_states = 1
        
        # Output seq_length is variable (original + marker tag length)
        super().__init__(
            parent_pools=[parent_pool],
            num_states=num_states,
            mode=mode,
            seq_length=None,
            name=name,
            iter_order=iter_order,
        )
    
    def _build_caches(self) -> int:
        """Build caches for sequential enumeration based on seq_length."""
        if self._seq_length is None:
            # Unknown seq_length (e.g., parent has markers with variable length)
            # If user specified positions, use len(positions) as num_states
            if self._positions is not None:
                # Just count positions, actual validation happens at generation time
                positions_list = validate_positions(
                    self._positions,
                    max_position=1000000,  # Large number, actual validation at runtime
                    min_position=0,
                )
                return max(1, len(positions_list))
            return 1
        # Compute number of valid positions based on effective seq_length
        # All positions 0..seq_length are valid insertion points
        num_all_positions = self._seq_length + 1
        if self._positions is not None:
            # User positions are indices into the valid positions array
            indices = validate_positions(
                self._positions,
                max_position=num_all_positions - 1,
                min_position=0,
            )
            num_states = len(indices)
        else:
            num_states = num_all_positions
        if num_states == 0:
            raise ValueError("No valid positions for marker insertion")
        return num_states
    
    def _get_valid_marker_positions(self, seq: str) -> list[int]:
        """Get valid marker insertion positions, excluding marker interiors."""
        from ..alphabet import MARKER_PATTERN
        
        # Find all marker spans (positions inside markers)
        marker_spans: set[int] = set()
        for match in MARKER_PATTERN.finditer(seq):
            for i in range(match.start(), match.end()):
                marker_spans.add(i)
        
        # Valid insertion positions: any position not inside a marker
        # This includes: before each non-marker char, and at the end
        all_valid = []
        for i in range(len(seq) + 1):
            # Position i is valid if:
            # - It's at the end of the sequence, OR
            # - The character at position i is not inside a marker
            if i == len(seq) or i not in marker_spans:
                all_valid.append(i)
        
        # User positions are INDICES into all_valid, not raw string positions
        if self._positions is not None:
            indices = validate_positions(
                self._positions,
                max_position=len(all_valid) - 1,
                min_position=0,
            )
            return [all_valid[i] for i in indices]
        
        return all_valid
    
    def compute_design_card(
        self,
        parent_seqs: list[str],
        rng: Optional[np.random.Generator] = None,
    ) -> dict:
        """Return design card with insertion position (index into valid positions)."""
        seq = parent_seqs[0]
        
        # Get valid positions (excludes marker interiors)
        valid_positions = self._get_valid_marker_positions(seq)
        if len(valid_positions) == 0:
            raise ValueError("No valid positions for marker insertion")
        
        if self.mode in ('random', 'hybrid'):
            if rng is None:
                raise RuntimeError(f"{self.mode.capitalize()} mode requires RNG - use Party.generate(seed=...)")
            # Choose random index into valid_positions
            position_index = int(rng.integers(0, len(valid_positions)))
        else:
            # Sequential mode: use counter state as index into valid positions
            state = self.counter.state
            state = 0 if state is None else state
            position_index = state % len(valid_positions)
        
        return {
            'position': position_index,  # Index into valid positions, not raw string position
            'marker_tag': self.marker.tag,
        }
    
    def compute_seq_from_card(
        self,
        parent_seqs: list[str],
        card: dict,
    ) -> dict:
        """Insert marker at position based on design card."""
        seq = parent_seqs[0]
        position_index = card['position']
        marker_tag = card['marker_tag']
        
        # Convert index to raw string position
        valid_positions = self._get_valid_marker_positions(seq)
        raw_position = valid_positions[position_index]
        
        result_seq = seq[:raw_position] + marker_tag + seq[raw_position:]
        return {'seq_0': result_seq}
    
    def _get_copy_params(self) -> dict:
        """Return parameters needed to create a copy of this operation."""
        return {
            'parent_pool': self.parent_pools[0],
            'marker': self.marker,
            'positions': self._positions,
            'mode': self.mode,
            'num_hybrid_states': self.num_states if self.mode == 'hybrid' else None,
            'name': None,
            'iter_order': self.iter_order,
        }
