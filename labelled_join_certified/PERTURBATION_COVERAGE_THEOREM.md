# Coverage bound for dense-U perturbations

Consider descriptions on n labelled coordinates of the form

    H = B + U V over GF(2),

where B has R displayed rows and every B column has support at most two, U is
R-by-p, and V is p-by-n. For each coordinate, B has

    L(R) = 1 + R + binomial(R,2)

possible columns. U has 2^(rp) possible matrices and V has 2^(pn), so the
number of descriptions is at most

    L(R)^n 2^(p(R+n)).

Different descriptions can produce the same matrix or row space, so this is an
upper bound on the number of representable row spaces for a fixed R. It already
allows dense U and dense V. If redundant displayed rows are allowed, sum this
bound over R=0,...,n; the resulting sum is still 2^(O(n log n)) for
p=O(log n). An invertible row change does not create a new row space, so
allowing arbitrary row bases does not require multiplying the bound by a GL
factor.

There are at least 2^(r(n-r)) distinct r-dimensional row spaces: every binary
r-by-(n-r) matrix M gives the systematic row space of [I_r | M], and two such
spaces have different projections onto the first r coordinates. Hence, even
after summing descriptions with every displayed row count R<=n, whenever

    2^(r(n-r)) > sum_R L(R)^n 2^(p(R+n)),

some rank-r row space has no B+UV representation at that p, in any row basis.
For r=floor(n/2) and p=O(log n), the lower-bound exponent is Theta(n^2),
while the description exponent is O(n log n). Thus dense U does not make a
universal logarithmic-label representation possible. The exact arithmetic
controls check the inequality at n=128,256,512 for representative logarithmic
budgets and record the largest excluded budgets (p = 9, 24 and 55 after
allowing every displayed row count). The threshold grows linearly in these
examples; the asymptotic comparison proves that every p=o(n) is eventually
excluded. The controls enumerate all small descriptions used in the finite
test. These thresholds mark where this counting obstruction stops; they are
not sufficiency results for universal coverage.

This is a limitation of one representation language. It is not a lower bound
for arbitrary SAT algorithms, nonlinear encodings, or objective-changing maps,
and it does not prove P != NP.
