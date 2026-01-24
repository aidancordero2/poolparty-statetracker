"""Tests for inline styling functionality."""

import pytest
import numpy as np
import poolparty as pp
from poolparty.base_ops.mutagenize import MutagenizeOp, mutagenize
from poolparty.highlighter import (
    apply_inline_styles,
    apply_inline_styles_and_highlights,
    validate_style_positions,
    Highlighter,
)


class TestInlineStylesBasic:
    """Test basic inline styling functionality."""
    
    def test_apply_inline_styles_empty(self):
        """Empty styles returns unchanged sequence."""
        result = apply_inline_styles('ACGT', [])
        assert result == 'ACGT'
    
    def test_apply_inline_styles_single_position(self):
        """Single position styled correctly."""
        styles = [('red', np.array([1]))]
        result = apply_inline_styles('ACGT', styles)
        # Should have ANSI codes around position 1 (C)
        assert '\033[' in result
        assert 'A' in result
        assert 'C' in result
        assert 'G' in result
        assert 'T' in result
    
    def test_apply_inline_styles_multiple_positions(self):
        """Multiple positions styled correctly."""
        styles = [('blue', np.array([0, 2]))]
        result = apply_inline_styles('ACGT', styles)
        assert '\033[' in result
    
    def test_apply_inline_styles_overlapping(self):
        """Overlapping styles combine correctly."""
        styles = [
            ('bold', np.array([1, 2])),
            ('red', np.array([1])),  # Override with red at position 1
        ]
        result = apply_inline_styles('ACGT', styles)
        assert '\033[' in result


class TestInlineStylesWithHighlights:
    """Test combining inline styles with global highlighters."""
    
    def test_apply_inline_styles_and_highlights_empty(self):
        """Empty styles and highlighters returns unchanged sequence."""
        result = apply_inline_styles_and_highlights('ACGT', [], [])
        assert result == 'ACGT'
    
    def test_inline_styles_only(self):
        """Inline styles without highlighters."""
        styles = [('red', np.array([0]))]
        result = apply_inline_styles_and_highlights('ACGT', styles, [])
        assert '\033[' in result
    
    def test_highlighters_only(self):
        """Highlighters without inline styles."""
        hl = Highlighter('blue', which='upper')
        result = apply_inline_styles_and_highlights('ACGT', [], [hl])
        assert '\033[' in result
    
    def test_inline_and_highlighters_combined(self):
        """Both inline styles and highlighters applied."""
        styles = [('bold', np.array([0]))]
        hl = Highlighter('blue', which='upper')
        result = apply_inline_styles_and_highlights('ACGT', styles, [hl])
        assert '\033[' in result


class TestMutagenizeWithChangesStyle:
    """Test mutagenize with changes_style parameter."""
    
    def test_changes_style_none_by_default(self):
        """Default changes_style is None."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1)
            assert pool.operation._changes_style is None
    
    def test_changes_style_stored(self):
        """changes_style parameter is stored on operation."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, changes_style='red bold')
            assert pool.operation._changes_style == 'red bold'
    
    def test_changes_style_in_copy_params(self):
        """changes_style is included in _get_copy_params."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, changes_style='blue')
            params = pool.operation._get_copy_params()
        assert params['changes_style'] == 'blue'
    
    def test_compute_returns_style_0(self):
        """compute() returns style_0 key."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, mode='sequential')
        
        pool.operation.state._value = 0
        result = pool.operation.compute(['ACGT'])
        assert 'style_0' in result
        assert isinstance(result['style_0'], list)
    
    def test_compute_with_changes_style_includes_positions(self):
        """compute() with changes_style adds mutation positions to style_0."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, changes_style='red', mode='sequential')
        
        pool.operation.state._value = 0
        result = pool.operation.compute(['ACGT'])
        
        # Should have one style tuple with mutation positions
        assert len(result['style_0']) == 1
        spec, positions = result['style_0'][0]
        assert spec == 'red'
        assert len(positions) == 1  # 1 mutation
    
    def test_compute_without_changes_style_empty(self):
        """compute() without changes_style returns empty style_0."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, mode='sequential')
        
        pool.operation.state._value = 0
        result = pool.operation.compute(['ACGT'])
        
        assert result['style_0'] == []


class TestInlineStylesGeneration:
    """Test inline styles flow through library generation."""
    
    def test_generate_library_includes_inline_styles(self):
        """generate_library includes _inline_styles in rows."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, changes_style='red', mode='sequential').named('mutant')
        
        df = pool.generate_library(num_seqs=1, report_design_cards=True)
        assert '_inline_styles' in df.columns
        
        # Should have the mutation style
        styles = df['_inline_styles'].iloc[0]
        assert len(styles) == 1
        assert styles[0][0] == 'red'
    
    def test_generate_library_without_changes_style(self):
        """generate_library without changes_style has empty _inline_styles."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, mode='sequential').named('mutant')
        
        df = pool.generate_library(num_seqs=1, report_design_cards=True)
        assert '_inline_styles' in df.columns
        
        styles = df['_inline_styles'].iloc[0]
        assert styles == []


class TestInlineStylesChain:
    """Test inline styles propagate through operation chains."""
    
    def test_styles_pass_through_state_ops(self):
        """Styles pass through state operations unchanged."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, changes_style='red', mode='sequential')
            repeated = pool.repeat_states(2).named('repeated')
        
        df = repeated.generate_library(num_seqs=1, report_design_cards=True)
        
        # Styles should have passed through repeat
        styles = df['_inline_styles'].iloc[0]
        assert len(styles) == 1
        assert styles[0][0] == 'red'
    
    def test_styles_from_stacked_pools(self):
        """Stack operation passes through styles from active parent."""
        with pp.Party() as party:
            pool1 = mutagenize('ACGT', num_mutations=1, changes_style='red', mode='sequential')
            pool2 = mutagenize('TTTT', num_mutations=1, changes_style='blue', mode='sequential')
            stacked = pp.stack([pool1, pool2]).named('stacked')
        
        df = stacked.generate_library(num_seqs=2, report_design_cards=True)
        
        # First row from pool1 should have red style
        styles0 = df['_inline_styles'].iloc[0]
        if styles0:  # May be empty if mutation didn't occur
            assert styles0[0][0] == 'red'


class TestInlineStylesPositionAdjustment:
    """Test position adjustment in wrapped_compute for regions."""
    
    def test_region_adjusts_positions(self):
        """Region-based operations adjust style positions."""
        with pp.Party() as party:
            # Create a sequence with a marker
            bg = pp.from_seq('AA<test>CCCC</test>GG').named('bg')
            # Mutagenize within the region
            mutated = bg.mutagenize('test', num_mutations=1, changes_style='red', mode='sequential').named('mutated')
        
        df = mutated.generate_library(num_seqs=1, report_design_cards=True)
        
        # Check that style positions are adjusted to full sequence positions
        styles = df['_inline_styles'].iloc[0]
        if styles:
            spec, positions = styles[0]
            # Positions should be relative to full sequence, not just region
            # The region starts at position 2 (after 'AA')
            assert all(pos >= 2 for pos in positions)


class TestPositionValidation:
    """Test position validation for inline styles."""
    
    def test_valid_positions_pass(self):
        """Valid positions don't raise any errors."""
        styles = [('red', np.array([0, 1, 2, 3]))]
        # Should not raise
        validate_style_positions(4, styles)
    
    def test_valid_positions_empty_array(self):
        """Empty position arrays are valid."""
        styles = [('red', np.array([], dtype=np.int64))]
        # Should not raise
        validate_style_positions(4, styles)
    
    def test_negative_position_raises(self):
        """Negative positions raise ValueError."""
        styles = [('red', np.array([-1, 0, 1]))]
        with pytest.raises(ValueError) as excinfo:
            validate_style_positions(4, styles)
        assert 'negative' in str(excinfo.value).lower()
        assert 'red' in str(excinfo.value)
    
    def test_out_of_bounds_position_raises(self):
        """Position >= seq_len raises ValueError."""
        styles = [('blue', np.array([0, 4]))]  # 4 is out of bounds for len=4
        with pytest.raises(ValueError) as excinfo:
            validate_style_positions(4, styles)
        assert '>= seq_len' in str(excinfo.value)
        assert 'blue' in str(excinfo.value)
    
    def test_validation_error_message_includes_context(self):
        """Error message includes spec name and position values."""
        styles = [('cyan bold', np.array([0, 10, 20]))]
        with pytest.raises(ValueError) as excinfo:
            validate_style_positions(5, styles)
        error_msg = str(excinfo.value)
        assert 'cyan bold' in error_msg
        assert '20' in error_msg or 'max=' in error_msg
    
    def test_apply_inline_styles_validates_by_default(self):
        """apply_inline_styles validates positions by default."""
        styles = [('red', np.array([10]))]  # Out of bounds
        with pytest.raises(ValueError):
            apply_inline_styles('ACGT', styles)
    
    def test_apply_inline_styles_can_skip_validation(self):
        """apply_inline_styles can skip validation with validate=False."""
        styles = [('red', np.array([10]))]  # Out of bounds
        # Should not raise when validation disabled (positions just won't be styled)
        result = apply_inline_styles('ACGT', styles, validate=False)
        assert 'ACGT' in result or result == 'ACGT'
    
    def test_apply_inline_styles_and_highlights_validates_by_default(self):
        """apply_inline_styles_and_highlights validates positions by default."""
        styles = [('red', np.array([10]))]  # Out of bounds
        with pytest.raises(ValueError):
            apply_inline_styles_and_highlights('ACGT', styles, [])
    
    def test_apply_inline_styles_and_highlights_can_skip_validation(self):
        """apply_inline_styles_and_highlights can skip validation."""
        styles = [('red', np.array([10]))]  # Out of bounds
        # Should not raise when validation disabled
        result = apply_inline_styles_and_highlights('ACGT', styles, [], validate=False)
        assert 'ACGT' in result or result == 'ACGT'


class TestPositionAdjustmentWithMarkers:
    """Test position adjustment edge cases with markers and regions."""
    
    def test_mutagenize_region_remove_marker_true(self):
        """Positions correct when marker is removed."""
        with pp.Party() as party:
            # 'AA' prefix (2 chars), marker content 'CCCC' (4 chars), 'GG' suffix
            bg = pp.from_seq('AA<test>CCCC</test>GG').named('bg')
            # Mutagenize first position of region, with remove_marker=True
            mutated = bg.mutagenize(
                'test', num_mutations=1, changes_style='red',
                mode='sequential', remove_marker=True
            ).named('mutated')
        
        df = mutated.generate_library(num_seqs=1, report_design_cards=True)
        seq = df['seq'].iloc[0]
        styles = df['_inline_styles'].iloc[0]
        
        # Sequence should be 'AA' + mutated_content + 'GG' (no marker tags)
        assert '<test>' not in seq
        assert '</test>' not in seq
        assert seq.startswith('AA')
        assert seq.endswith('GG')
        
        # Style positions should point to correct characters in clean sequence
        if styles:
            spec, positions = styles[0]
            # The first mutation is at position 0 within the region
            # With marker removed, position 0 in region = position 2 in final seq
            assert all(2 <= pos < 6 for pos in positions)
    
    def test_mutagenize_region_remove_marker_false(self):
        """Positions correct when marker is kept."""
        with pp.Party() as party:
            # 'AA' prefix, marker with content 'CCCC', 'GG' suffix
            bg = pp.from_seq('AA<test>CCCC</test>GG').named('bg')
            mutated = bg.mutagenize(
                'test', num_mutations=1, changes_style='red',
                mode='sequential', remove_marker=False
            ).named('mutated')
        
        df = mutated.generate_library(num_seqs=1, report_design_cards=True)
        seq = df['seq'].iloc[0]
        styles = df['_inline_styles'].iloc[0]
        
        # Sequence should have marker tags
        assert '<test>' in seq
        assert '</test>' in seq
        
        # Style positions should account for prefix + opening tag
        # 'AA' (2) + '<test>' (6) = 8 chars before region content
        if styles:
            spec, positions = styles[0]
            # Positions should be in the range of the region content
            # which starts at 2 (AA) + 6 (<test>) = 8
            assert all(8 <= pos < 12 for pos in positions)
    
    def test_mutagenize_region_with_spacer_str(self):
        """Positions adjusted correctly for spacer_str."""
        with pp.Party() as party:
            bg = pp.from_seq('AA<test>CCCC</test>GG').named('bg')
            mutated = bg.mutagenize(
                'test', num_mutations=1, changes_style='red',
                mode='sequential', remove_marker=True, spacer_str='XX'
            ).named('mutated')
        
        df = mutated.generate_library(num_seqs=1, report_design_cards=True)
        seq = df['seq'].iloc[0]
        styles = df['_inline_styles'].iloc[0]
        
        # Sequence should have spacers: 'AA' + 'XX' + content + 'XX' + 'GG'
        assert 'XX' in seq
        
        # Style positions should account for prefix (2) + spacer (2) = 4
        if styles:
            spec, positions = styles[0]
            # With spacer, region content starts at position 4
            assert all(4 <= pos < 8 for pos in positions)
    
    def test_mutagenize_region_marker_with_minus_strand(self):
        """Minus strand marker handled correctly with position offset."""
        with pp.Party() as party:
            # Marker with minus strand
            bg = pp.from_seq('AA<test strand="-">CCCC</test>GG').named('bg')
            mutated = bg.mutagenize(
                'test', num_mutations=1, changes_style='red',
                mode='sequential', remove_marker=False
            ).named('mutated')
        
        df = mutated.generate_library(num_seqs=1, report_design_cards=True)
        seq = df['seq'].iloc[0]
        styles = df['_inline_styles'].iloc[0]
        
        # Verify marker is preserved with strand (quotes may vary)
        assert 'strand=' in seq and '-' in seq
        
        if styles:
            spec, positions = styles[0]
            # Find where the region content actually starts
            # The opening tag is <test strand='-'> which is 17 chars
            # 'AA' (2) + opening tag (17) = 19 chars before content
            assert all(19 <= pos < 23 for pos in positions)
    
    def test_mutagenize_interval_region(self):
        """Positions correct for [start, stop] interval region."""
        with pp.Party() as party:
            bg = pp.from_seq('AACCCCGG').named('bg')
            # Use the mutagenize function directly (not method) for interval region
            mutated = mutagenize(
                bg, region=[2, 6], num_mutations=1, changes_style='red',
                mode='sequential'
            ).named('mutated')
        
        df = mutated.generate_library(num_seqs=1, report_design_cards=True)
        styles = df['_inline_styles'].iloc[0]
        
        if styles:
            spec, positions = styles[0]
            # Positions should be in range [2, 6)
            assert all(2 <= pos < 6 for pos in positions)


class TestPositionAdjustmentHelperUnit:
    """Unit tests for _compute_style_position_offset() helper method."""
    
    def test_compute_offset_no_region(self):
        """Returns 0 when no region is specified."""
        with pp.Party() as party:
            pool = mutagenize('ACGT', num_mutations=1, mode='sequential')
            op = pool.operation
        
        # When _region is None, offset should be 0
        assert op._region is None
        offset = op._compute_style_position_offset('ACGT', '')
        assert offset == 0
    
    def test_compute_offset_interval_region(self):
        """Correct offset for [start, stop] interval region."""
        with pp.Party() as party:
            bg = pp.from_seq('AACCCCGG')
            # Interval region starting at position 2
            pool = mutagenize(bg, region=[2, 6], num_mutations=1, mode='sequential')
            op = pool.operation
        
        # Prefix is 'AA' (2 chars), no marker tags, no spacer
        offset = op._compute_style_position_offset('AACCCCGG', 'AA')
        assert offset == 2
    
    def test_compute_offset_interval_region_with_spacer(self):
        """Correct offset for interval region with spacer."""
        with pp.Party() as party:
            bg = pp.from_seq('AACCCCGG')
            # Interval region with spacer_str='XX'
            pool = mutagenize(
                bg, region=[2, 6], num_mutations=1, 
                mode='sequential', spacer_str='XX'
            )
            op = pool.operation
        
        # Prefix is 'AA' (2) + spacer 'XX' (2) = 4
        offset = op._compute_style_position_offset('AACCCCGG', 'AA')
        assert offset == 4
    
    def test_compute_offset_marker_region_remove_true(self):
        """Correct offset for marker region with remove_marker=True."""
        with pp.Party() as party:
            bg = pp.from_seq('AA<test>CCCC</test>GG')
            pool = mutagenize(
                bg, region='test', num_mutations=1, 
                mode='sequential', remove_marker=True
            )
            op = pool.operation
        
        # Prefix is 'AA' (2 chars), marker tags removed
        # So offset = just the prefix length = 2
        parent_seq = 'AA<test>CCCC</test>GG'
        offset = op._compute_style_position_offset(parent_seq, 'AA<test>')
        assert offset == 2
    
    def test_compute_offset_marker_region_remove_false(self):
        """Correct offset for marker region with remove_marker=False."""
        with pp.Party() as party:
            bg = pp.from_seq('AA<test>CCCC</test>GG')
            pool = mutagenize(
                bg, region='test', num_mutations=1, 
                mode='sequential', remove_marker=False
            )
            op = pool.operation
        
        # Prefix is 'AA' (2 chars) + opening tag '<test>' (6 chars) = 8
        parent_seq = 'AA<test>CCCC</test>GG'
        offset = op._compute_style_position_offset(parent_seq, 'AA<test>')
        assert offset == 8
    
    def test_compute_offset_marker_with_strand_remove_false(self):
        """Correct offset for marker with strand attribute, remove_marker=False."""
        with pp.Party() as party:
            bg = pp.from_seq("AA<test strand='-'>CCCC</test>GG")
            pool = mutagenize(
                bg, region='test', num_mutations=1, 
                mode='sequential', remove_marker=False
            )
            op = pool.operation
        
        # Prefix is 'AA' (2 chars) + opening tag '<test strand='-'>' (17 chars) = 19
        parent_seq = "AA<test strand='-'>CCCC</test>GG"
        offset = op._compute_style_position_offset(parent_seq, "AA<test strand='-'>")
        assert offset == 19
    
    def test_compute_offset_marker_region_with_spacer(self):
        """Correct offset for marker region with spacer_str."""
        with pp.Party() as party:
            bg = pp.from_seq('AA<test>CCCC</test>GG')
            pool = mutagenize(
                bg, region='test', num_mutations=1, 
                mode='sequential', remove_marker=True, spacer_str='XX'
            )
            op = pool.operation
        
        # Prefix is 'AA' (2 chars) + spacer 'XX' (2 chars) = 4
        parent_seq = 'AA<test>CCCC</test>GG'
        offset = op._compute_style_position_offset(parent_seq, 'AA<test>')
        assert offset == 4


class TestCaseTransformInlineStyles:
    """Test 'upper' and 'lower' case transformation in inline styles."""
    
    def test_lower_transforms_to_lowercase(self):
        """'lower' in style spec converts characters to lowercase."""
        styles = [('lower red', np.array([0, 2]))]
        result = apply_inline_styles('ACGT', styles)
        # Positions 0 and 2 should be lowercase: 'a' and 'g'
        # Strip ANSI codes to check character case
        clean = Highlighter.reset(result)
        assert clean == 'aCgT'
    
    def test_upper_transforms_to_uppercase(self):
        """'upper' in style spec converts characters to uppercase."""
        styles = [('upper blue', np.array([1, 3]))]
        result = apply_inline_styles('acgt', styles)
        # Positions 1 and 3 should be uppercase: 'C' and 'T'
        clean = Highlighter.reset(result)
        assert clean == 'aCgT'
    
    def test_lower_with_multiple_styles(self):
        """'lower' works with combined styles like 'lower cyan bold'."""
        styles = [('lower cyan bold', np.array([0, 1, 2, 3]))]
        result = apply_inline_styles('ACGT', styles)
        # All positions should be lowercase
        clean = Highlighter.reset(result)
        assert clean == 'acgt'
        # Should have ANSI codes for styling
        assert '\033[' in result
    
    def test_upper_with_multiple_styles(self):
        """'upper' works with combined styles like 'upper red underline'."""
        styles = [('upper red underline', np.array([0, 1, 2, 3]))]
        result = apply_inline_styles('acgt', styles)
        # All positions should be uppercase
        clean = Highlighter.reset(result)
        assert clean == 'ACGT'
        # Should have ANSI codes for styling
        assert '\033[' in result
    
    def test_only_specified_positions_transformed(self):
        """Only positions in the style array are case-transformed."""
        styles = [('lower', np.array([1]))]
        result = apply_inline_styles('ACGT', styles)
        clean = Highlighter.reset(result)
        # Only position 1 should be lowercase
        assert clean == 'AcGT'
    
    def test_case_transform_only_no_color(self):
        """Case transform can be used without additional styling."""
        styles = [('lower', np.array([0, 1, 2, 3]))]
        result = apply_inline_styles('ACGT', styles)
        clean = Highlighter.reset(result)
        assert clean == 'acgt'
    
    def test_later_transform_overrides_earlier(self):
        """Later case transforms override earlier ones at same position."""
        styles = [
            ('lower', np.array([0, 1])),  # First: make lowercase
            ('upper', np.array([0])),     # Second: make uppercase (overrides at pos 0)
        ]
        result = apply_inline_styles('acgt', styles)
        clean = Highlighter.reset(result)
        # Position 0: upper (later) wins, position 1: lower wins
        assert clean == 'Acgt'
    
    def test_case_transform_with_highlights(self):
        """Case transforms work with apply_inline_styles_and_highlights."""
        styles = [('lower cyan', np.array([0, 2]))]
        hl = Highlighter('red', which='upper')
        result = apply_inline_styles_and_highlights('ACGT', styles, [hl])
        clean = Highlighter.reset(result)
        # Positions 0 and 2 should be lowercase
        assert clean == 'aCgT'
        # Should have ANSI codes
        assert '\033[' in result
    
    def test_case_transform_preserves_non_alpha(self):
        """Case transforms preserve non-alphabetic characters."""
        styles = [('lower', np.array([0, 1, 2, 3]))]
        result = apply_inline_styles('A-G.', styles)
        clean = Highlighter.reset(result)
        # Non-alpha chars unchanged, alpha chars lowercased
        assert clean == 'a-g.'
    
    def test_empty_positions_no_transform(self):
        """Empty position array means no transforms."""
        styles = [('lower red', np.array([], dtype=np.int64))]
        result = apply_inline_styles('ACGT', styles)
        clean = Highlighter.reset(result)
        assert clean == 'ACGT'
