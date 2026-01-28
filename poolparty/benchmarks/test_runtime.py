"""Runtime benchmarks using pytest-benchmark."""
import pytest
from .workloads import (
    workload_mutagenize,
    workload_mutagenize_sequential,
    workload_recombine,
    workload_deletion_scan,
    workload_insertion_scan,
    workload_complex_dag,
    workload_region_operations,
    workload_stack,
    workload_get_kmers,
    WORKLOAD_SIZES,
)


# --- Small workloads (fast, for CI) ---

class TestSmallWorkloads:
    """Small workloads for quick benchmarking."""
    
    def test_mutagenize_small(self, benchmark):
        result = benchmark(
            workload_mutagenize,
            seq_len=WORKLOAD_SIZES['small']['seq_len'],
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_mutagenize_sequential_small(self, benchmark):
        # 20bp with 1 mutation = 60 states (20 positions × 3 mutations each)
        result = benchmark(workload_mutagenize_sequential, seq_len=20, num_mut=1)
        assert len(result) == 60
    
    def test_recombine_small(self, benchmark):
        result = benchmark(
            workload_recombine,
            seq_len=WORKLOAD_SIZES['small']['seq_len'],
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_deletion_scan_small(self, benchmark):
        result = benchmark(
            workload_deletion_scan,
            seq_len=WORKLOAD_SIZES['small']['seq_len'],
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_insertion_scan_small(self, benchmark):
        result = benchmark(
            workload_insertion_scan,
            seq_len=WORKLOAD_SIZES['small']['seq_len'],
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_complex_dag_small(self, benchmark):
        result = benchmark(
            workload_complex_dag,
            seq_len=WORKLOAD_SIZES['small']['seq_len'],
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_region_operations_small(self, benchmark):
        result = benchmark(
            workload_region_operations,
            seq_len=WORKLOAD_SIZES['small']['seq_len'] + 20,  # Account for flanks
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_stack_small(self, benchmark):
        result = benchmark(
            workload_stack,
            seq_len=WORKLOAD_SIZES['small']['seq_len'],
            num_pools=3,
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']
    
    def test_get_kmers_small(self, benchmark):
        result = benchmark(
            workload_get_kmers,
            k=6,
            num_seqs=WORKLOAD_SIZES['small']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['small']['num_seqs']


# --- Medium workloads ---

class TestMediumWorkloads:
    """Medium workloads for standard benchmarking."""
    
    def test_mutagenize_medium(self, benchmark):
        result = benchmark(
            workload_mutagenize,
            seq_len=WORKLOAD_SIZES['medium']['seq_len'],
            num_seqs=WORKLOAD_SIZES['medium']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['medium']['num_seqs']
    
    def test_recombine_medium(self, benchmark):
        result = benchmark(
            workload_recombine,
            seq_len=WORKLOAD_SIZES['medium']['seq_len'],
            num_seqs=WORKLOAD_SIZES['medium']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['medium']['num_seqs']
    
    def test_complex_dag_medium(self, benchmark):
        result = benchmark(
            workload_complex_dag,
            seq_len=WORKLOAD_SIZES['medium']['seq_len'],
            num_seqs=WORKLOAD_SIZES['medium']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['medium']['num_seqs']


# --- Large workloads (slow, require --run-slow) ---

@pytest.mark.slow
class TestLargeWorkloads:
    """Large workloads for thorough benchmarking."""
    
    def test_mutagenize_large(self, benchmark):
        result = benchmark(
            workload_mutagenize,
            seq_len=WORKLOAD_SIZES['large']['seq_len'],
            num_seqs=WORKLOAD_SIZES['large']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['large']['num_seqs']
    
    def test_recombine_large(self, benchmark):
        result = benchmark(
            workload_recombine,
            seq_len=WORKLOAD_SIZES['large']['seq_len'],
            num_seqs=WORKLOAD_SIZES['large']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['large']['num_seqs']
    
    def test_complex_dag_large(self, benchmark):
        result = benchmark(
            workload_complex_dag,
            seq_len=WORKLOAD_SIZES['large']['seq_len'],
            num_seqs=WORKLOAD_SIZES['large']['num_seqs'],
        )
        assert len(result) == WORKLOAD_SIZES['large']['num_seqs']
    
    def test_mutagenize_sequential_large(self, benchmark):
        # 50bp with 2 mutations = large combinatorial space
        result = benchmark(workload_mutagenize_sequential, seq_len=50, num_mut=2)
        # C(50, 2) × 3^2 = 1225 × 9 = 11025 states
        assert len(result) == 11025
