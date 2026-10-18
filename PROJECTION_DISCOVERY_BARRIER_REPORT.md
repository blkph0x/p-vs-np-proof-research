# Exact projection-discovery barrier

**Status:** completed source-bound barrier with independent finite replay. It
does not prove P=NP or P!=NP.

For arbitrary CNF `G(y)`, lift variables by one bit and form

`F(z,y) = G(y) AND NOT z`.

Projecting `y` away leaves a one-bit relation. If `G` is satisfiable, the
relation is `[1,0]`, the negative unit `z=0`; if `G` is unsatisfiable, the
relation is `[0,0]`, the empty relation. Therefore an exact universal
projection classifier would decide SAT by checking whether its one-bit output
is empty, and would decide UNSAT by checking the opposite case. The boundary
width stays one while the hidden suffix is arbitrary.

This sharpens the existing future-equivalence barrier. Equivalence of the two
residuals encodes UNSAT; exact existential projection already encodes SAT. A
structural macro can therefore be polynomial only when its input proof family
supplies additional restrictions or a replayable certificate. The generic
projector must retain its cap and `UNKNOWN` behavior outside those restrictions.

The finite fixture exhausts all 256 subsets of the eight non-tautological
clauses over two variables. It finds 95 satisfiable and 161 unsatisfiable
instances, with exactly the same split between the `UNIT_Z_FALSE` and `EMPTY`
projected relations. A separate verifier recomputes every model set, lifted
formula, projection row, and classification; forged model counts and relation
bits are rejected.

Artifacts:

- `projection_discovery_barrier.py` — producer and finite replay;
- `verify_projection_discovery_barrier.py` — independent verifier;
- `test_projection_discovery_barrier.py` — six reduction and forgery tests;
- `PROJECTION_DISCOVERY_BARRIER.json` — serialized evidence;
- `PROJECTION_DISCOVERY_BARRIER_REPORT.md` — this report.
