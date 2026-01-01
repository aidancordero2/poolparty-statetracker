"""Tests for replace_marker operation."""
import pytest
import poolparty as pp
from poolparty.operations.replace_marker import ReplaceMarkerOp


class TestReplaceMarkerFactory:
    def test_basic_replacement(self):
        with pp.Party():
            m = pp.Marker(name='ins')
            bg = pp.from_seq('AAA{ins}TTT')
            ins = pp.from_seq('GGG')
            result = pp.replace_marker(bg, ins, m)
            df = result.generate_seqs(num_seqs=1)
        assert df['seq'].iloc[0] == 'AAAGGGTTT'

    def test_string_inputs(self):
        with pp.Party():
            m = pp.Marker(name='X')
            result = pp.replace_marker('CC{X}GG', 'AAA', m)
            df = result.generate_seqs(num_seqs=1)
        assert df['seq'].iloc[0] == 'CCAAAGG'

    def test_marker_from_string_name(self):
        with pp.Party():
            bg = pp.from_seq('AT{mymarker}CG')
            ins = pp.from_seq('XXXX')
            # String creates a new Marker with that name
            result = pp.replace_marker(bg, ins, 'mymarker')
            df = result.generate_seqs(num_seqs=1)
        assert df['seq'].iloc[0] == 'ATXXXXCG'

    def test_returns_pool_with_correct_op(self):
        with pp.Party():
            m = pp.Marker(name='m')
            result = pp.replace_marker('A{m}T', 'GG', m)
        assert hasattr(result, 'operation')
        assert isinstance(result.operation, ReplaceMarkerOp)


class TestCounterComposition:
    def test_counter_is_product_of_parents(self):
        with pp.Party():
            m = pp.Marker(name='slot')
            bg = pp.from_seqs(['A{slot}', 'G{slot}'], mode='sequential')
            ins = pp.from_seqs(['CC', 'TT', 'AA'], mode='sequential')
            result = pp.replace_marker(bg, ins, m)
        # bg has 2 states, ins has 3 states -> result should have 6 states
        assert result.num_states == 6

    def test_sequential_enumeration(self):
        with pp.Party():
            m = pp.Marker(name='slot')
            bg = pp.from_seqs(['X{slot}', 'Y{slot}'], mode='sequential')
            ins = pp.from_seqs(['1', '2'], mode='sequential')
            result = pp.replace_marker(bg, ins, m)
            df = result.generate_seqs(num_complete_iterations=1)
        seqs = df['seq'].tolist()
        # Ordered product: bg iterates slower, ins iterates faster
        assert 'X1' in seqs
        assert 'X2' in seqs
        assert 'Y1' in seqs
        assert 'Y2' in seqs
        assert len(seqs) == 4


class TestValidation:
    def test_error_when_marker_not_found(self):
        with pp.Party():
            m = pp.Marker(name='missing')
            bg = pp.from_seq('ACGT')  # No marker
            ins = pp.from_seq('TTT')
            result = pp.replace_marker(bg, ins, m)
            with pytest.raises(ValueError, match="not found in background"):
                result.generate_seqs(num_seqs=1)

    def test_error_when_marker_occurs_multiple_times(self):
        with pp.Party():
            m = pp.Marker(name='dup')
            bg = pp.from_seq('A{dup}T{dup}G')  # Marker appears twice
            ins = pp.from_seq('XX')
            result = pp.replace_marker(bg, ins, m)
            with pytest.raises(ValueError, match="occurs 2 times"):
                result.generate_seqs(num_seqs=1)

class TestWithMarkerScan:
    def test_marker_scan_then_replace(self):
        with pp.Party():
            m = pp.Marker(name='ins_point')
            scanned = pp.marker_scan('ACGT', marker=m, mode='sequential')
            insert = pp.from_seqs(['XX', 'YY'], mode='sequential')
            result = pp.replace_marker(scanned, insert, m)
            df = result.generate_seqs(num_complete_iterations=1)
        # 5 positions * 2 inserts = 10 sequences
        assert len(df) == 10
        # All sequences should have the insert and no marker tags
        for seq in df['seq']:
            assert '{' not in seq
            assert 'XX' in seq or 'YY' in seq
