"""Timing benchmarks for poolparty profiling.

Auto-discovers workload_* functions and exports ALL_WORKLOADS for run_profile.py.
"""
import importlib
import pkgutil
from pathlib import Path

# Auto-discover all public modules (exclude _utils.py, __init__.py, all.py)
_workload_modules = []
for module_info in pkgutil.iter_modules([str(Path(__file__).parent)]):
    if not module_info.name.startswith('_') and module_info.name != 'all':
        mod = importlib.import_module(f'.{module_info.name}', __package__)
        _workload_modules.append(mod)

# Build ALL_WORKLOADS from discovered modules
ALL_WORKLOADS = {}
for mod in _workload_modules:
    for name in dir(mod):
        if name.startswith('workload_'):
            fn = getattr(mod, name)
            key = name.replace('workload_', '')
            ALL_WORKLOADS[key] = fn
