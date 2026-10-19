# Two-cut SOS-strengthened RM(2,5) certificate

This experiment adds a second valid inequality to the exact one-cut quotient
model for the non-pin weight `t`. The polynomial

```text
(t - 6)(t - 7) >= 0,   t in {0, 1, ..., 31}
```

is nonnegative on every possible integer weight, so its expectation is a valid
linear inequality for every genuine distribution. At the one-cut optimum the
expectation is `-108/365`, exposing a finite pseudo-distribution that passes the
first SOS constraint but cannot be an integer-weight distribution.

The rebuilt two-cut model has 2,174 variable orbits and 27,926 equality-row
orbits. An exact primal/dual certificate closes the strengthened relaxation at

```text
primal upper bound = 367/57
dual lower bound   = 367/57
gap                = 0
```

The first square cut `(5*t-31)^2` has value `144/475` and dual multiplier `0`.
The integer-adjacent cut `(t-6)(t-7)` is tight with value `0` and exact dual
multiplier `7/171`. The dual uses 337 nonzero equality rows; all 2,174 exact
reduced costs are nonnegative and the minimum is `0`. The independent
stdlib-only reviewer and adversarial mutation tests replay the same certificate
without importing the model builder.

This is a finite, representation-specific certificate. It does not establish a
polynomial-time SAT algorithm and does not resolve P versus NP. Its value is
that it records a reproducible valid cut, the exact optimum it produces, and a
machine-checkable proof object for the next hierarchy level.

Reproduce it with:

```text
python local_marginal_code_lab/run_reed_muller_sos_two_cut.py
python local_marginal_code_lab/REED_MULLER_SOS_TWO_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v local_marginal_code_lab/test_reed_muller_sos_two_cut.py
```
