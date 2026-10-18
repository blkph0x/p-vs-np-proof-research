# Exact bounded-coordinate projections do not remove the Golay LP gap

This note proves a limitation of intersections of coordinate-projection convex
hulls. It does not assert a lower bound for Sherali-Adams, Lasserre, arbitrary
lifted formulations, general LP methods, or SAT algorithms. No novelty is claimed.

## Full projections from dual distance

Let C be a binary linear code on E={0,...,n-1}, with dual minimum distance delta.
For S contained in E, let pi_S denote restriction to S. The annihilator identity is

    (pi_S C)^perp = { h restricted to S : h in C^perp, supp(h) contained in S }.

To prove it, extend a vector on S by zeros outside S. Its dot product with every
codeword is zero exactly when it annihilates every projected codeword. The
extension/restriction maps are inverse on the two displayed spaces. Thus a
proper projected linear space would have a nonzero annihilator, yielding a
nonzero dual word supported on S. If |S|<delta, this is impossible, and

    pi_S C = {0,1}^S;       conv(pi_S C) = [0,1]^S.

Equivalently, a generator matrix restricted to S has rank |S|. A parity-check
formulation gives another equivalent criterion: the columns outside S still
span the full parity-check column space.

The zero dual code is a harmless boundary case: its primal is the full binary
cube, so every projection is full. The executable certificate records its dual
distance as null and explicitly records guarantees up to n coordinates.

## Pinning one coordinate

Let j not belong to S and consider the affine set C_j={c in C:c_j=1}.
If |S|+1<delta, the previous result makes pi_(S union {j}) C a full binary cube.
Every assignment on S therefore has an extension with the additional prescribed
value c_j=1. Hence

    pi_S C_j = {0,1}^S whenever |S|<=delta-2.

The condition also guarantees C_j is nonempty. A zero pin has the same
surjectivity statement, but the minimum-nonzero-weight application here uses a
one pin. For delta=1 the stated conditioned range is empty and makes no
feasibility assertion; the verifier reports no conditioned guarantee.

Define the relaxation that keeps x in [0,1]^n, pins x_j=1, and requires
pi_S x to lie in conv(pi_S C_j) for every set S of at most k other coordinates.
For k<=delta-2, this relaxation is exactly the box with x_j=1. In particular,
the unit vector e_j is feasible and the relaxed minimum weight is exactly one,
while the integer pinned optimum is at least the code's minimum distance d.

These strict thresholds are real. For a minimum-weight dual support T of size
delta, pi_T C satisfies its parity equation and is not a full cube. If j is in
T, pi_(T-{j}) C_j satisfies an odd-parity equation and is not full. A certificate
does not claim that projections at these boundary sizes remain cubes, or that
their nontrivial constraints necessarily eliminate a particular fractional point.

## Combining with every redundant-check parity polytope

The preceding projected-code hulls are different from a parity polytope on the
entire support of a dual check. A full-support dual constraint can involve many
coordinates and is already present in the all-dual LP relaxation.

For a code with dual distance delta, all exact unconditioned coordinate hulls
on at most delta-1 coordinates add only box constraints. After the one pin,
all exact conditioned hulls on at most delta-2 other coordinates also add only
box constraints. Adding either or both collections to the all-dual LP therefore
does not change its feasible set under that pin.

For the explicitly checked [24,12,8] self-dual code, delta=8. Thus all 536,155
unconditioned coordinate subsets of size at most seven, and all 145,499 subsets
of the other 23 coordinates of size at most six after the pin, have cube hulls.
These counts include the empty subset. The result follows for every pin from
the theorem, not from sampling the coordinate subsets.

Consequently the existing rational witness

    x_j=1; x_i=1/7 for i!=j; total weight=30/7

survives the all-dual LP plus every one of these exact projection hulls. The
independently checked octad lower certificate still applies: 253 weight-eight
dual checks contain the pin and every other coordinate appears in 77 of them.
Summing their singleton-pin inequalities proves total weight at least 30/7.
The combined relaxation therefore has **exact** optimum 30/7, while the pinned
integer optimum is eight, preserving the ratio 28/15.

The unit vector e_j is a witness only for the projection-hull relaxation by
itself. It fails an all-dual parity inequality through j and is not claimed
feasible for the combined relaxation.

## Executable evidence and limits

`projection_barrier.py` supplies a certificate containing a full dual basis,
its claimed minimum distance, and the precise guaranteed projection sizes.
The verifier checks generator/dual orthogonality and complementary ranks,
enumerates all dual words under an explicit cap, and then applies the proved
annihilator identity. Enumeration is exponential in dual dimension; exhaustion
of the allowed word count returns UNKNOWN without a distance claim.

For the Golay control, this checks 4,096 dual words, including zero, and imports
the separately verified exact rational all-dual witness. It also verifies a
boundary octad has projection dimension seven on its eight coordinates and
conditioned projection dimension six on its seven other coordinates.
`PROJECTION_RESULTS.json` records the generator, dual certificate, rational
point, counts, lower-certificate counts and boundary evidence.

Tests independently enumerate supports for 371 small generator configurations,
checking every coordinate subset and both pin values. Additional checks cover
all claimed small-instance projection guarantees, boundary parity constraints,
the combined Golay result, malformed certificates and explicit budget limits.
Run `python -m unittest -v test_projection_barrier` and then
`python projection_barrier.py` from this directory.

This model keeps a single coordinate vector and intersects its projected hull
constraints. Sherali-Adams and related hierarchies introduce additional lifted
variables, multiplied constraints, and joint-consistency requirements. No
feasible assignment to those larger systems has been constructed here, so no
claim about their level, rank or proof strength follows from this result.
