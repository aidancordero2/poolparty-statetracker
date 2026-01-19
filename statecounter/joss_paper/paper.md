---
title: 'StateCounter: state tracking for composite objects in complex combinatorial libraries'
tags:
  - Python
  - combinatorics
  - enumeration
  - experimental design
  - counter algebra
authors:
  - name: Zhihan Liu
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Justin B. Kinney
    orcid: 0000-0003-1897-3778
    corresponding: true
    affiliation: 1
affiliations:
  - name: Cold Spring Harbor Laboratory, Cold Spring Harbor, NY, USA
    index: 1
date: 17 January 2026
bibliography: paper.bib
---

# Summary

StateCounter is a Python library created to solve a technical problem that can arise in a variety of scientific computing tasks: given the state of a composite object created using complex combinatorial processes, determine the states of each component object. The core computational units in StateCounter are Counters, each of which represents the state of an abstract object. After defining a set of parent Counters, users create child counters using combinatorial operations that include Cartesian products, disjoint unions (i.e., stacking), repetition, slicing, shuffling, splitting, and sampling. Then when a user sets the state of a derived Counter, StateCounter automatically computes the state of all parent counters by traversing of the derived Counter's computational graph in reverse. We developed StateCounter specifically to allow tracking of DNA sequence generation and mutation processes used to create complex DNA sequence libraries. More generally, however, StateCounter addresses a fundamental computational need that is not addressed by existing Python software.

# Statement of Need

We encountered the need for StateCounter when creating PoolParty, a Python package for generating complex DNA sequence libraries. Fig. 1 shows one example application--creating a DNA sequence library comprising different types of variants of a cis-regulatory element (CRE). Each variant CRE is created using a specific mutational process applied to a wild-type sequence. The first sequence is the wild-type sequence; no mutations are applied. The next 5 sequences comprise CREs with randomly scattered point mutations. The next 5 sequences comprise CREs containing 5 nt deletions at tiled positions. The next 10 sequences comprise CREs with one of two binding sites inserted at 5 tiled postions. Each one of these sequences is then repeated 2 times and linked to a random 5-mer serving as a barcode. The problem we faced was this: given a value $n$, how do we compute which mutations to introduce into the sequence and which barcode to attach? This computation is particularly useful for systematically naming the generated sequences. 

![Figure 1: Sequence Library genereated by PoolParty](fig1.png)

The need we encountered here is quite general -- how does one trace the state of a complex composite object back to the states of its components. This is the problem that StateCounter was created to solve. 



# State of the Field

Python provides several tools for working with combinatorial structures, but none address the state propagation problem that StateCounter solves. The `itertools` module provides `product` for Cartesian products and `chain` for concatenation, but these return iterators or tuples without any mechanism to trace a flat index back to component values. NumPy's `unravel_index` and `ravel_multi_index` functions convert between flat and multi-dimensional indices, but only for rectangular array shapes; they cannot represent structures like disjoint unions or nested combinations of products and unions. Manual index arithmetic using `divmod` works for simple products but does not compose—each additional operation (slicing, shuffling, sampling) requires rewriting the index logic from scratch. 

# Software Design

StateCounter addresses this gap by constructing a directed acyclic graph (DAG) of counters where setting the state of a derived counter automatically propagates to all parent counters. Thus, while users construct the DAG from leaves to root, state information flows from root to leaves. This enables arbitrary composition of products, stacks, slices, shuffles, samples, and splits while maintaining correct state tracking throughout.

The basic unit is a Counter, which represents an object that can take on a finite number of discrete states numbered from 0 to $n-1$. Users first create "leaf" counters specifying the number of states, then compose them using operations to build derived counters. The following operations are supported:

| Operation | Description |
|-----------|-------------|
| `product` | Cartesian product; all parent counters active |
| `stack` | Disjoint union; one parent counter active at a time |
| `slice` | Select subset of states |
| `shuffle` | Randomly permute states |
| `sample` | Sample states with or without replacement |
| `split` | Divide into sub-counters by count or proportion |
| `repeat` | Cycle through states multiple times |
| `sync` | Synchronize counters in lockstep |
| `interleave` | Alternate between counters |

All counters must be created within a `Manager` context that tracks counter relationships and assigns unique identifiers. When a counter appears in multiple branches of the DAG, StateCounter detects conflicting state assignments—situations where two paths would require the same parent counter to have different values simultaneously.

## Example

![Figure 2: State tracking carried out by StateCounter](fig2.png)

The following code constructs the counter DAG for the sequence library in Fig. 1. Five leaf counters represent the component dimensions: mutation index, deletion position, insertion site, insertion position, and barcode variant. These are composed using `product` and `stack` to build the full 40-state counter.

```python
from statecounter import Manager, Counter, product, stack

# Initialize manager
with Manager() as mgr:
    
    # Define leaf counters
    mut_counter = Counter(5, name='mut_counter')
    del_counter = Counter(5, name='del_counter')
    ins_site_counter = Counter(2, name='ins_site_counter')
    ins_position_counter = Counter(5, name='ins_position_counter')
    v_counter = Counter(2).named('v_counter')
    
    # Build composite counters
    ins_counter = product([ins_position_counter, ins_site_counter],
        name='ins_counter')
    cre_counter = stack([mut_counter, del_counter, ins_counter],
        name='cre_counter')
    seq_counter = product([v_counter, cre_counter],
        name='seq_counter')
    
# Print DAG
seq_counter.print_dag('minimal')

# Print sequences
seq_counter.get_iteration_df()
```

The `print_dag()` method displays the counter hierarchy. The `cre` counter stacks three alternatives (5 mutations + 5 deletions + 10 insertions = 20 states), and `seq` takes the product with the 2-state barcode counter, yielding 40 total states.

```
seq_counter (n=40)
└── [Product]
    ├── v_counter (n=2)
    └── cre_counter (n=20)
        └── [Stack]
            ├── mut_counter (n=5)
            ├── del_counter (n=5)
            └── ins_counter (n=10)
                └── [Product]
                    ├── ins_position_counter (n=5)
                    └── ins_site_counter (n=2)
```

# Research Impact Statement

# AI Usage Disclosure
Z.L. and J.B.K. concieved the project and designed the software architecture. Code was written in Cursor by J.B.K. with iterative assisstance from Claude Opus 4.5. Tests and documentation were written by Opus 4.5 with human editing. Z.H. and J.B.K. wrote the paper using Claude Opus 4.5 for help with the initial draft. Z.L. and J.B.K. bear full responsibility for the text of the paper, the documentation, and the content of the software.   

# Acknowledgements

This work was supported by NIH grant R01 HG011787.

# References
