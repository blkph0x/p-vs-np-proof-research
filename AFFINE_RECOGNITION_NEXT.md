# Next experiment: bounded integration and cheap rejection evidence

P versus NP is unresolved. This brief follows the verified clause-grouping
and standalone recognition work. It proposes a separate experiment; it is
not an implemented solver improvement or a polynomial SAT theorem.

## Preserve the completed comparisons

Keep the same complete 58 earlier original requests and the same 22 stress
requests. The fixed baselines are 54/58 exact for weighted and compressed
methods, and respectively 2/22, 11/22 and 19/22 for weighted, unplanned
compression and checked grouping. Preserve every UNKNOWN and any regression.
The four earlier counting failures already have short SAT decision evidence.
Counting coverage and decision coverage must remain distinct.

The standalone complete recognizer is polynomial in the explicit signed sum,
but may still be expensive at every solver node. Its norm contractions and
failed discoveries must be charged before claiming any practical gain.

## Cheap certificates that a function is not one piece

Every nonzero piece has an affine support and constant nonzero magnitude on
that support. Its sign is a quadratic function there. These properties give
small rejection witnesses without reconstructing the entire support:

1. Two points with nonzero, unequal absolute values exclude one piece.
2. Nonzero support points a_1,...,a_t and a zero-valued point z equal to their
   XOR for odd t exclude affine support. Any affine set is closed under odd
   affine combinations over GF(2). A supplied selector with odd parity and
   the stated XOR suffices; there is no need to enumerate the whole span.
3. If all eight points of a three-direction affine cube have nonzero values
   of one common magnitude, the product of their signs must be +1 for a
   quadratic phase. A product of -1 excludes one piece: every monomial of
   degree at most two occurs an even number of times in the third difference.
   Repeated cube vertices do not produce a spurious negative product.

All evaluations must read the full original explicit sum, and the certificate
must bind exact coordinates and values. Finding one witness proves only this
representation rejection. Failing to find a witness proves nothing; use the
complete norm-based recognizer or return UNKNOWN on resource exhaustion.
The proposed sample schedule and every failed sample must be charged.

These cheap checks can precede a root norm, unlike the current standalone
implementation's uniform initial norm query. They may reduce the cost of
frequent negative calls. The identities above justify the rejection conditions,
but their discovery benefit has not been measured. They do not replace a
positive equality certificate, and they do not decide arbitrary SAT.

## The supplied whole sum is not the same as its useful subgroups

The saved [five-to-two control](AFFINE_RECOGNITION_LIMITS.json) has four
disjoint affine lines on the first three bits, with point sets
{0,1}, {4,6}, {3,7}, {2,5}, plus one additional pin at 000. All coefficients
are +1, and extra coordinates are free. The four lines partition the cube,
so the function is 1+1[x_0=x_1=x_2=0].

The current pair rules leave all five pieces. A whole-sum one-piece recognizer
must also reject: the function is everywhere nonzero but has magnitudes one
and two. Two pieces suffice by the displayed identity, and one is impossible,
so its exact minimum is two. Direct dependency checks and exact squared-norm
certificates retain this example at widths 3, 16 and 64.

Thus complete one-piece recognition does not find compressible proper subsets
or minimize the number of pieces. Trying all subsets is exponential. A later
candidate-group heuristic needs full discovery accounting, and its failed
groups must remain visible. No general small-group coverage theorem is known
from this example.

## A controlled integration

Use a separate adapter, preserving the frozen baseline. Start with an optional
recognition attempt after the existing greedy compressor successfully produces
an explicit sum. A verified one-piece equality can replace that sum. A verified
rejection retains it unchanged. A locally capped optional attempt can also
retain the already valid sum, provided its consumed work is charged and the
overall budget is not exhausted. Exhausting the overall budget remains UNKNOWN.

Choose and record deterministic size/coordinate triggers and a per-attempt
budget before the benchmark. Do not silently skip expensive failures or tune
thresholds against expected answers. Keep source factor ownership, marginal
proofs and complete original-clause binding unchanged. The checker must derive
the recognizer input from the already verified node output, not trust a supplied
replacement input list. Every accepted replacement needs fresh norm replay.

This first integration cannot rescue a node where the mandatory greedy stage
already fails before exposing an output. That limitation is intentional and
must be reported. Handling a retained-size overflow before rejection would
require a separate streaming design, including transient memory and proof
ownership; do not hide it inside the same experiment.

Report planning, greedy work, recognition attempts, rejected/limited attempts,
pair contractions, retained and transient pieces, coefficient bits and proof
replay separately. The optional recognizer may reduce later growth yet increase
total cost. Only the measured original-input comparison can establish the
outcome for this implementation.
