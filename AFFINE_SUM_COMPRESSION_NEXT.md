# Next candidate: certified addition identities

The compact-boundary phase succeeded on 54 of 58 frozen original CNFs, and reached
an explicit cap on four. The exponential branch/component reference solved all
58. Identical canonical pieces are already merged correctly. That rule leaves
algebraic identities between different supports unused. The next experiment must
measure whether a stronger rule reduces actual original-instance work, including
discovery and checking cost. No polynomial bound for general CNF follows.

## A precise merge rule to implement and check

Suppose A=a+im(U) and B=a+delta+im(U) are disjoint parallel affine spaces over
GF(2), with U injective and delta outside im(U). Their union is the affine space
C={a+Ut+s*delta : t in GF(2)^r, s in GF(2)}. The parametrization is bijective.
Consider two signed pieces on the disjoint supports:

    f(a+Ut) = c (-1)^q0(t)
    g(a+delta+Ut) = d (-1)^q1(t)

where c,d are nonzero rationals and q0,q1 have degree at most two. If |c|=|d|,
write d/c=(-1)^sigma. The sum on C equals

    c (-1)^[q0(t) + s*(q0(t)+q1(t)+sigma)].

This is a quadratic affine piece exactly when q0+q1 has degree at most one in
these common free coordinates. Sufficiency follows by the displayed identity.
Necessity for this representation follows from uniqueness of Boolean multilinear
polynomials: each quadratic term in q0+q1 would produce a distinct cubic term
containing s. An invertible affine coordinate change preserves the property of
having degree at most two, so another coordinate choice cannot remove this
obstruction. Unequal magnitudes cannot give a nonzero constant-magnitude affine
piece on the union. Support equality, parallelism, the independent displacement,
the coordinate maps, and the phase restriction identities can all be checked by
linear/quadratic algebra without enumerating the boundary truth table.

This rule covers 1[x=0]+1[x=1]=1 and 1[x=0]-1[x=1]=(-1)^x. It also covers
parallel cosets with arbitrary common quadratic phase on their free coordinates.
It requires a checked common parametrization; comparing raw phase term lists is
insufficient when the supports impose equations.

### An explicit polynomial replay construction

At one boundary node, first independently normalize both nonzero pieces using
the same retained original-variable order. Parallel supports then have the same
full-row-rank RREF left-hand matrix A, with different right-hand sides b0,b1.
The original nonpivot coordinates are common free coordinates for both pieces;
their canonical phases q0,q1 are already expressed in those coordinates. Put
d=b0+b1, choose any row j with d_j=1, and define s(x)=A_j*x+b0_j. The affine
union is described, without a truth table, by the rows

    (A_i+d_i*A_j)*x = b0_i+d_i*b0_j, for i != j.

These rows have rank rank(A)-1. On their support, s=0 gives Ax=b0 and s=1
gives Ax=b1, so their support is exactly the disjoint union. The canonical
phases have identical quadratic monomials precisely when q0+q1 is affine in
the common free coordinates. With this check and |c|=|d_coefficient|, construct
q0+s*(q0+q1+sigma), expand using x_i^2=x_i, and independently canonicalize the
result on the union support. All expressions remain of degree at most two.
This is a constructive special case of the common-parametrization argument;
it avoids guessing a coordinate map. The zero-rank case has no two distinct
parallel full-space supports and is correctly excluded.

A source-bound rewrite certificate can name two currently present message IDs,
their exact coefficients, the chosen row j, and the proposed normalized output.
The checker reads the two pieces from its independently derived current message
multiset, repeats the checks above, consumes both IDs exactly once, and inserts
one fresh output ID. Every unconsumed piece remains in the multiset. Thus each
rewrite preserves the pointwise sum even in the presence of other overlapping
pieces. The enclosing factor-ownership certificate and complete pre-merge
cross-product enumeration remain required; this arithmetic rewrite never
licenses removal of an original factor or refunds the work of producing a pair.

## A separate overlapping-support candidate

For the same support and equal magnitudes, after absorbing the relative sign,

    c(-1)^q0 + c(-1)^q1 = 2c(-1)^q0 * 1[q0+q1=0].

An affine phase difference yields one extra linear support equation and is a
safe compact merge. A general quadratic phase difference does not automatically
yield affine support: xy=0 contains three of four assignments. Some special
quadratic level sets are affine (xy=1 pins both variables), so a later extension
could accept them with an explicit support-equivalence certificate. Do not
silently replace quadratic constraints by linear ones.

## Nested-support codimension-one subtraction

Let A be a nonempty affine support, and let B=A intersect [L(x)=b] be a
nonempty proper affine hyperplane of A. In particular L is not constant on A.
Suppose the two quadratic phases agree on B. For any nonzero rational c,

    c 1_A (-1)^qA - c 1_B (-1)^qB
      = c 1_{A intersect [L(x)=1+b]} (-1)^qA.

The proof is pointwise. Outside A both sides are zero. On B the two summands
cancel because their restricted phases agree. On A minus B only the first
summand remains. Because L takes both Boolean values on A, this complement is
the other nonempty affine hyperplane of A. Restricting qA to that support keeps
degree at most two, so the result is one valid compact affine quadratic piece.

More generally, for input coefficients cA,cB and phases qA,qB, the precise sign
condition is that qA+qB restricts to a constant epsilon on B and

    cB = (-1)^(epsilon+1) cA.

Then the same complement identity holds with coefficient cA. Thus coefficients
that look equal may still cancel when the phases differ by the constant one on
B. Checking raw coefficient signs or ambient phase lists alone is insufficient.
For nonzero inputs, this is the exact compatibility condition for cancellation
on all of B; it is not a characterization of every possible affine-sum rewrite.

The source-bound certificate names two current verified message IDs, identifies
which support is A and which is B, supplies a candidate original-coordinate row
L and right-hand side b, and supplies the normalized output. The checker must:

- Independently establish that A and B are nonempty and that normalizing A with
  the added row L=b gives exactly B, with rank increased by one.
- Parametrize B, restrict both phases to its free coordinates, and check that
  their XOR is the constant epsilon by exact Boolean polynomial algebra.
- Check the rational coefficient equation above, and independently normalize
  A with L=1+b, phase qA, and scalar cA to derive the output.
- Consume the two named current message IDs exactly once, insert the verified
  output under a fresh ID, and retain every other current piece unchanged.

The extra row can be discovered by row reduction: for nested consistent
supports, the equation row space of B extends that of A by exactly one
dimension. All checks and this pairwise discovery use polynomial linear and
quadratic algebra in the explicit boundary representation. Empty, equal,
non-nested, or higher-codimension supports require other rules; they cannot be
silently accepted by this certificate. The enclosing source ownership,
projected-variable accounting, and complete pre-merge production obligations
remain unchanged.

The immediate positive control is a unit clause. Its two defect pieces
1 - 1[literal=false] become the single pin 1[literal=true]. Multiplying that pin
into later factors performs ordinary exact propagation and may turn a larger
clause's violation support into a codimension-one restriction of the current
affine support. This is a representation of familiar propagation algebra, not
a new general tractability result. It is reasonable to test whether this
reduces the saved connected-mixed fixture's work, but no such improvement has
yet been measured or established.

For contrast, subtracting a nonempty codimension-k affine subspace B from a
d-dimensional A leaves 2^(d-k)*(2^k-1) supported points. For k>=2 this is not a
power of two, so the complement cannot itself be the support of one nonzero
affine piece. In particular a plain OR with two or more distinct, unfixed
variables does not collapse to one affine piece by this cancellation rule.
This is a precise obstruction to that single rewrite, not a lower bound for
representing the function by several pieces or for another algorithm.

Before implementation, the rule's controls should include both effective sign
cases, phases that agree only after restriction to B, a nonconstant phase
difference on B that must be rejected, wrong containment/rank, rational
coefficients, sparse original IDs, and a unit pin propagated through a shared
variable while preserving the original free-variable count.

## Experimental and proof requirements

Keep every pre-merge coefficient, support, and phase tied to its original factor
DAG. A merge certificate must prove equality of functions on the union of its
input supports, including zeros and signs. The checker must reconstruct the
common coordinates independently and reject a phase identity valid on only one
coset. Test rational magnitudes, opposite signs, nonparallel supports, incompatible
quadratic phases, sparse/permuted original IDs, and cancellation.

Charge all candidate-pair discovery, unsuccessful attempts, intermediate pieces,
canonical reductions, and verification. Pairwise scanning can be quadratic in K
per pass, and K can already be exponential. A smaller final answer is not a bound
on the work required to find it. Re-run the same 58 original CNFs with the same
resource units, retaining every UNKNOWN, and compare with the frozen reference.
This is a proposed next experiment, not an implemented or verified speedup.
