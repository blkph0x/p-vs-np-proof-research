# Independent audit: all-dual parity-polytope barrier

Reviewed 2026-10-18. The proposed fractional-point lemma, random-systematic
existence argument and Golay witness are correct, with the qualifications below.
This is a barrier to a specified relaxation, not a resolution of P versus NP.

## General fractional point

Let C be a binary code with finite dual minimum distance delta>=3. Set one
coordinate x_j=1 and every other coordinate to epsilon=1/(delta-1). For a
nonzero dual check with support S of size w, the even-parity polytope requires,
for each odd F contained in S,

    sum_{i in F}(1-x_i) + sum_{i in S-F} x_i >= 1.

Since 0<epsilon<=1/2, minimizing over the possible odd set sizes gives:

- j outside S: minimum is 1+(w-2)epsilon, attained at |F|=1.
- j in S and in F: minimum is (w-1)epsilon, attained at F={j}.
- j in S but outside F: minimum is 2+(w-3)epsilon, attained at |F|=1.

Every value is at least one because w>=delta. Coordinate bounds hold as well.
The point therefore survives **all** redundant parity checks, and its objective
is 1+(n-1)/(delta-1). This is an upper bound on the LP optimum, not generally
an equality.

The pin here is specifically x_j=1. The pinned integer problem is feasible:
if no codeword had coordinate j equal to one, the unit vector e_j would belong
to the dual, contradicting delta>=3. Its optimum is at least the primal
minimum distance d. Thus if d and delta both grow linearly with n, the ratio
of integer optimum to LP optimum grows as Omega(n), for every choice of j.
This also defeats solving each of the n one-coordinate-pinned relaxations
separately and taking the best bound. No corresponding statement about
arbitrary deeper branching follows.

## All-size existence with an explicit finite threshold

Let n=2k and choose a uniformly random binary k by k matrix M. The systematic
code C={ (u,uM) } has dimension k without any rank-conditioning event. Its dual
is { (vM^T,v) }. For each fixed nonzero u, uM is uniform; the analogous fact
holds for each fixed nonzero v in the dual. Consequently the expected total
number of nonzero primal or dual words of weight at most t is bounded by

    2 * 2^(-k) * sum_{i=0}^t C(n,i).

For n=10m and t=m, the elementary binomial-ball bound gives the exact expression

    expectation <= 2 * [10^10 / (32 * 9^9)]^m.

One way to prove the ball bound is to sum the binomial distribution with
success probability 1/10: each probability factor at i<=m is at least its
value at i=m. Rearranging gives
sum_{i<=m} C(10m,i) <= (10^10/9^9)^m.

The strict inequality 10^10<32*9^9 proves H_2(1/10)<1/2 but, by itself,
does not quantify a threshold n=120. A sufficient exact strengthening is

    6 * 10^10 < 160 * 9^9,

which puts the bracketed ratio below 5/6. For m>=12,
2(5/6)^m<=2(5/6)^12<1, with the last inequality equivalent to
2*5^12<6^12. Therefore for every n divisible by ten with n>=120, some
systematic code has both primal and dual distances at least n/10+1.
The direct exact expectation bound at n=120 is approximately 0.151719.

For any pin j in such a code, epsilon=10/n is already sufficient for feasibility
and gives fractional objective 11-10/n<11. The integer optimum is at least
n/10+1>11. The resulting integrality ratio is at least

    (n/10+1)/(11-10/n) > n/110.

This is an existence theorem at each stated length. It does not efficiently
construct a generator with certified distances, prove average-case decoding
hardness, or establish hardness for every random matrix.

## Independent Golay audit and an exact LP optimum

Using the twelve raw generator rows supplied by `all_dual_lp_barrier.py`, an
independent XOR enumeration (not its span function or certificate verifier)
produced 4,096 distinct codewords. Pairwise generator orthogonality plus
dimension twelve proves the length-24 code is self-dual. Its weight distribution
was exactly

    weight 0: 1; weight 8: 759; weight 12: 2576;
    weight 16: 759; weight 24: 1.

The minimum weight among words with coordinate zero equal to one was eight.
For the proposed fractional vector (1,1/7,...,1/7), every one of the 4,095
nonzero dual checks was independently tested against every possible odd-set
size and pin-membership case in the inequality above, using rational
arithmetic. All passed; the minimum left-hand side was exactly one. Its
objective is 30/7.

There is also a short exact LP lower certificate. Among the 759 weight-eight
dual checks, exactly 253 contain coordinate zero. Each of the other 23
coordinates occurs in exactly 77 of these 253 checks, as independently counted
in the enumerated supports. For every such check S, its singleton forbidden
set F={0} gives

    sum_{i in S-{0}} x_i >= x_0 = 1.

Summing these 253 inequalities yields

    77 * sum_{i!=0} x_i >= 253,

and hence total objective at least 1+253/77=30/7. Together with the feasible
point, this proves the **exact** all-dual pinned LP optimum is 30/7. The pinned
integer optimum is eight, so the exact finite integrality ratio is 28/15.
An integer decision threshold of five separates the fractional relaxation
from the integer feasible set.

## Scope of the obstruction

Even including exponentially many redundant checks does not make this
intersection of local parity polytopes exact. That does not rule out other
valid global inequalities, richer liftings, different proof systems, native
algorithms, or polynomial SAT algorithms. In particular, no P!=NP conclusion
can be drawn from these integrality gaps.

## Independent rank-native solver audit

The rank-based exceptional-column solver was reviewed independently, including
its certificate verifier and budget semantics. No correctness or optimality
gap was found in this review. This is mathematical/code review and finite
testing, not a machine-checked formal proof.

For a fixed exceptional-column syndrome, every exceptional support induces the
same residual graph problem. Exceptional and graph coordinates are disjoint,
so their Hamming weights add. Keeping the cheapest exceptional support per
syndrome is therefore sound. The dynamic program must distinguish the empty
zero-syndrome support from the cheapest nonempty zero-syndrome support. For a
zero target with a nonzero-word requirement, the former requires a nonempty
graph cycle, whereas the latter permits the empty graph support. Both cases
are present. For a nonzero target, or when zero is permitted, the nonempty
zero-syndrome exceptional support is dominated by the empty one and may be
omitted. The row transformation is invertible, so testing whether the original
target is zero is equivalent to testing whether the transformed target is zero.

The verifier independently replays the scalar Bellman costs and checks the
final exceptional witnesses against those costs and syndromes. It then checks
the required graph branches and their certificates. A partial dynamic program
does not certify coverage of final syndromes. A partial graph search may return
a feasible upper-bound word, but must retain UNKNOWN status and no exact
distance. The inspected implementation follows these distinctions.

An independent exhaustive-support oracle checked 100 random input cases with
zero to five parity-check rows and zero to eight coordinates under four budget
settings, for 400 comparisons including 169 UNKNOWN outcomes. Every exact
answer agreed with enumeration, and every reported upper-bound word was
feasible. A targeted partial graph search returned upper bound three where the
complete optimum is two. Another targeted instance with 100 identical
exceptional columns and exceptional rank one returned distance two, exercising
the necessary nonempty zero-syndrome case.

One verifier resource-hardening opportunity remains: if the declared state
limit is already smaller than 2^p, a supplied certificate containing extra
dynamic-program layers can be rejected before replaying those layers. The
current verifier rejects that inconsistent certificate after replay. This is
extra work on malformed input, not acceptance of a false optimum or a failure
of the producer's budget enforcement. Stable solver code was left unchanged.

The algorithmic scope is O(q*2^p) exceptional-state work, followed by at most
2^p+1 certified graph calls, up to polynomial bookkeeping factors. Here q is
the number of exceptional columns and p is their binary rank in the certified
row basis. This applies to the explicit disjoint graph/exceptional-column
decomposition; it is not a result for arbitrary low-rank perturbations.
