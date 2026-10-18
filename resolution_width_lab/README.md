# Bounded-width resolution closure

This lab saturates all non-tautological clauses up to a supplied width under
weakening and resolution. A derived empty clause is independently replayed; a
fixed point without the empty clause certifies that this bounded-width proof
system has no refutation. Clause and step caps return `UNKNOWN`.

The audit also sweeps widths from zero through the widest supplied axiom and
records the first width with an empty-clause derivation. The sweep is repeated
by the independent reviewer, so the saved threshold is an exact result for
these finite controls rather than a timeout-based estimate.

Run:

    python -m unittest -v test_resolution.py
    python run_audit.py
    python review.py
    python run_incremental.py
    python review_incremental.py
    python run_indexed.py
    python review_indexed.py
    python run_bitset.py
    python review_bitset.py
    python run_pebble.py
    python review_pebble.py
    python run_php_width.py
    python review_php_width_proof.py

See [`THEOREM.md`](THEOREM.md) for the completeness and exponential-cost
argument.

The pebble-game bridge uses the primary Atserias-Dalmau characterization to
replace an inconclusive capped PHP(5,4) width-4 saturation with an exact finite
width result. Its independent tuple replay is recorded in
[`PEBBLE_REPORT.md`](PEBBLE_REPORT.md) and `PEBBLE_REVIEW.json`.

The uniform standard PHP family has a separate constructive certificate. The
all-`n` stage proof, its independent replay, and the finite saved campaign are
documented in [`PHP_WIDTH_REPORT.md`](PHP_WIDTH_REPORT.md),
[`PHP_WIDTH_RESULTS.json`](PHP_WIDTH_RESULTS.json), and
[`PHP_WIDTH_REVIEW.json`](PHP_WIDTH_REVIEW.json). For `n >= 2`, the exact
minimum resolution width is `n`; PHP(2,1) is the width-two edge case.
