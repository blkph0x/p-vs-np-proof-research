# Complete one-piece recognition for an explicit signed affine sum

Status: mathematical design independently reviewed in conversation; a separate
implementation and saved adversarial audit are still required. No P-versus-NP
conclusion or novelty claim is made. This extends the narrower disjoint-partition
recognizer: overlaps, unequal coefficients and cancellations are allowed in the
input sum. The input must be an **explicit list** of pieces.

## The precise proposed theorem

Let x range over GF(2)^m and let

    f(x) = sum_{i=1}^K c_i * 1[A_i*x=b_i] * (-1)^q_i(x),

where every coefficient is rational and each q_i is quadratic. There is a
deterministic algorithm, polynomial in m, the explicit list size, equation and
phase descriptions, and coefficient bit lengths, that decides whether f is zero
or one nonzero rational affine-supported quadratic sign. In the positive case
it constructs that piece. The coordinate universe is explicit; a short binary
header is not permission to allocate an uncharged enormous dimension.

The key is that squared norms on affine restrictions can be computed from
pairwise contractions. This is one-piece recognition, not minimum-rank
decomposition, not a bound on K, and not an algorithm for a succinct CNF product.

## 1. An exact restricted-norm primitive

For any affine restriction P define

    N(P) = sum_{x in P} f(x)^2.

Expand f^2 into K diagonal terms and K(K-1)/2 doubled off-diagonal terms. Each
pair product has the intersected affine support, coefficient c_i*c_j, and
quadratic phase q_i+q_j over GF(2). Intersect it with P and use the already
checked compact marginalizer to sum all coordinates. Thus one norm query
requires K(K+1)/2 exact compact contractions, plus rational arithmetic.

Although individual pair contributions can be negative, the completed N(P)
is nonnegative because the functions are real. It is zero exactly when f
vanishes at every point of P. An exact negative result is an implementation
or proof failure, never a usable answer. No floating-point sign tests occur.

Products, normalizations, failed queries, all original terms and all pair
multiplicities must be charged and certified. Reusing a query requires exact
binding to its restrictions and original input sum. Rational denominator and
numerator lengths are bounded polynomially in the sum of input bit lengths,
log K and m; treating arbitrary large integers as unit cost is unnecessary.

## 2. Recover the affine hull of the nonzero support

First compute N(all). If it is zero, f is the zero function. Otherwise find a
point a with f(a) nonzero by assigning coordinates one at a time. Given a
restriction known to have positive norm, query its x_j=0 half. Choose that
half if its norm is positive; otherwise choose x_j=1. The halves partition
the current restriction, so the chosen half still has positive norm. After
m steps the restriction is one point. Directly evaluate f there as a check.

Initialize H={a}. Maintain H as the affine span of explicitly found points
where f is nonzero. Write its independent affine equations as L_j(x)=b_j.
For every row, query N(L_j(x)=1-b_j). A positive result yields another nonzero
point outside H, using the same prefix search with that violated row retained.
Add its difference from a to the direction basis of H; the rank strictly
increases. Restart the equation scan after updating H.

There are at most m strict rank increases. At termination, every violated-row
norm is zero. Every point outside H violates at least one defining equation,
so f vanishes outside H. Conversely, H is spanned by actual nonzero support
points, so it lies in the affine hull of that support. Consequently H is
exactly the affine hull of supp(f). The scans and prefix searches use O(m^2)
norm queries, with polynomial rank and equation computations.

For a compact certificate, record the independent nonzero support points,
their rank, and the final zero norms for every violated defining equation.
Those establish hull equality without asking the checker to trust discovery
statistics or repeat every unsuccessful search. Discovery cost remains part
of the producer's total separately.

## 3. Determine the only possible quadratic piece

Choose a canonical affine parametrization x=a_0+B*u of H, with d independent
free coordinates u. The canonical anchor a_0 need not be one of the points
found during support discovery. Evaluate c=f(a_0). If c=0, reject: a nonzero
single piece whose support has hull H must be nonzero everywhere on H.

Evaluate f at the points with u=e_i and u=e_i+e_j. Each must have magnitude
|c|; otherwise no single piece is possible. Absorb the sign at u=0 into c,
so the candidate phase has constant term zero. Let s_i and s_ij be the bits
specified by f(e_i)/c=(-1)^s_i and f(e_i+e_j)/c=(-1)^s_ij. The only possible
quadratic phase in these coordinates is

    q(u) = sum_i s_i*u_i + sum_{i<j}(s_ij+s_i+s_j)*u_i*u_j.

Boolean multilinear quadratics are uniquely determined by their values on
coordinate weights zero, one and two. Construct g=c*1_H*(-1)^q, lift the free
coordinate phase into the original coordinate representation, and normalize
using the existing checked routine. Empty and one-dimensional hulls use the
same argument with the corresponding missing terms omitted.

## 4. Finish with a complete equality test

Compute sum_x (f(x)-g(x))^2, using the same norm primitive on K+1 pieces.
If it is zero, output g with the equality certificate. If it is positive,
f is not one piece: any possible nonzero single piece would have support H,
coefficient c at a_0, and the unique sampled phase just constructed, so it
would equal g. No different affine support or quadratic candidate remains.

A failed magnitude sample, zero canonical anchor, or positive final difference
norm is a mathematical rejection of this narrow representation class, provided
the support and evaluation evidence verifies. A resource limit is UNKNOWN,
never a rejection or an approximate output. Invalid original inputs are rejected
as malformed. A positive equality claim must replay against every original
piece, independently of any claimed success statistics.

## Cost and non-circularity

The construction uses O(m^2*K^2) compact pair contractions, polynomially many
rank operations and point evaluations, and polynomial-size rational arithmetic
and certificates. A concrete implementation should state its own conservative
operation bounds rather than infer a practical speedup from this asymptotic
existence argument. Repeating a complete recognition attempt at every solver
node may be much more expensive than the present local rules.

The original SAT formula is a product of clause functions. Expanding that
product into this explicit sum can require exponentially many pieces. The
norm of the unexpanded Boolean CNF function is its exact satisfying-assignment
count, because f^2=f. Supplying a cheap norm oracle for that succinct product
would simply assume the central hard computation. This design supplies the
oracle only for an already explicit affine sum and charges every pair.

It therefore offers a rigorous next compression primitive while leaving the
universal representation-size and discovery questions unresolved. A recursive
split into one-piece leaves can also require exponentially many leaves.

## Required implementation controls

Retain zero cancellation; overlapping supports; unequal input coefficients;
noncanonical hull anchors; gapped support; incompatible cubic sign patterns;
the four-line greedy trap; and wide symbolic positive families. Compare small
original sums with direct truth tables. Mutate support points, hull equations,
pair multiplicities, source bindings, sample signs and final norm certificates.
Caps must cover every pair, coordinate, rational bit length and proof object.
Integrate into a solver only after independent review, then preserve the same
complete original inputs and report all regressions and UNKNOWN outcomes.
