# Exact coefficient complexity barrier

The compact generating products used by the packed matching route do not make
the target coefficient easy to isolate in general. The source-bound theorem in
`COEFFICIENT_COMPLEXITY_THEOREM.md` gives a parsimonious reduction from X3C to
the coefficient of a product of binomials with binary exponents. Its restricted
instances have the form `prod_i (1+z**e_i)`, with every `e_i` the sum of three
base powers.

The independent replay checks every family of the complete `2x2x2` tripartite
universe (256 families and 6,561 selections), 1,351 small general families,
and 400 seeded additional families. It recomputes the answer from base-digit
coverage rather than from encoded integer exponents. All checks pass and the
source hash is recorded in `COEFFICIENT_COMPLEXITY_REVIEW.json`.

This closes the proposed “short product, then one exact coefficient query”
shortcut unless that query itself yields a polynomial algorithm for an
NP-complete problem. It leaves other representations, promises, approximation,
and direct SAT algorithms open; it is not a proof of P!=NP.

