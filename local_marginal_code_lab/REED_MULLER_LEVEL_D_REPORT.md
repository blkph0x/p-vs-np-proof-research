# The level-d boundary closes the smallest RM local gap

This report records a finite exact result for the pinned evaluation code
`RM(1,3)`. It is a check on the next level of the combined relaxation, not a
P-versus-NP result.

## Statement

Let `C` be the length-eight first-order Reed--Muller code, pin coordinate `0`
to one, and let `C_0` be the eight codewords satisfying that pin. For every
scope `S` with `|S| <= 4`, introduce a nonnegative table
`mu_S(a)` for each assignment `a` in the projection of `C_0` onto `S`.
The local system is

```text
sum_a mu_S(a) = 1
mu_(S\{t})(b) - sum_{a: a without t = b} mu_S(a) = 0
```

for every scope, deleted coordinate, and supported parent assignment. Its
objective is the sum of the singleton one-marginals. This is the exact
level-four local projection-marginal relaxation used by the combined
all-dual/local experiment.

The saved certificate proves

```text
OPT(level-four local projection marginals) = 4.
```

The lower-bound certificate uses only these local equalities. Therefore the
same lower bound holds after adding every dual parity-polytope inequality.
The codeword with bit mask `15` is pinned, has weight four, and supplies a
feasible integral upper bound. Consequently the combined all-dual/local
relaxation also has exact optimum four at level `d=4`.

## Exact dual certificate

The finite LP has 163 scopes, 982 supported nonnegative atoms, and 2,544
normalization/marginal equality rows. The artifact contains 113 integer
multipliers for those rows. The independent replay reconstructs every row and
checks, using exact rational arithmetic, that the resulting coefficient of
each atom is at most its objective coefficient. The sum of the multipliers on
normalization rows is four, so weak duality gives the lower bound four.

The same replay checks the weight-four primal word, every local projection,
and every dual parity check. Thus the two sides meet exactly; no floating-point
optimality claim is used in the published result. The dual was discovered by
an exploratory LP search, but the checked artifact is the integer certificate,
not the numerical solver output.

## What this changes

The sparse one-hot witness from the boundary-level `d-1` report survives at
level three for `RM(1,3)` but is rejected at level four. This certificate shows
that the next level closes the entire finite gap for the smallest saved
Reed--Muller control. It does not establish that level `d` closes the gap for
`RM(2,5)` or any general code family, and it says nothing about arbitrary SAT
algorithms or P versus NP.

## Reproduction

From this directory:

```text
python REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d.py
```

The machine-readable certificate is
[`REED_MULLER_LEVEL_D_DUAL.json`](REED_MULLER_LEVEL_D_DUAL.json). The replay
result and independent review are saved in
[`REED_MULLER_LEVEL_D_RESULTS.json`](REED_MULLER_LEVEL_D_RESULTS.json) and
[`REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.json`](REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.json).
