# Independent review of the common-basis obstruction

Reviewed by the root agent, independently of the lab author. No gap was found
in the stated complex-field, common invertible two-by-two basis theorem.

The review checked the complete normal-form argument: invertibility excludes
zero entries in the even-parity EQ3 branch; the two equations force the ratio's
sixth power to one; the determinant removes its negative-cube branch. Nonzero
diagonal scalings preserve zeros on both sides, while a column swap covers
every odd-parity branch. Each clause then retains nonzero entries of opposite
parities. Thus the finite polynomial identities support a quantified algebraic
proof, rather than an extrapolation from a rational search grid.

The saved `independent_review.py` uses SymPy Kronecker matrices, independently
of the lab's sparse tensor-polynomial generator, to check all 40 original
branch equations and all 12 normal-form entries. It multiplies the four
Bezout identities symbolically. A separate smallest-vertex matching recursion
checks all 40 entries of the five explicit graph controls, against both saved
tables and independent matrix multiplication. Three altered certificates are
rejected. All four author-source hashes remained unchanged and match RESULTS.
`INDEPENDENT_REVIEW.json` records these results and hashes.

The review also checked the product-type certificate. The two transformed
EQ3 zero equations were split by the 16 possible zero/nonzero masks; after
excluding the all-nonzero determinant contradiction, only masks 0110 and 1001
remain, corresponding to anti-diagonal and diagonal bases. Independent exact
representatives preserve three nonzero OR3 and SLACK3 weight classes in both cases.

The result excludes precisely the two common-basis gate pairs in the theorem
for matchgate parity and the common product-type target in the additional case
split. It neither gives a lower bound for arbitrary SAT algorithms nor rules
out different encodings or other tractable tensor classes. The review is not a
proof-assistant formalization. No code correction was required.
