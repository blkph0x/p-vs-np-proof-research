# Graph order-hardness lab

This lab connects active-variable order discovery to vertex separation. It
provides exact small-graph layout certificates and maps each graph to an
always-satisfiable monotone 2-CNF.

```text
python -m unittest -v test_vertex_separation.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

Read [THEOREM.md](THEOREM.md) for the reduction and its complexity scope. The
subset optimizer is exponential by design.
