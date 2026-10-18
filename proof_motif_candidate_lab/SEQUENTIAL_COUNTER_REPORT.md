# Prefix-threshold sequential-counter audit

**Status:** completed bounded certificate audit. This does not prove P=NP or
P!=NP.

The experiment adds a cardinality language beyond pairwise at-most-one (AMO).
For inputs `x_1,...,x_n`, state `q[i,j]` means that the first `i` inputs contain
at least `j` true values. Each state is defined by the exact recurrence

```text
q[i,j] = q[i-1,j] OR (x_i AND q[i-1,j-1]).
```

The final unit `NOT q[n,k+1]` is therefore the unweighted inequality
`sum(x_i) <= k`. The producer reconstructs every CNF clause from a supplied
input/state role map; the independent reviewer reconstructs the same clauses
without importing the producer.

The saved positive instance has five inputs and threshold two. Exhaustive
enumeration of all 20 variables agrees with the projected relation exactly.
Removing a recurrence clause, changing a literal, or checking the formula with
threshold one is rejected. A role-permuted copy is accepted when its explicit
certificate supplies the renamed roles. A separate bounded signed
incidence-graph search recovers that role map without metadata; the
deliberately canonical-layout scanner still returns `NOT_FOUND` for the same
copy. Capping the graph search at eight variables returns `UNKNOWN_CAP`, so
the structural proposal step is not presented as universal polynomial
discovery.

The scaling rows use thresholds `floor(n/2)` for `n=1..7`. Rows through the
20-variable semantic budget receive exhaustive projection checks; larger rows
are structurally checked and report `ACCEPT_STRUCTURAL_UNKNOWN_SEMANTIC`.
This makes the exact cost boundary visible: certificate validation is
polynomial in the supplied role map and clause list, while unrestricted role
discovery and semantic projection are not silently counted as polynomial.

This is a reusable proof-producing cardinality primitive, not a general PB
solver. The next unresolved question is whether standard sequential, totalizer,
or sorting-network encodings can be discovered from arbitrary CNF with a
complete complexity bound, rather than moving the hard search into a bounded
graph or role recognizer.

Artifacts:

- `sequential_counter.py` — counter reconstruction, verifier, and bounded signed graph search;
- `run_sequential_counter.py` — positive, mutation, role-permutation, and scale fixtures;
- `review_sequential_counter.py` — independent recurrence and projection replay;
- `SEQUENTIAL_COUNTER_RESULTS.json` — serialized certificate and controls;
- `SEQUENTIAL_COUNTER_REVIEW.json` — independent review record.
