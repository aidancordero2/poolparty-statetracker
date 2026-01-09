"""Tests for the highlighter module."""

import pytest
import poolparty as pp
from poolparty.highlighter import (
    Highlighter,
    apply_highlights,
    add_highlight,
    clear_highlights,
    set_highlights,
    STYLE_CODES,
    _BASIC_FG_CODES,
    _resolve_styles,
)


class TestHighlighterBasics:
    """Test basic Highlighter creation and attributes."""

    def test_create_with_style(self):
        """Test creating highlighter with just a style."""
        hl = Highlighter('red')
        assert hl.style == 'red'
        assert hl._code == '91'
        assert hl.region is None
        assert hl.which == 'contents'

    def test_all_styles(self):
        """Test all available styles have correct codes."""
        for style, code in STYLE_CODES.items():
            hl = Highlighter(style)
            assert hl._code == code

    def test_with_region(self):
        """Test creating highlighter with region."""
        hl = Highlighter('green', region='cre')
        assert hl.region == 'cre'

    def test_with_which_upper(self):
        """Test creating highlighter with which='upper'."""
        hl = Highlighter('blue', which='upper')
        assert hl.which == 'upper'
        assert hl._excludes_tags is True

    def test_with_which_lower(self):
        """Test creating highlighter with which='lower'."""
        hl = Highlighter('cyan', which='lower')
        assert hl.which == 'lower'
        assert hl._excludes_tags is True

    def test_with_which_gap(self):
        """Test creating highlighter with which='gap'."""
        hl = Highlighter('yellow', which='gap')
        assert hl.which == 'gap'
        assert hl._excludes_tags is True

    def test_with_which_tags(self):
        """Test creating highlighter with which='tags'."""
        hl = Highlighter('magenta', which='tags')
        assert hl.which == 'tags'
        assert hl._excludes_tags is False

    def test_with_regex_overrides_which(self):
        """Test that regex parameter overrides which."""
        hl = Highlighter('red', which='upper', regex=r'ACG')
        assert hl.regex == r'ACG'
        assert hl.which is None

    def test_repr(self):
        """Test string representation."""
        hl = Highlighter('red', region='M', which='lower')
        r = repr(hl)
        assert 'Highlighter' in r
        assert "'red'" in r
        assert "'M'" in r
        assert "'lower'" in r


class TestHighlighterReset:
    """Test Highlighter.reset() static method."""

    def test_strips_ansi_codes(self):
        """Test that reset strips ANSI escape codes."""
        text = '\033[91mRED\033[0m normal \033[92mGREEN\033[0m'
        assert Highlighter.reset(text) == 'RED normal GREEN'

    def test_strips_combined_codes(self):
        """Test that reset strips combined ANSI codes."""
        text = '\033[1;4;95mSTYLED\033[0m'
        assert Highlighter.reset(text) == 'STYLED'

    def test_preserves_plain_text(self):
        """Test that reset preserves plain text."""
        text = 'ACGTACGT'
        assert Highlighter.reset(text) == text


class TestHighlighterApply:
    """Test Highlighter.apply() method."""

    def test_apply_all(self):
        """Test apply with which='all'."""
        hl = Highlighter('red', which='all')
        result = hl.apply('ACG')
        assert result == '\033[91mACG\033[0m'

    def test_apply_upper(self):
        """Test apply with which='upper' only highlights uppercase."""
        hl = Highlighter('red', which='upper')
        result = hl.apply('AcGt')
        # Should highlight A and G, not c and t
        assert '\033[91mA\033[0m' in result
        assert 'c' in result
        assert '\033[91mG\033[0m' in result
        assert 't' in result

    def test_apply_lower(self):
        """Test apply with which='lower' only highlights lowercase."""
        hl = Highlighter('cyan', which='lower')
        result = hl.apply('AcGt')
        # Should highlight c and t, not A and G
        clean = Highlighter.reset(result)
        assert clean == 'AcGt'
        assert '\033[96mc\033[0m' in result

    def test_apply_gap(self):
        """Test apply with which='gap' highlights gap characters."""
        hl = Highlighter('yellow', which='gap')
        result = hl.apply('A-C.G T')
        assert '\033[93m-\033[0m' in result or '\033[93m' in result

    def test_apply_empty_string(self):
        """Test apply on empty string."""
        hl = Highlighter('red')
        assert hl.apply('') == ''

    def test_apply_with_region(self):
        """Test apply only highlights within specified region."""
        hl = Highlighter('green', region='M')
        result = hl.apply('AA<M>CC</M>TT')
        clean = Highlighter.reset(result)
        assert clean == 'AA<M>CC</M>TT'
        # CC should be highlighted, AA and TT should not
        assert '\033[92mCC\033[0m' in result

    def test_apply_preserves_markers(self):
        """Test that apply preserves XML marker tags."""
        hl = Highlighter('red', region='M')
        result = hl.apply('AA<M>GGG</M>TT')
        clean = Highlighter.reset(result)
        assert '<M>' in clean
        assert '</M>' in clean


class TestApplyHighlights:
    """Test apply_highlights() function for multiple highlighters."""

    def test_empty_highlighters(self):
        """Test with empty highlighters list returns original text."""
        result = apply_highlights('ACGT', [])
        assert result == 'ACGT'

    def test_single_highlighter(self):
        """Test with single highlighter."""
        hl = Highlighter('red')
        result = apply_highlights('ACGT', [hl])
        assert '\033[91mACGT\033[0m' in result

    def test_strips_existing_ansi(self):
        """Test that existing ANSI codes are stripped first."""
        hl = Highlighter('green')
        result = apply_highlights('\033[91mACGT\033[0m', [hl])
        assert '\033[92mACGT\033[0m' in result
        assert '\033[91m' not in result


class TestOverlappingHighlightPriority:
    """Test that overlapping foreground colors use correct priority."""

    def test_later_foreground_wins_cyan_over_yellow(self):
        """Test cyan (later) wins over yellow when overlapping."""
        h1 = Highlighter('yellow')  # priority 0
        h2 = Highlighter('cyan')    # priority 1
        result = apply_highlights('A', [h1, h2])
        # Cyan (96) should win
        assert '\033[96m' in result
        assert '\033[93m' not in result

    def test_later_foreground_wins_red_over_yellow(self):
        """Test red (later) wins over yellow - the bug fix case."""
        h1 = Highlighter('yellow')  # priority 0
        h2 = Highlighter('red')     # priority 1
        result = apply_highlights('A', [h1, h2])
        # Red (91) should win, not yellow (93)
        assert '\033[91m' in result
        assert '\033[93m' not in result

    def test_partial_overlap_uses_priority(self):
        """Test partial overlap with region uses correct priority."""
        h1 = Highlighter('yellow', region='M')   # priority 0, all contents
        h2 = Highlighter('red', region='M', which='lower')  # priority 1, lowercase only
        result = apply_highlights('AA<M>GGcc</M>TT', [h1, h2])
        clean = Highlighter.reset(result)
        assert clean == 'AA<M>GGcc</M>TT'
        # GG should be yellow (93), cc should be red (91)
        assert '\033[93mGG\033[0m' in result
        assert '\033[91mcc\033[0m' in result


class TestAdditiveStyles:
    """Test that non-foreground styles combine additively."""

    def test_bold_plus_underline(self):
        """Test bold + underline combine."""
        h1 = Highlighter('bold')
        h2 = Highlighter('underline')
        result = apply_highlights('A', [h1, h2])
        # Should have both codes: 1 and 4
        assert '\033[1;4m' in result or '\033[4;1m' in result

    def test_bold_plus_color(self):
        """Test bold + color combine."""
        h1 = Highlighter('bold')
        h2 = Highlighter('red')
        result = apply_highlights('A', [h1, h2])
        # Should have both: 1 and 91
        assert '1' in result.split('\033[')[1]
        assert '91' in result

    def test_bold_underline_color_combine(self):
        """Test bold + underline + color all combine."""
        h1 = Highlighter('bold')
        h2 = Highlighter('underline')
        h3 = Highlighter('magenta')
        result = apply_highlights('A', [h1, h2, h3])
        # Should have all three: 1, 4, 95
        codes_part = result.split('\033[')[1].split('m')[0]
        assert '1' in codes_part
        assert '4' in codes_part
        assert '95' in codes_part


class TestResolveStyles:
    """Test _resolve_styles() helper function."""

    def test_single_foreground(self):
        """Test with single foreground color."""
        result = _resolve_styles({'91': 0})
        assert result == ['91']

    def test_two_foregrounds_picks_higher_priority(self):
        """Test with two foreground colors, picks higher priority."""
        result = _resolve_styles({'91': 0, '93': 1})
        assert result == ['93']  # priority 1 wins

    def test_foreground_plus_bold(self):
        """Test foreground + bold both included."""
        result = _resolve_styles({'91': 0, '1': 0})
        assert sorted(result) == ['1', '91']

    def test_multiple_foregrounds_one_bold(self):
        """Test multiple foregrounds + bold."""
        result = _resolve_styles({'91': 0, '93': 1, '1': 0})
        # Should include bold and the higher-priority foreground (93)
        assert '1' in result
        assert '93' in result
        assert '91' not in result


class TestPartyIntegration:
    """Test add_highlight, clear_highlights, set_highlights."""

    def test_add_highlight_creates_and_adds(self):
        """Test add_highlight creates Highlighter and adds to party."""
        pp.clear_highlights()
        pp.add_highlight('red')
        party = pp.get_active_party()
        assert len(party._highlights) == 1
        hl = party._highlights[-1]
        assert isinstance(hl, Highlighter)
        assert hl.style == 'red'

    def test_add_highlight_with_params(self):
        """Test add_highlight with all parameters."""
        pp.clear_highlights()
        pp.add_highlight('green', region='M', which='lower')
        party = pp.get_active_party()
        hl = party._highlights[-1]
        assert hl.style == 'green'
        assert hl.region == 'M'
        assert hl.which == 'lower'

    def test_clear_highlights(self):
        """Test clear_highlights removes all highlights."""
        pp.add_highlight('red')
        pp.add_highlight('blue')
        pp.clear_highlights()
        party = pp.get_active_party()
        assert len(party._highlights) == 0

    def test_set_highlights_replaces(self):
        """Test set_highlights replaces existing highlights."""
        pp.add_highlight('red')
        pp.add_highlight('blue')

        new_highlights = [Highlighter('green'), Highlighter('yellow')]
        pp.set_highlights(new_highlights)

        party = pp.get_active_party()
        assert len(party._highlights) == 2
        assert party._highlights[0].style == 'green'
        assert party._highlights[1].style == 'yellow'

    def test_set_highlights_empty_clears(self):
        """Test set_highlights with empty list clears highlights."""
        pp.add_highlight('red')
        pp.set_highlights([])
        party = pp.get_active_party()
        assert len(party._highlights) == 0


class TestHighlighterWithTags:
    """Test which='tags' highlighting."""

    def test_tags_highlights_all_tags(self):
        """Test which='tags' highlights all XML tags."""
        hl = Highlighter('green', which='tags')
        result = hl.apply('AA<M>BB</M>CC')
        # Tags <M> and </M> should be highlighted
        assert '\033[92m<M>\033[0m' in result
        assert '\033[92m</M>\033[0m' in result

    def test_tags_with_region_highlights_specific(self):
        """Test which='tags' with region highlights only that region's tags."""
        hl = Highlighter('green', region='M', which='tags')
        result = hl.apply('AA<M>BB</M><N>CC</N>')
        clean = Highlighter.reset(result)
        assert clean == 'AA<M>BB</M><N>CC</N>'
        # Only <M> and </M> should be highlighted, not <N> and </N>
        assert '\033[92m<M>\033[0m' in result
        assert '\033[92m</M>\033[0m' in result


class TestHighlighterWithRegex:
    """Test custom regex patterns."""

    def test_regex_pattern(self):
        """Test custom regex pattern."""
        hl = Highlighter('magenta', regex=r'ACG')
        result = hl.apply('XXACGXX')
        assert '\033[95mACG\033[0m' in result

    def test_regex_multiple_matches(self):
        """Test regex with multiple matches."""
        hl = Highlighter('cyan', regex=r'AA')
        result = hl.apply('AAXXYAA')
        # Both AA should be highlighted
        clean = Highlighter.reset(result)
        assert clean == 'AAXXYAA'
        assert result.count('\033[96m') == 2
