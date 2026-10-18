# Packing clause bounds changes the matching question

This is a correct polynomial-size reduction to **a perfect matching of one
exact binary-encoded total weight**. It does not reduce SAT to ordinary
minimum-weight perfect matching. The distinction is essential: a minimum
below the target does not prove that the target weight is attainable.

No novelty or P-versus-NP resolution is claimed. The NP-complete source is
SAT with at most three literals per clause; see Karp's original problem 11
on printed page 95 in [Reducibility Among Combinatorial Problems](https://theory.stanford.edu/~trevisan/cs172-07/karp.pdf).
The sibling multiobjective audit checks that source and the uncompressed
per-clause matching construction independently.

## Input and normalization

Take variables x_1,...,x_n and m nonempty clauses of sizes k_j in {1,2,3}.
Within a clause, underlying variables are distinct. Repeated identical
literals can be removed; tautological clauses can be deleted. An empty
clause makes the input immediately unsatisfiable and can be mapped to a
fixed impossible exact-weight instance. The executable encoder deliberately
rejects such inputs rather than silently performing preprocessing. Unused
variables can be removed and remaining variables renumbered before encoding;
thus the graph size is polynomial in the actual encoded formula length even
if the original header declares a huge unused variable range.

For a logical assignment let c_j be the number of false literals in clause j.
Satisfaction is equivalent to c_j <= b_j, where b_j=k_j-1. Add b_j independent
binary slack variables s_(j,t). Every integer from zero through b_j can be
their sum. Consequently

    c_j <= b_j  iff  there exist slacks with c_j + sum_t s_(j,t) = b_j.

All quantities are nonnegative, and the left side of this equality lies
between zero and 2k_j-1 <= 5.

## Exact scalar packing with no carries

Use base B=6 and target W=sum_j b_j 6^j. Give a logical truth choice the
weight sum_j 6^j over the literals that it falsifies. Give each slack choice
weights zero and 6^j. Then the total chosen weight is

    sum_j (c_j + sum_t s_(j,t)) 6^j.

Every coefficient is a digit from zero through five. Uniqueness of positional
base-six representation therefore makes equality to W equivalent to **every**
per-clause equality above. There are no hidden carries, negative slacks or
overflow approximations.

Every satisfying assignment extends: choose exactly b_j-c_j slack bits in
clause j to be one. Conversely, any collection of truth and slack choices
with total W has c_j <= b_j for every clause and therefore satisfies the
original formula. Both directions are constructive.

## Ordinary four-cycle graph, additional exact-weight condition

Represent each binary choice of weights (w_0,w_1) by a separate four-cycle
with vertices a,b,c,d. In cycle order its edge costs are w_0,w_1,0,0. Its
two perfect matchings have total costs w_0 and w_1, respectively. Their union
over all choices is a disjoint union of four-cycles. There are

    q = n + sum_j b_j <= n+2m

cycles, 4q vertices and 4q edges. Every edge cost is a nonnegative integer.
The matching choices for each logical variable are shared across all its
clause digits, so variable consistency has not been assumed or lost.

The formula is satisfiable iff this graph has a perfect matching whose total
weight equals W. Verification of a proposed matching and its exact sum uses
polynomial bit complexity. Combined with the preceding reduction, this
specific exact binary-weight matching decision problem is NP-complete, even
on disjoint four-cycles. This is **not** a hardness claim for unconstrained
minimum-weight matching or for the special red/blue edge-count formulation.

Each individual weight is below 6^m and has at most 3m bits. A fully explicit
description thus has polynomial size, despite exponentially large numerical
weights. The reduction is not claimed strongly NP-hard with unary weights.
A bound polynomial in the numerical target W would be only pseudopolynomial
in this binary-encoded input.

## A gap that minimum and maximum cannot detect

The unsatisfiable formula

    (x) AND (NOT x) AND (y OR z)

has the four choice pairs (1,6),(36,0),(36,0),(0,36) and target W=36.
Its attainable matching costs are

    {1,6,37,42,73,78,109,114}.

Thus the minimum is 1, the maximum is 114, and the target lies strictly
between them but is unattainable. Replacing equality by cost <=36 gives a
false positive. Interpolating between minimum and maximum also gives a false
positive. This counterexample uses exact integers and a 16-vertex graph.

## Bounded exact fallback and its honest cost

The reference dynamic program stores every reachable prefix cost not exceeding
W. From a prefix set R and choice weights w_0,w_1, the next set is

    {r+w_b : r in R, b in {0,1}, r+w_b <= W}.

Pruning above W is sound only because all remaining weights are nonnegative.
The implementation saves all completed layers for an EXACT result. A separate
checker reconstructs each required recurrence from the original choice weights,
checks every state and the final decision, and validates a choice witness if
one exists. Original graph coverage and clause satisfaction are checked as well.
The checker has a separate work cap; exhaustion returns UNKNOWN.

There may be exponentially many reachable costs or a pseudopolynomial number
in W. Source-size polynomial weights do not imply polynomially many states.
The implementation has explicit state and transition caps and returns UNKNOWN
on exhaustion. It is a bounded exponential reference algorithm, not a proposed
polynomial SAT solver. Some saved positive controls intentionally grow its
state sets while retaining an easy independently verified satisfying assignment;
that demonstrates a limitation of this particular DP, not inherent hardness of
those instances or of all algorithms.

## Reproduce

Run `python -m unittest -v test_packing` and `python run_experiments.py` here.
The tests compare the encoding and reachable-cost recurrence with independent
small enumeration, mutate certificates, check large binary integers, and
separate exact-weight membership from ordinary minimization. The result file
retains original formulas, packed graphs, full EXACT layers or honest UNKNOWN
results, ordinary minima/maxima, independent original-formula truth tables,
matching witnesses, work counts and source hashes.
