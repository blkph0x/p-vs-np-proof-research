# Complete bounded-width resolution closure

For a CNF formula on `n` variables and width bound `w`, this lab saturates the
finite set of all non-tautological clauses of width at most `w` under two
inferences: weakening by adding literals, and binary resolution whose
resolvent has width at most `w`. Initial clauses wider than `w` are excluded,
because they cannot occur in a width-`w` derivation.

The closure is complete for this inference system. Induct on a bounded proof:
each axiom is inserted, each weakening is enumerated, and each resolution is
generated when both parents have entered the closure. Therefore a fixed-point
closure without the empty clause is a certificate that no weakening-resolution
refutation of width at most `w` exists. When the empty clause appears, the
saved axiom, weakening, and resolution records form a replayable refutation.
Explicit clause and step caps return `UNKNOWN` before saturation.

The universe has at most `sum_{i=0}^w 2^i binomial(n,i)` clauses. The simple
implementation scans known clause pairs, so its worst-case work is quadratic
in that universe times the number of pivots, plus weakening generation. This
is an exact bounded-width procedure, not a polynomial algorithm for arbitrary
SAT. The pigeonhole and all-assignment controls test width boundaries; a
satisfiable control and cap-triggered run prevent treating a missing bounded
refutation as an UNSAT result.

Run:

    python -m unittest -v test_resolution.py
    python run_audit.py
    python review.py
