# Symbolic fused-suffix macro

**Status:** completed bounded rule with independent replay. It does not prove
P=NP or P!=NP.

The two remaining scale-scan UNKNOWN records were the final two nodes of the
fused resolution chain. Their left parent is the B clause after resolving a
prefix of positive representative units, and each right parent is the exact
Hall-plus-implication unit proof for the preceding group. A node with boundary
`r_k,...,r_{g-1}` therefore has the projected relation

`NOT r_k OR ... OR NOT r_{g-1}`.

The macro checks the serialized proof rather than trusting the derived clause:
it identifies the equal-width Hall family, checks the B clause, replays every
reachable resolution node, verifies each unit parent uses exactly one group's A
leaves, and verifies the chain reaches B. It records an extension argument: set
all variables in the resolved prefix groups to true. Any boundary assignment
satisfying the negative suffix then extends to a satisfying assignment of the
leaf formula, so the projection is exact. For the two audited boundaries the
candidates are a two-variable PB inequality (`sum <= 1`) and a negative unit.

On the 4,097-node, 256-group, width-eight proof this recovers both sub-DAG-cap
records with 4,065 and 4,081 reachable-node checks. A 23-point sweep over group
counts through 256 and widths through 16 matches the exact work formulas
`2*w*(groups-2)+1` and `2*w*(groups-1)+1`; no `2^local` assignment table is
constructed. The independent verifier rejects altered pivots, clauses, and
candidate bounds. A six-test suite covers the small proof, the scale case, the
parameter sweep, a near miss, and forged certificates.

Scope remains explicit: this recognizes one generated proof family and does not
provide a general-purpose way to discover arbitrary proof macros or residual
relations. The universal semantic-equivalence barrier still applies outside
such certified structure.

Artifacts:

- `symbolic_suffix_template.py` â€” producer and structural certificate;
- `verify_symbolic_suffix_template.py` â€” independent verifier;
- `test_symbolic_suffix_template.py` â€” five adversarial and scale tests;
- `SYMBOLIC_SUFFIX_TEMPLATE.json` â€” compact small-instance fixture;
- `SYMBOLIC_SUFFIX_TEMPLATE_REPORT.md` â€” this report.
