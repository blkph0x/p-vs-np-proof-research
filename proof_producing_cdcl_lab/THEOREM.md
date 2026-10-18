# General proof-producing CDCL baseline

This lab implements a deterministic CDCL solver for arbitrary CNF formulas.
Boolean propagation scans the current clause database, first-UIP learning
resolves each conflict against implication reasons, and every learned clause
stores its full resolution chain. A level-zero conflict is resolved to the
empty clause and is independently replayable. A satisfying result stores a
model that is checked against every original clause.

The independent reviewer does not import the solver. It reconstructs the
canonical input database, replays every resolution step, checks the terminal
empty clause for UNSAT, and checks the model and direct finite oracle for SAT
controls. Resource caps return `UNKNOWN` and preserve the partial trace.

The proof trace establishes correctness of each finite result; it does not
bound the number of decisions, conflicts, learned clauses, or resolution
steps by a polynomial in the input length. The scan-based implementation has
additional polynomial overhead per propagation. Pigeonhole and all-assignment
controls are retained as adversarial examples: an exact solver is available,
but no uniform polynomial runtime claim is made. This is a universal exact
baseline and a certificate mechanism, not a resolution of P versus NP.

Run from this directory:

    python run_audit.py
    python review.py
    python -m unittest -v test_cdcl.py
