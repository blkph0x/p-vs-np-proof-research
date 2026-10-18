# Clause composition, simultaneous bounds and exact packed weights

**P versus NP remains unresolved.** This phase tests attempts to combine
locally correct graph gadgets into a general SAT solver. It supplies correct
encodings and precise counterexamples, and identifies which extra global
problem those encodings actually require solving. No novelty is claimed.

## The central distinction

| Construction | What is proved | What is still missing |
| --- | --- | --- |
| One OR clause as a matching threshold | k disjoint unit edges give cost k-j when j logical pairs are true | Adding clause cutoffs does not enforce their conjunction |
| Flat clause cost on promised-valid inputs | A 4k-2 vertex, nonnegative-cost gadget gives false cost one and true cost zero | Invalid physical states can also have zero cost; global validity must be enforced |
| Keep one cost bound per clause | SAT is encoded exactly on disjoint four-cycles with 0/1 costs and bounds at most two | Feasibility with polynomially many simultaneous bounds is itself NP-complete |
| Pack the bounds into one integer | Base-six digits and nonnegative slack give an exact polynomial-size encoding | It asks for a matching of one exact binary weight, not an ordinary minimum-cost matching |

These alternatives are different mathematical problems. Treating them as
interchangeable would silently assume the missing solver.

## Scalar aggregation fails in a checkable way

For the unsatisfiable formula (x) AND (NOT x) AND (x OR y), assignment x=y=1
has clause costs (0,1,0). Their total meets the sum of the local cutoffs, even
though the second clause fails. This remains a false positive even if
consistent Boolean variable semantics are granted for free.

A stronger trade excludes every affine score on the original four bits for
(a OR b) AND (c OR d). Two accepted assignments have the same coordinatewise
sum as two rejected assignments. Any affine score therefore has equal total
on those two pairs; a single cutoff cannot put both accepted scores below it
and both rejected scores above it. The certificate checks exact feature sums
and original truth labels and permits arbitrary real scoring coefficients.
It does not exclude nonlinear features or different decision encodings.

The [threshold proof](threshold_composition_lab/THEOREM.md) includes the full
OR boundary model and these counterexamples. Five graph controls check 1,364
physical states using 37,448 edge-subset comparisons. The independent review
found and repaired a large-integer hashing defect; binary rational hashing now
passes regression checks without changing interpreter settings.

## Saturation is possible on a promise, so the scope matters

It would be too strong to conclude that flat clause costs are impossible.
A capacity construction with k-1 pairs of internal vertices gives an explicit
flat OR gadget on valid 00/11 paired inputs: the all-false input costs one,
and every satisfying input costs zero. All costs are zero or one.

For at least two inputs, its invalid zero-cost boundary states supply the
exchange states that an exact all-physical-input clause penalty would forbid.
The latter is impossible at those arities by the independently reviewed
matching exchange proof. The [saturation audit](saturated_clause_limits/THEOREM.md)
proves the distinction, gives the all-size construction, and proves that six
vertices are necessary for its two-input promised version, even with signed
costs and modular terminal offsets.

The earlier AND obstruction refers to the gate relation with an output port,
z=x AND y. It does not forbid the input-only conjunction predicate. Likewise,
the [odd-NOT-cycle control](matching_composition_controls/THEOREM.md) still
shows why correct promised truth tables alone do not establish global validity.

## A correct general encoding retains a hard constraint

One four-cycle per variable has exactly two perfect matchings, representing
false and true. Each nonempty normalized clause's 0/1 edge-cost row counts
its false literals; the bound is its length minus one. Empty clauses receive
a separate impossible-bound construction. Every matching satisfies all bounds
iff its shared variable assignment satisfies the entire formula.

This is a full reduction, including normalization, empty clauses and both
directions of witness recovery. It proves NP-completeness with a growing
number of bounds even though the graph is bipartite and has degree two. No
hardness for a fixed number of bounds or for ordinary matching is claimed.
The [multiobjective proof](multiobjective_matching_limits/THEOREM.md) records
the source problem and complete size accounting. Its saved checks cover 740
formulas, 6,558 assignments and 6,595 matchings; independent review adds a
separate set of tests.

Packing those bounds does not remove the distinction. For clause size k<=3,
add k-1 binary slack choices and use one base-six digit per clause. Every
digit lies between zero and five, so exact total-weight equality enforces
all clauses without carries. The graph still consists of four-cycles, and
each weight has polynomial bit length. Numerical weight magnitude may be
exponential. Used variables must be compactly renumbered before claiming a
bound in actual formula text length; the reference API accepts an explicit
variable count and does not perform that preprocessing itself.

The unsatisfiable formula (x) AND (NOT x) AND (y OR z) gives a 16-vertex graph
with attainable costs {1,6,37,42,73,78,109,114}, while the required cost is 36.
Both a minimum-below-target test and a minimum/maximum range test would be
wrong. This exact binary-weight problem is NP-complete by the reduction; it
is distinct from the special red/blue edge-count matching problem.

The [packing proof](packed_cost_exact_matching/THEOREM.md) and reference code
make the gap explicit. Across 34 saved requests, the bounded reachable-cost
DP completes 30 exact proofs and returns four honest UNKNOWN results at its
512-state cap. Original-formula checks cover 28 SAT and six UNSAT inputs.
The UNKNOWN cases include a small UNSAT formula and three easy SAT growth
controls; they show this DP's limitations, not hardness of those individual
instances. Feasible original witnesses are retained separately.

## Verification and reproducibility

All **37 tests across four suites** pass on frozen sources, independently of
the preceding checkpoint's 78 tests. See [THRESHOLD_TEST_SUMMARY.json](THRESHOLD_TEST_SUMMARY.json).
The [artifact audit](THRESHOLD_ARTIFACT_AUDIT.json) matches all 27 saved source
references and replays the feature trade, all 1,364 OR boundary states,
28 saturation witnesses, 24 simultaneous-bound witnesses, and the 34 packed
requests, including 30 exact DP proofs and 87 matching witnesses.

Original inputs, proof layers, failed shortcuts, UNKNOWN results, limits,
source hashes and independent reviews are saved. Written mathematical proofs
were independently reviewed, not formalized in a proof assistant.

Run `python run_threshold_phase_checks.py` and
`python verify_threshold_artifacts.py` from this directory. Each new lab
contains its experiment command. The earlier solver sources and archived
snapshots were preserved; no packages were installed for this phase.

## The next substantive question

A compact graph or integer representation is now available for the complete
SAT decision question, but its remaining exact-weight condition retains the
hard part. An algebraic shortcut must prove efficient extraction of the
relevant coefficient or another exact decision method, including all bit
costs. Merely storing an exponential-degree polynomial in a short product
does not supply that operation. [NEXT_ALGEBRAIC_BRIEF.md](NEXT_ALGEBRAIC_BRIEF.md)
records a concrete coefficient and modular-aliasing control for the next
investigation. The ultimate research goal remains active.
