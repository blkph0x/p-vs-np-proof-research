# Bounded-width resolution closure

This lab saturates all non-tautological clauses up to a supplied width under
weakening and resolution. A derived empty clause is independently replayed; a
fixed point without the empty clause certifies that this bounded-width proof
system has no refutation. Clause and step caps return `UNKNOWN`.

Run:

    python -m unittest -v test_resolution.py
    python run_audit.py
    python review.py

See [`THEOREM.md`](THEOREM.md) for the completeness and exponential-cost
argument.
