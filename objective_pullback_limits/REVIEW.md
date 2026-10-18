# Independent review of additive objective pullbacks

Reviewed on 2026-10-18. The theorem and its scope are correct. This review is
mathematical/code inspection with finite checks, not formal verification or
a novelty claim.

For a linear binary map, f(0)=0 fixes the additive constant and evaluations
at input unit vectors fix every possible unary coefficient. The exact pair
identity

    f(e_j)+f(e_k)-f(e_j+e_k)
      = 2 * sum_{i: T_ij=T_ik=1} a_i

then rules out all additive assignments whenever any positive-weight row
contains two entries. Nonnegativity is essential because it prevents other
overlapping outputs from cancelling that defect. Conversely, each row with
positive weight and at most one entry contributes to just one unary cost.
Zero rows, zero-weight rows, unused inputs, and zero input/output dimensions
are all covered. The resulting coefficients are nonnegative even when the
candidate representation is allowed signed unary coefficients.

The three nonzero test assignments suffice because f(0)=0 follows directly
from the supplied homogeneous linear map; it need not be separately trusted
as certificate data. The obstruction checker recomputes all three costs on
the externally supplied map and weights. The positive checker checks both
the row-support condition and each unary cost. Strict schemas, integer and
Boolean distinctions, dimension bounds, pair distinctness, and external
input binding were inspected. No false classification or acceptance of a
false additive certificate was found.

The stated exclusions are necessary and well separated. A constrained input
domain can remove the offending assignments. Signed output weights can
cancel identical XOR outputs. An affine offset can make complementary XOR
outputs sum to a constant even with positive weights. None of these controls
contradicts the all-input, nonnegative, purely linear theorem. Arbitrary
one-variable functions are also covered by the theorem's affine unary form,
since their values at zero can be absorbed into the constant.

One implementation edge case was found and reported: decimal JSON hashing
of valid large integer inputs triggers Python's default integer-to-string
limit. The requests `classify([1], 1, [1<<15000])` and
`classify([1<<15000], 15001, [1])` reproduced this failure despite satisfying
the documented input conditions and column budget. The producer owner
replaced that hash with length-prefixed binary integer encoding, without
changing the process-wide conversion guard. The repair was read and all
three large-integer regression cases were independently rerun successfully,
including an overlapping positive-cost output. This was a valid-input
handling defect, not a counterexample to the theorem or a false accepted
certificate.

After the fix, 300 additional seeded cases with up to six input and eight
output coordinates were compared against complete, independently evaluated
truth tables. Output weights included zero, ordinary small integers, and
2^15000. Every classification and verified certificate agreed. Every required
certificate-field deletion was rejected, as were Boolean constant/value
mutations. For each negative certificate its defect was also independently
checked against twice the positive weighted column overlap. No outstanding
correctness issue remains from this audit.

The classifier and verifier remain polynomial in the explicit dimensions
and integer bit lengths. The column cap specifically bounds unary-array
allocation; it is not a total time, output-row, or input-bit-length budget.
