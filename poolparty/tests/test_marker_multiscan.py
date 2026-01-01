"""Tests for marker_multiscan operation."""
import pytest
import poolparty as pp
from poolparty.operations.marker_multiscan import MarkerMultiScanOp
from poolparty.marker import Marker
from poolparty.alphabet import MARKER_PATTERN


class TestMarkerMultiScanFactory:
    def test_returns_pool_and_converts_strings(self):
        with pp.Party():
            result = pp.marker_multiscan(
                'ACGT',
                markers=['m0', 'm1'],
                num_insertions=2,
                insertion_mode='ordered',
                mode='random',
            )
        assert hasattr(result, 'operation')
        assert isinstance(result.operation, MarkerMultiScanOp)

    def test_rejects_invalid_modes(self):
        with pp.Party():
            with pytest.raises(ValueError, match="supports only mode='random' or 'hybrid'"):
                pp.marker_multiscan('ACGT', markers=['m'], num_insertions=1, mode='sequential')

    def test_hybrid_requires_num_states(self):
        with pp.Party():
            with pytest.raises(ValueError, match="num_hybrid_states is required"):
                pp.marker_multiscan('ACGT', markers=['m'], num_insertions=1, mode='hybrid')


class TestInsertionModes:
    def test_ordered_requires_len_match(self):
        with pp.Party():
            with pytest.raises(ValueError, match="requires len\\(markers\\) == num_insertions"):
                pp.marker_multiscan(
                    'ACGT',
                    markers=['m0'],
                    num_insertions=2,
                    insertion_mode='ordered',
                    mode='random',
                )

    def test_unordered_len_check(self):
        with pp.Party():
            with pytest.raises(ValueError, match="len\\(markers\\) >= num_insertions"):
                pp.marker_multiscan(
                    'ACGT',
                    markers=['m0'],
                    num_insertions=2,
                    insertion_mode='unordered',
                    mode='random',
                )

    def test_unordered_unique_tags(self):
        with pp.Party():
            pool = pp.marker_multiscan(
                'AAAA',
                markers=['a', 'b', 'c'],
                num_insertions=2,
                insertion_mode='unordered',
                mode='random',
            )
            df = pool.generate_seqs(num_seqs=1, seed=11)
        tags = MARKER_PATTERN.findall(df['seq'].iloc[0])
        assert len(tags) == 2
        assert len(tags) == len(set(tags))

    def test_ordered_assigns_in_sequence_order(self):
        with pp.Party():
            pool = pp.marker_multiscan(
                'ACGT',
                markers=['first', 'second'],
                num_insertions=2,
                insertion_mode='ordered',
                mode='random',
            )
            df = pool.generate_seqs(num_seqs=1, seed=2)
        seq = df['seq'].iloc[0]
        assert seq.index('{first}') < seq.index('{second}')


class TestPositionsAndExclusions:
    def test_excludes_marker_interiors(self):
        with pp.Party():
            pool = pp.marker_multiscan(
                'A{pre}B',
                markers=['outer'],
                num_insertions=1,
                insertion_mode='ordered',
                mode='random',
            )
            df = pool.generate_seqs(num_seqs=1, seed=3)
        seq = df['seq'].iloc[0]
        assert '{outer}' in seq
        assert seq.count('{') == 2  # outer plus pre

    def test_positions_are_sorted_and_count_matches(self):
        with pp.Party():
            pool = pp.marker_multiscan(
                'ABCDE',
                markers=['m0', 'm1', 'm2'],
                num_insertions=3,
                insertion_mode='unordered',
                mode='random',
            )
            df = pool.generate_seqs(num_seqs=1, seed=5)
        seq = df['seq'].iloc[0]
        tags = list(MARKER_PATTERN.finditer(seq))
        assert len(tags) == 3
        positions = [m.start() for m in tags]
        assert positions == sorted(positions)
