# Symbolic Hall-plus-implication unit template

**Status:** completed bounded structural macro experiment. No proof of P=NP or
P!=NP.

The generic projector needs to enumerate the boundary and local variables. For
the repeated fragment

    (r OR x_1 OR ... OR x_k)
    AND (r OR NOT x_1) AND ... AND (r OR NOT x_k),

that projection has one boundary variable and `k` local variables. With local
cap six, the width-eight instance becomes `UNKNOWN` even though the relation is
`r = true` from the clause structure.

This experiment adds a narrowly scoped symbolic recognizer. It checks the exact
Hall-plus-implication pattern and emits a resolution certificate for the
unsatisfiable fragment plus `NOT r`. Resolving the Hall clause successively with
each implication derives `(r)`, then one final resolution derives the empty
clause. A satisfying witness for `r=true` completes the projected relation
certificate.

The serialized sweep covers widths 2 through 256. The certificate has
`2*(width-1)+3` nodes, so width 256 uses 513 nodes and linear discovery work,
while exhaustive projection would inspect `2^256` assignments. The recognizer
rejects a one-clause near miss and a forged terminal resolution clause.

This is a useful escape for a known structural family, not a universal macro
discovery algorithm. An arbitrary residual can still require semantic
equivalence testing; the coNP-hard residual barrier and explicit `UNKNOWN`
contract remain in force.

Artifacts:

- `symbolic_unit_template.py` — recognizer and certificate producer;
- `verify_symbolic_unit_template.py` — independent pattern and proof replay;
- `test_symbolic_unit_template.py` — cap, size, near-miss, and forgery tests;
- `SYMBOLIC_UNIT_TEMPLATE.json` — widths, certificates, and adversarial controls.
