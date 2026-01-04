"""OpsContainer class housing convenience methods for Pool."""
from .types import Pool_type, Union, Optional, Real, Callable, Integral, beartype


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
        remove_marker: bool = True,
        name: Optional[str] = None,
        iter_order: Optional[Real] = None,
    ) -> Pool_type:
        """Apply a transformation to the content of a marked region.
        
        This is a thin wrapper around poolparty.apply_at_marker().
        See that function for full documentation of parameters.
        """
        from .marker_ops.apply_at_marker import apply_at_marker
        return apply_at_marker(
            self.pool, marker_name, transform_fn,
            remove_marker=remove_marker, name=name, iter_order=iter_order,
        )
    
    def mutagenize(
        self,
        marker_name: str,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply mutagenize() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to mutagenize.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the mutagenized content.
        **kwargs
            Arguments passed to mutagenize() (e.g., num_mutations,
            mutation_rate, mark_changes, mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with the marker region mutagenized.
        """
        from .base_ops.mutagenize import mutagenize
        return self.apply_at_marker(
            marker_name,
            lambda p: mutagenize(p, **kwargs),
            remove_marker=remove_marker,
        )
    
    def deletion_scan(
        self,
        marker_name: str,
        deletion_length: Integral,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply deletion_scan() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to scan.
        deletion_length : Integral
            Number of characters to delete at each position.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the scanned content.
        **kwargs
            Arguments passed to deletion_scan() (e.g., deletion_marker,
            spacer_str, positions, mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with deletion scan applied to the marker region.
        """
        from .scan_ops.deletion_scan import deletion_scan
        return self.apply_at_marker(
            marker_name,
            lambda p: deletion_scan(p, deletion_length, **kwargs),
            remove_marker=remove_marker,
        )
    
    def insertion_scan(
        self,
        marker_name: str,
        ins_pool: Union[Pool_type, str],
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply insertion_scan() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to scan.
        ins_pool : Pool or str
            The insert Pool or sequence string to be inserted.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the scanned content.
        **kwargs
            Arguments passed to insertion_scan() (e.g., positions,
            spacer_str, mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with insertion scan applied to the marker region.
        """
        from .scan_ops.insertion_scan import insertion_scan
        return self.apply_at_marker(
            marker_name,
            lambda p: insertion_scan(p, ins_pool, **kwargs),
            remove_marker=remove_marker,
        )
    
    def replacement_scan(
        self,
        marker_name: str,
        ins_pool: Union[Pool_type, str],
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply replacement_scan() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to scan.
        ins_pool : Pool or str
            The insert Pool or sequence string to replace segments.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the scanned content.
        **kwargs
            Arguments passed to replacement_scan() (e.g., positions,
            spacer_str, mark_changes, mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with replacement scan applied to the marker region.
        """
        from .scan_ops.replacement_scan import replacement_scan
        return self.apply_at_marker(
            marker_name,
            lambda p: replacement_scan(p, ins_pool, **kwargs),
            remove_marker=remove_marker,
        )
    
    def mutagenize_scan(
        self,
        marker_name: str,
        mutagenize_length: Integral,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply mutagenize_scan() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to scan.
        mutagenize_length : Integral
            Length of the region to mutagenize at each position.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the scanned content.
        **kwargs
            Arguments passed to mutagenize_scan() (e.g., num_mutations,
            mutation_rate, positions, spacer_str, mark_changes, mode).
        
        Returns
        -------
        Pool
            A Pool with mutagenize scan applied to the marker region.
        """
        from .scan_ops.mutagenize_scan import mutagenize_scan
        return self.apply_at_marker(
            marker_name,
            lambda p: mutagenize_scan(p, mutagenize_length, **kwargs),
            remove_marker=remove_marker,
        )
    
    def shuffle_scan(
        self,
        marker_name: str,
        shuffle_length: Integral,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply shuffle_scan() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to scan.
        shuffle_length : Integral
            Length of the region to shuffle at each position.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the scanned content.
        **kwargs
            Arguments passed to shuffle_scan() (e.g., positions,
            spacer_str, mark_changes, mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with shuffle scan applied to the marker region.
        """
        from .scan_ops.shuffle_scan import shuffle_scan
        return self.apply_at_marker(
            marker_name,
            lambda p: shuffle_scan(p, shuffle_length, **kwargs),
            remove_marker=remove_marker,
        )
    
    def seq_shuffle(
        self,
        marker_name: str,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Apply seq_shuffle() to a marked region.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker whose content to shuffle.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the shuffled content.
        **kwargs
            Arguments passed to seq_shuffle() (e.g., start, end,
            mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with the marker content shuffled.
        """
        from .base_ops.seq_shuffle import seq_shuffle
        return self.apply_at_marker(
            marker_name,
            lambda p: seq_shuffle(p, **kwargs),
            remove_marker=remove_marker,
        )
    
    def from_iupac_motif(
        self,
        marker_name: str,
        iupac_seq: str,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Replace marker content with IUPAC-generated sequences.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker to replace.
        iupac_seq : str
            IUPAC sequence string (e.g., 'RN' for purine + any base).
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the inserted content.
        **kwargs
            Arguments passed to from_iupac_motif() (e.g., mark_changes,
            mode, num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with marker replaced by IUPAC-generated sequences.
        """
        from .base_ops.from_iupac_motif import from_iupac_motif
        from .marker_ops.replace_marker_content import replace_marker_content
        from .marker_ops.apply_at_marker import _replace_keeping_marker
        content = from_iupac_motif(iupac_seq, **kwargs)
        if remove_marker:
            return replace_marker_content(self.pool, content, marker_name)
        else:
            return _replace_keeping_marker(self.pool, content, marker_name)
    
    def from_prob_motif(
        self,
        marker_name: str,
        prob_df,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Replace marker content with probability-sampled sequences.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker to replace.
        prob_df : pd.DataFrame
            DataFrame with probability values for each position.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the inserted content.
        **kwargs
            Arguments passed to from_prob_motif() (e.g., mode,
            num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with marker replaced by probability-sampled sequences.
        """
        from .base_ops.from_prob_motif import from_prob_motif
        from .marker_ops.replace_marker_content import replace_marker_content
        from .marker_ops.apply_at_marker import _replace_keeping_marker
        content = from_prob_motif(prob_df, **kwargs)
        if remove_marker:
            return replace_marker_content(self.pool, content, marker_name)
        else:
            return _replace_keeping_marker(self.pool, content, marker_name)
    
    def get_kmers(
        self,
        marker_name: str,
        length: int,
        remove_marker: bool = True,
        **kwargs,
    ) -> Pool_type:
        """Replace marker content with k-mer sequences.
        
        Parameters
        ----------
        marker_name : str
            Name of the marker to replace.
        length : int
            Length of k-mers to generate.
        remove_marker : bool, default=True
            If True, marker tags are removed from the result.
            If False, marker tags are preserved around the inserted content.
        **kwargs
            Arguments passed to get_kmers() (e.g., mode,
            num_hybrid_states).
        
        Returns
        -------
        Pool
            A Pool with marker replaced by k-mer sequences.
        """
        from .base_ops.get_kmers import get_kmers
        from .marker_ops.replace_marker_content import replace_marker_content
        from .marker_ops.apply_at_marker import _replace_keeping_marker
        content = get_kmers(length, **kwargs)
        if remove_marker:
            return replace_marker_content(self.pool, content, marker_name)
        else:
            return _replace_keeping_marker(self.pool, content, marker_name)
