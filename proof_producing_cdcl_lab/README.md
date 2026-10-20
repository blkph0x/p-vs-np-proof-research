# Proof-producing CDCL baseline

This lab is a universal exact CNF baseline, not a polynomial-time claim. The
solver uses full clause scans, first-UIP conflict learning, and explicit
resolution traces. SAT models, UNSAT empty-clause derivations, and capped
`UNKNOWN` outcomes are independently checked.

Run:

    python -m unittest -v test_cdcl.py test_review_validation.py
    python -O -m unittest -v test_review_validation.py
    python run_audit.py
    python review.py

See [`THEOREM.md`](THEOREM.md) for the correctness and complexity scope.

The optional [public SAT adapter](PUBLIC_SAT_BASELINE.md) compares pinned
Glucose3 with this reference on identical originals. Its 114 final runs
verify; the real failed pilot remains available. Search, proof size and
checking costs are separate: faster public search is not an overall win
with the simple Python RUP checker.

Stored evidence needs no public solver installation:

    python run_public_sat.py --replay PUBLIC_SAT_BASELINE
    python -m unittest -v test_rup_verify test_public_sat_certificate test_public_sat_evidence
    python -O -m unittest -v test_rup_verify test_public_sat_certificate test_public_sat_evidence

The 20 October reviewer repair replaces acceptance assertions with explicit
checks. It checks models against original clauses and replays all resolution
parents, pivots and conclusions without exhaustively solving the formula.
Normal and optimized-mode negative tests reject forged outputs. This is an
independent Python checker, not a proof-assistant certification. Reported
runtime counters and the historical cause of UNKNOWN are not authenticated.

The solver's terminal `derive_empty` path can exceed `max_resolution_steps`;
that parameter is not currently a hard global resource limit. This is a
resource-contract issue, not an invalid empty-clause derivation. The solver
source is unchanged in this repair.
