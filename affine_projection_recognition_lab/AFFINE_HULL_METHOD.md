# Certified affine hulls of projected Boolean models

This method computes the exact **affine hull**, not the exact relation, of
`R={x : exists y F(x,y)}`. It does not classify arbitrary projections as
affine. Under a separately justified affinity promise, the hull equals the
projection. Empty relations have a separate `EMPTY` result.

For standalone satisfiability of `F`, the first SAT call already answers
the original decision problem. The remaining hull computation supplies no
independent SAT algorithm or speedup. It may serve as reusable preprocessing
for later restrictions, but benefit requires savings exceeding all initial
SAT, construction, and proof-checking costs. A polynomial outer loop does
not make those SAT calls polynomial-time.

This is a certified specialization of established symbolic affine abstraction.
[Reps, Sagiv and Yorsh (2004), Figure 1 and Theorem 1](https://research.cs.wisc.edu/wpis/papers/vmcai04.BT.pdf)
already give the model-outside-current-abstraction/join algorithm and its
finite-height correctness argument. No novelty is claimed for that principle,
the elementary reduction below, or the complexity accounting.

## Algorithm and all-input correctness

Variables are explicitly ordered as `m` visible coordinates followed by
`q` hidden coordinates, with ordinary signed one-based CNF literals.
Input length includes all variables. The first query is `F` itself.

* On UNSAT, return `EMPTY`, retaining the resolution certificate.
* On SAT, check the complete query model and take its visible projection
  as the initial point of `H`.
* If `dim H=m`, finish. Otherwise ask for a model of
  `F AND (x outside H)`.
* A new model expands the affine hull by one dimension. UNSAT proves that
  all projected models lie in `H`. A resource limit returns `UNKNOWN`.

All basis points belong to `R`. Hence the invariant is
`H subseteq aff(R)`, not `H subseteq R`. Each successful outside query
adds one independent direction. At terminal UNSAT, `R subseteq H`; together
these inclusions give `H=aff(R)`. Full dimension gives the same conclusion
without another SAT call. This proves correctness independently of any
empirical timings.

For `F=(NOT x1 OR NOT x2)`, the three points `00,01,10` have the full
square as their hull. The recovered hull contains `11`, which is not in
the relation. The saved `nonaffine_hole` control prevents promotion of a
hull certificate to a relation-equivalence certificate. The
`nonconstant_hidden_counts` control has full projected support but one
hidden witness at one visible point and two at the other. Affine support
also does not certify a constant-valued counting marginal.

## Canonical equations and polynomial-size queries

Reduce the visible difference vectors `point XOR anchor` to reduced row
echelon form with pivot columns increasing from zero. For each free column
`f`, form the annihilator vector having a one at `f` and a one at each
pivot `p` whose row contains `f`. Its right side is its dot product with
the anchor. These `m-d` equations specify the unique hull, in free-column
order. They are independent; no minimization search is needed.

To encode `x outside H`, take the disjunction of violations of these
equations. Each parity is built with binary XOR gates. A fresh gate output
`z=a XOR b` is defined by the four clauses excluding odd assignments to
`(a,b,z)`. The final clause requires at least one computed parity to
disagree with its equation's right side.

For every assignment to the original variables, these definitions have
unique gate extensions; the final clause is satisfiable exactly outside
`H`. This is projection equivalence, not just whole-formula
equisatisfiability. Distributive expansion of a parity truth table is never
used. Each normal has at most `d+1` nonzero bits, so the query adds at most
`d(m-d) <= floor(m^2/4)` gates, four clauses per gate, and one final clause.
The initial query requires no hull gates.

## Oracle cost versus actual computation

There are at most `m+1` model-returning SAT calls. For final dimension
`d<m`, the run uses `d+1` SAT calls and one terminal UNSAT call:
`d+2 <= m+1`. For dimension `m`, it uses `m+1` SAT calls and stops.
The `m=0` case uses a single call, including for an empty relation.

A model-returning SAT operation is not one decision-SAT query. Standard
prefix self-reduction recovers a visible point with at most `m` further
decision queries, or a complete original witness with at most `m+q`.
Thus safe decision-query bounds are `(m+1)^2` for the hull alone and
`(m+1)(m+q+1)` when full witnesses are retained. Auxiliary gate values are
determined and need not be self-reduced.

If `N=m+q` and original bit length is `L`, each query, including prefix
pins, has bit length
`O(L+(m^2+N+1) log(N+m^2+2))`. Rebuilding dense linear algebra over
`F_2` costs at most `O(m^4)` Boolean field operations across all iterations.
Bookkeeping and query-writing costs are polynomial in the explicit input.
These statements put canonical hull computation in `FP^NP`. **They do not
bound SAT-oracle execution or UNSAT proof size by a polynomial.**

The implementation makes actual calls to
[`proof_producing_cdcl_lab/cdcl.py`](../proof_producing_cdcl_lab/cdcl.py).
Its saved counters describe this solver, not an oracle charged unit time.
The default cumulative decision cap is 1,000, the call cap is `m+1`, and
input caps are 64 original variables and 4,096 clauses. Caps return
`UNKNOWN` with no hull equations or dimension. It deliberately does not
use the backend's separate resolution/conflict caps: the current terminal
resolution path does not enforce its resolution cap consistently.

There is no claimed literal-scan, memory, or wall-clock instrumentation.
For this non-restarting backend, each decision raises the decision level,
and each nonroot conflict lowers it. Thus conflicts are at most decisions
plus the number of calls. Implication reasons only use earlier trail
assignments, bounding resolution steps per conflict by the query's variable
count. These are coarse structural bounds for this implementation; the
reported statistics are not a proof that the solver is fast on arbitrary
CNFs.

## Why a promised affine output does not remove SAT hardness

For any source CNF `G(y)`, build

```text
F_G(x,y) = AND over C in G: (NOT x OR C).
```

Its one-bit projection is `{0}` when `G` is unsatisfiable and
`{0,1}` otherwise. Both outputs are nonempty linear subspaces containing
zero. Exact recovery, or merely their dimension, therefore decides SAT
even under this promise. One projected member is easy to supply (`x=0`);
discovering the whole relation is a different problem.

Consequently deterministic polynomial-time exact recovery on all promised
affine projections exists if and only if `P=NP`: the forward implication
uses this guard, and the reverse implication replaces the polynomially many
SAT queries above by a polynomial SAT algorithm. This is an equivalence,
not an algorithm establishing either possibility. The total canonical-hull
function is `FP^NP`-complete under polynomial-time **Turing** reductions,
since its dimension can simulate each SAT query. No stronger function-
reduction convention is asserted.

## Trust model and reproducibility

The producer checks every returned SAT model. The independent checker
`review_affine_hull.py` imports neither the producer nor the SAT solver.
It rebuilds the affine equations using Boolean matrices and reconstructs
each guarded query from the external original CNF. Every SAT assignment is
checked against every query clause. Every UNSAT answer needs a valid
resolution derivation ending in the empty clause, with all parent clauses
already available. The checker uses explicit exceptions, not Python
assertions, and does not perform exhaustive satisfiability search.

The retained transcript includes all calls so their input binding and
reported counters can be audited. Only the satisfying basis witnesses and
a final outside-hull UNSAT proof (or full rank) are mathematically necessary.
Checking a resolution certificate is polynomial in the input plus certificate
length. No universal polynomial bound on that length is claimed. Counts of
derived resolution steps and learned clauses are rebuilt from the trace;
decision and propagation counters are reported execution data rather than
independently certified runtime.

Run in this directory with Python 3.10 or later:

```text
python review_affine_hull.py
python -m unittest -v test_hull_engine.py test_hull_certificate.py
python -O -m unittest -v test_hull_certificate.py
```

Regenerate separately with `python run_affine_hull.py`. Committed results
contain complete original CNFs, caps, SAT models, UNSAT traces, source hashes,
and explicit unknown outcomes. Hashes use UTF-8 with CRLF/lone-CR normalized
to LF. The dependency on the existing CDCL source is included.

Tests exhaust all 256 relations on three visible bits, sample 100 seeded
CNFs with hidden variables, and compare against separately enumerated exact
hulls. They also check gate projection equivalence, zero-dimensional cases,
nonzero affine offsets, missing points, nonconstant hidden multiplicities,
caps, and mutation rejection. The exhaustive assignment oracles are confined
to tests; they are not the certificate verifier.

## Relation to existing work and the earlier lab

| Work | Representation and conclusion | Position here |
| --- | --- | --- |
| Reps--Sagiv--Yorsh (2004), Figure 1 / Theorem 1 | Symbolically represented concrete states and model-returning decision procedure; computes best abstraction in a finite-height domain. | Direct algorithmic predecessor. The height here is controlled by Boolean affine dimension. |
| [Henshall, Schachte, Sondergaard and Whiting, *Binary Decision Diagrams for Affine Approximation*, Proposition 5 and section 3](https://arxiv.org/pdf/0804.0066) | Affine envelopes, including commutation with existential projection; algorithms for explicit model sets and ROBDDs. | Projection/hull reasoning is inherited. A compact input CNF need not have a polynomial-size ROBDD. |
| [The variable-width recognition theorem](COMPLEXITY_THEOREM.md) | Deciding whether a projected CNF relation itself is nonempty affine is `Pi_2^P`-complete. | Exact hull recovery cannot validate that promise. The missing reverse inclusion remains the obstruction. |
| [Existing explicit affine-sum recognizer](../affine_one_piece_lab/THEOREM.md) | Exact norm queries for an explicitly supplied rational sum of affine pieces. | Its polynomial norm computations do not automatically give polynomial SAT or counting queries for succinct CNF input. |

The next useful test is whether hull information can reduce a proved solver
cost while all SAT calls and proof costs remain charged. The exact hull can
overapproximate the relation and must never replace it without a separate
equivalence proof.
There is still no resolution of P versus NP.
