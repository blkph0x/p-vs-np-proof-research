# Repair of historical semantic branch-DP certificates

Repaired on 2026-10-18 in `../semantic_branch_dp_lab/engine.py` and
`../semantic_branch_dp_lab/test_lab.py`. The final local suite passes
**16 tests**. Complete output, observed pre-repair behavior, exact source
hashes and the source-stability check are saved in
[SEMANTIC_CERTIFICATE_REPAIR.json](SEMANTIC_CERTIFICATE_REPAIR.json).
The archival manifest, historical result files and new holographic labs
were not modified.

## The defect and its scope

Before repair, producing a proof for `[(1,)]` and then checking it against
`[(1,), ()]` returned `True`. The external formula is UNSAT because its
second clause is empty. The checker recomputed the one stored leaf but did
not require the root to cover every original clause. The producer also
accepted incomplete clause orders, permitting the same omission at creation.

The repaired checker rejects that proof, and the producer raises `ValueError`
for the incomplete order `[0]` on the two-clause formula. Producing a complete
proof for the full formula returns UNSAT and verifies. This is a correctness
repair of the historical certificate contract, not a new algorithmic
complexity result. Historical records that depended only on local replay
should not be read as proof that original-formula coverage was checked.

## Checked certificate contract

Original clauses are supplied externally. The producer and checker validate
list/tuple formulas containing list/tuple clauses of nonzero exact integer
literals; Boolean and numeric coercions are rejected. Repeated literals,
tautologies, repeated clauses and empty clauses retain their original
semantics. Indices identify clause occurrences, so identical clauses still
have distinct indices.

Before accepting a proof, the verifier now establishes all of the following:

- The root contains exactly every original clause index, without duplicates.
- Every internal node has two children. Their index sets are disjoint and
  their union is exactly the parent's set.
- Every ordinary leaf owns exactly one clause. The sole exception is the
  empty formula, represented by one childless identity node with no indices.
- The graph of node objects is a tree. Cycles, shared children, one-sided
  branches, non-node objects and missing or malformed fields are rejected.
- Each node's variables are exactly those occurring in its original clauses.
  Its boundary is exactly the variables that also occur in a clause outside
  that node, computed from the entire external formula.
- Truth tables are nonnegative exact integers of the required width. Boolean
  aliases, negative values and bits outside that width are rejected.

The producer accepts a supplied order only when it is a complete permutation
of the original clause indices. An iterable permutation remains supported.
Verification uses iterative traversals, so even a valid highly unbalanced
tree does not depend on Python's recursion limit. The usual producer still
builds its original balanced tree.

The empty formula deliberately returns SAT with scalar truth table 1, empty
variables and boundary, and one physical identity node. An indexed empty
clause returns scalar 0 and therefore UNSAT. These cases are distinct.

## Why the semantic conclusion follows

For each validated node, its table represents the boundary assignments
extendible to a satisfying assignment of precisely its owned original
clauses. This holds at a leaf by direct enumeration of that clause's internal
variables. At an internal node, any variable shared between the children is
in both validated child boundaries. Their internal variables therefore
overlap only through the checked interfaces. Joining the two child tables
on consistent shared values and projecting to the parent boundary is exactly
existential conjunction of their disjoint clause sets. The verifier recomputes
that join and projection after checking both children.

Induction gives the claimed interpretation at every node. Exact root coverage
makes its boundary empty, so its single truth value is SAT precisely when
the whole externally supplied formula is satisfiable. The checker validates
this semantic fact against the current external clauses; it does not require
that one proof be usable for only one syntactic formula. A proof that also
correctly checks for a semantically equivalent formula is harmless.

The checker shares the leaf and join arithmetic helpers with the producer.
The additional tests independently enumerate original assignments and each
node's projected relation to check those computations. Message type keys and
diagnostic statistics remain outside the certificate assertion. There is no
claim of polynomial verification in a succinct formula: explicit message
tables and their replay can still require exponentially many assignments.
No new time or state budget is introduced by this narrow repair.

## Validation and provenance

Run from `semantic_branch_dp_lab`:

```text
python -m unittest discover -s . -p 'test*.py' -v
```

All 16 tests passed in the recorded run (approximately 0.783 seconds),
including the three pre-existing tests. The new controls cover the original
omission exploit, invalid orders, duplicated or omitted child ownership,
forged variables/interfaces, malformed leaves and tables, cycles and shared
children, and the empty-formula/empty-clause distinction. They also cover:

- All 820 formulas of zero through three clauses from a nine-clause pool,
  checked against independent direct assignments in both natural and reverse
  order: 1,640 producer/verifier runs.
- Every stored node relation on 80 seeded formulas, compared with independent
  enumeration and projection of its original clauses.
- A valid tree with 1,100 clause leaves and 2,199 total nodes, verifying the
  iterative handling of depth beyond the usual Python recursion limit.

The independent `breakthrough_audit` reviewer found no correction. With seed
2026101847, it additionally tested 400 original formulas with at most six
variables and eight clauses. All 2,884 stored boundary messages matched
direct projection of original assignments; all 2,884 single-table-bit
mutations were rejected. Appending an empty clause to the external original
formula caused rejection for all 400 otherwise valid certificates. The exact
historical exploit was independently replayed and rejected. The reviewer
also reran all 16 tests and confirmed unchanged hashes. Its wider follow-up
assessment is [AFFINE_DECOMPOSITION_NEXT_REVIEW.md](AFFINE_DECOMPOSITION_NEXT_REVIEW.md).

The tested files were unchanged from immediately before to immediately after
the recorded run:

| File | SHA-256 |
|---|---|
| `semantic_branch_dp_lab/engine.py` | `f17f0380015652d9f4a3d7ffd452de70c4e71f9eb5c85f5f4d22d916b1af41aa` |
| `semantic_branch_dp_lab/test_lab.py` | `18a3e87ecd6be99c1a6d9a1853f85341a4b915e1c3dbe41b495c7c464dc7bc36` |
