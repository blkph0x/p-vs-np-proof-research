# Affine Character Factor Lab

This is a bounded, certificate-producing experiment for products of local
factors coupled by an explicitly supplied GF(2) affine system. It preserves
factor ownership and evaluates the affine indicator by exact character
expansion.

Run:

```text
python -m unittest -v test_engine.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
python elimination_controls.py
python verify_elimination_controls.py
python run_order_controls.py
python verify_order_controls.py
python run_auto_route_controls.py
python verify_auto_route_controls.py
```

Read [THEOREM.md](THEOREM.md) for the identity, cost parameter, controls and
scope. The component-aware variant factors disconnected affine couplings before
expansion; connected rank remains explicit. The result is a precise
rank-parameterized route for a transformed family, not a general SAT algorithm
or a P-versus-NP proof.

[ELIMINATION_REPORT.md](ELIMINATION_REPORT.md) records the cross-check against
the weighted affine DAG: an interleaved order solves the connected chain through
128 blocks with peak retained terms three, while a poor order reaches its cap.

[ORDER_DISCOVERY_THEOREM.md](ORDER_DISCOVERY_THEOREM.md) describes the capped
filled-graph search that discovers and verifies width-bounded variable orders.
[AUTO_ROUTE_THEOREM.md](AUTO_ROUTE_THEOREM.md) binds that discovery to the
weighted solver and its independent replay.
