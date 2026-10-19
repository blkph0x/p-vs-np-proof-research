# Three-cut SOS-strengthened RM(2,5) certificate

The exact two-cut witness has a negative expectation for the valid integer
polynomial

```text
(t - 6)(t - 7)(t - 23)(t - 24) >= 0,   t in {0, 1, ..., 31}.
```

Its value on that witness is `-2400/19`. Adding this third cut to the same
full level-eight quotient gives a new finite linear program with 2,174
variable orbits and 27,926 equality-row orbits.

An exact rational primal/dual pair closes the strengthened relaxation at

```text
primal upper bound = 5231/801
dual lower bound   = 5231/801
gap                = 0
```

The earlier square and adjacent-pair cuts have primal values `17392/6675`
and `200/89`, with zero dual multipliers. The four-factor integer cut is
tight, with dual multiplier `7/9612`. The dual has 1,182 nonzero equality
rows, 1,183 exact basis columns, and all 2,174 reduced costs are nonnegative;
the minimum is `0`. A pure-stdlib reviewer rebuilds the scope quotient,
moment vectors, cuts, primal equations, dual objective, and reduced costs
without importing the producer. Mutation tests reject changed masses, dual
rows, cut constants, multipliers, and source matrix entries.

This is a finite, representation-specific certificate. It is evidence about
one local-marginal relaxation for `RM(2,5)`, not a polynomial-time SAT
algorithm and not a resolution of P versus NP. The exact result is useful
because the object, its assumptions, and its failure modes are public and
replayable.

Reproduce it with:

```text
python local_marginal_code_lab/run_reed_muller_sos_three_cut.py
python local_marginal_code_lab/REED_MULLER_SOS_THREE_CUT_INDEPENDENT_REVIEW.py
python -m unittest -v local_marginal_code_lab/test_reed_muller_sos_three_cut.py
```
