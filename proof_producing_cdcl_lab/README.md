# Proof-producing CDCL baseline

This lab is a universal exact CNF baseline, not a polynomial-time claim. The
solver uses full clause scans, first-UIP conflict learning, and explicit
resolution traces. SAT models, UNSAT empty-clause derivations, and capped
`UNKNOWN` outcomes are independently checked.

Run:

    python -m unittest -v test_cdcl.py
    python run_audit.py
    python review.py

See [`THEOREM.md`](THEOREM.md) for the correctness and complexity scope.
