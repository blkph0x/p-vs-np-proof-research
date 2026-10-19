# Exact seventh-cut SOS certificate for RM(2,5)

This report records an exact finite probe after the sixth-cut replay. The underlying object remains the complete pinned RM(2,5) level-eight projection-marginal quotient: 2,174 variable orbits and 27,926 equality rows.

## The new valid cut

For every integer weight `t` in `0..31`,

```text
P(t) = (t-6)(t-7)(31-t) >= 0.
```

The adjacent factors are nonnegative on integer `t`, and `31-t` is nonnegative on the interval. Its binomial-basis linear part is

```text
-402*C(t,1) + 82*C(t,2) - 6*C(t,3),
```

with constant term `1302`. The exact six-cut witness violates this valid inequality by `-3473117738496/217025866361`. This is an integer-domain certificate, not a fitted floating-point row.

## Exact result

Adding the cut and replaying the quotient gives

```text
primal upper bound = 35873801083/5129253893
dual lower bound   = 35873801083/5129253893
unresolved gap     = 0
```

The exact primal masses satisfy every rebuilt quotient equality and are nonnegative. The independent dual has 1,100 nonzero base quotient rows. The only nonzero cut multipliers are

```text
(t-6)(t-7)(t-23)(t-24)       1843191/20517015572
(t-6)(t-7)(31-t)             181738963/30775523358
```

All reduced costs are nonnegative; the minimum is `0`, the positive minimum is `154880840/165459803`, and 2,144 columns have zero reduced cost. The exported active basis has 2,125 columns and 2,123 quotient rows, with the two active cut equations completing the exact square solve.

The saved certificate is [REED_MULLER_SOS_SEVEN_CUT_RESULTS.json](REED_MULLER_SOS_SEVEN_CUT_RESULTS.json). The producer replay is [run_reed_muller_sos_seven_cut.py](run_reed_muller_sos_seven_cut.py), and the independent standard-library replay is [REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_REVIEW.py](REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_REVIEW.py). The adversarial tests are in [test_reed_muller_sos_seven_cut.py](test_reed_muller_sos_seven_cut.py).

## Reproduce

From this directory:

```text
python run_reed_muller_sos_seven_cut.py
python REED_MULLER_SOS_SEVEN_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_seven_cut.py
```

This is a finite, representation-specific exact certificate. It does not classify all SAT instances, establish a polynomial-time algorithm, or resolve P versus NP. Its purpose is to make one more relaxation-strengthening step public, rational, replayable, and falsifiable.
