# Horn + affine CDCL(T) audit

**Status:** executed research prototype. No proof of P=NP or P!=NP.

This package tests whether adding a certifying Horn propagator to the existing GF(2)
portfolio creates a general polynomial solver. It does not. The fixed two-bridge relation
already developed in the typed-merge work is implemented here as a small Horn relation plus
an affine relation. Its existential projection is positive exact-one, so arbitrary
positive 1-in-3-SAT reduces to the mixed portfolio language.

The code has three purposes:

1. verify the gadget semantically by exhaustive truth-table checks;
2. run a deterministic proof-producing search solver on the encoded instances;
3. independently replay every Horn and affine certificate emitted during the audit.

The finite audit covers all 16 subsets of the four 3-variable clauses on four variables
and complete-triple instances for target sizes 3 through 10. All direct and encoded
satisfiability results agree. The solver returns only assignments that satisfy the original
exact-one constraints, and the independent certificate replay passes.

The result is a rigorous negative answer to one proposed route: a generic combination of
Horn and affine polynomial subsolvers cannot be assumed polynomial, because the language
contains an NP-complete exact-one fragment through a constant-size existential gadget.
That is a barrier and a conditional complexity result, not a resolution of P versus NP.

See [THEOREM.md](THEOREM.md) for the reduction statement and [RESULTS.json](RESULTS.json)
for the machine-readable audit.

## Clause learning

The follow-up `cdcl.py` adds a first-UIP CDCL(T) layer. Horn and affine explanations remain
certificate-producing theory lemmas, and every learned clause carries a complete resolution
derivation. `review_cdcl.py` independently recomputes the theory clauses, affine row
combinations, and resolution pivots.

The new control family encodes 3-colorability with positive exact-one clauses. K4 and two
sparse non-3-colorable graphs (12 and 14 vertices) are rejected by an independent coloring
checker and by the mixed solver. Clause learning cuts the deterministic search from 287 to
29 decisions on the sparse-12 control and from 491 DFS nodes to 88 decisions on sparse-14.
The widest learned clause in these controls is width 7, so even this compressed proof
interface does not stay at a fixed width. All proof events replay successfully. The
improvement is substantial but remains a search optimization; the fixed exact-one
projection still blocks any claim of a general polynomial-time solver.

See [CDCL_RESULTS.json](CDCL_RESULTS.json) and [CDCL_REVIEW.json](CDCL_REVIEW.json).

## Algebraic cross-check

An exhaustive finite polymorphism audit finds only projections common to the two fixed
relations at arities 1 through 4. The named Horn/affine operations are separated: AND and
majority fail on the affine relation, while minority/XOR fails on the Horn relation. This
supports the reduction's interpretation as a genuinely mixed language, but the finite
arity check is supplemented by the all-arity proof in
[POLYMORPHISM_THEOREM.md](POLYMORPHISM_THEOREM.md).

The artifacts are [POLYMORPHISM_RESULTS.json](POLYMORPHISM_RESULTS.json) and
[POLYMORPHISM_REVIEW.json](POLYMORPHISM_REVIEW.json).
