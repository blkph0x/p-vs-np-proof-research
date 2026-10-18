# Connected affine cover lab

This lab proves and checks a lower bound for **nonnegative** decompositions of
the connected path CNF

`AND_i (x_i OR x_(i+1))`.

Run:

```text
python -m unittest -v test_cover.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

Read [THEOREM.md](THEOREM.md) for the affine-support proof and its limits. The
result is a representation barrier; signed cancellation and unrestricted SAT
algorithms remain outside its scope. Run `python weighted_crosscheck.py` and
`python verify_weighted_crosscheck.py` for the independent weighted-DAG escape
control: five path instances through 128 variables are exact with peak message
size four.
