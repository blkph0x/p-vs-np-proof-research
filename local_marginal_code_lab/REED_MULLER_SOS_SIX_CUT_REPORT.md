# Exact sixth-cut SOS certificate for RM(2,5)

This report records the next exact finite probe after the fifth-cut replay. The
underlying object is still the complete pinned RM(2,5) level-eight
projection-marginal quotient: 2,174 variable orbits and 27,926 equality rows.
The objective is the reduced non-pin weight; its integral benchmark is `7`
(total pinned weight `8`).

## The new valid cut

For every integer weight `t` in `0..31`,

```text
P(t) = (t-6)(t-7)(31-t)(t+32)^2 >= 0.
```

The adjacent factors `(t-6)(t-7)` are nonnegative on integer `t`; `31-t` is
nonnegative on the interval; and the square is always nonnegative. Therefore
the product is valid on the complete integer weight domain. Its binomial-basis
linear part is

```text
-353148*C(t,1) + 43528*C(t,2) + 7212*C(t,3)
- 720*C(t,4) - 120*C(t,5),
```

with constant term `1333248`. The fifth-cut witness violates this valid
inequality by the exact amount `-6759234824400/48731153`. That independently
motivates the sixth cut; it is not a fitted floating-point row.

## Exact result

Adding the cut and replaying the quotient gives

```text
primal upper bound = 22465669893401/3255387995415
dual lower bound   = 22465669893401/3255387995415
unresolved gap     = 0
```

The exact primal masses satisfy every rebuilt quotient equality and are
nonnegative. The independent dual has 1,793 nonzero base quotient rows. The
only nonzero cut multipliers are

```text
(t-6)(t-7)(t-23)(t-24)             3927706426/9766163986245
(t-6)(t-7)(31-t)(t+32)^2           82328743/39064655944980
```

The earlier cuts are slack at this optimum. All reduced costs are nonnegative;
the minimum is `0`, the positive minimum is `40712341292/651077599083`, and
2,147 columns have zero reduced cost. The exported active basis has 2,133
columns and 2,133 rows, and the exact basis solve has no negative primal mass.

The saved certificate is
[`REED_MULLER_SOS_SIX_CUT_RESULTS.json`](REED_MULLER_SOS_SIX_CUT_RESULTS.json).
The producer replay is
[`run_reed_muller_sos_six_cut.py`](run_reed_muller_sos_six_cut.py), and the
independent standard-library replay is
[`REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW.py`](REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW.py).
The ten adversarial tests are in
[`test_reed_muller_sos_six_cut.py`](test_reed_muller_sos_six_cut.py).

## Reproduce

From this directory:

```text
python run_reed_muller_sos_six_cut.py
python REED_MULLER_SOS_SIX_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_six_cut.py
```

This is a finite, representation-specific exact certificate. It does not
classify all SAT instances, establish a polynomial-time algorithm, or resolve
P versus NP. Its purpose is to make one more relaxation-strengthening step
public, rational, replayable, and falsifiable.
