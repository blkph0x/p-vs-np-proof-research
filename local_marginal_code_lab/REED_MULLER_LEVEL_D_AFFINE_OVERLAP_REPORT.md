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
both give

```text
selected affine-overlap optimum = 31/5
integer pinned optimum           = 8
selected-model ratio             = 40/31
```

The dual certificate has nonnegative reduced costs for all 28 quotient
variables, with minimum reduced cost zero. The independent pure-standard-
library replay reconstructs the finite geometry, all 28 and 53 orbits, every
quotient matrix entry, the primal equations, and the dual objective without
using an LP solver.

For the integral comparison, an integral table forces even parity on every
affine 3-flat. The 620 flat-incidence vectors have binary rank 16, so their
orthogonal space is exactly the 16-dimensional `RM(2,5)` code. Conditioning
the pin therefore leaves true codewords, whose minimum weight is 8; this
justifies the selected-model ratio `8/(31/5)=40/31`.

Because every full level-eight local projection solution restricts to this
selected model, the result proves the scoped lower bound

```text
full RM(2,5) level-8 optimum >= 31/5.
```

This report deliberately makes no claim about extension to every arbitrary
eight-coordinate scope. The later [full level-eight replay](REED_MULLER_LEVEL_D_FULL_REPORT.md)
closed that finite arbitrary-scope model at `31/5`; this selected-model report
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
