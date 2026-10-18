# Linear frontier order lab

This lab implements the exact GF(2) cut-information formula and a bounded
subset-DP optimizer for variable order. It saves cut-rank certificates and
replays them with an independent implementation.

```text
python -m unittest -v test_frontier.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

The optimizer is intentionally exponential; the result is a certified small
instance and an adversarial ordering control, not a general P=NP solver.
