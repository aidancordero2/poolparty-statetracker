"""Insert multiple markers into a sequence."""
from ..types import (
    Union,
    Sequence,
    ModeType,
    Optional,
    Integral,
    Real,
    PositionsType,
    Marker_type,
    beartype,
)
from ..seq_utils import validate_positions
from ..operation import Operation
from ..pool import Pool
from ..marker import Marker
import numpy as np


@beartype
def marker_multiscan(
    pool: Union[Pool, str],
    markers: Union[Sequence[Union[str, Marker_type]], str, Marker_type],
    num_insertions: Integral,
    positions: PositionsType = None,
    insertion_mode: str = 'ordered',
    mode: ModeType = 'random',
    num_hybrid_states: Optional[Integral] = None,
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool:
    """
    Insert multiple markers into a sequence.
    """
    from .from_seq import from_seq

    pool = from_seq(pool) if isinstance(pool, str) else pool
    op = MarkerMultiScanOp(
        parent_pool=pool,
        markers=markers,
        num_insertions=num_insertions,
        positions=positions,
        insertion_mode=insertion_mode,
        mode=mode,
        num_hybrid_states=num_hybrid_states,
        name=op_name,
        iter_order=op_iter_order,
    )
    return Pool(operation=op, name=name, iter_order=iter_order)


@beartype
class MarkerMultiScanOp(Operation):
    """Insert multiple markers at selected positions."""

    factory_name = "marker_multiscan"
    design_card_keys = ['positions', 'marker_tags']

    def __init__(
        self,
        parent_pool: Pool,
        markers: Union[Sequence[Union[str, Marker_type]], str, Marker_type],
        num_insertions: Integral,
        positions: PositionsType = None,
        insertion_mode: str = 'ordered',
        mode: ModeType = 'random',
        num_hybrid_states: Optional[Integral] = None,
        name: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> None:
        if num_insertions < 1:
            raise ValueError(f"num_insertions must be >= 1, got {num_insertions}")
        if mode not in ('random', 'hybrid'):
            raise ValueError("marker_multiscan supports only mode='random' or 'hybrid'")
        if mode == 'hybrid' and num_hybrid_states is None:
            raise ValueError("num_hybrid_states is required when mode='hybrid'")

        self._positions = positions
        self._mode = mode
        self._seq_length = parent_pool.seq_length
        self.num_insertions = int(num_insertions)
        self.insertion_mode = insertion_mode
        self._markers = self._coerce_markers(markers)
        self._validate_marker_counts()

        num_states = 1 if mode == 'random' else num_hybrid_states
        super().__init__(
            parent_pools=[parent_pool],
            num_states=num_states,
            mode=mode,
            seq_length=None,
            name=name,
            iter_order=iter_order,
        )

    def _coerce_markers(
        self, markers: Union[Sequence[Union[str, Marker_type]], str, Marker_type]
    ) -> list[Marker]:
        """Normalize markers input to a list of Marker objects."""
        if isinstance(markers, (str, Marker)):
            markers = [markers]
        if not markers:
            raise ValueError("markers must not be empty")
        result: list[Marker] = []
        for m in markers:
            if isinstance(m, Marker):
                result.append(m)
            elif isinstance(m, str):
                result.append(Marker(name=m))
            else:
                raise TypeError(f"Unsupported marker type: {type(m)}")
        return result

    def _validate_marker_counts(self) -> None:
        """Validate marker counts against insertion_mode."""
        if self.insertion_mode not in ('ordered', 'unordered'):
            raise ValueError(
                "insertion_mode must be one of 'ordered', 'unordered'"
            )
        if self.insertion_mode == 'ordered' and len(self._markers) != self.num_insertions:
            raise ValueError(
                "insertion_mode='ordered' requires len(markers) == num_insertions"
            )
        if self.insertion_mode == 'unordered' and len(self._markers) < self.num_insertions:
            raise ValueError(
                "insertion_mode='unordered' requires len(markers) >= num_insertions"
            )

    def _get_valid_marker_positions(self, seq: str) -> list[int]:
        """Valid insertion positions excluding marker interiors."""
        from ..alphabet import MARKER_PATTERN

        marker_spans: set[int] = set()
        for match in MARKER_PATTERN.finditer(seq):
            for i in range(match.start(), match.end()):
                marker_spans.add(i)

        all_valid: list[int] = []
        for i in range(len(seq) + 1):
            if i == len(seq) or i not in marker_spans:
                all_valid.append(i)

        if self._positions is not None:
            indices = validate_positions(
                self._positions,
                max_position=len(all_valid) - 1,
                min_position=0,
            )
            return [all_valid[i] for i in indices]

        return all_valid

    def _select_positions(
        self, valid_positions: list[int], rng: np.random.Generator
    ) -> list[int]:
        if len(valid_positions) < self.num_insertions:
            raise ValueError(
                f"Not enough valid positions ({len(valid_positions)}) "
                f"for {self.num_insertions} insertions"
            )
        chosen = rng.choice(
            valid_positions,
            size=self.num_insertions,
            replace=False,
        )
        return sorted(int(x) for x in chosen)

    def _select_marker_tags(
        self, rng: np.random.Generator
    ) -> list[str]:
        if self.insertion_mode == 'ordered':
            return [m.tag for m in self._markers]
        # unordered: each marker used at most once
        idxs = rng.choice(len(self._markers), size=self.num_insertions, replace=False)
        return [self._markers[int(i)].tag for i in idxs]

    def compute_design_card(
        self,
        parent_seqs: list[str],
        rng: Optional[np.random.Generator] = None,
    ) -> dict:
        seq = parent_seqs[0]
        if rng is None:
            raise RuntimeError(f"{self.mode.capitalize()} mode requires RNG - use Party.generate(seed=...)")

        valid_positions = self._get_valid_marker_positions(seq)
        positions = self._select_positions(valid_positions, rng)
        marker_tags = self._select_marker_tags(rng)

        return {
            'positions': positions,
            'marker_tags': marker_tags,
        }

    def compute_seq_from_card(
        self,
        parent_seqs: list[str],
        card: dict,
    ) -> dict:
        seq = parent_seqs[0]
        positions = list(card['positions'])
        marker_tags = list(card['marker_tags'])

        inserts = sorted(zip(positions, marker_tags), key=lambda x: x[0])
        offset = 0
        for pos, tag in inserts:
            raw_pos = int(pos) + offset
            seq = seq[:raw_pos] + tag + seq[raw_pos:]
            offset += len(tag)
        return {'seq_0': seq}

    def _get_copy_params(self) -> dict:
        return {
            'parent_pool': self.parent_pools[0],
            'markers': self._markers,
            'num_insertions': self.num_insertions,
            'positions': self._positions,
            'insertion_mode': self.insertion_mode,
            'mode': self.mode,
            'num_hybrid_states': self.num_states if self.mode == 'hybrid' else None,
            'name': None,
            'iter_order': self.iter_order,
        }
