# Exact fifth-cut SOS certificate for RM(2,5)

This report records the next exact finite probe after the four-cut replay.  The
underlying object is the complete pinned RM(2,5) level-eight projection-marginal
quotient: 2,174 variable orbits, 27,926 equality rows, and an integer optimum
of eight.  The result is about this finite relaxation only.

## The new valid cut

For every integer weight `t` in `0..31`,

```text
P(t) = t(31-t)(t-3)(t-4) >= 0.
```

The factors `t` and `31-t` are nonnegative on the interval.  The two remaining
factors have the same sign for every integer `t`: both are nonnegative for
`t <= 3` or `t >= 4`, and there is no integer strictly between 3 and 4.
Thus the product is valid on the integer weight domain.  Its binomial-basis
linear part is

```text
180*C(t,1) - 244*C(t,2) + 192*C(t,3) - 24*C(t,4),
```

with constant term zero.  The four-cut witness violates this valid inequality
by the exact amount `-61440933600/184149541`.  That sign is the reason for
testing the fifth cut rather than presenting it as a fitted numerical row.

## Exact result

Adding the cut and replaying the quotient gives

```text
primal upper bound = 324713143/48731153
dual lower bound   = 324713143/48731153
unresolved gap     = 0
```

The exact primal masses satisfy every rebuilt quotient equality and are
nonnegative.  The independent dual has 1,733 nonzero base quotient rows.  The
three nonzero cut multipliers are

```text
(t-6)(t-7)                         21978467/1315741131
(t-6)(t-7)(t-23)(t-24)             560525/1315741131
t(31-t)(t-3)(t-4)                 178066/1315741131
```

The earlier boundary product with the extra `(t+28)` factor is now slack at
`703472907600/48731153`, so its multiplier is zero.  All reduced costs are
nonnegative; the minimum is `0`, the positive minimum is
`12221440/146193459`, and 2,144 columns have zero reduced cost.  The exported
active basis has 2,134 columns and 2,134 rows, and the exact basis solve has no
negative primal mass.

The saved certificate is
[`REED_MULLER_SOS_FIVE_CUT_RESULTS.json`](REED_MULLER_SOS_FIVE_CUT_RESULTS.json).
The producer replay is
[`run_reed_muller_sos_five_cut.py`](run_reed_muller_sos_five_cut.py), and the
independent standard-library replay is
[`REED_MULLER_SOS_FIVE_CUT_INDEPENDENT_REVIEW.py`](REED_MULLER_SOS_FIVE_CUT_INDEPENDENT_REVIEW.py).
The ten adversarial tests are in
[`test_reed_muller_sos_five_cut.py`](test_reed_muller_sos_five_cut.py).

## Reproduce

From this directory:

```text
python run_reed_muller_sos_five_cut.py
python REED_MULLER_SOS_FIVE_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_five_cut.py
```

This is a finite, representation-specific exact certificate.  It does not
classify all SAT instances, establish a polynomial-time algorithm, or resolve
P versus NP.  Its purpose is to make one more relaxation-strengthening step
public, rational, replayable, and falsifiable.
