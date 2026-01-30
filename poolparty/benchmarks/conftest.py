"""Pytest configuration for benchmarks."""
import csv
import pytest

FIELDS = ['test_name', 'mean', 'stddev', 'min', 'max', 'rounds']


def _format_time_ms(seconds: float) -> str:
    """Format time value in milliseconds with consistent decimal places."""
    ms = seconds * 1000
    return f"{ms:.2f}"


def _print_table(rows: list[dict]):
    """Print benchmarks as a formatted table to stdout."""
    headers = ['Test Name', 'Mean (ms)', 'StdDev (ms)', 'Min (ms)', 'Max (ms)', 'Rounds']
    right_align = [False, True, True, True, True, True]
    
    formatted = []
    for row in rows:
        formatted.append([
            row['test_name'],
            _format_time_ms(row['mean']),
            _format_time_ms(row['stddev']),
            _format_time_ms(row['min']),
            _format_time_ms(row['max']),
            str(row['rounds']),
        ])
    
    widths = [len(h) for h in headers]
    for row in formatted:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))
    
    print()
    header_line = "  ".join(
        h.rjust(widths[i]) if right_align[i] else h.ljust(widths[i])
        for i, h in enumerate(headers)
    )
    print(header_line)
    print("-" * len(header_line))
    for row in formatted:
        print("  ".join(
            val.rjust(widths[i]) if right_align[i] else val.ljust(widths[i])
            for i, val in enumerate(row)
        ))
    print()


def _write_csv(rows: list[dict], csv_path: str):
    """Write benchmarks to CSV file."""
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} benchmarks to {csv_path}")


def pytest_addoption(parser):
    """Add benchmark-specific command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow benchmarks (large workloads)",
    )
    parser.addoption(
        "-T", "--table",
        action="store_true",
        default=False,
        help="Print benchmark results as formatted table",
    )
    parser.addoption(
        "-O", "--output",
        type=str,
        default=None,
        help="Output CSV file path for benchmark results",
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --run-slow is given."""
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Output custom benchmark table/CSV after pytest-benchmark's output."""
    show_table = config.getoption("--table", default=False)
    output_path = config.getoption("--output", default=None)
    
    if not show_table and not output_path:
        return
    
    # Access pytest-benchmark's stored results
    benchmarks = getattr(config, '_benchmarksession', None)
    if benchmarks is None or not hasattr(benchmarks, 'benchmarks'):
        return
    
    benchmark_list = benchmarks.benchmarks
    if not benchmark_list:
        return
    
    # Extract stats from each benchmark
    rows = []
    for bench in benchmark_list:
        stats = bench.stats
        rows.append({
            'test_name': bench.name,
            'mean': stats.mean,
            'stddev': stats.stddev,
            'min': stats.min,
            'max': stats.max,
            'rounds': stats.rounds,
        })
    
    if show_table:
        _print_table(rows)
    
    if output_path:
        _write_csv(rows, output_path)
