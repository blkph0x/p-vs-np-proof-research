# Scope and exact checks for the scaling campaign

For `F_n`, the all-assignment family contains one width-`n` clause for each
assignment to `n` variables, with that assignment falsifying its clause. The
independent reviewer exhausts all `2^n` assignments for `n <= 10`, so
unsatisfiability is checked directly in addition to proof replay. For the
deterministic CDCL implementation in `proof_producing_cdcl_lab/cdcl.py`,
false-first decisions and the saved traces satisfy the exact identities

    decisions = 2^(n-1) - 1
    conflicts = learned_clauses = 2^(n-1)
    resolution_steps = 2^n - 1.

The reviewer checks these identities for every saved `n` rather than assuming
that a timing curve proves them. Since `F_n` itself has `n * 2^n` literal
occurrences, this family is not a super-polynomial-in-input-size lower bound;
it is a deterministic-heuristic control and a proof-replay check.

The pigeonhole controls use `h + 1` pigeons and `h` holes for `1 <= h <= 8`.
The independently reconstructed clauses require each pigeon to occupy at least
one hole, at most one hole, and require distinct pigeons to use distinct holes.
The resulting injection would map `h + 1` pigeons into `h` holes, so the family
is unsatisfiable by a direct counting argument. The reviewer checks the exact
clause construction, the counting condition, and every CDCL resolution step.

The recorded CDCL traces are resolution proofs. Therefore the data can expose
growth in this proof system, but it cannot by itself prove a lower bound against
extended resolution, cutting planes, algebraic methods, randomized algorithms,
or arbitrary polynomial-time SAT algorithms. Wall-clock measurements are
machine observations and are never used as complexity proofs.

The historical context is Haken's all-size resolution lower bound for the
pigeonhole principle and the width-size relationship of Ben-Sasson and
Wigderson. This lab cites those primary sources for context; it replays only
the finite certificates generated here and does not claim to reproduce either
theorem.
