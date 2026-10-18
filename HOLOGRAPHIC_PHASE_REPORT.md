# Exact basis changes, tractable signed tensors, and checked limits

**P versus NP remains unresolved.** This phase delivers an exact evaluator for
a verified family on arbitrary graphs, two algebraic obstructions to a particular
SAT encoding, and reproducible controls for signed cancellation. It does not
provide a polynomial algorithm for unrestricted SAT. No novelty is claimed.

## What was established

The [tensor-basis lab](tensor_basis_lab/THEOREM.md) preserves the full original
formula under opposite rational basis actions on variables and clauses. Literal
signs, shared variables, repeated occurrences, unused variables and empty clauses
remain explicit. Original SAT counts and slack-weighted counts are separate:
one positive ternary clause has counts 7 and 10; repeating it gives 7 and 16.
The implementation independently checks every local transform and, under a cap,
every global contraction term. Transforming the tensors alone is not an efficient
general contraction algorithm. A deliberately wrong same-basis action changes
the count and is retained as a regression control.

The [simultaneous-basis theorem](simultaneous_basis_lab/THEOREM.md) proves that
no common invertible complex two-by-two basis makes both EQ3 and OR3 have
matchgate parity. The same result holds for EQ3 paired with the ternary slack
factor [0,1,2,1]. This covers all eight parity branches, using a complete basis
normal form and four small integer Bezout identities. A separate symbolic
review checks all original equations. Groebner computations are corroboration,
not an unexplained impossibility certificate. Five explicit planar graphs are
positive controls, including clauses that work individually but fail with EQ3.
The theorem concerns this encoding and one common basis, not all reductions.
The same theorem now includes a separate product-type obstruction. For a
symmetric ternary product-type target, transformed EQ3 must have only weight-0
and weight-3 support. The two exact zero equations force every invertible basis
to be diagonal or anti-diagonal; OR3 and SLACK3 retain three nonzero weight classes under
either case. This closes the other main symmetric Boolean Holant target for the
common binary basis model, while leaving larger domains, non-symmetric
encodings and other tractable families outside scope.

The [real-affine evaluator](holographic_tractability_lab/THEOREM.md) supplies the
positive result. Given explicit rational tensors and a common rational basis,
it checks affine support and a quadratic sign phase at every node. It then
solves one global Boolean linear system and evaluates its quadratic signed sum
in polynomial bit complexity. No planarity or small-width hypothesis is used.
Independent certificates check the original transforms, full solution space,
phase restriction and elimination identities. This is a real rational subclass
of the known affine holographic family, with a supplied basis; arbitrary complex
class recognition and general basis discovery are not implemented.

A connected 120-edge family obtained by an inverse nonsymmetric basis change
has exact value 2. The original basis fails recognition; the supplied basis
succeeds. Exact local transformations and connectivity independently establish
the value without enumerating 2^120 assignments. This illustrates real algorithmic
scope, but the family is not a general SAT encoding. High-degree succinct equality
nodes may also require exponential truth-table expansion in this implementation;
the cap and the explicit-input complexity statement expose that limitation.

The [crossing-sign lab](crossing_sign_lab/THEOREM.md) independently reconstructs
the published six-vertex signed crossing graph and all its boundary sums. The
ordinary ordered crossing violates a necessary matchgate identity by 2. The
signed crossing satisfies the identities but changes a contraction against EQ4
from 2 to 0. Nonzero unary rescalings cannot repair that sign. An exact rational
Pfaffian evaluator and congruence certificates provide a positive polynomial
algorithm for signed pairing sums; an explicit graph with two perfect matchings
has signed value zero. That value is not a general no-matching certificate.

## Verification and saved evidence

All **53 new tests** pass on frozen sources: 14 tensor-basis, 18 simultaneous-basis,
12 real-affine and 9 crossing/Pfaffian tests. Every lab has an independent written
review. Additional reviews checked all 6,561 ternary tables over {-1,0,1}, 560
seeded quadratic sums, 400 rational skew matrices with a separate exterior-algebra
oracle, and additional original-formula and tensor-transform controls. These
finite checks corroborate the mathematical arguments; they do not prove a general
complexity conclusion by extrapolation. No proof assistant was used.

The artifact audit checks **21 current source references** and replays:

| Artifact | Replayed claims and retained limits |
|---|---|
| Tensor basis | 69 exact contraction proofs, 4 UNKNOWN, 2 local proofs, 2 wrong-action controls |
| Simultaneous basis | 8 original parity systems, 4 Bezout identities, 40 positive graph entries, 1 product-type obstruction |
| Real affine | 15 exact proofs, 26 UNSUPPORTED, 1 UNKNOWN, 6 original satisfying witnesses |
| Crossing/Pfaffian | 38 exact proofs, 2 UNKNOWN, 2,676 pairing terms, 16 graph boundary entries |

`UNSUPPORTED` rejects only the supplied basis and implemented family. `UNKNOWN`
means a work or representation limit was reached. Neither is an UNSAT result.
For the exact original nonnegative SAT/slack encodings, zero does certify UNSAT;
the full count-preservation argument is essential. An unrelated signed sum may
be zero through cancellation.

The [same-original comparison](HOLOGRAPHIC_CROSSCHECK.json) uses 34 formulas from
the preceding algebraic phase plus six edge cases, in both count modes and three
bases: **240 requests**. Full edge contraction gives 132 EXACT and 108 UNKNOWN;
the affine method gives 26 EXACT and 214 UNSUPPORTED. Every exact count agrees
with independent original-variable counting or a checked disjoint-clause product.
The affine method resolves **zero additional capped SAT requests in this batch**.
This negative result is retained rather than replacing the batch with only its
successful structural examples.

## Historical certificate repair found during reuse review

The reuse audit found a concrete omission bug in the older semantic branch-DP
checker: a valid proof for `(x)` was accepted against the different original
formula `(x) AND false`. The checker did not require the root to cover every
original clause. This affected that historical interface, not the four new labs.

The [repair record](SEMANTIC_CERTIFICATE_REPAIR.md) documents the fix. The producer
now requires a complete clause order, and the checker validates full root coverage,
disjoint child partitions, original variables and boundaries, tree shape and all
tables. Cycles and shared children are rejected; empty formulas have a checked
true scalar. Its separate **16-test suite** passes. Independent review checked
400 additional formulas and all 2,884 boundary messages, rejecting every altered
table and added-empty-clause omission tested. Historical reports and archive
manifests are preserved; current tested source hashes are recorded separately.

## Reproduction and next work

From this directory, using the existing Python 3.10.10 environment:

```powershell
python run_holographic_phase_checks.py
python run_holographic_crosscheck.py
python verify_holographic_artifacts.py
```

The lab runners retain all original inputs, fractions, certificates, limits and
source hashes. Existing SymPy 1.14.0 is used for supplementary symbolic checks;
the principal certificate verifiers use the standard library. No packages were
installed. The [literature check](HOLOGRAPHIC_LITERATURE_CHECK.md) records primary
definitions and an erratum that this proof deliberately avoids relying on.

The next step is to extend the existing branching machinery with compact exact
signed boundary messages. The [boundary design](AFFINE_BOUNDARY_DESIGN.md)
proves closure for one affine piece and gives two polynomial elimination rules;
that new interface is designed but not yet implemented. The remaining difficulty
is the total number and discovery cost of pieces for general SAT. A short local
decomposition does not prove a small global one. The
[next review](AFFINE_DECOMPOSITION_NEXT_REVIEW.md) records what existing code to
reuse, an exponential-growth control and the missing general bound. The ultimate
resolution goal remains active.
