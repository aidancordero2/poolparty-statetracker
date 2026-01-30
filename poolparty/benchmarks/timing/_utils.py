"""Shared utilities for timing benchmarks."""

DEFAULT_NUM_SEQS = 1000
DEFAULT_SEQ_LEN = 100


def make_sequence(length: int) -> str:
    """Generate a DNA sequence of specified length."""
    bases = "ACGT"
    return (bases * (length // 4 + 1))[:length]


def collect_local_specs(module_globals: dict) -> dict:
    """Collect benchmark specs from workload functions in the given module."""
    specs = {}
    for name, obj in module_globals.items():
        if name.startswith("workload_") and hasattr(obj, "benchmark_specs"):
            for spec in obj.benchmark_specs:
                test_class, param, values = spec[:3]
                constants = spec[3] if len(spec) > 3 else {}
                if test_class not in specs:
                    specs[test_class] = []
                specs[test_class].append((obj, param, values, constants, True))
    return specs


def generate_benchmark_tests(specs: dict) -> dict:
    """Generate pytest benchmark test classes from a specification dict."""
    classes = {}
    for class_name, benchmarks in specs.items():
        methods = {}
        for workload, param, values, constants, enabled in benchmarks:
            if not enabled:
                continue

            for val in values:
                val_str = str(val).replace(".", "_")
                const_parts = [f"{k}_{str(v).replace('.', '_')}" for k, v in constants.items()]
                param_part = f"{param}_{val_str}"
                name_parts = [workload.__name__] + const_parts + [param_part]
                test_name = "test_" + "_".join(name_parts)
                all_kwargs = {**constants, param: val}

                def make_test(w, kwargs):
                    def test(self, benchmark):
                        benchmark(w, **kwargs)

                    return test

                methods[test_name] = make_test(workload, all_kwargs)

        classes[f"{class_name}"] = type(f"{class_name}", (), methods)
    return classes
