# The RM(2,5) affine-flat star control does not close the gap

This is an exact negative control for the next Reed--Muller boundary. It is
deliberately weaker than the full level-eight local projection relaxation, so
it does not decide that full case.

## Relaxation and exact value

For pinned `RM(2,5)`, take every affine three-flat of the 5-dimensional
evaluation space as an eight-coordinate scope. There are

```text
[5 choose 3]_2 * 2^(5-3) = 155 * 4 = 620
```

such flats. Give each flat a probability table supported on the pinned-code
projection, but share only the singleton marginals between tables. No
seven-coordinate overlap tables are shared. This is therefore a star
relaxation, weaker than full level-eight local consistency.

The all-dual minimum-check incidence lower bound already gives

```text
sum_i x_i >= 1 + 155/35 = 38/7.
```

The same point is feasible in the star relaxation. Put `x_0=1` and
`x_i=1/7` for every other coordinate. On a flat containing the pin, use the
uniform distribution over the seven assignments with pin one and exactly one
free one; this has odd free parity and each free marginal `1/7`. On a flat
omitting the pin, use mass `3/7` on the all-zero assignment and mass `4/7`
uniformly over the 28 weight-two assignments; each coordinate again has
marginal `(4/7)*(2/8)=1/7` and the parity is even. Thus the exact star optimum
is `38/7`, with integer pinned optimum eight and ratio `28/19`.

The independent replay checks the Gaussian-binomial counts, both rational
tables, all marginal arithmetic, and the lower-bound formula without an LP
solver. This star model does not itself certify the arbitrary-scope
relaxation; the later full level-eight replay supplies that missing overlap
consistency and closes the finite model at `31/5`.

## Reproduction

```text
python run_reed_muller_level_d_flat_star.py
python REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW.py
```

The saved result and review are
[`REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json`](REED_MULLER_LEVEL_D_FLAT_STAR_RESULTS.json)
and
[`REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW.json`](REED_MULLER_LEVEL_D_FLAT_STAR_INDEPENDENT_REVIEW.json).
