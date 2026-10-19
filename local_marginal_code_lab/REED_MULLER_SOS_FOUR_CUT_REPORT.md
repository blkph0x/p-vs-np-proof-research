# Four-cut SOS-strengthened RM(2,5) certificate

The exact three-cut witness has a negative expectation for the valid
integer-weight polynomial

```text
Q(t) = t(31-t)(t-3)(t-4)(t+28) >= 0,   t in {0, 1, ..., 31}.
```

The inequality is pointwise on the integer domain: `t`, `31-t`, and `t+28`
are nonnegative, while `(t-3)(t-4)` is nonnegative for every integer `t`.
In the binomial basis used by the exact moment replay,

```text
Q(t) = 5220*C(t,1) - 6960*C(t,2) + 5220*C(t,3) - 120*C(t,5).
```

The three-cut witness evaluates `Q` at `-3248000/89`, so this is a new
finite separation rather than a fitted numerical constraint. Adding the cut
to the same full level-eight quotient gives a finite linear program with
2,174 variable orbits and 27,926 equality-row orbits. An exact rational
primal/dual pair closes it at

```text
primal upper bound = 1219047171/184149541
dual lower bound   = 1219047171/184149541
gap                = 0
```

The square cut is slack with value `1896398416/4603738525` and zero dual
multiplier. The `(t-6)(t-7)` and four-factor cuts are tight, with dual
multipliers `173285/184149541` and `391573/552448623`; the new `Q` cut is
tight with multiplier `4151/1657345869`. The exact dual has 1,088 nonzero
rows. Its 2,174 reduced costs are all nonnegative, with minimum `0`, and
2,141 have zero reduced cost. The exported simplex basis contains 2,134
columns and 2,134 rows; solving that basis over exact rationals yields 2,094
positive primal masses and no negative mass.

The producer, pure-standard-library independent reviewer, and adversarial
tests rebuild the code, scope orbits, moment vectors, primal equations, dual
objective, and reduced costs without importing the producer's model builder.
The saved JSON is the public certificate; the exploratory numerical basis
search is not a trusted input to the replay.

This is a finite, representation-specific certificate. It is evidence about
one local-marginal relaxation for `RM(2,5)`, not a polynomial-time SAT
algorithm and not a resolution of P versus NP.

Reproduce it with:

```text
python local_marginal_code_lab/run_reed_muller_sos_four_cut.py
python local_marginal_code_lab/REED_MULLER_SOS_FOUR_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v local_marginal_code_lab/test_reed_muller_sos_four_cut.py
```
