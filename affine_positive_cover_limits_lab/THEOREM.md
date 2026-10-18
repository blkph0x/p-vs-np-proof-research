# Affine positive-cover and overlap limits for disjoint three-variable clauses

This elementary note concerns the explicit, succinct CNF

    F_m(x) = AND_{i=1}^m (x_(3i-2) OR x_(3i-1) OR x_(3i)),
    S_m = (GF(2)^3 minus {000})^m.

There are m clauses, 3m variables and 3m literal occurrences; its usual indexed
encoding has polynomial length. F_m has 7^m satisfying assignments. The empty
case m=0 is the scalar one. The all-ones assignment is an immediate SAT witness;
disjoint factorization computes the model count 7^m with polynomial work and
bit length. Component elimination can process one clause at a time and never
construct the exponential whole-function positive sum. Thus even an
exponential representation lower bound here implies neither slow decision nor
slow counting, and does not defeat component elimination. The result limits a
representation, not SAT decision complexity.
No novelty claim or external lower-bound theorem is needed.

## Nonnegative affine indicators require exponentially many pieces

Suppose F_m = sum_(j=1)^K c_j 1_(A_j), where each A_j is a nonempty affine
subspace of GF(2)^(3m) and c_j is a strictly positive real number. Zero
coefficients may be discarded. At an unsatisfying point the sum is zero, so
every term must vanish there: A_j is contained in S_m.

The projection of such an A_j onto each three-bit block is affine and avoids
000. A dimension-three affine subset is the whole block, so each projection
has dimension at most two. The simultaneous block projections are injective
on the direction space of A_j; consequently

    dim(A_j) <= sum_i dim(projection_i A_j) <= 2m,
    |A_j| <= 4^m.

Every point of S_m belongs to some term support. Even allowing arbitrary
overlap and arbitrary positive real coefficients gives

    7^m <= sum_j |A_j| <= K 4^m,
    K >= ceil((7/4)^m).

The support bound is attained: in every block impose its first bit equal to
one and leave the other two free. A constructive exact upper bound is 3^m
pieces: partition each block according to its first one, with local pieces
x=1, x=0 and y=1, and x=y=0 and z=1; take their Cartesian products.
This gives an explicit exponential lower bound for this succinct CNF family
within the nonnegative indicator language.

The identical support-cover lower bound also holds for arbitrary signed or
quadratic-phase terms if their supports are separately assumed to lie inside
S_m: every satisfying point must still be covered. General signed expansions
do not satisfy this additional assumption.

## Why nonnegative coefficients alone are insufficient

In the signed quadratic language an atom is 1_A(-1)^q. A pointwise nonnegative
nonzero term must have constant effective sign on its support, so after
absorbing the constant sign it is just a positive indicator. Merely requiring
positive displayed coefficients does not imply pointwise nonnegative terms:

    (1 + (-1)^x)/2 = 1_(x=0).

Both displayed coefficients are positive, but the two full supports cancel
at x=1. No argument may infer support containment from coefficient signs alone.

For one three-bit OR, 1 - 1_(000) is a two-term signed representation with a
full-cube support that includes the forbidden point. It cannot be one affine
quadratic atom because its support has size seven. Its positive-indicator
minimum is three: two supports of size at most four cannot cover seven.
If both have size four they are affine hyperplanes avoiding zero; distinct
ones intersect in two points, while identical ones have union size four.
If either is smaller, their union has at most six points. The first-one
partition attains three. Thus cancellation already changes the exact minimum.

For all m, expanding product_i (1 - 1_(block_i=000)) gives 2^m signed
indicator terms. This upper bound is still exponential and neither proves
nor disproves a substantially smaller signed quadratic representation.

## A signed overlap bound survives

For every nonempty affine H in GF(2)^(3m),

    |H intersect S_m|^2 / |H| <= (49/8)^m.                 (1)

Proof is by induction, starting with the one-point zero-coordinate universe.
Let P be H's affine projection on the first block, of dimension d. Every
fiber above P is an affine coset of the same kernel B, of size |B|, in the
remaining 3(m-1) coordinates. The induction hypothesis bounds the number of
satisfying points in each allowed fiber by sqrt((49/8)^(m-1)|B|). There are
t=|P minus {000}| allowed fibers and |H|=2^d|B|. Hence the ratio in (1) is at
most (t^2/2^d)(49/8)^(m-1). The possible multipliers are

    0, 1/2, 1, 2, 9/4, 4, 49/8.

Dimension three forces P to be the whole block, giving the maximum 49/8;
all lower-dimensional cases are smaller. This proves (1). The full cube H
attains equality because its intersection size is 7^m and its size is 8^m.
The equal-size-fiber step permits arbitrary dependencies between blocks.

Equip the truth-function space with its ordinary Euclidean inner product.
Let psi=F_m/sqrt(7^m), and let phi=1_H times a unit-modulus phase, divided by
sqrt(|H|). The triangle inequality and (1) show

    |<psi,phi>|^2 <= (7/8)^m.                            (2)

Equality is attained by the constant phase on the full cube. Real quadratic
phases are included, and the inequality itself also permits any complex
unit-modulus phases. This mathematical extension does not add complex
arithmetic to any implementation.

If psi=sum_j alpha_j phi_j is any exact normalized-atom decomposition, then
1=|<psi,psi>| <= (7/8)^(m/2) sum_j |alpha_j|. Cauchy--Schwarz gives

    (sum_j |alpha_j|)^2 >= (8/7)^m,
    K sum_j |alpha_j|^2 >= (8/7)^m.                      (3)

For unnormalized real rational atoms F_m=sum_j c_j 1_(H_j)(-1)^q_j, the latter
inequality is exactly

    K sum_j c_j^2 |H_j| >= 8^m.                         (4)

These are coefficient-weight or coefficient-energy bounds, not unrestricted
rank lower bounds. Without a justified upper bound on sum_j |alpha_j|^2,
equation (3) gives no lower bound on K alone. Exponentially large rational
magnitudes may have only linearly many bits; a polynomial bit-length
assumption does not supply the missing energy bound.

There is a related conditioning consequence. Let G be the positive
semidefinite Gram matrix of the K normalized atoms in an exact decomposition.
Since 1=alpha* G alpha >= lambda_min(G)||alpha||_2^2, (3) implies

    lambda_min(G) <= K (7/8)^m.

This is trivial when the atoms are dependent. Even for an independent
representation it only says a small representation must be poorly
conditioned; polynomial encoding length alone does not exclude exponentially
small eigenvalues. No conditioning lower bound is asserted here.

## Relation to the existing capacity theorem and finite controls

The earlier affine_sum_capacity_lab theorem allows signed quadratic atoms
and proves an existential lower bound for arbitrary truth functions. It does
not identify a polynomial-size CNF family. The present support-cover theorem
does identify a succinct family but restricts its positive representation.
Neither result fills the other's missing assumption. Equations (1)--(4)
quantify signed overlap/weight, not a general signed piece-count barrier.
These statements do not constrain every SAT algorithm or settle P versus NP.

The bounded script enumerates every nonempty affine support through six bits
for m=0,1,2, and every ambient quadratic phase on every three-bit affine
support. It verifies the support and overlap bounds exactly with rational
arithmetic. An independent subset-closure test checks the three-bit affine
enumerator. The actual original CNFs and both constructive decompositions
are saved for m=0..4 and checked on every original assignment. Symbolic
integer counts reach m=512 without expanding their truth tables or terms.
The tests are evidence for indexing and formulas; the induction proves the
all-size claims. Unsupported enumeration sizes raise ValueError; this lab
is a bounded control, not a decision solver returning a universal result.

Reproduce with `python -m unittest discover -v` and `python controls.py`.
RESULTS.json binds controls.py, test_controls.py and this theorem by SHA-256,
and confirms that those files remained unchanged during the saved run.
