# Matching-gadget boundary experiments

All checks passed on 1,100 labelled simple graphs with at most five vertices, using every terminal-prefix size: 6,505 boundary relations, of which 4,494 were nonempty. Every nonempty relation had fixed vertex parity and satisfied even symmetric exchange. The empty relations are not called delta-matroids.

Replayed 9,000 explicit alternating-path flips, checking both resulting perfect matchings and exact cost conservation. A terminal prefix of every size covers arbitrary terminal placements up to relabelling because all labelled graphs are enumerated.

An additional 400 seeded weighted requests used signed and nonnegative integer weights. All 298 nonempty global-minimum supports passed exchange. Nonnegative zero-optimum support always agreed exactly with the feasible support of the zero-edge subgraph.

Every one of 884 distinct nonempty cost-cutoff supports passed the weaker two-sided exchange condition. This condition holds for arbitrary signed costs and any common threshold, and still excludes exact paired copy and AND. It does not assert that threshold supports are delta-matroids.

The saved examples include ordinary and two-sided exchange failures for exact paired copy and AND, six-vertex promised-domain copy and AND gadgets, a valid-pair gadget, the failure of naive edge-union to enforce relation intersection, a positive-threshold counterexample to ordinary exchange that passes two-sided exchange, and a signed-zero-level counterexample. Every graph signature includes exact costs and matching witnesses.

Run `python -m unittest test_matching_boundary.py` and `python run_experiments.py` here to reproduce the unit tests and this bounded experiment. The JSON records input and source hashes. Seed 2026101811; Python 3.10.10; measured experiment time 5.563488s.

The all-size statements follow from the alternating-path proof in THEOREM.md. Finite enumeration alone would not exclude larger gadgets. No impossibility of general matching reductions or conclusion about P versus NP is claimed.
