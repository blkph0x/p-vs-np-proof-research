# Independent equality certificates and compression review

The implemented compressor's four rules (coefficient addition plus three
support/phase identities) are sound on canonical real affine quadratic pieces.
The independent checks here do not discover or reproduce those rules. They
verify their pointwise consequences by another exact algorithm. No novelty,
optimal compression, polynomial general-CNF bound, or P-versus-NP claim follows.

## A generic squared-norm certificate

Let a compact piece on retained bits y be

    f_i(y) = c_i 1[A_i y=b_i] (-1)^q_i(y),

where c_i is rational and q_i is a Boolean quadratic polynomial. To compare two
explicit sums, append the negatives of the proposed output pieces to the input
list. Remove only verified zero pieces, obtaining h=sum_(i=1)^K f_i. Compute

    ||h||^2 = sum_y h(y)^2
            = sum_i sum_y f_i(y)^2 + 2 sum_(i<j) sum_y f_i(y)f_j(y).

Each product is another affine quadratic piece: stack support equations, XOR
phases, and multiply rational coefficients. The frozen, independent block-support
reference computes and certificate-checks each closed sum without a boundary
truth table. The resulting exact rational norm is zero if and only if h(y)=0
for every Boolean y. Individual pair contributions may be negative, but the
completed expression is the sum of real squares, hence nonnegative. This is why
cancellation in the expanded calculation does not undermine the zero test.

There are exactly K(K+1)/2 closed contractions after zero removal. A nonzero
two-input/one-output rewrite needs six. The reference verifier is externally
bound to each derived product request; the norm checker requires the complete
ordered pair coverage and recalculates the rational total. It evaluates the
checked closed output's scalar AND phase: an equivalent noncanonical constant
phase is not incorrectly read as its bare scalar. A valid positive norm certifies
inequality; INVALID or UNKNOWN certifies neither equality nor inequality.

This gives a polynomial checker in the explicit number K of supplied pieces,
coordinates, support rows, phase terms and coefficient bit lengths, using the
polynomial block primitive. If every input numerator/denominator has at most B
bits and there are m retained bits, a pair value has O(2B+m) bits. A simple
common-denominator bound for the sum of t=K(K+1)/2 terms is O(tB+m+log t) bits,
so intermediate exact rational arithmetic also has polynomial bit complexity.
Actual scalar bit lengths and reference operation counts are recorded. The
implemented review checker caps products, cumulative reference-checker work,
and scalar bits; individual reference calls also have their own cap. Input
traversal, hashing, rational operations and Python object handling are additional
explicit-representation costs, not hidden in those named operation counters.
Neither this checker nor the identities supply a bound on discovery effort or K.

## Rule-specific adversaries

The controls include parallel unions, opposite rational signs, same-support
phase splitting, nested subtraction whose phases agree only after restriction,
and effective cancellation when ambient coefficient signs look equal. Invalid
proposed outputs cover nonparallel supports, unequal magnitudes, incompatible
quadratic differences, a nonaffine quadratic zero set, nested codimension two,
nonconstant restricted difference, and the wrong effective sign. Each is tested
by direct small original assignments and by the block norm; forged producer
certificates are separately rejected by the production checker.

The independent source review confirms that canonical RREF supports and phases
are needed for the common-coordinate comparisons. For nesting, the check uses
augmented rowspace containment, rank increase exactly one, and phase restriction
on the inner support. Streaming IDs consume two distinct live inputs once and
create a fresh ID, and every external arrival and final survivor is bound.
False failed-pair observations cannot change a value: they are no-op trace
entries, not certificates that no mathematical rewrite is possible. Producer
discovery cost is measured separately from the checker's replay cost.

## Greedy reduction is not confluent in final size

Take the eight coefficient-one singleton indicators on GF(2)^3. Pair

    (0,1), (4,6), (3,7), (2,5).

Their four affine lines have respective directions 1,2,4,7. They are pairwise
disjoint and nonparallel, hence neither identical, same-support, nested, nor
parallel-coset rules apply to any remaining pair. This schedule is stuck at
four pieces. Instead pair (0,1),(2,3),(4,5),(6,7), then merge parallel lines to
two parallel planes, and merge those planes. The result is the single constant
one piece. Every rewrite is valid and both final sums are identically one.

The actual first-match streaming producer reproduces final sizes four and one
for input orders [0,1,4,6,3,7,2,5] and [0,1,2,3,4,5,6,7], respectively. Both
explicit schedules and actual certificates are saved. This is a planning
limitation of the pairwise greedy strategy. It is not an intrinsic lower bound:
the good schedule is already a counterexample to such an interpretation.

## Adapter and evidence scope

The new adapter preserves original factor occurrences, their disjoint structural
ownership, every child cross-product before compression, original active and
retained universes, and final free-variable multiplicity. Its checker reconstructs
the full original list of marginal messages and consumes freshly checked
compression outputs. The review compares every sampled intermediate message
directly with its original factor subproduct, not merely with another solver's
final answer. Signed native contractions remain signed contractions; zero does
not imply an original CNF was unsatisfiable unless the factors are its original
nonnegative Boolean indicators.

Aggregate budgets are verified across structural nodes. Forged producer stats
do not bypass the checker's own accounting. Complete generated input lists and
certificates remain materialized; the retained piece cap is not a total memory
bound. Frozen production and dependency hashes, exact original review inputs,
saved proof replays, seeds and all counted checks are in RESULTS.json.

Run `python -m unittest discover -v` and `python run_review.py` from this folder.
The latter writes only the owned review artifacts. Bounded tests supplement the
mathematical argument; neither is represented as a machine-checked formal proof.
