"""Codon table utilities for ORF-aware operations.

Provides codon table management including:
- Standard genetic code with human codon usage ordering
- Custom genetic code support
- Pre-computed mutation lookup tables for efficient codon mutations
"""
from typing import Union
import copy


# Human codon usage table - codons sorted by frequency (high → low)
# Source: Kazusa Codon Usage Database - Homo sapiens
# https://www.kazusa.or.jp/codon/cgi-bin/showcodon.cgi?species=9606
#
# This ordering is important for mutation types like 'missense_only_first'
# and 'nonsynonymous_first' which select the first (most frequent) codon.
STANDARD_GENETIC_CODE: dict[str, list[str]] = {
    "F": ["TTC", "TTT"],
    "L": ["CTG", "CTC", "CTT", "TTG", "TTA", "CTA"],
    "I": ["ATC", "ATT", "ATA"],
    "M": ["ATG"],
    "V": ["GTG", "GTC", "GTT", "GTA"],
    "S": ["AGC", "TCC", "TCT", "TCA", "AGT", "TCG"],
    "P": ["CCC", "CCT", "CCA", "CCG"],
    "T": ["ACC", "ACA", "ACT", "ACG"],
    "A": ["GCC", "GCT", "GCA", "GCG"],
    "Y": ["TAC", "TAT"],
    "H": ["CAC", "CAT"],
    "Q": ["CAG", "CAA"],
    "N": ["AAC", "AAT"],
    "K": ["AAG", "AAA"],
    "D": ["GAC", "GAT"],
    "E": ["GAG", "GAA"],
    "C": ["TGC", "TGT"],
    "W": ["TGG"],
    "R": ["AGA", "AGG", "CGG", "CGC", "CGA", "CGT"],
    "G": ["GGC", "GGA", "GGG", "GGT"],
    "*": ["TGA", "TAA", "TAG"],
}


class CodonTable:
    """Codon table with pre-computed mutation lookup tables.
    
    Provides efficient access to:
    - Codon-to-amino acid mappings
    - Amino acid-to-codon mappings
    - Synonymous codon lists
    - Pre-computed mutation alternatives for each mutation type
    
    Uses class-level caching for standard genetic code (shared across instances).
    
    Attributes:
        aa_to_codons: Dict mapping amino acid -> list of codons
        codon_to_aa: Dict mapping codon -> amino acid
        synonymous: Dict mapping codon -> list of synonymous codons
        stop_codons: List of stop codons
        all_codons: List of all codons
        mutation_lookup: Dict mapping mutation_type -> codon -> list of alternative codons
    """
    
    # Class-level cache for standard genetic code
    _STANDARD_CACHE: dict | None = None
    
    def __init__(self, codon_table: Union[str, dict] = 'standard'):
        """Initialize CodonTable.
        
        Args:
            codon_table: Either 'standard' to use the standard genetic code,
                or a custom dict mapping amino acid -> list of codons.
        
        Raises:
            ValueError: If codon_table is invalid.
        """
        if codon_table == 'standard':
            self._use_cached_standard()
        elif isinstance(codon_table, dict):
            self._build_from_dict(codon_table)
        else:
            raise ValueError(
                f"codon_table must be 'standard' or a dict, got {type(codon_table)}"
            )
    
    def _use_cached_standard(self) -> None:
        """Use class-level cached standard genetic code tables."""
        if CodonTable._STANDARD_CACHE is None:
            CodonTable._STANDARD_CACHE = self._build_tables(STANDARD_GENETIC_CODE)
        
        cached = CodonTable._STANDARD_CACHE
        # Copy so instances can't mutate the shared cache
        self.aa_to_codons = {aa: codons[:] for aa, codons in cached['aa_to_codons'].items()}
        self.codon_to_aa = cached['codon_to_aa'].copy()
        self.synonymous = {codon: syns[:] for codon, syns in cached['synonymous'].items()}
        self.stop_codons = cached['stop_codons'][:]
        self.all_codons = cached['all_codons'][:]
        self.mutation_lookup = copy.deepcopy(cached['mutation_lookup'])
    
    def _build_from_dict(self, aa_to_codons: dict) -> None:
        """Build tables from a custom genetic code dict."""
        tables = self._build_tables(aa_to_codons)
        self.aa_to_codons = tables['aa_to_codons']
        self.codon_to_aa = tables['codon_to_aa']
        self.synonymous = tables['synonymous']
        self.stop_codons = tables['stop_codons']
        self.all_codons = tables['all_codons']
        self.mutation_lookup = tables['mutation_lookup']
    
    @staticmethod
    def _build_tables(aa_to_codons: dict) -> dict:
        """Build all codon tables from an AA -> codons mapping.
        
        Args:
            aa_to_codons: Dict mapping amino acid -> list of codons
        
        Returns:
            Dict with keys: aa_to_codons, codon_to_aa, synonymous,
                           stop_codons, all_codons, mutation_lookup
        """
        # Build codon -> AA mapping
        codon_to_aa = {}
        for aa, codon_list in aa_to_codons.items():
            for codon in codon_list:
                codon_to_aa[codon] = aa
        
        # Build synonymous codon lists
        synonymous = {}
        for aa, codon_list in aa_to_codons.items():
            for codon in codon_list:
                synonymous[codon] = [c for c in codon_list if c != codon]
        
        stop_codons = aa_to_codons.get("*", [])
        all_codons = list(codon_to_aa.keys())
        
        # Build mutation lookup tables
        mutation_lookup = CodonTable._build_mutation_lookup(
            aa_to_codons, codon_to_aa, synonymous, stop_codons, all_codons
        )
        
        return {
            'aa_to_codons': aa_to_codons,
            'codon_to_aa': codon_to_aa,
            'synonymous': synonymous,
            'stop_codons': stop_codons,
            'all_codons': all_codons,
            'mutation_lookup': mutation_lookup,
        }
    
    @staticmethod
    def _build_mutation_lookup(
        aa_to_codons: dict,
        codon_to_aa: dict,
        synonymous: dict,
        stop_codons: list,
        all_codons: list,
    ) -> dict:
        """Build mutation lookup tables for all mutation types.
        
        Mutation types:
        - any_codon: All 63 other codons (uniform)
        - nonsynonymous_first: First codon of each different amino acid including stop (uniform)
        - nonsynonymous_random: All codons encoding different amino acids including stop (non-uniform)
        - missense_only_first: First codon of each different AA, excluding stop (uniform)
        - missense_only_random: All codons for different AAs, excluding stop (non-uniform)
        - synonymous: Synonymous codons only (non-uniform)
        - nonsense: Stop codons for non-stop codons, empty for stops (uniform)
        
        Returns:
            Dict mapping mutation_type -> codon -> list of alternative codons
        """
        lookup: dict[str, dict[str, list[str]]] = {}
        
        # 1. any_codon: all other codons
        lookup['any_codon'] = {
            codon: [c for c in all_codons if c != codon]
            for codon in all_codons
        }
        
        # 2. nonsynonymous_first: different AA/stop, first codon
        lookup['nonsynonymous_first'] = {}
        for codon in all_codons:
            current_aa = codon_to_aa[codon]
            lookup['nonsynonymous_first'][codon] = [
                aa_to_codons[aa][0]
                for aa in aa_to_codons.keys()
                if aa != current_aa
            ]
        
        # 3. nonsynonymous_random: different AA/stop, all codons
        lookup['nonsynonymous_random'] = {}
        for codon in all_codons:
            current_aa = codon_to_aa[codon]
            mutations = []
            for aa, codon_list in aa_to_codons.items():
                if aa != current_aa:
                    mutations.extend(codon_list)
            lookup['nonsynonymous_random'][codon] = mutations
        
        # 4. missense_only_first: different AA, first codon, NO stop
        lookup['missense_only_first'] = {}
        for codon in all_codons:
            current_aa = codon_to_aa[codon]
            lookup['missense_only_first'][codon] = [
                aa_to_codons[aa][0]
                for aa in aa_to_codons.keys()
                if aa != current_aa and aa != '*'
            ]
        
        # 5. missense_only_random: different AA, all codons, NO stop
        lookup['missense_only_random'] = {}
        for codon in all_codons:
            current_aa = codon_to_aa[codon]
            mutations = []
            for aa, codon_list in aa_to_codons.items():
                if aa != current_aa and aa != '*':
                    mutations.extend(codon_list)
            lookup['missense_only_random'][codon] = mutations
        
        # 6. synonymous: synonymous codons (copy to avoid mutation)
        lookup['synonymous'] = {
            codon: syns[:] for codon, syns in synonymous.items()
        }
        
        # 7. nonsense: stop codons for non-stop codons
        lookup['nonsense'] = {
            codon: [] if codon in stop_codons else stop_codons[:]
            for codon in all_codons
        }
        
        return lookup
    
    def get_mutations(self, codon: str, mutation_type: str) -> list[str]:
        """Get available mutations for a codon.
        
        Args:
            codon: The codon to mutate (uppercase)
            mutation_type: Type of mutation
        
        Returns:
            List of alternative codons
        
        Raises:
            ValueError: If mutation_type is invalid
            KeyError: If codon is not in the codon table
        """
        if mutation_type not in self.mutation_lookup:
            valid_types = list(self.mutation_lookup.keys())
            raise ValueError(
                f"mutation_type must be one of {valid_types}, got '{mutation_type}'"
            )
        return self.mutation_lookup[mutation_type][codon.upper()]
    
    def num_mutations(self, codon: str, mutation_type: str) -> int:
        """Get number of available mutations for a codon.
        
        Args:
            codon: The codon to mutate (uppercase)
            mutation_type: Type of mutation
        
        Returns:
            Number of alternative codons available
        """
        return len(self.get_mutations(codon, mutation_type))
    
    def is_uniform(self, mutation_type: str) -> bool:
        """Check if a mutation type has uniform alternatives across all codons.
        
        Uniform means every codon has the same number of mutation alternatives.
        This is required for sequential mode enumeration.
        
        Args:
            mutation_type: Type of mutation to check
        
        Returns:
            True if uniform, False otherwise
        """
        counts = [
            len(alts) for alts in self.mutation_lookup[mutation_type].values()
        ]
        return len(set(counts)) == 1
    
    def uniform_num_mutations(self, mutation_type: str) -> int | None:
        """Get the uniform number of mutations for a mutation type.
        
        Args:
            mutation_type: Type of mutation
        
        Returns:
            Number of alternatives if uniform, None if non-uniform
        """
        if not self.is_uniform(mutation_type):
            return None
        # All counts are the same, return the first
        first_codon = next(iter(self.mutation_lookup[mutation_type]))
        return len(self.mutation_lookup[mutation_type][first_codon])


# Pre-instantiated standard codon table for convenience
STANDARD_CODON_TABLE = CodonTable('standard')


def get_codon_table(codon_table: Union[str, dict] = 'standard') -> CodonTable:
    """Get a CodonTable instance.
    
    Args:
        codon_table: Either 'standard' or a custom dict mapping AA -> codons
    
    Returns:
        CodonTable instance
    """
    if codon_table == 'standard':
        return STANDARD_CODON_TABLE
    return CodonTable(codon_table)
