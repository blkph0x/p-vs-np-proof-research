# When a linear decoding map preserves an additive objective

This elementary characterization makes the objective warning in the graph-lift
coverage audit exact. It is not a lower bound on general algorithms, and no
novelty claim is made.

Let T be an n-by-m binary matrix and a_i >= 0 output weights. For all binary
inputs z, define f(z) = sum_i a_i (Tz)_i, evaluating Tz over GF(2) and its cost
over the real numbers. The following statements are equivalent:

1. There are constants c,b_j such that f(z)=c+sum_j b_j z_j for **every** z.
2. Every positive-weight row of T has at most one nonzero entry.
3. Distinct columns of T overlap only in zero-weight output coordinates.

When they hold, c=0 and b_j=sum_i a_i T_ij >= 0. Thus allowing negative unary
input costs does not enlarge this all-input linear-map model.

Proof: z=0 forces c=0, and z=e_j forces b_j=f(e_j). For any distinct j,k,

    f(e_j) + f(e_k) - f(e_j+e_k)
        = 2 sum_{i: T_ij=T_ik=1} a_i.

Additivity forces every such nonnegative overlap sum to vanish. A positive-cost
row containing two ones would violate this condition for those two columns.
Conversely, if every positive-cost output depends on at most one input, sum its
weight into that input's unary cost. Zero rows contribute nothing. This proves
the identity for every z without enumerating the input cube.

An obstruction therefore has only three nonzero input assignments: e_j, e_k,
and e_j+e_k, together with their independently evaluated original costs. A
strictly positive displayed defect disproves *every* additive cost assignment
on the unrestricted input cube. The implementation constructs such a witness
from any positive-cost row with two entries, and independently checks it.
Both construction and checking are polynomial in the explicit matrix and
integer-weight bit length. A column budget prevents a huge encoded dimension
from causing an unbounded allocation; that case returns UNKNOWN.

For ordinary Hamming weight all a_i=1. The only allowed maps are disjoint
coordinate replication (and zero output coordinates). An arbitrary generator
matrix can map unconstrained graph-loop variables onto any code, but its
Hamming objective is generally nonadditive. The map

    T(z1,z2) = (z1,z2,z1 XOR z2)

gives costs 2,2,2 on 10,01,11. Its defect is 2, so it cannot be replaced by
fixed edge costs on those two freely selectable variables.

## Exact scope

The theorem requires the identity on **all** input vectors. It need not hold
if only a constrained subset is relevant: T(z)=z1 XOR z2 has objective zero
on the subspace {00,11}, despite its overlapping columns. Such a reduction
must explicitly preserve and efficiently handle that restricted domain.

Nonnegative original costs and a purely linear map are also necessary for the
stated characterization. Signed weights on two identical XOR outputs can
cancel. An affine map with outputs XOR(z1,z2) and its complement has constant
cost one with positive weights, despite overlapping dependence. These examples
are included as controls, rather than silently extending the theorem.

This does not exclude nonlinear decoding, additional constraints, minimum over
auxiliary solutions, affine encodings, or reductions that preserve only a
decision threshold instead of the entire objective. It does exclude treating
an arbitrary linear generator map from free graph loops as an already
cost-preserving reduction to the implemented graph optimizer.

## Reproduction

`python -m unittest -v test_objective_pullback` checks every binary matrix with
at most three input and three output coordinates, all zero/one output weight
assignments, 150 seeded larger integer-weight controls, certificate tampering,
budgets, and the scope counterexamples. All truth-table oracle evaluations
are separate from the polynomial classifier and its verifier.

Seven tests passed, including valid integers beyond Python's decimal-conversion
limit. An independent review found and rechecked the repair of that hashing
edge case; see [REVIEW.md](REVIEW.md). Hashing now uses length-prefixed integer
bytes and does not change process-wide interpreter settings.

`python run_examples.py` saves 186 original-map examples and checked
certificates in `RESULTS.json`: 102 additive and 84 nonadditive, agreeing with
3,695 complete input-assignment evaluations. Every saved certificate is
serialized and replayed. The exhaustive unit test separately checks all
5,054 matrix/zero-one-weight combinations in its stated dimensions. Neither
finite count replaces the general pair-overlap proof.
