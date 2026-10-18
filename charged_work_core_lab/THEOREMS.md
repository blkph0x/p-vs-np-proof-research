# Exact conditioning and its fixed-order state tradeoff

All vector spaces and ranks below are over GF(2). Let `C = ker H` on coordinate
set `E`, with a full-row-rank parity-check matrix H. Let `D` be a set of `d` fixed
coordinates and `R = E - D`. The order on R is inherited from one supplied order
on E. These are elementary statements about this representation, not general
computational lower bounds.

## 1. Exact minimum-distance reconstruction

Partition codewords by their restriction `b` to D. The remaining coordinates must
satisfy `H_R x = H_D b`, and their full weight is `weight(x) + weight(b)`.
The partition is disjoint and covers C. Therefore minimizing these quantities over
all feasible branches, excluding only the zero full word, yields the minimum
nonzero codeword weight. If C contains only zero, no such minimum exists and the
solver returns exact distance `None`.

For a residual prefix P, the DP stores partial syndrome s and whether any fixed
or processed bit is nonzero. With branch target t, the state is extendable exactly
when `t + s` belongs to the span of suffix columns. Two partial assignments with
the same syndrome and nonzero flag have identical future feasibility and additive
future costs. Retaining the least-weight one is therefore exact. At the end, only
syndrome t with a true nonzero flag is accepted. Original-code membership and
weight are checked again on the reconstructed full word.

## 2. Residual syndrome-state count

For a nonempty affine branch and residual partition `R = A union B`, feasible
prefix syndromes form

    span(H_A) intersect (t + span(H_B)).

This nonempty affine intersection is a translate of
`span(H_A) intersect span(H_B)`. Its dimension is

    lambda_R(A) = rank(H_A) + rank(H_B) - rank(H_R).

There are exactly `2^lambda_R(A)` distinct extendable syndromes. Every feasible
branch has this same count. The nonzero flag can add at most a factor of two to
the number of DP entries. This counts the zero branch before excluding its final
zero word; even a branch containing only zero is a feasible affine branch.

For width `w_D = max_A lambda_R(A)`, the implementation uses at most
`O(2^d |R| 2^(w_D+1))` transition attempts, plus polynomial work per attempt
for span membership and integer operations. A bound in terms of feasible branches
replaces the exponential factor by `2^q`, but the current implementation still
enumerates all `2^d` assignments to test feasibility. Suffix-span construction and
Gaussian elimination also require polynomial setup work and storage.

## 3. Branch count and the width tradeoff

Let `q = dim(projection_D C)`. The image of the projection is a q-dimensional
linear space, so exactly `2^q` assignments to D give nonempty branches. By
rank-nullity, its kernel is the shortened code on R and hence

    q = (|E| - rank(H)) - (|R| - rank(H_R))
      = d - rank(H) + rank(H_R).

At an original prefix cut P, put `A = P intersect R` and
`B = (E - P) intersect R`. The span intersection for the residual cut is a
subspace of that for the original cut, giving `lambda_R(A) <= lambda_E(P)`.
For the opposite bound, define the rank increments

    a = rank(H_P) - rank(H_A)
    b = rank(H_(E-P)) - rank(H_B)
    c = rank(H) - rank(H_R).

Adding the deleted columns on the two sides gives `a + b <= d`. Expanding the
connectivity ranks yields

    lambda_E(P) - lambda_R(A) = a + b - c <= d - c = q.

Every original cut maps to a residual cut; every residual cut is attained this
way. Taking maxima along the two inherited orders gives

    w - q <= w_D <= w
    2^q * 2^w_D >= 2^w.

The weaker bound `w - d <= w_D` follows from `q <= d`. This product inequality
concerns peak distinct syndrome counts and feasible affine branches, not total
transition counts or runtime. It does not rule out better native representations,
reuse across branches, improved order discovery, or parallelism.

## 4. Charged work lower bound

Count one unit for each enumerated deleted-coordinate assignment and one unit
for each attempted residual DP transition. For a completed run, let `w` be the
width of the original supplied order. Choose a cut attaining `w`.

If the cut leaves at least one residual coordinate, every feasible affine
branch has one DP state for each extendable prefix syndrome. If the residual
cut width is `u` and the fixed-coordinate projection has dimension `q`, there
are exactly `2^q 2^u` such state/branch pairs, and the rank calculation above
gives `q+u >= w`. Each state emits transition attempts, so the charged work is
at least `2^q 2^u >= 2^w`.

If the cut leaves no residual coordinate, its residual width is zero and the
same inequality gives `q >= w`; the enumeration of deleted assignments alone
charges at least `2^q >= 2^w`. Thus every exact fixed-order conditioning run
has

    deleted-assignment attempts + residual transition attempts >= 2^w.

This closes a bookkeeping loophole in which smaller per-branch tables could be
reported as a speedup while silently omitting the branch loop. It still says
nothing about a different order, a native solver, or general SAT.

## 5. Discovery and certificate boundaries

For fixed d, checking all `C(n,d)` candidate coordinate sets with polynomial rank
calculations is polynomial, but the degree depends on d. The implementation has
an explicit candidate cap and only minimizes a supplied-order profile. It does
not find an optimal trellis order or solve general decomposition discovery.

The separate F7 certificate theorem and its primary reference are in
`FANO_NOTES.md`. That certificate excludes graphic/cographic matroid representations.
It supplies no computational lower bound for minimum distance.
