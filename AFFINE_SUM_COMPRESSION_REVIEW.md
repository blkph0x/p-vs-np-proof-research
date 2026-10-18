# Independent review of the proposed affine-sum identities

**Clean mathematical verdict within the stated merge scope.** This reviews
[AFFINE_SUM_COMPRESSION_NEXT.md](AFFINE_SUM_COMPRESSION_NEXT.md) with SHA-256
`6a271b4597991f07ff6ee6813ac6b55deaefb663857832e32cd631ccbb01fa40`.
The implementation of an arithmetic rewrite checker and its measured impact
on original SAT instances remain future work. No production code was changed.

## Common coordinates and the exact phase criterion

Let the supports be disjoint cosets a+im(U) and a+delta+im(U), where U is
injective and delta is outside its image. Their union has the bijective
coordinates (t,s) mapped to a+Ut+s delta. For nonzero coefficients c,d of
equal magnitude, write d/c=(-1)^sigma. The sum is nonzero at every point of
this union and has phase

\[
q_0(t)+s\bigl(q_0(t)+q_1(t)+\sigma\bigr).
\]

The criterion in the draft is necessary and sufficient: the common-coordinate
difference q0+q1 must have degree at most one. Sufficiency follows by multiplying
an affine difference by s. For necessity, every quadratic monomial of the
difference introduces its own cubic monomial containing the new independent
coordinate s. Such terms cannot cancel against q0, which has no s, or against
one another because their monomial masks are distinct. Uniqueness of the
Boolean multilinear polynomial then gives degree three.

This obstruction cannot be removed by an invertible affine change of the
coordinates of the union. Substituting affine forms into a polynomial cannot
increase algebraic degree; Boolean square reduction can only decrease it.
Applying the same statement to the inverse change gives the reverse inequality,
so degree is invariant. A different affine-support representation cannot evade
this argument either: the sum's support is exactly the union, since the inputs
are disjoint and their coefficients are nonzero. If their magnitudes differ,
that support has two distinct nonzero magnitudes and therefore cannot be one
nonzero constant-magnitude affine piece.

These statements require common affine coordinates. Comparing raw phase lists
before restriction to support would be unsound. The draft correctly calls for
canonical restriction under the same ordered original retained variables.

## Checked union construction

For canonical parallel supports with the same full-row-rank matrix A and
right sides b0 and b1, write d=b0+b1 and choose j with d_j=1. The proposed
rows `(A_i+d_i A_j)x=b0_i+d_i b0_j`, for i other than j, are correct.
Their coefficient combinations are independent: the coefficient vector of
row i has its own non-j coordinate equal to one. Therefore the transformed
matrix has rank rank(A)-1.

On the new support, set s=A_j x+b0_j. Every original row then satisfies
`A_i x+b0_i=d_i s`, including j, so Ax=b0+s d. Conversely either original
coset satisfies every new row. This proves exact union equality and identifies
the selector s without enumeration. Under common RREF pivot order, the original
nonpivot coordinates are the same independent free coordinates for both
cosets. The draft's phase comparison and quadratic output construction thus
apply directly. Rank zero admits no distinct parallel full-space cosets.

The same-support identity is also correct after incorporating relative sign:
the sum is twice one phase restricted to the zero set of the phase difference.
An affine difference provides a linear equation, including constant-zero and
constant-one cases. An arbitrary quadratic zero set is not automatically affine;
the draft explicitly preserves that limitation.

## Added nested-support subtraction rule

The final draft's codimension-one addition is also sound. If B is a nonempty
proper affine hyperplane of A and qA+qB restricts to epsilon on B, then
`cB=(-1)**(epsilon+1)*cA` makes the two contributions cancel everywhere on B.
On A minus B only the first contribution remains. Flipping the single added
linear equation describes precisely that complementary hyperplane; restricting
the original quadratic phase to it preserves degree at most two. This handles
both apparent coefficient signs, since an effective sign may instead be stored
in the restricted phase.

The proposed checks of nonempty supports, exact containment after adding the
row, rank increase one, restricted phase difference, and exact rational
coefficient relation are sufficient. The certificate must still bind the actual
current piece IDs and preserve all other pieces. For codimension k at least
two, the stated complement size `2**(d-k)*(2**k-1)` is not a power of two, so
that complement cannot be the support of a single nonzero affine piece.
The draft correctly confines this obstruction to one-piece cancellation and
does not infer a lower bound for general sums or other algorithms. This section
is a mathematical audit; the finite controls below target the parallel-coset
criterion and union construction, not a future nested-rule implementation.

## Reproducible finite controls

Run from the overnight research directory:

```text
python AFFINE_SUM_COMPRESSION_REVIEW.py
```

The script imports no production implementation and writes only
[AFFINE_SUM_COMPRESSION_REVIEW.json](AFFINE_SUM_COMPRESSION_REVIEW.json).
It checks the draft's exact reviewed hash before running and refuses to bind
an altered draft without a new review. The JSON records the hashes of the
draft, script and this review and confirms they did not change during execution.

- **33,320 phase/sign cases:** exhaust every pair of quadratic Boolean phases
  through three common free coordinates and both relative signs. Construct
  the two-coset truth table, recover its polynomial using an independent
  Boolean Mobius transform, and compare its degree with the proposed criterion.
  These are deliberately small reference tables; no table-based production
  implementation is proposed.
- **1,000 full-row-rank union systems**, seed 2026101903, dimensions one through
  seven: check **35,126 original assignments** against both the original coset
  syndromes and the proposed union equations. Also check the rank drop,
  selector on every supported assignment, and expected union cardinality.

The finite controls substantiate the independently checked general identities;
they do not prove an unrestricted complexity claim. Rewrite certificates must
still bind the actual two current pieces, preserve all unconsumed pieces, and
retain original factor ownership. Candidate discovery and verification costs
must be charged, and the number of pieces may remain exponential. The draft
states these limits correctly.
