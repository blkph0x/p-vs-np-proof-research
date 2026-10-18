# Capacity of sums of real affine quadratic pieces

This is a representation bound for **arbitrary Boolean truth functions** on n
boundary bits. It does not prove a lower bound for polynomial-size CNF, for a
particular SAT algorithm, or for all polynomial algorithms. It is not a resolution
of P versus NP. Its purpose is to delimit a proposed universal boundary-compression
claim before confusing it with the restricted formulas of interest. No novelty
claim is made.

## Exact number of directions

An atom is the nonzero vector 1_A(x)(-1)^q(x), where A is a nonempty affine
subspace of GF(2)^n and q restricts to a Boolean polynomial of degree at most two.
An arbitrary real coefficient absorbs the atom's overall sign. Normalize each
direction to have value +1 at a fixed first point of its support.

For support dimension d, the number of linear d-subspaces is the binary Gaussian
binomial G(n,d), and each has 2^(n-d) affine cosets. On each support there are
2^[d(d+1)/2] quadratic phases modulo constants: d linear and d(d-1)/2 quadratic
coefficients in independent free coordinates. Uniqueness of Boolean multilinear
polynomials makes these directions distinct. Therefore the exact dictionary size is

    D_n = sum_{d=0}^n G(n,d) 2^[n-d+d(d+1)/2]
        = 2^n product_{i=0}^{n-1} (1+2^i).

For completeness, the subspace recurrence is
G(n,d)=G(n-1,d)+2^(n-d)G(n-1,d-1). Subspaces inside a fixed hyperplane give the
first term. Otherwise choose the (d-1)-dimensional intersection and one outside
vector modulo that intersection, giving 2^(n-d) choices. Let
S_n=sum_d G(n,d)2^[d(d-1)/2]. Substitution of the recurrence gives
S_n=(1+2^(n-1))S_(n-1), with S_0=1, proving the product identity.

## Arbitrary coefficients do not evade the counting bound

Let N=2^n. A real subspace W of R^N of dimension r contains at most 2^r Boolean
vectors. Choose r coordinate evaluations whose rows form an invertible minor of
a basis matrix for W. Projection onto those coordinates is injective on W; each
Boolean vector projects into {0,1}^r. This proof permits arbitrary real
coefficients, with no rationality or coefficient-bit restriction.

Every sum of at most K atoms lies in a span of at most K dictionary directions.
Hence at most sum_{j=0}^{min(K,D_n)} binom(D_n,j)2^j Boolean functions have such
a representation. A convenient looser bound pads an ordered K-tuple by a zero
direction: the number is at most [2(D_n+1)]^K. Let

    B_n = 1 + ceil(log2(D_n+1)).

There are 2^N Boolean functions in total. If K B_n < N, some Boolean function
needs more than K pieces. In particular, some require at least

    floor((2^n-1)/B_n)+1

pieces. Since log2 D_n=O(n^2), this is Omega(2^n/n^2). All functions can also be
written using at most 2^n singleton pins, so the statement concerns the size of
this particular representation language, not the existence of a representation.

## Scope that must accompany this bound

Counting does not exhibit an efficiently described sequence of hard functions.
A function identified only by its full truth table already has 2^n input bits;
the bound is not superpolynomial in that explicit input length. Although every
Boolean function can be written as a CNF by excluding each false assignment,
that CNF may also be exponentially large in n. Nothing here proves the same
lower bound for polynomial-size original CNFs, for the intermediate messages
of every possible decomposition plan, or for algorithms using other languages.
Evaluation of a supplied polynomial-size sum remains tractable by the previous
affine marginalization theorem. Discovery and representation size are separate.

## Finite checks

An independent exponential oracle enumerates all nonempty support subsets
through n=4, tests translation closure, and evaluates all ambient quadratic
phases. It obtains D_0..D_4 = 1,4,24,240,4320. A separate two-coordinate determinant
oracle enumerates Boolean vertices of every pair span through n=3, confirming
the four-vertex bound and full two-piece coverage of those small truth functions.
These finite checks supplement the proofs above. They do not replace the all-size
arguments or supply a succinct hard family.
