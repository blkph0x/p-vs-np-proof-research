# RM(2,5) SOS-strengthened exact-dual closure

## Result

The SOS-strengthened RM(2,5) level-eight quotient is now closed exactly:

\[
  \operatorname{OPT}=7037/1095.
\]

The primal witness and the dual certificate have the same rational objective.
The dual replay checks all 2,174 reduced-cost inequalities over the rebuilt
27,926-row quotient, with minimum reduced cost zero. The production result is
therefore labelled `EXACT_OPTIMUM`.

## How the certificate was found

The first reconstruction used only the 719 rows that were nonzero in an
initial floating dual. Its objective matched the primal, but rational rounding
left 169 negative reduced costs. That candidate was correctly rejected.

The successful search solved the complete sparse dual LP over all 27,926
equality rows with an interior-point pass. The floating solution exposed
2,140 numerically active column inequalities. Those active rows have rank
1,890, exactly the number of nonzero dual rows plus the SOS multiplier in the
chosen sparse support. Selecting a full-rank active basis and multiplying the
SOS column by five gives an integer 1,890-by-1,890 system. FLINT solved that
system over the rationals. The resulting certificate has 1,889 nonzero
equality-dual rows and multiplier `35/876`.

The exact replay then verifies, independently of the floating solve:

1. every primal marginal equality;
2. the Boolean-square cut equality;
3. every dual reduced cost is nonnegative, with minimum `0`;
4. the dual objective is exactly `7037/1095`; and
5. the primal and dual bounds coincide, so the gap is `0`.

The pure-stdlib reviewer repeats the arithmetic from the saved quotient matrix,
while the production runner rebuilds the quotient from its source code. The
certificate also records the active basis indices used to obtain it.

## Interpretation

This proves the optimum of one finite, symmetry-quotiented SOS-strengthened
RM(2,5) relaxation. It does not provide a polynomial-time algorithm for
arbitrary SAT, a lower bound for all proof systems, or a resolution of P versus
NP. Any broader claim would require an all-input construction with a proven
complexity bound and a separate soundness proof.
