# A rank limit for replacing parity checks by syndrome projections

The proposed obstruction is valid. This is the elementary column-dependence
proof of the Singleton bound, applied to a specified relaxation; no novelty
claim is made. It does not give a lower bound for general algorithms or settle
P versus NP.

## Exact statement

Let H be a binary matrix with n columns and rank r. Let C = ker(H) have
minimum nonzero weight d. For the zero code one may use d = infinity. Choose
any matrix Q of compatible dimensions and put A = QH, with **actual rank** q.
Its number of rows need not equal q, and rank(Q) can exceed q if H has
dependent rows. The relaxed code C_Q = ker(A) contains C.

If n > q, there is a nonzero word w with

    support(w) contained in the first q+1 coordinates,
    A w = 0,                  weight(w) <= q+1.

Indeed, any q+1 columns of a rank-q matrix are linearly dependent. The
nonzero binary dependence coefficients, placed in those coordinates, give w.
In particular d(C_Q) <= q+1. Therefore, if **q+1 < d**, then

    d(C_Q) < d(C),             H w != 0.

Every minimum-weight nonzero word of C_Q is also spurious for C, because its
weight is at most q+1 < d. The explicit witness verifies that at least one
short word is spurious; the stronger statement about every projected minimum
additionally uses the certified lower bound d on the original code.

The conclusion holds for every realized Q, so adaptive or random selection of
Q cannot evade it while the final optimization problem remains ker(QH) with
the stated rank. If d grows linearly with n, an exact replacement of this form
requires q >= d-1 and hence linear rank. This is a necessary condition for
this replacement, not a general running-time lower bound.

The strict conditions matter. When n=q, A may have only the zero kernel and
the nonzero dependency need not exist. When q+1=d, exact preservation is
possible: an identity projection of the length-three repetition code has
q=2 and d=3. For Golay, q<=6 is covered by the strict bound; q=7 is not.

## Constructive witness and accounting

`syndrome_projection.py` first computes q by binary Gaussian elimination on
the supplied rows. It then eliminates the first q+1 columns, retaining a
binary mask of original column IDs with every basis vector. The first column
that reduces to zero returns its nonzero mask. Prior masks use only earlier
coordinates, so the new column's coefficient cannot cancel from that mask.
The builder checks the resulting syndrome and weight explicitly.

With m supplied rows, row-rank elimination uses O(m min(m,n)) operations on
n-bit integers. Prefix construction uses at most m(q+1) bit checks; column
elimination uses O(q^2) operations on m-bit vectors and q+1-bit masks. Thus
both construction and witness verification have polynomial bit complexity.
The producer records rank steps, prefix checks and column reductions. It does
not enumerate codewords or subsets to construct the dependency. The verifier
recomputes the projection and rank, checks the coordinate prefix and weight,
and independently evaluates both A w and H w.

Adding redundant rows, duplicating projected checks, or evaluating additional
sources leaves this conclusion unchanged if the final constraint matrix still
has actual rank q. Conversely, keeping several projections simultaneously
means applying the bound to the rank of their **stacked** constraint matrix.

## What this rules out, and what it leaves open

It rules out treating the minimum nonzero weight in ker(QH) as the exact
original distance uniformly on high-distance codes when q+1<d. Merely checking
the returned projected minimum against H will reject it; that rejection does
not supply the original optimum.

It does not rule out multistage procedures that retain original constraints,
add cuts, branch, intersect further projections, or otherwise exclude spurious
words before certifying an optimum. It also gives no rank-independent lower
bound for algorithms exploiting other structure. This syndrome projection is
a different operation from the earlier bounded-coordinate projection/LP audit.

## Limited affine extension

For a **consistent**, unrestricted affine system Ax=c of rank q, some solution
has weight at most q: choose q independent columns spanning the column space,
express c in that basis, and use those coefficients. Consequently, if an
original feasible affine system Hx=b has optimum D>q, replacing it by
QHx=Qb makes every projected affine minimum spurious. This statement allows
the zero solution when Qb=0; it must not be silently applied to a problem
that separately excludes zero. If the projected affine system is inconsistent,
the original is infeasible as well and no finite-solution bound applies.

## Finite checks and Golay evidence

Six tests passed in 0.724 seconds. They include all **5,058 binary matrices**
with at most three rows and four columns, and all **7,466 combinations** of
small H matrices and projectors (n<=3, H has <=2 rows, Q has <=3 rows).
Independent small enumeration checks ranks, projection products, kernel
membership and every strict-distance claim. Additional tests cover consistent
affine systems, malformed certificates, redundant checks, rank(Q)>rank(QH),
and both boundary conditions above.

`RESULTS.json` contains **20 seeded Golay projectors**, cycling through actual
ranks zero to six. Each has eight additional redundant rows, making the row
count visibly different from rank. Every explicit witness satisfies QHw=0
and Hw!=0. Their observed weights are between one and four; the theorem only
requires the upper bound q+1<=7. No exact projected distance is claimed from
these witnesses, and twenty samples are not presented as exhaustive coverage
of all projectors: the universal claim comes from the proof.

The original 24-coordinate check matrix is the existing Golay construction in
`../all_dual_lp_barrier.py`. Its original verifier was rerun successfully.
This audit also separately checked rank twelve, self-orthogonality and the
complete 4,096-word row space. Because that space is self-dual, it is exactly
ker(H), with weight distribution

    weight:  0    8     12    16   24
    count:   1   759   2576   759   1

Thus its distance eight is verified, not assumed from its name. The JSON saves
the original rows, all projectors and witnesses, source/test SHA-256 hashes,
and hashes of the existing Golay source, theorem and prior projection result.
The artifact is approximately 26 KB. Only this new directory was modified.

Reproduce from `overnight_research_2026_10_18/projection_limits`:

    python -m unittest -v test_syndrome_projection
    python syndrome_projection.py
