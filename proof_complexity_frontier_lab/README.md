# Proof width, CDCL traces, and frontier-state growth

This lab puts two exact finite representations beside the same adversarial CNF
families: the proof-producing CDCL statistics from
`proof_complexity_scaling_lab`, and supplied-order frontier dynamic programming
state counts.  The producer saves only compact summaries; the independent
reviewer reconstructs every formula, boundary, state layer, and transition
count from scratch.

Textual source hashes are computed after CRLF/CR line endings are normalized
to LF, so the same artifact verifies on Windows and Linux checkouts.

Run:

    python run_frontier.py
    python review_frontier.py
    python -m unittest -v test_frontier.py

The all-assignment family is included as a control whose input already has
exponential size in its variable parameter.  The pigeonhole family has
polynomial-size CNFs in the number of holes and a direct injection proof of
unsatisfiability.  The measured frontier width and this particular CDCL
resolution trace are separate quantities.  Their finite correlation does not
lower-bound arbitrary SAT algorithms or resolve P versus NP.
