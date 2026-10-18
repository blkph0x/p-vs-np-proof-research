# Every redundant parity check can still leave a large fractional gap

This is an obstruction to one specified relaxation, not a proof that P!=NP or
that general linear programming cannot solve the problem. It combines an
elementary analytic witness with standard random-code counting. No novelty claim
is made for this style of pseudocodeword argument.

## 1. Relaxation and the nonzero condition

Let C be a binary linear code of length n. For every nonzero h in its dual
C-perp, take the convex hull of the Boolean assignments with even parity on
support(h). Intersect the resulting cylinders with the box [0,1]^n. Denote
this intersection Q_all(C). It includes **every** redundant parity check, not
merely the rows of a supplied parity-check matrix.

Fix a coordinate j and impose x_j=1. Integer feasible points are exactly the
codewords of C whose jth bit is one, so the zero word is genuinely excluded.
This is stronger than the often unsafe relaxation sum(x)>=1.

## 2. Uniform fractional-point lemma

Assume the dual minimum distance delta=d(C-perp) is at least three. Define

    p = 1/(delta-1),
    x_j = 1,
    x_i = p for i != j.

Then x belongs to Q_all(C), with objective

    sum_i x_i = 1 + (n-1)/(delta-1).

### Proof by explicit local convex mixtures

Take any nonzero dual check h of weight w>=delta. Write a=1 if its support
contains j, and a=0 otherwise. Its remaining m=w-a coordinates all equal p.
Because the pinned bit is a, those m coordinates need parity a for the total
check to be even.

A uniform k-element subset of the m free coordinates has every coordinate
marginal k/m. Mixing two adjacent permitted cardinalities therefore realizes
the desired marginal p whenever mp lies between the smallest and largest
cardinalities of parity a.

If a=1, then m=w-1>=delta-1>=2 and mp>=1. The largest permitted odd cardinality
is m if m is odd and m-1 if m is even. Since p<=1/2, mp<=m/2<=m-1, so mp lies
in the required interval.

If a=0, then m=w>=3. The smallest even cardinality is zero and the largest is
m if m is even and m-1 if m is odd. Again 0<=mp<=m/2<=m-1. Thus a convex mixture
exists here as well.

Choose the adjacent permitted integers k_low<=mp<=k_high. If equal, use that
cardinality alone; otherwise mix the two uniform subset distributions with
probabilities

    (k_high-mp)/(k_high-k_low), (mp-k_low)/(k_high-k_low).

They are nonnegative, sum to one, and give the exact local marginal p. Restore
the pinned bit when present. This supplies an explicit even-parity convex
decomposition for every check, proving the claim without a numerical LP solver.

### Equivalent forbidden-set calculation

The even-parity polytope has the box constraints and the inequalities

    sum_(i in S) (1-x_i) + sum_(i in support(h)-S) x_i >= 1

for every odd subset S of support(h). Since p<=1/2, the nearest forbidden odd
Boolean vector has support {j} when j is in the check, with distance

    (w-1)p >= 1.

Otherwise a singleton minimizes the distance, which is

    1-p+(w-1)p = 1+(w-2)p >= 1.

Every forbidden-set inequality is therefore satisfied. The preceding explicit
mixture proof also verifies sufficiency directly.

## 3. Codes with both primal and dual linear distance exist

Let n be even and choose a uniformly random n/2-dimensional binary subspace C.
For any fixed nonzero vector v,

    Pr(v in C) = (2^(n/2)-1)/(2^n-1) < 2^(-n/2).

C-perp is also uniform among n/2-dimensional subspaces, so the same bound
holds for the dual. For 0<alpha<1/2 the number of vectors with weight at most
floor(alpha*n) is at most 2^(n H_2(alpha)), where

    H_2(alpha) = -alpha log2(alpha) - (1-alpha) log2(1-alpha).

For completeness, the counting bound follows by expanding
(alpha+(1-alpha))^n=1. For i<=alpha*n,
alpha^i*(1-alpha)^(n-i) is at least
alpha^(alpha*n)*(1-alpha)^((1-alpha)*n)=2^(-n H_2(alpha)).
Multiply by binomial(n,i) and sum over those i.

A union bound over the primal and dual low-weight events gives

    Pr(d(C)<=alpha*n or d(C-perp)<=alpha*n)
       < 2^(1 - n*(1/2-H_2(alpha))).

Whenever H_2(alpha)<1/2, this is less than one for all sufficiently large even n.
Thus some C has both distances greater than floor(alpha*n), and in particular
both distances at least alpha*n. No independence between C and its dual is
assumed or needed.

For alpha=1/10 the strict entropy bound can be verified without rounded
logarithms. Put rho=2^(10*(H_2(1/10)-1/2)); then

    rho = 10^10/(32*9^9) < 5/6,

because the integer inequality 6*10^10 < 160*9^9 holds. For every even n>=120,
the failure probability is less than

    2*rho^(n/10) <= 2*(5/6)^12 < 1.

The last comparison follows from 2*5^12 < 6^12. This gives an explicit
all-even-length existence range. It does not certify the distances of an
arbitrary large sampled matrix or provide a polynomial-time
code-construction-and-distance-certification method.

## 4. Linear integrality gap after every parity check and a pin

Let the integer pinned optimum be d_j. If d(C-perp)>=3 then no coordinate of
C is identically zero: otherwise its unit vector belongs to C-perp. Thus the
pinned integer problem is feasible and d_j>=d(C).

For codes with both distances at least alpha*n, the fractional optimum is at
most

    beta_n = 1 + (n-1)/(alpha*n-1) = O(1),

while d_j>=alpha*n. Consequently the integer/fractional ratio is Omega(n).
This holds for every coordinate j. For alpha=0.1 and n>=100, beta_n<=12, so
for every even n>=120 the existence argument supplies a code with ratio at
least n/120.

One may choose any integer threshold k with beta_n<=k<alpha*n. For sufficiently
large n the pinned all-dual LP then reports feasibility although no integer
solution exists. Adding all XOR combinations alone cannot close this gap.

This does not preclude cuts outside the parity-check family, stronger extended
formulations, branching, or other native algorithms.

## 5. Explicit 24-coordinate certificate

`all_dual_lp_barrier.py` constructs twelve rows from shifts of

    g(x)=1+x+x^5+x^6+x^7+x^9+x^11

with an appended parity bit. Independent exact checks establish:

- the rows span a 12-dimensional self-orthogonal space in length 24, hence a
  self-dual code;
- its entire 4,096-word span has weight distribution
  `{0:1, 8:759, 12:2576, 16:759, 24:1}`;
- its minimum distance, and minimum weight under each coordinate pin, is eight.

The uniform point x_j=1, x_i=1/7 has weight 30/7<=5. Explicit rational subset
mixtures verify all 4,095 nonzero dual-check polytopes. Hence at integer upper
bound five the all-dual LP is feasible and the true pinned problem is infeasible.

The validator uses only integer and Fraction arithmetic. It checks malformed
claims and rejects the tempting smaller point x_i=1/8 because a weight-eight
check containing the pin excludes it. Tests also independently expand small
subset mixtures into individual assignments and validate each marginal.

### Matching lower bound: the fractional optimum is exactly 30/7

Exact enumeration finds 253 weight-eight dual checks containing any specified
pin j. Each other coordinate belongs to exactly 77 of those checks. Every
such check includes the valid singleton forbidden-set inequality

    x_j <= sum_(i in support(h)-{j}) x_i.

Sum all 253 inequalities and divide by 77. With x_j=1 this gives

    sum_(i != j) x_i >= 253/77 = 23/7.

Thus every point in the pinned all-dual relaxation has total weight at least
30/7. The constructed point attains that bound, proving the exact fractional
optimum. These incidence counts are verified separately for all 24 possible
pins. This is an explicit rational primal/dual LP certificate, not a conclusion
drawn from a numerical LP solution.

## 6. Relation to established work

Kashyap calls a code geometrically perfect when its codeword polytope equals the
fundamental polytope obtained from the entire dual. His decomposition treatment
records the excluded-minor characterization and makes clear that equality does
not hold universally. See [A Decomposition Theory for Binary Linear Codes,
Section 6](https://ece.iisc.ac.in/~nkashyap/Papers/code_decomp_final.pdf).

Even finding a violated redundant parity-check inequality is a nontrivial
algorithmic problem: Puchert and Tillmann prove NP-hardness of exact separation
over that family. See [Exact Separation of Forbidden-Set Cuts Associated with
Redundant Parity Checks of Binary Linear Codes](https://arxiv.org/abs/2004.03387).
The gap theorem above is stronger in a different direction: it persists even
if an oracle supplies every parity check for free. It makes no statement about
separation of stronger, non-parity inequalities.
