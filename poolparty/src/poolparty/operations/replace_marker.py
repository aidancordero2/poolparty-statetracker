"""Replace a marker in sequences with insertion sequences."""
from numbers import Real
from ..types import Union, Optional, beartype
from ..operation import Operation
from ..pool import Pool
from ..marker import Marker
import numpy as np


@beartype
def replace_marker(
    bg_pool: Union[Pool, str],
    ins_pool: Union[Pool, str],
    marker: Union[Marker, str],
    name: Optional[str] = None,
    op_name: Optional[str] = None,
    iter_order: Optional[Real] = None,
    op_iter_order: Optional[Real] = None,
) -> Pool:
    """
    Replace a marker in background sequences with insertion sequences.

    Parameters
    ----------
    bg_pool : Pool or str
        Background Pool or sequence containing the marker to replace.
    ins_pool : Pool or str
        Insertion Pool or sequence to substitute for the marker.
    marker : Marker or str
        The marker to replace. If str, looks up existing Marker by name.
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
        A Pool yielding bg_pool sequences with the marker replaced by ins_pool sequences.
    """
    from .from_seq import from_seq

    bg_pool = from_seq(bg_pool) if isinstance(bg_pool, str) else bg_pool
    ins_pool = from_seq(ins_pool) if isinstance(ins_pool, str) else ins_pool

    # Handle marker argument - create new Marker if string
    if isinstance(marker, str):
        marker = Marker(name=marker)

    op = ReplaceMarkerOp(
        bg_pool=bg_pool,
        ins_pool=ins_pool,
        marker=marker,
        name=op_name,
        iter_order=op_iter_order,
    )
    return Pool(operation=op, name=name, iter_order=iter_order)


@beartype
class ReplaceMarkerOp(Operation):
    """Replace a marker with insertion sequences."""

    factory_name = "replace_marker"
    design_card_keys = []

    def __init__(
        self,
        bg_pool: Pool,
        ins_pool: Pool,
        marker: Marker,
        name: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> None:
        self.marker = marker
        # seq_length is unknown (bg_pool length - marker tag + ins_pool length)
        super().__init__(
            parent_pools=[bg_pool, ins_pool],
            num_states=1,
            mode='fixed',
            seq_length=None,
            name=name,
            iter_order=iter_order,
        )

    def compute_design_card(
        self,
        parent_seqs: list[str],
        rng: Optional[np.random.Generator] = None,
    ) -> dict:
        """Return empty design card (no design decisions)."""
        return {}

    def compute_seq_from_card(
        self,
        parent_seqs: list[str],
        card: dict,
    ) -> dict:
        """Replace marker in bg_seq with ins_seq."""
        bg_seq = parent_seqs[0]
        ins_seq = parent_seqs[1]
        marker_tag = self.marker.tag

        # Validate marker occurs exactly once
        count = bg_seq.count(marker_tag)
        if count == 0:
            raise ValueError(
                f"Marker {marker_tag} not found in background sequence: {bg_seq!r}"
            )
        if count > 1:
            raise ValueError(
                f"Marker {marker_tag} occurs {count} times in background sequence "
                f"(expected exactly 1): {bg_seq!r}"
            )

        result_seq = bg_seq.replace(marker_tag, ins_seq, 1)
        return {'seq_0': result_seq}

    def _get_copy_params(self) -> dict:
        """Return parameters needed to create a copy of this operation."""
        return {
            'bg_pool': self.parent_pools[0],
            'ins_pool': self.parent_pools[1],
            'marker': self.marker,
            'name': None,
            'iter_order': self.iter_order,
        }
