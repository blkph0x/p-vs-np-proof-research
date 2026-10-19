# SOS-strengthened RM(2,5) level-eight bracket

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

The strengthened finite relaxation now has independently replayed rational
certificates on both sides:

| Certificate | Exact value |
| --- | ---: |
| Dual feasible objective | `983398195747256721400419/153027121820069630875000` |
| Certified lower bound | `64263/10000` |
| Primal feasible objective | `7037/1095` |
| Remaining interval | `403/2190000` |

The dual reduced costs are all nonnegative; the minimum saved reduced cost is
`280893295569599/140538273453549500000`. The primal satisfies every one of the
27,926 original quotient equalities and lies exactly on the new SOS cut. The
production replay rebuilds the 2,174-variable model with exact arithmetic. The
pure-stdlib independent reviewer consumes the saved quotient matrix and
rejects mutations to the primal, dual, cut, and source matrix.

The status is deliberately `BRACKETED_NOT_EXACT`: the two certificates leave a
positive gap, so this experiment does not claim the exact strengthened optimum.
It is a finite hierarchy calculation for one binary-code family. It gives no
algorithm for arbitrary SAT and no P-versus-NP resolution.

## Replay

```text
python run_reed_muller_sos_strengthened.py
python REED_MULLER_SOS_STRENGTHENED_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_sos_strengthened.py
```

The source artifacts are `REED_MULLER_LEVEL_D_FULL_RESULTS.json` and
`REED_MULLER_SOS_MOMENT_RESULTS.json`; the new certificate is stored in
`REED_MULLER_SOS_STRENGTHENED_RESULTS.json`.
