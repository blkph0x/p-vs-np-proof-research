# Independent review of simultaneous matching bounds

Review date: 2026-10-18. Verdict: the reduction, implementation and stated
scope are sound. No production correction is required. This review writes
only this file and does not change the producer, tests or saved experiment.

## Mathematical audit

A four-cycle with cyclic edge IDs 0,1,2,3 has exactly the two perfect matchings
{0,2} and {1,3}. Their disjoint union therefore has one matching choice per
variable and no additional matching states. The false/true convention in the
source agrees with the theorem and decoder.

For a normalized clause, charging edge 0 of a positive literal's cycle counts
that literal exactly when false. Charging edge 1 for a negative literal counts
it exactly when false. Each relevant matching uses exactly one charged edge.
Different variables have disjoint edge sets. Thus the row sum is the number
of false literals, and the bound |C|-1 holds exactly when C is satisfied.
Because all rows use the same selected matching, consistency of a variable
across clauses is enforced without any additional gluing assumption. This
establishes both directions of the original SAT-to-bounded-matching decision
equivalence and yields a direct assignment decoder.

Removing repeated literals preserves each clause on every assignment. A
clause containing opposite literals is identically true and can be removed.
Every remaining clause has distinct variables, so a row entry stays in {0,1}.
An empty clause is correctly represented by charging all four edges of one
cycle with bound one: both perfect matchings cost two. If there is no variable,
the added dummy cycle serves this purpose and neither of its two matchings
passes the bound. With no variables and no clauses, the empty graph and empty
matching correctly give a feasible instance. Multiple empty clauses and unused
variables do not change these conclusions.

For the hardness restriction, start from at-most-three-literal SAT. The bounds
are then 0,1,2 for nonempty clauses and one for the special empty-clause row.
The graph is simple, bipartite and degree two, and all edge costs are 0/1.
Membership in NP follows by checking original vertex coverage and every
original cost inequality, with polynomial-size matching witnesses and exact
integer arithmetic of polynomial bit complexity. The NP-hardness construction
has bounded cost and bound magnitudes, so the stated strong NP-completeness
in the usual numerical-encoding sense is justified. This is not a hardness
claim about ordinary perfect matching or a proof that P differs from NP.

The number of bounds is part of the input and can grow with the formula. The
proof establishes no hardness for a fixed number of bounds. The eight-clause
example is a finite control, not an asymptotic fixed-eight-bound hardness
result. On that example every assignment yields row costs with multiset
{0,1,1,1,2,2,2,3}: exactly one clause fails, while total cost 12 is below total
bound 16. That refutes the specified unweighted summation rule only.

## Input size and implementation scope

The dense construction has O(nm) cost entries and O(n) graph size. As stated in
the theorem, the polynomial reduction first relabels variables actually
present in the explicit formula. Their number is bounded by the input's
literal occurrences even when the original variable names are large binary
integers. No output proportional to the numerical value of a large label is
needed. The convenience API accepts an explicit variable count and constructs
that many cycles; its output cannot be polynomial in log(n) for an artificially
succinct huge count of unused variables. The theorem expressly avoids that
interpretation. No claim that this API performs the preliminary renumbering
is needed or made.

The constructor also accepts general CNF clauses longer than three. Their
rows remain 0/1 but their bounds can exceed two. This is consistent with the
theorem: the constant-bound hardness subclass uses at most three literals,
while the broader executable controls can validate other CNF inputs.

The witness checker recomputes coverage and every row cost from the supplied
graph and bounds. It does not trust a stored assignment or a stored cost
vector. A modified cost matrix or bound is a different input, not a witness
for the original instance. The bounded graph/truth-table enumeration helpers
are finite experimental oracles, not polynomial SAT solvers.

## Independent executable checks

All eight supplied tests passed independently in 0.057 seconds. They include
231 raw two-variable clause pairs, independent edge-subset enumeration,
empty/tautological/duplicate cases, witness mutations and exact arithmetic
with a 15,001-bit integer.

An additional read-only inline check used seed 92241018 and 750 raw formulas
on zero through four variables, including duplicate literals, opposite
literals, empty clauses, unused variables and clauses longer than three.
It enumerated graph edge subsets by their original endpoints, cached every
perfect matching for each cycle count, and compared every resulting bound
verdict against direct evaluation of the original, unnormalized formula. It
did not call the producer's SAT evaluator, matching oracle or witness checker.

- 750 additional formulas passed.
- 4,910 original graph matching outcomes agreed with direct Boolean evaluation.
- 11,624 clause costs were checked against the supplied original rows.
- All 24 explicitly saved matching witnesses were independently replayed for
  vertex coverage, exact costs, violated-bound indices and original truth.
- All saved source hashes matched before and after the read-only checks.

These finite checks substantiate the implementation. The universal conclusion
comes from the preceding reduction proof, not the number of tested instances.

Reviewed frozen sources:

| File | SHA-256 |
|------|---------|
| clause_bounds.py | 23e6a46189f6d0fe8cc1bad4bd9cd7cf13e9681490a9f84c206bda486b77c518 |
| test_clause_bounds.py | b4469f00be145f99fcaa40c1438afabe0d1f1705bc360373f162570acae7619e |
| THEOREM.md | f739aee8eb8fc852aae9ac91793a0cccdb966b8ac819e654ec2a06efbae756e8 |
