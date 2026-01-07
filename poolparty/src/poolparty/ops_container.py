"""OpsContainer class housing convenience methods for Pool."""
from .types import Pool_type, Union, Optional, Real, Callable, Integral, Sequence, beartype


@beartype
class OpsContainer:
    """Container for Pool convenience methods that wrap Operation factory functions."""
    
    def __init__(self, pool: Pool_type) -> None:
        """Initialize with a reference to the parent Pool."""
        self.pool = pool
    
    def apply_at_marker(
        self,
        marker_name: str,
        transform_fn: Callable,
        remove_tags: Optional[bool] = None,
        **kwargs,
    ) -> Pool_type:
        """Apply a transformation to the content of a marked region."""
        from .marker_ops.apply_at_marker import apply_at_marker
        if remove_tags is None:
            remove_tags = self.pool._party.get_default('remove_marker', True)
        iter_order = kwargs.pop('iter_order', None)
        return apply_at_marker(self.pool, marker_name, transform_fn, remove_marker=remove_tags, op_iter_order=iter_order, **kwargs)
    
    def mutagenize(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .base_ops.mutagenize import mutagenize
        return mutagenize(pool=self.pool, region=region, **kwargs)
    
    def mutagenize_scan(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .scan_ops.mutagenize_scan import mutagenize_scan
        return mutagenize_scan(pool=self.pool, region=region, **kwargs)
    
    def deletion_scan(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .scan_ops.deletion_scan import deletion_scan
        return deletion_scan(pool=self.pool, region=region, **kwargs)
    
    def insertion_scan(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .scan_ops.insertion_scan import insertion_scan
        return insertion_scan(pool=self.pool, region=region, **kwargs)
    
    def replacement_scan(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .scan_ops.insertion_scan import replacement_scan
        return replacement_scan(pool=self.pool, region=region, **kwargs)
    
    def shuffle_scan(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .scan_ops.shuffle_scan import shuffle_scan
        return shuffle_scan(pool=self.pool, region=region, **kwargs)
    
    def shuffle_seq(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .base_ops.shuffle_seq import shuffle_seq
        return shuffle_seq(pool=self.pool, region=region, **kwargs)
    
    def insert_from_iupac(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .base_ops.from_iupac_motif import from_iupac_motif
        return from_iupac_motif(pool=self.pool, region=region, **kwargs)
    
    def insert_from_motif(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .base_ops.from_prob_motif import from_prob_motif
        return from_prob_motif(pool=self.pool, region=region, **kwargs)
    
    def insert_kmers(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .base_ops.get_kmers import get_kmers
        return get_kmers(pool=self.pool, region=region, **kwargs)
    
    #########################################################################
    # Fixed operation convenience methods
    #########################################################################
    
    def reverse_complement(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .fixed_ops.reverse_complement import reverse_complement
        return reverse_complement(pool=self.pool, region=region, **kwargs)
    
    def swapcase(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .fixed_ops.swapcase import swapcase
        return swapcase(pool=self.pool, region=region, **kwargs)
    
    def upper(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .fixed_ops.upper import upper
        return upper(pool=self.pool, region=region, **kwargs)
    
    def lower(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .fixed_ops.lower import lower
        return lower(pool=self.pool, region=region, **kwargs)
    
    def clear_gap_chars(self, region: Optional[str] = None, **kwargs) -> Pool_type:
        from .fixed_ops.clear_gap_chars import clear_gap_chars
        return clear_gap_chars(pool=self.pool, region=region, **kwargs)
    
    #########################################################################
    # State operation convenience methods
    #########################################################################
    
    def repeat_states(
        self,
        times: int,
        seq_name_prefix: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> Pool_type:
        """Repeat the Pool's states a specified number of times."""
        from .state_ops.repeat import repeat
        return repeat(
            self.pool,
            times,
            seq_name_prefix=seq_name_prefix,
            op_iter_order=iter_order,
        )
    
    def sample_states(
        self,
        num_states: Optional[Integral] = None,
        sampled_states: Optional[Sequence[Integral]] = None,
        seed: Optional[Integral] = None,
        with_replacement: bool = True,
        seq_name_prefix: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> Pool_type:
        """Sample states from the Pool. Wrapper for state_sample()."""
        from .state_ops.state_sample import state_sample
        return state_sample(
            self.pool,
            num_states=num_states,
            sampled_states=sampled_states,
            seed=seed,
            with_replacement=with_replacement,
            seq_name_prefix=seq_name_prefix,
            op_iter_order=iter_order,
        )
    
    def shuffle_states(
        self,
        seed: Optional[Integral] = None,
        permutation: Optional[Sequence[Integral]] = None,
        seq_name_prefix: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> Pool_type:
        """Shuffle (permute) the Pool's states. Wrapper for state_shuffle()."""
        from .state_ops.state_shuffle import state_shuffle
        return state_shuffle(
            self.pool,
            seed=seed,
            permutation=permutation,
            seq_name_prefix=seq_name_prefix,
            op_iter_order=iter_order,
        )
    
    def slice_states(
        self,
        key: Union[Integral, slice],
        seq_name_prefix: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> Pool_type:
        """Slice the Pool's states. Wrapper for state_slice()."""
        from .state_ops.state_slice import state_slice
        return state_slice(
            self.pool,
            key,
            seq_name_prefix=seq_name_prefix,
            op_iter_order=iter_order,
        )
    
    #########################################################################
    # Marker management methods
    #########################################################################
    
    def insert_marker(
        self,
        marker_name: str,
        start: int,
        stop: Optional[int] = None,
        strand: str = '+',
        **kwargs,
    ) -> Pool_type:
        """Insert an XML-style marker at a fixed position in sequences."""
        from .marker_ops.insert_marker import insert_marker
        iter_order = kwargs.pop('iter_order', None)
        return insert_marker(self.pool, marker_name, start, stop, strand, op_iter_order=iter_order, **kwargs)
    
    def remove_marker(
        self,
        marker_name: str,
        keep_content: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Remove a marker from sequences."""
        from .marker_ops.remove_marker import remove_marker
        iter_order = kwargs.pop('iter_order', None)
        return remove_marker(self.pool, marker_name, keep_content, op_iter_order=iter_order, **kwargs)
    
    def replace_marker_content(
        self,
        content_pool: Union[Pool_type, str],
        marker_name: str,
        **kwargs,
    ) -> Pool_type:
        """Replace a marker region with content from another Pool."""
        from .marker_ops.replace_marker_content import replace_marker_content
        iter_order = kwargs.pop('iter_order', None)
        return replace_marker_content(self.pool, content_pool, marker_name, op_iter_order=iter_order, **kwargs)
    
    def clear_markers(self, **kwargs) -> Pool_type:
        """Remove all marker tags from sequences, keeping content."""
        from .fixed_ops.fixed import fixed_operation
        from .marker_ops.parsing import strip_all_markers
        
        iter_order = kwargs.pop('iter_order', None)
        result = fixed_operation(
            parent_pools=[self.pool],
            seq_from_seqs_fn=lambda seqs: strip_all_markers(seqs[0]),
            seq_length_from_pool_lengths_fn=lambda lengths: None,
            op_iter_order=iter_order,
            **kwargs,
        )
        result._markers = set()
        return result
