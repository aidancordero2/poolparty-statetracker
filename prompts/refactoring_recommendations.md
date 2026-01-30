# Poolparty Refactoring Recommendations

This document captures code simplification and consolidation opportunities identified in the poolparty codebase. The goal is to improve maintainability and make the code easier for users to understand.

---

## Executive Summary

The poolparty codebase has grown organically and now has several areas with duplicated code, inconsistent naming, and complex abstractions. Key opportunities for improvement:

1. **Consolidate duplicated scan operation code** - Multiple scan ops share 70%+ identical code
2. **Simplify the Pool class** - 894 lines with 30+ method wrappers
3. **Standardize parameter naming** - Same concepts have different names across files
4. **Reduce Operation base class complexity** - Region and style handling are intricate
5. **Eliminate factory function boilerplate** - Repetitive pattern across all operations

---

## Priority 1: Reduce Duplication in Scan Operations

### Problem

The scan operations (`deletion_scan`, `insertion_scan`, `shuffle_scan`, `region_scan`) share approximately 70% identical code:

- `_validate_positions()` helper is duplicated verbatim in:
  - `poolparty/src/poolparty/scan_ops/deletion_scan.py` (lines 12-29)
  - `poolparty/src/poolparty/region_ops/region_scan.py` (lines 97-114)
- `_build_caches()` methods are nearly identical across scan operations
- Sequential/random mode handling logic is repeated
- Position validation against sequence length follows same pattern

### Recommendation

Create a `ScanOpMixin` class or extract shared utilities:

```python
# Extract to scan_ops/base.py or utils/scan_utils.py
class ScanOpMixin:
    def _validate_positions(self, positions, max_position, min_position=0) -> list[int]:
        """Validate and normalize position specification."""
        ...

    def _build_position_cache(self, seq_length, item_length, positions) -> int:
        """Build cache for sequential enumeration based on seq_length."""
        ...

    def _select_position(self, valid_indices, rng):
        """Select position based on mode (random or sequential)."""
        ...
```

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| Medium | High | Low |

---

## Priority 2: Simplify the Pool Class

### Problem

`poolparty/src/poolparty/pool.py` is 894 lines and contains a method wrapper for nearly every operation (30+ methods). Each wrapper just calls through to the factory function:

```python
def mutagenize(self, region=None, num_mutations=None, ...) -> Pool_type:
    from .base_ops.mutagenize import mutagenize
    return mutagenize(pool=self, region=region, num_mutations=num_mutations, ...)
```

This creates:
- Maintenance burden when adding new operations
- Docstring sync issues (the hack at end of `__init__.py` lines 150-202)
- Large class that's hard to navigate

### Recommendation

Option A: Use `__getattr__` to dynamically delegate to factory functions

Option B: Move operation methods to separate mixin classes:

```python
class Pool(PoolBase, SequenceOpsMixin, StateOpsMixin, ScanOpsMixin, RegionOpsMixin):
    ...
```

Option C: Remove Pool methods entirely - users call factory functions directly

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| Medium | High | Medium |

---

## Priority 3: Consolidate Inconsistent Parameter Naming

### Problem

The same concept has different names across the codebase:

| Concept | Variations Found |
|---------|------------------|
| Parent pool | `parent_pool`, `pool`, `bg_pool`, `parent_pools[0]` |
| State count | `num_states`, `num_values`, `validated_num_values` |
| Operation state | `op.state`, `self.state`, `self._state` |

Examples:
- `mutagenize.py`: uses `pool` parameter
- `deletion_scan.py`: uses `parent_pool` in Op, `pool` in factory
- `deletion_multiscan.py`: uses `bg_pool`
- `state_sample.py`: uses `parent_pool`

### Recommendation

Standardize on:
- `pool` for single parent input, `parent_pools` for list (in factory functions)
- `parent_pool` in Operation `__init__` when single parent
- `num_states` at public API level, `num_values` only in statetracker layer
- Add a naming convention section to contributing documentation

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| Low | Medium | Low |

---

## Priority 4: Simplify Operation Base Class

### Problem

`poolparty/src/poolparty/operation.py` is 640 lines with complex logic:

- `__init__` has many branching paths for mode/state handling (lines 33-110)
- Region handling logic (lines 146-254) is intricate
- `wrapped_compute()` style position adjustment (lines 365-514) duplicates concepts
- Every subclass must implement `_get_copy_params()` boilerplate

### Recommendation

1. **Extract region handling** to a `RegionHandler` helper class:

```python
class RegionHandler:
    def __init__(self, region: RegionType, remove_tags: bool):
        ...

    def extract(self, seq: str) -> tuple[str, str, str]:
        """Return (prefix, region_content, suffix)."""
        ...

    def reassemble(self, prefix, new_content, suffix) -> str:
        """Reassemble sequence with new region content."""
        ...
```

2. **Extract style adjustment** to utility functions in `style_utils.py`

3. **Consider auto-generating `_get_copy_params()`** via introspection or a decorator

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| High | High | Medium |

---

## Priority 5: Reduce Factory Function + Operation Class Boilerplate

### Problem

Every operation requires two components with repetitive structure:

1. **Factory function** - validates args, creates Op, wraps in Pool
2. **Operation class** - with `__init__`, `compute`, `_get_copy_params`

Example pattern repeated ~20 times:

```python
@beartype
def some_operation(pool, arg1, arg2, mode='random', num_states=None, ...) -> Pool:
    """Docstring..."""
    from ..fixed_ops.from_seq import from_seq
    pool = from_seq(pool) if isinstance(pool, str) else pool
    op = SomeOp(pool=pool, arg1=arg1, arg2=arg2, mode=mode, num_states=num_states, ...)
    return Pool(operation=op)
```

### Recommendation

Create a decorator or metaclass that generates the factory function:

```python
@operation(
    factory_name='mutagenize',
    design_card_keys=['positions', 'wt_chars', 'mut_chars'],
    accepts_string_pool=True,
)
class MutagenizeOp(Operation):
    def __init__(self, pool, num_mutations=None, mutation_rate=None, ...):
        ...
```

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| High | Medium | Medium |

---

## Priority 6: Simplify Region Handling

### Problem

Regions are handled in multiple places with complex logic:

- `RegionType = Union[str, Sequence[Integral], None]` has three interpretations
- `_resolve_region()`, `_extract_region_parts()`, `wrapped_compute()` all do region work
- `remove_tags` parameter name is confusing (it removes region *tags*, not all tags)
- Region parsing utilities in `parsing_utils.py` (566 lines) are complex

### Recommendation

1. **Rename `remove_tags`** to `strip_region_tags` for clarity

2. **Create a `RegionContext` class** that encapsulates region extraction, transformation, and reassembly:

```python
class RegionContext:
    """Manages region extraction and reassembly for an operation."""

    def __init__(self, seq: str, region: RegionType, strip_tags: bool = True):
        self.prefix, self.content, self.suffix = self._extract(seq, region)
        self.strip_tags = strip_tags
        ...

    def reassemble(self, new_content: str) -> str:
        """Reassemble sequence with new region content."""
        ...
```

3. **Make region handling opt-in** at the Operation class level rather than always in base class

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| High | High | High |

---

## Priority 7: Clean Up `__init__.py`

### Problem

`poolparty/src/poolparty/__init__.py` (203 lines) does too much:

- Imports every public symbol explicitly (lines 1-76)
- Has docstring manipulation code `_remove_pool_param_from_docstring` (lines 153-161)
- Maps Pool methods to factory functions for docstring copying (lines 164-202)
- Initializes default Party on import (line 135)

### Recommendation

1. **Move `_POOL_FACTORY_MAP`** and docstring logic to a separate `_docstrings.py` module
2. **Generate `__all__`** from submodule `__all__` lists instead of explicit listing
3. **Move default party initialization** to a lazy pattern (only init when first accessed)

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| Low | Medium | Low |

---

## Priority 8: Consolidate Style Utilities

### Problem

Style handling is spread across multiple locations:

- `poolparty/src/poolparty/utils/style_utils.py` (424 lines) - core utilities
- Each operation's `_adjust_styles` method (e.g., `deletion_scan.py` lines 314-353)
- `Operation.wrapped_compute()` style reassembly (lines 394-513)

The same style adjustment patterns are reimplemented in multiple operations.

### Recommendation

All style adjustment should go through centralized functions in `style_utils.py`:

```python
# style_utils.py additions
def adjust_styles_for_deletion(styles, del_start, del_end, gap_len) -> StyleList:
    """Adjust style positions after deletion with optional gap insertion."""
    ...

def adjust_styles_for_insertion(styles, insert_pos, insert_len) -> StyleList:
    """Adjust style positions after insertion."""
    ...

def adjust_styles_for_region_op(styles, region_start, region_end, new_len) -> StyleList:
    """Adjust style positions after region content replacement."""
    ...
```

### Effort/Impact

| Effort | Impact | Risk |
|--------|--------|------|
| Medium | Medium | Low |

---

## Quick Wins (Low Effort, High Impact)

These improvements can be made quickly with minimal risk:

1. **Extract `_validate_positions()` to `utils/`**
   - Currently duplicated identically in multiple files
   - Move to `utils/scan_utils.py` or similar

2. **Add type stubs for forward references**
   - `Pool_type` and `Operation_type` are confusing string aliases in `types.py`
   - Consider using `TYPE_CHECKING` imports for clearer type hints

3. **Add a `mode` property to Operation**
   - Currently `self.mode` is set directly as an attribute
   - Making it a property enables validation and documentation

4. **Document the Pool→Operation→State relationship**
   - The architecture isn't obvious to newcomers
   - Add a ARCHITECTURE.md or section in README

---

## Summary Table

| Priority | Area | Effort | Impact | Risk |
|----------|------|--------|--------|------|
| 1 | Scan Op consolidation | Medium | High | Low |
| 2 | Pool class methods | Medium | High | Medium |
| 3 | Parameter naming | Low | Medium | Low |
| 4 | Operation base class | High | High | Medium |
| 5 | Factory boilerplate | High | Medium | Medium |
| 6 | Region handling | High | High | High |
| 7 | `__init__.py` cleanup | Low | Medium | Low |
| 8 | Style utilities | Medium | Medium | Low |

---

## Recommended Execution Order

1. **Start with Quick Wins** - Build momentum with low-risk improvements
2. **Priority 3 (Parameter naming)** - Makes subsequent refactoring easier
3. **Priority 1 (Scan op consolidation)** - High impact, low risk
4. **Priority 7 (`__init__.py` cleanup)** - Improves code organization
5. **Priority 8 (Style utilities)** - Medium effort preparation for Priority 4
6. **Priority 2 (Pool class)** - Simplify the main user-facing class
7. **Priority 4 (Operation base)** - Core architectural improvement
8. **Priorities 5 & 6** - Larger refactors, tackle after foundation is solid

---

## Architecture Reference

### Core Class Relationships

```
Party (context manager)
├── registers pools and operations
├── manages state iteration via statetracker.Manager
└── holds genetic code (CodonTable)

Pool (DAG node)
├── wraps an Operation
├── has a State (from statetracker)
├── tracks regions present in sequences
└── provides chainable method API

Operation (transformation)
├── defines computation logic
├── may have its own State
├── specifies design_card_keys for output
└── implements compute() and _get_copy_params()

State (from statetracker)
├── represents iteration state
├── num_values = number of states
├── value = current state (0 to num_values-1)
└── supports products and syncing
```

### Key Files by Responsibility

| Responsibility | File |
|----------------|------|
| Public API | `__init__.py` |
| Core Pool class | `pool.py` |
| Operation base | `operation.py` |
| Context management | `party.py` |
| Library generation | `generate_library.py` |
| Type definitions | `types.py` |
| Region parsing | `utils/parsing_utils.py` |
| Style handling | `utils/style_utils.py` |
| DNA utilities | `utils/dna_utils.py` |
