# SOS-strengthened RM(2,5) level-eight optimum

The full RM(2,5) level-eight local-marginal model has a fractional witness of
value `31/5`. The earlier SOS audit showed that this witness violates the
valid Boolean square

```text
(5t - 31)^2 >= 0,    t = sum_{p != 0} x_p.
```

In the quotient variables the added row is

```text
E[t^2] - (62/5) E[t] + 961/25 >= 0.
```

The strengthened finite relaxation now has independently replayed exact
primal and dual certificates:

| Certificate | Exact value |
| --- | ---: |
| Dual feasible objective | `7037/1095` |
| Primal feasible objective | `7037/1095` |
| Certified optimum gap | `0` |
| Dual nonzero equality rows | `1889` |
| Minimum reduced cost | `0` |

The primal satisfies every one of the 27,926 original quotient equalities and
lies exactly on the new SOS cut. The dual multiplier is `35/876`; all 2,174
reduced costs are checked as exact rational numbers. The production replay
rebuilds the 2,174-variable model with exact arithmetic. The pure-stdlib
independent reviewer consumes the saved quotient matrix and rejects mutations
to the primal, dual, cut, and source matrix.

The status is `EXACT_OPTIMUM` for this finite, symmetry-quotiented relaxation.
It is not an algorithm for arbitrary SAT and does not resolve P versus NP.

The exact basis construction, including the earlier rejected reconstruction,
is recorded in `REED_MULLER_EXACT_DUAL_SEARCH_REPORT.md`.

## Replay

```text
python run_reed_muller_sos_strengthened.py
python REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_strengthened.py
```

The source artifacts are `REED_MULLER_LEVEL_D_FULL_RESULTS.json` and
`REED_MULLER_SOS_MOMENT_RESULTS.json`; the exact certificate is stored in
`REED_MULLER_SOS_STRENGTHENED_RESULTS.json`.
