# Recognizing one signed quadratic piece on an affine partition

This standalone experiment recognizes a supplied collection, not an optimal
subcollection of a larger sum. It is not integrated into the frozen DAG adapter.
The result is polynomial in the explicit collection and coordinate description.
It neither bounds how many pieces a SAT computation generates nor establishes
general SAT tractability. No novelty claim is made.

## Exact recognition theorem

Let the retained Boolean coordinates be an ordered list I. For each nonzero
input piece write f_i(x)=c_i 1[A_i](-1)^q_i(x), where A_i is a nonempty affine
space over GF(2), q_i is a Boolean quadratic polynomial, and c_i is nonzero
rational. Verified zero pieces can be ignored arithmetically, but remain in the
external source binding. Assume all |c_i| have the same value c>0 and the A_i
are pairwise disjoint. Let H be their affine hull.

The union of the A_i equals H exactly when

    sum_i 2^dim(A_i) = 2^dim(H).

Every A_i is contained in H by construction. Disjointness makes the left side
the cardinality of the union, so equality of the two finite cardinalities proves
coverage. Neither cardinality alone nor hull equality alone proves coverage.

Suppose this partition condition holds. Choose an affine bijection from
GF(2)^r onto H. The sum is one affine quadratic piece if and only if there is a
quadratic q on those r free coordinates whose restriction to every A_i is

    q_i + epsilon_i,  where epsilon_i = 1[c_i<0].

Indeed, the supports are disjoint and cover H, so the only possible output
support is H and its nonzero magnitude must be c. The displayed equations
then express exact equality of its signs. Conversely such a q constructs the
single piece c 1[H](-1)^q. The phase is unique as a Boolean function on H;
uniqueness of multilinear ANF makes its quadratic coefficients unique too.
The constant phase is absorbed into the sign of the output scalar.

## Constructive polynomial algorithm

Canonical support rows give an anchor a_i and injective direction basis U_i for
each input. Start with one anchor a_0. H has anchor a_0 and direction space
spanned by all columns of U_i and every a_i+a_0. Gaussian elimination and an
orthogonal-complement calculation produce canonical equations for H.

Each pairwise support intersection is solved by combining its equations. An
inconsistent system produces a subset of those original rows whose XOR is
0=1. This is a short, independently checkable disjointness witness. If any pair
intersects, the narrow recognizer returns UNSUPPORTED. If cardinalities do not
fill H, it also returns UNSUPPORTED.

Let t be H's r canonical free coordinates. An unknown quadratic ANF has
D=1+r+binom(r,2) coefficients. Each A_i parametrization gives an affine map
t=L_i s+a_i in its own free coordinates s. Substitution of an unknown quadratic
into this affine map has degree at most two, and every resulting coefficient
is linear in the D unknown coefficients. Equate its constant, linear and
quadratic coefficients with those of q_i+epsilon_i. Solving this GF(2) linear
system therefore decides the exact phase compatibility condition.

No truth table on H is expanded. The implementation streams coefficient
equations into a binary row basis instead of retaining the complete constraint
matrix. Coverage ensures the homogeneous restriction map has trivial kernel:
a quadratic vanishing on every A_i vanishes everywhere on H. Thus a consistent
fit has rank D and a unique solution. An inconsistent fit returns UNSUPPORTED.

If k is the number of nonzero pieces and m=|I|, pairwise support checks cost
polynomially many operations in k,m and the support rows. There are O(m^2)
unknown phase coefficients and at most O(km^2) coefficient equations. Expanding
each restricted monomial and Gaussian elimination are polynomial in those
explicit sizes; no claim of a small constant or an optimal exponent is made.
Bit masks have polynomial lengths, and rational arithmetic is only exact
normalization, comparison and sign handling. Input rational bit lengths are
explicitly capped. Cardinalities have at most m+1 bits.

The counters charge support-row operations, pair checks, polynomial products,
fit elimination and phase samples. They are operation counters, not complete
bit-operation or wall-clock accounting. Explicit traversal, hashing, Python
objects, parameter construction and bitwise-operation bit costs remain
additional polynomial representation costs. Individual row counts, pieces,
coordinates, phase terms, unknown coefficients and work also have explicit caps.
The phase fitter checks D against the unknown-coefficient cap before constructing
its quadratic monomial list. This allocation preflight preserves the existing
operation-counter convention; it does not claim that setup is metered bit by bit.

## A checker that does not rerun the fit

`verify_partition` binds every external input, including order and zero pieces,
by a typed binary hash. It validates the canonical descriptors and checks:

1. Every required pair has a valid original-row XOR witness for 0=1.
2. Support dimensions and exact cardinality sum match the proposed H.
3. H contains every original anchor and direction. A separate highest-bit rank
   computation on the original direction generators gives exactly dim(H),
   proving that H is their affine hull.
4. The output has the common magnitude, and its sign agrees with each original
   input everywhere on that input support.

The final check uses a method different from the producer's coefficient fit.
On an input parametrization x=a+Us of dimension d, evaluate the phase difference
at s=0, each unit vector e_i, and each e_i+e_j. There are 1+d+binom(d,2) such
points. A polynomial of degree at most two is determined by those values:
its constant is the zero value, its linear coefficients are single-point
differences, and its quadratic coefficients are the corresponding four-point
differences. Testing the required constant effective sign at these points
therefore proves it everywhere. This is not arbitrary sampling and does not
assume a general Boolean function is determined by a few values.

The coefficient-fitting code is not called by the checker. Separate tests also
use the frozen block-support reference to evaluate the exact squared norm of
inputs minus output. All three methods preserve the original coordinate and
coefficient conventions. The tests are executable evidence, not a claim of a
machine-checked formal proof.

## Status and scope

`recognize(n, retained, messages, **caps)` returns EXACT with one canonical
message and a certificate on recognition. An empty/all-zero list returns the
canonical zero with complete source binding. `verify_partition` returns VERIFIED
only after the checks above. A producer or checker cap yields UNKNOWN with no
message claim. Invalid input or producer caps raise ValueError; malformed proof
or external input to the checker gives INVALID (invalid cap configuration is a
caller error and raises ValueError).

UNSUPPORTED means this narrow test failed: overlapping supports, a gap in H,
unequal magnitudes, or incompatible quadratic phases. It returns no message or
certificate. It is not a general proof that the original sum cannot be one
piece: overlapping pieces can cancel, and unequal inputs can combine in other
ways. Only the theorem's disjoint equal-magnitude partition conditions give the
complete phase-recognition statement. Subgroup selection, rewrite planning and
group-size growth remain separate questions.

The four-line greedy obstruction is a positive control. Lines with directions
1,2,4,7 partition GF(2)^3, and their common constant phase is fitted at once, so
the new group recognizer returns one constant piece. This improvement on that
explicit representation does not imply that every hard case admits such a
partition or that finding useful groups is polynomial.

## Reproducible evidence

Run `python -m unittest discover -v` and `python run_experiments.py` here. The
saved originals include every one of the 912 affine set partitions of GF(2)^3,
all 256 three-bit singleton sign tables (128 quadratic / 128 cubic-incompatible),
160 seeded signed quadratic partitions, and named wide controls through 128
retained coordinates. The controls include mixed support dimensions, shifted
hulls, sparse/permuted IDs, zero pieces, rational signs, all specified rejection
conditions, resource caps and rehashed semantic certificate mutations. Saved
results contain source/dependency hashes and independently replayed norms.
