# High-Width Code Core Stress Lab

**New research increment to the shared-ledger / SAT / typed-merge project.**

Start with `REPORT.md` for results and `THEOREMS.md` for complete elementary proofs.

Reproduce tests:

```bash
python -m unittest -v test_lab
FAST_AUDIT=1 python run_lab.py
```

To repeat all exhaustive random-core cut checks from source (takes tens of seconds), compile `rank_audit.cpp` with `g++ -O3 -std=c++17` and run `python run_lab.py` without FAST_AUDIT.

Files:
- `core_math.py`: graphic-matroid connectivity, exact width theorem and finite cut verifier.
- `rank_audit.cpp`: exhaustive small random binary matroid connectivity verifier.
- `random_code_audits.json`: seed, generator columns, ranks, counts and witness cuts.
- `trellis_solver.py`: exact nonzero minimum-weight DP on extendable syndrome states.
- `native_graph_solvers.py`: graph min cut and girth/shortest-cycle solvers.
- `probabilistic_width.py`: elementary high-pathwidth existence bound.
- `*_results.csv/json`: detailed outcome tables.
- `test_lab.py`, `TEST_OUTPUT.txt`: checker suite.

**Limitations:** The new theorem is an exact characterization for the named complete-graph family, not a general P-vs-NP result. The random-core tests are finite, while the asymptotic random-code result is existential only.
