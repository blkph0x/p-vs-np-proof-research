# RM(2,5) affine-overlap consistency raises the level-8 lower bound

This checkpoint strengthens the earlier affine-flat star control. It selects
all affine 3-flats of `F_2^5` as eight-coordinate scopes, then includes every
affine 2-flat, affine line, and singleton contained in those scopes. Each
scope receives a probability table supported on the pinned `RM(2,5)`
projection, and every selected containment edge must have matching marginals.

The selected finite model has exactly 620 eight-flats, 1,240 four-point
affine flats, 496 affine lines, and 32 singletons. Its `GL(5,2)`-invariant
quotient has 28 variable orbits and 53 equality-row orbits. Averaging over
`GL(5,2)` is valid because the group fixes the pinned coordinate and preserves
the Reed--Muller code, so solving the quotient preserves the optimum of this
selected model.

## Exact value

The saved rational primal tables and rational dual reduced-cost certificate
both use the reduced objective over the 31 non-pinned coordinates and give

```text
selected affine-overlap reduced optimum = 31/5
selected affine-overlap total optimum   = 36/5
integer pinned reduced benchmark        = 7
integer pinned total benchmark          = 8
reduced ratio                           = 35/31
total-weight ratio                      = 10/9
```

The dual certificate has nonnegative reduced costs for all 28 quotient
variables, with minimum reduced cost zero. The independent pure-standard-
library replay reconstructs the finite geometry, all 28 and 53 orbits, every
quotient matrix entry, the primal equations, and the dual objective without
using an LP solver.

The separate [compact dual note](REED_MULLER_AFFINE_OVERLAP_DUAL_NOTE.md)
extracts the certificate's human-readable core. For every feasible quotient
point, the reduced-objective gap is the positive combination

```text
objective - 31/5 =
  (434/5) z_2 + (682/5) z_3 + (124/5) z_4
  + (496/5) z_7 + (1736/5) z_8 + 248 z_9 >= 0.
```

The accompanying test reconstructs the quotient matrix and checks this exact
identity with rational arithmetic; it is not a decimal fit or a claim about
an unbounded hierarchy.

For the integral comparison, an integral table forces even parity on every
affine 3-flat. The 620 flat-incidence vectors have binary rank 16, so their
orthogonal space is exactly the 16-dimensional `RM(2,5)` code. Conditioning
the pin therefore leaves true codewords, whose minimum weight is 8; this
justifies the selected-model ratios `7/(31/5)=35/31` and
`8/(36/5)=10/9`.

Because every full level-eight local projection solution restricts to this
selected model, the result proves the scoped lower bound

```text
full RM(2,5) level-8 reduced optimum >= 31/5
(equivalently total-weight optimum >= 36/5).
```

This report deliberately makes no claim about extension to every arbitrary
eight-coordinate scope. The later [full level-eight replay](REED_MULLER_LEVEL_D_FULL_REPORT.md)
closed that finite arbitrary-scope model at reduced value `31/5` (total `36/5`); this selected-model report
remains a stronger barrier and a controlled negative result, not a complete
solution to the Reed--Muller instance or to P versus NP.

## Reproduction

```text
python run_reed_muller_level_d_affine_overlap.py
python REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_affine_overlap.py
```

The machine-readable certificate is
`REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json`; the independent replay is
`REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.json`.
