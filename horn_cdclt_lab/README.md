# Horn CDCL(T) lab

Run:

```text
python -m unittest -v test_lab.py
python run_experiments.py
python run_cdcl_experiments.py
```

The experiment writes `RESULTS.json`, `REVIEW.json`, and `EXPERIMENT_OUTPUT.txt`.
The implementation is deliberately deterministic and proof-producing, but the search
layer is exponential in the worst case. The exact complexity conclusion is recorded in
`THEOREM.md`.

The CDCL experiment writes `CDCL_RESULTS.json`, `CDCL_REVIEW.json`, and
`CDCL_EXPERIMENT_OUTPUT.txt`.

`run_polymorphism.py` enumerates common Boolean polymorphisms through arity four and
writes `POLYMORPHISM_RESULTS.json` plus `POLYMORPHISM_REVIEW.json`.
