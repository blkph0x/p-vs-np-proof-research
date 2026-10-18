# Mixed information frontier lab

This lab is an exact small-instance oracle for semantic state minimization at a
variable cut. It compares nominal local-state products, reachable product
states, and exact future-equivalence classes for parity, cardinality, and OR
constraints.

```text
python -m unittest -v test_mixed_frontier.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

Read [THEOREM.md](THEOREM.md) for the proof-backed controls and their limits.
The analyzer is deliberately exponential and is evidence about quotient
structure, not a general P=NP solver. The six-case run also includes a
partial-scope cardinality/parity bundle whose ten reachable summaries all
remain future-distinct.
