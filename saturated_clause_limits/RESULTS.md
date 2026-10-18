# Common-cost clause saturation checks

The exact flat OR relation fails ordinary even exchange for every arity at least two, as proved in THEOREM.md. Signed weights, modular terminal offsets and extra internal vertices do not permit that exact relation to be the global-minimum boundary support.

A constructive positive control does implement flat OR on the promised paired domain: the all-false state costs one and every other valid state costs zero. Full signatures and matching witnesses are saved for arities one, two and three (2, 6 and 10 vertices). The all-size construction has 4k−2 vertices. Its invalid zero-cost states remain explicit.

The two-input control uses six vertices, the minimum under these four-terminal deletion semantics, including signed costs and modular terminal offsets. The lower bound is proved algebraically. A supplemental enumeration checked all 4,096 simple four-vertex graphs with each edge absent or weighted −1, 0 or 1; in all 2,304 graphs supporting the required pair states, the forced common-cost offsets also allowed the false state.

Raw disjoint-pair threshold controls were checked for arities one through four. Their score rewards additional true literals; the saved two-clause example shows how these rewards can conceal an unsatisfied clause when thresholds are simply added. Scalar saturation fixes that numerical truth table, but a complete reduction still needs correct interface composition and exclusion of invalid encodings.

Run `python -m unittest test_saturated_clause.py -v` and `python run_experiments.py` in this folder. The JSON includes requests, matching witnesses, and before/after source hashes. Python 3.10.10; measured experiment time 0.484186s. No general impossibility of matching reductions or conclusion about P versus NP is claimed.
