# An explicit exponentially ill-conditioned affine dictionary

This is a limitation of a possible proof step, not a SAT lower bound. P versus
NP remains unresolved. No novelty claim is made.

For n >= 1, let V be the full binary n-cube. For j=0,...,n-1 let H_j contain
the words whose first j coordinates are zero and whose coordinate j is one;
later coordinates are free. The H_j are disjoint affine supports of size
2^(n-j-1). Their union is V minus its zero word. Consequently the exact identity

    1[{0}] = 1[V] - sum_j 1[H_j]

uses n+1 affine pieces with original coefficients +1 and -1. It is a literal
partition identity at every n, not a numerical approximation. At zero only
the full-cube term survives; every nonzero word belongs to its unique first-one
shell and cancels. The indicators are linearly independent: evaluation at zero
forces the full-cube coefficient to zero in any dependence, and evaluation in
each shell then forces that shell coefficient to zero. Each support has an
explicit polynomial-size linear description.

Normalize the full-cube vector to v=1[V]/sqrt(2^n) and each shell to
w_j=1[H_j]/sqrt(2^(n-j-1)). The w_j are orthonormal. Their overlaps with v are
a_j=2^(-(j+1)/2), with sum_j a_j^2=1-2^(-n). Thus the normalized Gram matrix is

    G = [[1, a^T], [a, I_n]].

The n-1 directions perpendicular to a have eigenvalue one. On the remaining
two-dimensional space the matrix is [[1, ||a||], [||a||, 1]]. Its other
eigenvalues are 1 +/- sqrt(1-2^(-n)). In particular

    2^(-(n+1)) <= lambda_min(G) <= 2^(-n),
    det(G) = 2^(-n).

The first inequality follows by rationalizing
lambda_min=2^(-n)/(1+sqrt(1-2^(-n))); it requires no floating-point calculation.
The condition number lambda_max/lambda_min lies between 2^n and 2^(n+2).

For the unit target 1[{0}], the normalized coefficient vector is
alpha=(sqrt(2^n), -sqrt(|H_0|), ..., -sqrt(|H_(n-1)|)). Therefore
||alpha||_2^2=2^(n+1)-1 while alpha^T G alpha=1. This is substantial cancellation
in normalized coordinates, although every original rational coefficient has
constant bit length. Exponentially small eigenvalues do not by themselves
imply exponentially many bits or pieces.

The target itself has a one-piece representation. This example therefore
disproves a universal polynomial lower bound for the smallest eigenvalue of
every linearly independent affine dictionary. It does **not** disprove a
conditioning bound limited to minimum-size representations of a particular
target, and it does not supply such a bound. Inferring an exponential rank
lower bound merely from small overlap with each atom would require an
additional justified control on cancellation.

The adjacent script saves complete original support equations, exact truth
checks through 12 bits, an independent rational determinant calculation
through 24 bits, and symbolic numerical identities at widths 32,64,128,256.
Wide rows verify the formulas and explicit support descriptions; they are not
wide truth-table enumeration. The all-size argument is the partition and
two-dimensional spectral proof above. It has not been formalized in a proof
assistant.
