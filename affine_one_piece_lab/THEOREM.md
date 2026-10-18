# Complete one-piece recognition for an explicit real affine sum

For an explicit list f=sum_i c_i 1[A_i](-1)^q_i with rational c_i, affine Boolean
supports A_i and quadratic phases q_i, this algorithm decides whether f is zero
or one real affine-supported quadratic-sign piece, and constructs it when so.
The unbounded mathematical algorithm is polynomial in the explicit coordinate,
support, phase, piece-count and coefficient-bit descriptions. The executable is
bounded: exhausting a cap returns UNKNOWN without a message or certificate.

This is a separate experiment, not integrated into any frozen SAT/DAG solver.
It does not decide minimum multi-piece representation, find useful subsets, or
bound the number of pieces generated from a succinct product. No novelty or
P-versus-NP claim is made. The derivation in
`../AFFINE_ONE_PIECE_RECOGNITION_DESIGN.md` was independently reviewed before
implementation; this document describes the actual optimization and certificates.

## Restricted squared norms and exact arithmetic

For an affine restriction P, let N(P)=sum_(x in P) f(x)^2. Expanding gives one
diagonal contraction per nonzero input and a doubled contraction per unordered
distinct pair. Each product has stacked support equations, XORed phases and the
exact product coefficient. The frozen independent block marginalizer sums that
compact affine quadratic function. Its separate checker verifies the certificate
against the externally derived original operands and restrictions.

Individual pair contributions can be negative. Their completed rational total
is nonnegative because it equals a sum of real squares. N(P)=0 is equivalent to
f vanishing at every point of P. Negative completed norms are errors, not useful
answers. No floating-point comparison is used. The actual checked closed scalar
and constant phase are evaluated together, permitting equivalent noncanonical
closed block messages without a scalar-only sign bug.

All original occurrences remain bound, including duplicate and zero pieces.
Zero operands can be omitted from pair enumeration only after canonical input
validation. A difference query appends the negative proposed candidate under
its own index and includes every diagonal and doubled off-diagonal pair. Typed
binary hashes bind original order, coordinates, support, phase and coefficients.

## Complete support-hull discovery

If N(all)=0, return the canonical zero. Otherwise find a nonzero support point
by prefix pinning: query the zero half, select it if its norm is positive, and
otherwise select the one half. A positive current restriction is partitioned
by the two halves, so the selected half remains positive. The implementation
searches only the canonical free coordinates of the affine hull of all input
supports; every possible nonzero point is already contained there. The remaining
coordinates are determined, and the resulting point is directly evaluated.

Maintain H as the affine span of the nonzero points found so far. For each
independent equation L=b of H, query N(L=1-b). If positive, prefix search finds a
nonzero point outside H. Adding it strictly increases affine dimension. There
are at most m such increases on m retained coordinates. Restart the row scan
after an increase. At termination, every violated equation has zero norm, so
f vanishes outside H. Since actual nonzero points span H, it is exactly the
affine hull of supp(f). Hull scans and prefix searches use O(m^2) norm queries.

The completed obstruction certificate retains independent nonzero support
points, canonical H and every final outside-half zero norm. The checker directly
evaluates the points, checks their independent span and containment, then checks
all outside norms. It need not rerun discovery, nor trust discovery counters.

## The only possible quadratic candidate

Parametrize H canonically as x=a+Bu with d free original coordinates. Its anchor
a need not be in supp(f), despite being in that support's hull. If f(a)=0 while
the original norm is positive, no nonzero one-piece representation is possible.

Otherwise set c=f(a). Evaluate f at u=e_i and u=e_i+e_j. Every magnitude must
equal |c|. A violation certifies nonmembership. With compatible magnitudes,
write f(e_i)/c=(-1)^s_i and f(e_i+e_j)/c=(-1)^s_ij. The only possible quadratic is

    q(u)=sum_i s_i u_i + sum_(i<j)(s_ij+s_i+s_j)u_i u_j.

Its constant term is zero because c carries the anchor's sign. This uniqueness
follows from the Boolean multilinear coefficients determined by samples of
coordinate weights zero, one and two. It holds in dimensions zero and one too.

Construct g=c 1[H](-1)^q and compute N_f-g(all). Zero proves equality. A positive
value proves that f is not one piece: any possible nonzero piece would have
support H, anchor coefficient c and precisely this sampled quadratic, so there
is no alternative candidate left. These are complete representation obstructions
for the stated real rational class, unlike a mere failure of a local rewrite.

## Safe positive-only optimization

Before full support discovery, the producer forms the affine hull of the INPUT
supports, samples a candidate there, and tries the full difference norm. A zero
difference immediately certifies a positive result. A zero anchor, magnitude
failure or positive difference on this enclosing hull is NEVER used to reject:
cancellation may make the true support hull smaller. Every failure falls back
to the complete support-discovery algorithm, or returns UNKNOWN if its budget
is exhausted. The failed attempt's work is fully charged.

This adds one polynomial candidate attempt and makes wide positive partitions
practical. The `1-pin` and canceled-wide-hull controls require fallback and verify
that the optimization cannot create a false UNSUPPORTED result.

## API, certificates and resource boundaries

`recognize(n, retained, messages, **caps)` accepts the established canonical
message schema. `verify_one_piece` (alias `verify`) takes the same external
original inputs and the result. EXACT has a canonical message and certificate.
UNSUPPORTED has no message but a checkable anchor, magnitude or final-phase
obstruction. UNKNOWN has neither a message nor certificate. An empty sum and
overlap cancellation can give EXACT zero. Invalid producer inputs/cap settings
raise ValueError; the checker rejects malformed proofs and external inputs as
INVALID, while invalid cap configuration is a caller error.

Zero and equality certificates need only the original norm and, for equality,
the candidate and difference norm. Positive equality alone proves the full
function, so support-discovery traces are not required in those certificates.
Negative certificates additionally bind the actual support hull and original
sample evaluations. Checkers consume independently checked block results and
recalculate values; producer statistics do not certify the computation.

Caps cover the explicit original dimension, piece/row/term counts, rational
bits, norm queries, every pair contraction, point evaluations, cumulative named
work and retained certificate products. A norm's product count is preflighted
before proof allocation; complete certificate size is checked separately.
Support helper and block work are added to the same outer work budget, including
failed fast candidates and unsuccessful discovery halves. Producer and checker
work differ because their algorithms differ. Proofs discarded during discovery
still count as generated pair contractions; the final certificate-product cap
does not claim to bound all Python bytes or total discovery work.

Sample points are generated lazily. Discovery hulls have at most m+1 witnesses.
The mathematical total is O(m^2 K^2) compact contractions, polynomially many
point/rank operations, and polynomial-size arithmetic. Let L bound the total
input rational bit description and D be the product of input denominators.
Point sums have denominators dividing D; norm and partial pair sums have
denominators dividing D^2. Their numerators have polynomial bit length in
L,m,log K, since each contraction sums at most 2^m signed terms. A sampled
candidate coefficient is itself a point sum. Thus unit-cost treatment of
arbitrarily large integers is not needed for the polynomial theorem.

The reported operation counters are not a literal bit-operation or wall-clock
bound. Input traversal, hashing, object allocation and bitwise operand lengths
carry their usual additional explicit-representation costs. Resource exhaustion
is not evidence of nonmembership.

## What remains outside this result

An explicit sum of K pieces may already have exponential K. Expanding a general
CNF product is not made polynomial by this recognizer. The squared norm of an
unexpanded Boolean CNF is its satisfying-assignment count; pretending such a
norm is supplied cheaply would assume the hard computation.

Even complete one-piece recognition does not solve two-piece or minimum-piece
decomposition. Four disjoint lines that partition GF(2)^3 plus an extra point
have value two at that point and one elsewhere. The whole sum is correctly
UNSUPPORTED as one piece although the four-line subset merges to one, leaving
an exact two-piece expression. No partial-subset search is performed here.

## Evidence and reproduction

Run `python -m unittest discover -v` and `python run_experiments.py` in this
folder. The evidence includes all 93 ternary truth tables through two bits,
all 256 three-bit sign tables, 120 seeded arbitrary signed sums, overlap and
zero cancellation, strict input-hull/actual-hull differences, a canonical-anchor
hole, cubic signs with final norm exactly 4, sparse/permuted coordinates, wide
32/128-coordinate controls, caps and rehashed source/norm/hull/sample mutations.
Original requests, complete proofs, independent bounded classifications and
source/dependency hashes are saved. Tests and source review supplement the
mathematical argument; they are not presented as a machine-checked formal proof.
