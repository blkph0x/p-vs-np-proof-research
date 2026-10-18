# Circuit-order lower-bound audit

This lab constructs a pinned-OR Tseitin circuit from a chosen graph. Every
control is trivially satisfiable, while the source graph is present in the
circuit CNF's primal graph. Exact small subset searches and an independent
replay verify the resulting source-width lower bound and record the extra
width introduced by gate variables. The source order can also be extended
constructively with width at most one larger; the replay checks that additive
upper bound as well.

```text
python -m unittest discover -v
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

See [THEOREM.md](THEOREM.md) for the scope. The experiment is a structural
search-bound audit, not a universal SAT algorithm or a P-versus-NP result.
