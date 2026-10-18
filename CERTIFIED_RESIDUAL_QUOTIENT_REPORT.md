# Certified residual-state quotienting

**Status:** sound incomplete classifier with replayable certificates. It does not
prove P=NP or P!=NP.

The preceding residual-equivalence reduction shows why exact future-state
minimization cannot be assumed polynomial. This experiment implements the safe
response rather than hiding that difficulty behind a heuristic. For two
residual CNFs it returns one of:

- `MERGED_SYNTACTIC` when normalized clause sets are identical;
- `MERGED_EXACT` when exhaustive truth-table comparison fits the assignment cap;
- `MERGED_PROOF` when both implications have explicit resolution certificates;
- `DISTINCT_WITNESS` when one assignment separates the residuals;
- `DISTINCT_EXACT` when bounded enumeration finds a separator;
- `UNKNOWN` when none of those certificates is available.

The proof certificate for an implication `H => K` contains one resolution
refutation for each clause of `K`: the premises are `H` plus the negated target
clause. The independent checker verifies every leaf, pivot, derived clause and
empty root for both directions. This is a standard sound certificate format;
the producer's small saturation builder is only a fixture generator, not a
claimed polynomial proof search algorithm.

The saved artifact demonstrates all six behaviors. It merges a redundant clause
by a five-obligation bidirectional proof, certifies distinct residuals from a
single witness, finds a bounded exact distinction, and returns `UNKNOWN` for an
eight-variable unsatisfiable pair when exhaustive work is capped at 16
assignments. A witness still certifies distinctness beyond that cap.

Six tests and an independent replay pass, including forged-certificate rejection. The result is a practical contract
for future frontier solvers: semantic merging is accepted only with a visible
certificate, while hard equivalence cases remain explicit `UNKNOWN` states.
This preserves soundness without claiming that certificate discovery is
polynomial on arbitrary inputs.

Artifacts:

- `certified_residual_quotient.py` — classifier and bounded certificate fixture builder;
- `verify_certified_residual_quotient.py` — independent resolution/case checker;
- `test_certified_residual_quotient.py` — behavior and cap tests;
- `CERTIFIED_RESIDUAL_QUOTIENT.json` — serialized cases and proof obligations.
