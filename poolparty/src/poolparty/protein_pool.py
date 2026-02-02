"""ProteinPool class for protein sequence pools."""

import logging
from typing import Literal

import pandas as pd
import statetracker as st

from .pool_mixins import StateOpsMixin
from .region import Region
from .types import Integral, Operation_type, Optional, Real, Sequence, Union, beartype

logger = logging.getLogger(__name__)


@beartype
class ProteinPool(StateOpsMixin):
    """Pool containing protein sequences.

    Similar to Pool but without DNA-specific operations. Supports state
    operations (sample, repeat, stack) and output generation.
    """

    def __init__(
        self,
        operation: Operation_type,
        name: Optional[str] = None,
        state: Optional[st.State] = None,
        iter_order: Optional[Real] = None,
        regions: Optional[set[Region]] = None,
    ) -> None:
        """Initialize ProteinPool."""
        from .party import get_active_party

        party = get_active_party()
        if party is None:
            raise RuntimeError(
                "ProteinPools must be created inside a Party context. "
                "Use: with pp.Party() as party: ..."
            )
        self._party = party
        self._id = party._get_next_pool_id()
        self.operation = operation
        if state is not None:
            self.state = state
        else:
            self.state: st.State = operation.build_pool_counter(operation.parent_pools)
        if iter_order is not None:
            self.state.iter_order = iter_order
        self._name: str = ""
        self.name = name if name is not None else f"pool[{self._id}]"

        # Track regions: inherit from parents if not explicitly provided
        if regions is not None:
            self._regions: set[Region] = set(regions)
        else:
            self._regions = set()
            for parent in operation.parent_pools:
                if hasattr(parent, "_regions"):
                    self._regions.update(parent._regions)

        party._register_pool(self)
        logger.debug(
            "Created ProteinPool id=%s name=%s seq_length=%s num_states=%s",
            self._id,
            self._name,
            self.seq_length,
            self.num_states,
        )

    @property
    def iter_order(self) -> Real:
        """Iteration order for this pool."""
        if self.state.num_values == 1:
            return 0
        return self.state.iter_order

    @iter_order.setter
    def iter_order(self, value: Real) -> None:
        """Set iteration order for this pool."""
        self.state.iter_order = value

    @property
    def name(self) -> str:
        """Name of this pool."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set pool name and update state name."""
        self._party._validate_pool_name(value, self)
        old_name = self._name
        self._name = value
        if self.state is self.operation.state:
            op_name = self.operation.name
            is_default_op_name = op_name.startswith("op[") and "]:" in op_name
            if not is_default_op_name:
                pass
            else:
                self.state.name = f"{value}.state"
        else:
            self.state.name = f"{value}.state"
        if old_name:
            self._party._update_pool_name(self, old_name, value)

    @property
    def num_states(self) -> int:
        """Number of states for this pool."""
        return self.state.num_values

    @property
    def parents(self) -> list:
        """Get parent pools from the operation."""
        return self.operation.parent_pools

    @property
    def seq_length(self) -> Optional[int]:
        """Sequence length (None if variable)."""
        return self.operation.seq_length

    @property
    def regions(self) -> set[Region]:
        """Set of Region objects present in this pool's sequences."""
        return self._regions

    def has_region(self, name: str) -> bool:
        """Check if a region with the given name is present in this pool."""
        return any(r.name == name for r in self._regions)

    def __repr__(self) -> str:
        num_states_str = "None" if self.num_states is None else str(self.num_states)
        return f"ProteinPool(id={self._id}, name={self.name!r}, op={self.operation.name!r}, num_states={num_states_str})"

    #########################################################################
    # Counter-based operators (same as Pool)
    #########################################################################

    def __add__(self, other: "ProteinPool") -> "ProteinPool":
        """Stack two pools (union of states via sum_counters)."""
        from .state_ops.stack import stack

        return stack([self, other])

    def __mul__(self, n: int) -> "ProteinPool":
        """Repeat this pool n times (repeat states)."""
        from .state_ops.repeat import repeat

        return repeat(self, n)

    def __rmul__(self, n: int) -> "ProteinPool":
        """Repeat this pool n times (repeat states)."""
        return self.__mul__(n)

    def __getitem__(self, key: Union[int, slice]) -> "ProteinPool":
        """Slice this pool's states (not sequences)."""
        from .state_ops.state_slice import state_slice

        return state_slice(self, key)

    def named(self, name: str) -> "ProteinPool":
        """Set the name of this pool, return self for chaining."""
        self.name = name
        return self

    def generate_library(
        self,
        num_cycles: int = 1,
        num_seqs: Optional[int] = None,
        seed: Optional[int] = None,
        init_state: Optional[int] = None,
        seqs_only: bool = False,
        report_design_cards: bool = False,
        aux_pools: Sequence = (),
        pools_to_report: Union[str, Sequence] = "all",
        organize_columns_by: Literal["pool", "type"] = "type",
        _include_inline_styles: bool = False,
        discard_null_seqs: bool = False,
        max_iterations: Optional[int] = None,
        min_acceptance_rate: Optional[float] = None,
        attempts_per_rate_assessment: int = 100,
    ) -> Union[pd.DataFrame, list[str]]:
        """Generate library of protein sequences."""
        from .generate_library import generate_library

        return generate_library(
            pool=self,
            num_cycles=num_cycles,
            num_seqs=num_seqs,
            seed=seed,
            init_state=init_state,
            seqs_only=seqs_only,
            report_design_cards=report_design_cards,
            aux_pools=aux_pools,
            pools_to_report=pools_to_report,
            organize_columns_by=organize_columns_by,
            _include_inline_styles=_include_inline_styles,
            discard_null_seqs=discard_null_seqs,
            max_iterations=max_iterations,
            min_acceptance_rate=min_acceptance_rate,
            attempts_per_rate_assessment=attempts_per_rate_assessment,
        )

    def print_library(
        self,
        num_seqs: Optional[Integral] = None,
        num_cycles: Optional[Integral] = None,
        show_header: bool = True,
        show_state: bool = True,
        show_name: bool = True,
        show_seq: bool = True,
        pad_names: bool = True,
        seed: Optional[Integral] = None,
        discard_null_seqs: bool = False,
        max_iterations: Optional[int] = None,
        min_acceptance_rate: Optional[float] = None,
        attempts_per_rate_assessment: int = 100,
    ) -> "ProteinPool":
        """Print preview protein sequences from this pool; returns self for chaining."""
        gen_kwargs = {
            "seqs_only": False,
            "report_design_cards": True,
            "init_state": 0,
            "seed": seed,
            "_include_inline_styles": True,
            "discard_null_seqs": discard_null_seqs,
            "max_iterations": max_iterations,
            "min_acceptance_rate": min_acceptance_rate,
            "attempts_per_rate_assessment": attempts_per_rate_assessment,
        }
        if num_seqs is not None:
            gen_kwargs["num_seqs"] = num_seqs
        else:
            gen_kwargs["num_cycles"] = num_cycles if num_cycles is not None else 1
        df = self.generate_library(**gen_kwargs)
        has_name = show_name and "name" in df.columns and df["name"].notna().any()
        max_name_len = df["name"].str.len().max() if has_name and pad_names else 0

        if show_header:
            num_states_str = "None" if self.num_states is None else str(self.num_states)
            print(f"{self.name}: seq_length={self.seq_length}, num_states={num_states_str}")
            header_parts = []
            if show_state:
                header_parts.append("state")
            if has_name:
                header_parts.append(f"{'name':<{max_name_len}}" if pad_names else "name")
            if show_seq:
                header_parts.append("seq")
            if header_parts:
                print("  ".join(header_parts))

        state_col = f"{self.name}.state"
        for _, row in df.iterrows():
            row_parts = []
            if show_state:
                row_parts.append(f"{row[state_col]:5d}")
            if has_name:
                name = row["name"] if row["name"] is not None else ""
                if pad_names:
                    row_parts.append(f"{name:<{max_name_len}}")
                else:
                    row_parts.append(f"{name}")
            if show_seq:
                seq = row["seq"]
                if seq is None:
                    row_parts.append("None")
                else:
                    from .utils.style_utils import SeqStyle

                    inline_styles = row.get("_inline_styles", SeqStyle.empty(0))
                    if inline_styles is not None:
                        seq = inline_styles.apply(seq)
                    row_parts.append(seq)
            print("  ".join(row_parts))
        print("")
        return self

    def print_dag(self, style: str = "clean", show_pools: bool = True) -> "ProteinPool":
        """Print the ASCII tree visualization rooted at this pool."""
        from .text_viz import print_pool_tree

        print_pool_tree(self, style=style, show_pools=show_pools)
        return self
