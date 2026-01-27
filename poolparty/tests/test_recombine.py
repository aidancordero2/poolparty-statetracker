"""Tests for the Recombine operation."""

import pytest
import numpy as np
import poolparty as pp
from poolparty.base_ops.recombine import RecombineOp, recombine


class TestRecombineFactory:
    """Test recombine factory function."""
    
    def test_returns_pool(self):
        """recombine returns a Pool object."""
        with pp.Party() as party:
            pool = recombine(source_pools=['ACGT', 'TGCA'])
            assert pool is not None
            assert hasattr(pool, 'operation')
    
    def test_creates_recombine_op(self):
        """Pool's operation is RecombineOp."""
        with pp.Party() as party:
            pool = recombine(source_pools=['ACGT', 'TGCA'])
            assert isinstance(pool.operation, RecombineOp)
    
    def test_accepts_string_inputs(self):
        """Factory accepts strings in source_pools."""
        with pp.Party() as party:
            pool = recombine(source_pools=['ACGT', 'TGCA']).named('recombined')
        
        df = pool.generate_library(num_seqs=1, seed=42)
        assert len(df['seq'].iloc[0]) == 4
    
    def test_accepts_pool_inputs(self):
        """Factory accepts Pool objects in source_pools."""
        with pp.Party() as party:
            pool1 = pp.from_seq('ACGT')
            pool2 = pp.from_seq('TGCA')
            pool = recombine(source_pools=[pool1, pool2]).named('recombined')
        
        df = pool.generate_library(num_seqs=1, seed=42)
        assert len(df['seq'].iloc[0]) == 4
    
    def test_accepts_mixed_inputs(self):
        """Factory accepts mix of strings and Pools in source_pools."""
        with pp.Party() as party:
            pool1 = pp.from_seq('ACGT')
            pool = recombine(source_pools=[pool1, 'TGCA']).named('recombined')
        
        df = pool.generate_library(num_seqs=1, seed=42)
        assert len(df['seq'].iloc[0]) == 4


class TestRecombineParameterValidation:
    """Test parameter validation."""
    
    def test_requires_at_least_two_source_pools(self):
        """source_pools must have at least 2 pools."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="must contain at least 2 pools"):
                recombine(source_pools=['ACGT'])
    
    def test_requires_fixed_length(self):
        """All source pools must have fixed seq_length."""
        with pp.Party() as party:
            pool1 = pp.from_seqs(['ACGT', 'AAAAA'])  # Variable length
            with pytest.raises(ValueError, match="must have a fixed seq_length"):
                recombine(source_pools=[pool1, 'ACGT'])
    
    def test_requires_same_length(self):
        """All source pools must have the same seq_length."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="must have the same seq_length"):
                recombine(source_pools=['ACGT', 'TGCAA'])
    
    def test_num_breakpoints_minimum(self):
        """num_breakpoints must be >= 1."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="num_breakpoints must be >= 1"):
                recombine(source_pools=['ACGT', 'TGCA'], num_breakpoints=0)
    
    def test_num_breakpoints_maximum(self):
        """num_breakpoints must be <= seq_length - 1."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="exceeds seq_length - 1"):
                recombine(source_pools=['ACGT', 'TGCA'], num_breakpoints=4)
    
    def test_not_enough_positions(self):
        """positions must have enough elements for num_breakpoints."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="Not enough positions"):
                recombine(source_pools=['ACGT', 'TGCA'], num_breakpoints=2, positions=[0])
    
    def test_invalid_position_negative(self):
        """Negative positions are invalid."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="Invalid position"):
                recombine(source_pools=['ACGT', 'TGCA'], positions=[-1, 0, 1])
    
    def test_invalid_position_too_large(self):
        """Positions >= seq_length - 1 are invalid."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="Invalid position"):
                recombine(source_pools=['ACGT', 'TGCA'], positions=[0, 1, 2, 3])
    
    def test_styles_wrong_length(self):
        """styles must have length num_breakpoints + 1."""
        with pp.Party() as party:
            with pytest.raises(ValueError, match="styles must have length 2"):
                recombine(source_pools=['ACGT', 'TGCA'], num_breakpoints=1, styles=['red'])


class TestRecombineBasicFunctionality:
    """Test basic recombination functionality."""
    
    def test_simple_recombination_fixed_mode(self):
        """Simple recombination in fixed mode."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],  # Break after index 1
                mode='fixed'
            ).named('recombined')
        
        df = pool.generate_library()
        assert len(df) == 1
        # Fixed mode uses first position (1) with round-robin pool assignment
        # Segment 0: [0:2] from pool 0 = 'AA'
        # Segment 1: [2:4] from pool 1 = 'TT'
        assert df['seq'].iloc[0] == 'AATT'
    
    def test_recombination_preserves_length(self):
        """Recombined sequences preserve length."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['ACGTACGT', 'TGCATGCA'],
                num_breakpoints=2,
                mode='random',
                num_states=10
            ).named('recombined')
        
        df = pool.generate_library(seed=42)
        assert all(len(seq) == 8 for seq in df['seq'])
    
    def test_breakpoint_interpretation(self):
        """Breakpoint position i means 'after index i'."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[0],  # Break after index 0
                mode='fixed'
            ).named('recombined')
        
        df = pool.generate_library()
        # Segment 0: [0:1] from pool 0 = 'A'
        # Segment 1: [1:4] from pool 1 = 'TTT'
        assert df['seq'].iloc[0] == 'ATTT'
    
    def test_multiple_breakpoints(self):
        """Recombination with multiple breakpoints."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=2,
                positions=[0, 2],  # Break after indices 0 and 2
                mode='fixed'
            ).named('recombined')
        
        df = pool.generate_library()
        # Segment 0: [0:1] from pool 0 = 'A'
        # Segment 1: [1:3] from pool 1 = 'TT'
        # Segment 2: [3:4] from pool 2%2=0 = 'A'
        assert df['seq'].iloc[0] == 'ATTA'


class TestRecombineSequentialMode:
    """Test sequential mode enumeration."""
    
    def test_sequential_enumeration_count(self):
        """Sequential mode enumerates correct number of states."""
        with pp.Party() as party:
            # 2 source pools, 1 breakpoint, 3 valid positions [0,1,2]
            # States = C(3,1) × N × (N-1)^K = 3 × 2 × 1 = 6
            # (consecutive segments must come from different pools)
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                mode='sequential'
            ).named('recombined')
        
        assert pool.num_states == 6
        df = pool.generate_library()
        assert len(df) == 6
    
    def test_sequential_all_unique(self):
        """Sequential mode generates all combinations with no self-recombination."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[0, 1],
                mode='sequential'
            ).named('recombined')
        
        df = pool.generate_library()
        # C(2,1) × N × (N-1)^K = 2 × 2 × 1 = 4 states
        assert len(df) == 4
        # All should be unique since consecutive segments differ
        assert len(df['seq'].unique()) == 4
    
    def test_no_self_recombination(self):
        """Consecutive segments must come from different pools."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                mode='sequential'
            ).named('recombined')
        
        op_name = pool.operation.name
        df = pool.generate_library(report_design_cards=True)
        
        # Check that no pool_assignments have consecutive identical values
        for assignments in df[f'{op_name}.key.pool_assignments']:
            for i in range(1, len(assignments)):
                assert assignments[i] != assignments[i-1], \
                    f"Self-recombination detected: {assignments}"


class TestRecombineRandomMode:
    """Test random mode functionality."""
    
    def test_random_mode_with_seed(self):
        """Random mode with seed is reproducible."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['ACGT', 'TGCA'],
                num_breakpoints=1,
                mode='random',
                num_states=10
            ).named('recombined')
        
        df1 = pool.generate_library(seed=42)
        df2 = pool.generate_library(seed=42)
        assert df1['seq'].tolist() == df2['seq'].tolist()
    
    def test_random_mode_different_seeds(self):
        """Random mode with different seeds produces different results."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['ACGT', 'TGCA'],
                num_breakpoints=1,
                mode='random',
                num_states=10
            ).named('recombined')
        
        df1 = pool.generate_library(seed=42)
        df2 = pool.generate_library(seed=123)
        # Very unlikely to be identical with random breakpoints and assignments
        assert df1['seq'].tolist() != df2['seq'].tolist()


class TestRecombineStyles:
    """Test style inheritance and overlay."""
    
    def test_style_inheritance_from_source_pools(self):
        """Segments inherit styles from their source pools."""
        with pp.Party() as party:
            # Create source pools with styles
            pool1 = pp.from_seq('AAAA').mutagenize(num_mutations=1, style='red', mode='random', num_states=1)
            pool2 = pp.from_seq('TTTT').mutagenize(num_mutations=1, style='blue', mode='random', num_states=1)
            
            pool = recombine(
                source_pools=[pool1, pool2],
                num_breakpoints=1,
                positions=[1],
                mode='fixed'
            ).named('recombined')
        
        df = pool.generate_library(seed=42)
        # Should have some styling inherited from source pools
        assert len(df) == 1
    
    def test_styles_overlay(self):
        """styles parameter overlays on inherited styles."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed',
                styles=['green', 'yellow']
            ).named('recombined')
        
        df = pool.generate_library()
        # Should have applied green to segment 0, yellow to segment 1
        assert len(df) == 1
    
    def test_empty_string_styles(self):
        """Empty string '' means no additional styling for segment."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed',
                styles=['green', '']
            ).named('recombined')
        
        df = pool.generate_library()
        assert len(df) == 1


class TestRecombineRegionBased:
    """Test region-based recombination."""
    
    def test_region_recombination(self):
        """Recombination can replace a region."""
        with pp.Party() as party:
            # Create a pool with a region
            pool = pp.from_seq('NNNNNNNN').insert_tags(region_name='middle', start=2, stop=6)
            
            # Recombine into the region
            result = pool.recombine(
                region='middle',
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed'
            ).named('recombined')
        
        df = result.generate_library()
        # Should be: NN + AATT + NN = NNAATTNN
        assert df['seq'].iloc[0] == 'NNAATTNN'
    
    def test_region_content_discarded(self):
        """Region content is replaced, not used as source."""
        with pp.Party() as party:
            # Create a pool with content in the region
            pool = pp.from_seq('GGGGGGGG').insert_tags(region_name='middle', start=2, stop=6)
            
            # Recombine into the region (region content 'GGGG' is discarded)
            result = pool.recombine(
                region='middle',
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed'
            ).named('recombined')
        
        df = result.generate_library()
        # Should be: GG + AATT + GG = GGAATTGG
        # NOT using the original GGGG from the region
        assert df['seq'].iloc[0] == 'GGAATTGG'


class TestRecombineDesignCard:
    """Test design card generation."""
    
    def test_design_card_has_breakpoints(self):
        """Design card includes breakpoints."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed'
            ).named('recombined')
        
        op_name = pool.operation.name
        df = pool.generate_library(report_design_cards=True)
        assert f'{op_name}.key.breakpoints' in df.columns
        assert df[f'{op_name}.key.breakpoints'].iloc[0] == (1,)
    
    def test_design_card_has_pool_assignments(self):
        """Design card includes pool_assignments."""
        with pp.Party() as party:
            pool = recombine(
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed'
            ).named('recombined')
        
        op_name = pool.operation.name
        df = pool.generate_library(report_design_cards=True)
        assert f'{op_name}.key.pool_assignments' in df.columns
        assert df[f'{op_name}.key.pool_assignments'].iloc[0] == (0, 1)


class TestRecombineMixinMethod:
    """Test Pool.recombine() mixin method."""
    
    def test_mixin_method_exists(self):
        """Pool objects have recombine method."""
        with pp.Party() as party:
            pool = pp.from_seq('NNNNNNNN')
            assert hasattr(pool, 'recombine')
    
    def test_mixin_method_works(self):
        """Pool.recombine() mixin method works correctly."""
        with pp.Party() as party:
            pool = pp.from_seq('NNNNNNNN').insert_tags(region_name='middle', start=2, stop=6)
            result = pool.recombine(
                region='middle',
                source_pools=['AAAA', 'TTTT'],
                num_breakpoints=1,
                positions=[1],
                mode='fixed'
            ).named('recombined')
        
        df = result.generate_library()
        assert df['seq'].iloc[0] == 'NNAATTNN'
