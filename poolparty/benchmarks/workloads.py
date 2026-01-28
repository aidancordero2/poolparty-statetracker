"""Benchmark workloads for poolparty profiling."""
import poolparty as pp
from typing import Literal

# Workload size configurations
WORKLOAD_SIZES = {
    'small': {'seq_len': 20, 'num_seqs': 100},
    'medium': {'seq_len': 100, 'num_seqs': 1000},
    'large': {'seq_len': 500, 'num_seqs': 10000},
}


def make_sequence(length: int) -> str:
    """Generate a DNA sequence of specified length."""
    bases = 'ACGT'
    return (bases * (length // 4 + 1))[:length]


def workload_mutagenize(
    seq_len: int = 100,
    num_mut: int = 2,
    num_seqs: int = 1000,
    mode: Literal['random', 'sequential'] = 'random',
):
    """Mutagenize benchmark workload."""
    pp.init()
    seq = make_sequence(seq_len)
    pool = pp.mutagenize(seq, num_mutations=num_mut, mode=mode)
    return pool.generate_library(num_seqs=num_seqs)


def workload_mutagenize_sequential(seq_len: int = 20, num_mut: int = 1):
    """Sequential mutagenize - generates all possible mutations."""
    pp.init()
    seq = make_sequence(seq_len)
    pool = pp.mutagenize(seq, num_mutations=num_mut, mode='sequential')
    return pool.generate_library(num_cycles=1)


def workload_recombine(
    seq_len: int = 100,
    num_sources: int = 3,
    num_breakpoints: int = 2,
    num_seqs: int = 1000,
    mode: Literal['random', 'sequential'] = 'random',
):
    """Recombine benchmark workload."""
    pp.init()
    # First pool is the background, rest are sources
    bg = pp.from_seq(make_sequence(seq_len))
    sources = [pp.from_seq(make_sequence(seq_len)) for _ in range(num_sources - 1)]
    pool = pp.recombine(bg, sources=sources, num_breakpoints=num_breakpoints, mode=mode)
    return pool.generate_library(num_seqs=num_seqs)


def workload_deletion_scan(
    seq_len: int = 100,
    deletion_len: int = 5,
    num_seqs: int = 1000,
    mode: Literal['random', 'sequential'] = 'random',
):
    """Deletion scan benchmark workload."""
    pp.init()
    seq = make_sequence(seq_len)
    pool = pp.deletion_scan(seq, deletion_length=deletion_len, mode=mode)
    return pool.generate_library(num_seqs=num_seqs)


def workload_insertion_scan(
    seq_len: int = 100,
    insert_seq: str = 'NNNN',
    num_seqs: int = 1000,
    mode: Literal['random', 'sequential'] = 'random',
):
    """Insertion scan benchmark workload."""
    pp.init()
    bg = pp.from_seq(make_sequence(seq_len))
    insert = pp.from_seq(insert_seq)
    pool = pp.insertion_scan(bg, insert, mode=mode)
    return pool.generate_library(num_seqs=num_seqs)


def workload_complex_dag(
    seq_len: int = 100,
    num_seqs: int = 1000,
):
    """Complex DAG with multiple chained operations."""
    pp.init()
    seq = make_sequence(seq_len)
    
    # Chain: mutagenize -> join with barcode
    mutants = pp.mutagenize(seq, num_mutations=2, mode='random')
    barcode = pp.get_kmers(length=8, mode='random')
    pool = pp.join([mutants, '----', barcode])
    
    return pool.generate_library(num_seqs=num_seqs)


def workload_region_operations(
    seq_len: int = 100,
    num_seqs: int = 1000,
):
    """Workload with region-based operations."""
    pp.init()
    # Create sequence with region tags
    inner_len = seq_len - 20
    seq = f"ACGTACGTAC<cre>{make_sequence(inner_len)}</cre>ACGTACGTAC"
    
    pool = pp.mutagenize(seq, num_mutations=2, region='cre', mode='random')
    return pool.generate_library(num_seqs=num_seqs)


def workload_stack(
    seq_len: int = 50,
    num_pools: int = 5,
    num_seqs: int = 1000,
):
    """Stack multiple pools together."""
    pp.init()
    pools = [
        pp.mutagenize(make_sequence(seq_len), num_mutations=1, mode='random')
        for _ in range(num_pools)
    ]
    pool = pp.stack(pools)
    return pool.generate_library(num_seqs=num_seqs)


def workload_get_kmers(
    k: int = 8,
    num_seqs: int = 1000,
    mode: Literal['random', 'sequential'] = 'random',
):
    """K-mer generation workload."""
    pp.init()
    pool = pp.get_kmers(length=k, mode=mode)
    return pool.generate_library(num_seqs=num_seqs)


# Collect all workloads for easy iteration
ALL_WORKLOADS = {
    'mutagenize': workload_mutagenize,
    'mutagenize_sequential': workload_mutagenize_sequential,
    'recombine': workload_recombine,
    'deletion_scan': workload_deletion_scan,
    'insertion_scan': workload_insertion_scan,
    'complex_dag': workload_complex_dag,
    'region_operations': workload_region_operations,
    'stack': workload_stack,
    'get_kmers': workload_get_kmers,
}
