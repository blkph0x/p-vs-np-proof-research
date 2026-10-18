# Primal-order SAT lab

This lab closes the implementation gap between a SAT frontier solver and the
order problem. It builds the primal graph of a CNF, searches exactly for a
minimum-boundary variable order by subset dynamic programming, and then feeds
that order to a proof-producing SAT DP. The search is exponential by design and
returns `UNKNOWN` when its explicit subset cap fires.

```text
python -m unittest -v test_primal_order.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

The primal-graph boundary equals the SAT frontier boundary: a processed
variable is active exactly when it shares a clause with an unprocessed
variable. Thus this is an end-to-end exact solver for small instances, while
the order-discovery cost remains explicit rather than hidden.
