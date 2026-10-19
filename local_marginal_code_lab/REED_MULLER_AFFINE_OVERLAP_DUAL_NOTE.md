# A compact dual inequality for the RM(2,5) affine-overlap model

This note extracts the useful mathematical content of the exact dual
certificate in `REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json`. It concerns
the selected model with affine 3-flats, their affine 2-flats, lines, and
singletons. The full level-eight model contains this selected model by
restriction, so the selected-model lower bound is also a lower bound for the
full model.

## The identity

Let `z_i` denote the nonnegative mass of quotient variable orbit `i`, using
the orbit ordering in the saved certificate. For every feasible quotient
point, the exact dual multipliers satisfy

```text
objective(z) - 31/5
  = (434/5) z_2
  + (682/5) z_3
  + (124/5) z_4
  + (496/5) z_7
  + (1736/5) z_8
  + 248 z_9.
```

All six coefficients are strictly positive and every `z_i` is nonnegative.
Consequently every feasible point has objective at least `31/5`. The saved
primal point has `z_2=z_3=z_4=z_7=z_8=z_9=0`, so the same certificate has
objective exactly `31/5`.

The six slack orbits are:

| orbit | scope representative | atom representative | orbit size |
| ---: | --- | ---: | ---: |
| 2 | pinned affine 3-flat `[0,1,2,3,4,5,6,7]` | 23 | 4,340 |
| 3 | pinned affine 3-flat `[0,1,2,3,4,5,6,7]` | 63 | 3,255 |
| 4 | pinned affine 3-flat `[0,1,2,3,4,5,6,7]` | 255 | 155 |
| 7 | unpinned affine 3-flat `[1,2,4,7,8,11,13,14]` | 15 | 6,510 |
| 8 | unpinned affine 3-flat `[1,2,4,7,8,11,13,14]` | 23 | 26,040 |
| 9 | unpinned affine 3-flat `[1,2,4,7,8,11,13,14]` | 63 | 13,020 |

Here an atom is the bit mask in the local coordinate order of its scope.
The other 22 reduced costs are zero. Thus complementary slackness explains
why the exact primal witness uses only the remaining quotient orbits.

## Where the identity comes from

The quotient has equality system `A z = b`, objective vector `c`, and dual
row vector `y`. The replay computes the exact rational relation

```text
c - A^T y =
  (0, 0, 434/5, 682/5, 124/5, 0, 0, 496/5,
   1736/5, 248, 0, ..., 0),
```

and `b^T y = 31/5`. Therefore, for any feasible `z`,

```text
c^T z = y^T A z + (c-A^T y)^T z
      = 31/5 + (c-A^T y)^T z.
```

The dual has only fifteen nonzero row multipliers. They are attached to two
normalization-orbit equations and thirteen consistency-orbit equations:

| row representative | multiplier |
| --- | ---: |
| normalization, scope `[1,2]` | `-124/5` |
| normalization, scope `[1]` | `31` |
| consistency, parent `[0,1,2,3,4,5,6,7]`, child `[0,1,2,3]`, atom `3` | `-248/5` |
| same parent and child, atom `7` | `-248/5` |
| parent `[0,1,2,3,4,5,6,7]`, child `[1,2,4,7]`, atom `0` | `-124/5` |
| same parent and child, atom `1` | `-62` |
| same parent and child, atom `15` | `-124/5` |
| parent `[1,2,4,7,8,11,13,14]`, child `[1,2,4,7]`, atom `0` | `124/5` |
| same parent and child, atom `1` | `62` |
| same parent and child, atom `3` | `-124/5` |
| same parent and child, atom `7` | `-248/5` |
| parent `[1,2,4,7,8,11,13,14]`, child `[1,2]`, atom `0` | `-124/5` |
| parent `[0,1,2,3,4,5,6,7]`, child `[1]`, atom `0` | `31` |
| parent `[0,1,2,3]`, child `[1,2]`, atom `1` | `-248/5` |
| parent `[1,2,4,7]`, child `[1,2]`, atom `3` | `-124/5` |

The table is a readable projection of the exact quotient certificate; the
independent replay remains the authoritative check of every coefficient and
orbit multiplicity.

## What this does and does not establish

This is a compact explanation of one finite rational optimum. It does not
identify a new general proof system, prove a scaling law, or resolve P versus
NP. The identity is useful because it exposes the lower bound as a positive
combination of six explicitly named quotient masses rather than as an opaque
2,174-variable full-model computation.

## Exact reproduction

From this directory run:

```text
python REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py
python -m unittest -v test_reed_muller_level_d_affine_overlap.py
```

The `test_compact_dual_identity` test reconstructs `A`, `b`, and `c` and
requires the six reduced costs and the dual objective above using exact
`Fraction` arithmetic.
