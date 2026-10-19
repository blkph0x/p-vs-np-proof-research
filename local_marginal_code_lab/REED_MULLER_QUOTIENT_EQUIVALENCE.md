# Quotient-equivalence theorem for the full RM(2,5) model

This note states the mathematical fact used by the full level-eight replay. It
separates the symmetry argument from the code that enumerates the 2,174
variables and 27,926 rows.

## Theorem

Let `G = GL(5,2)` act on the 32 coordinates of `F_2^5`, fixing coordinate zero.
Let `L` be the pinned RM(2,5) projection-marginal LP with one supported table
for every coordinate scope of size at most eight, normalization equations, and
all exact containment-marginal equations. Let `L^G` be the restriction to
tables invariant under the induced scope and atom actions of `G`. Then

```text
opt(L) = opt(L^G).
```

The orbit-indexed LP in
`REED_MULLER_LEVEL_D_FULL_RESULTS.json` is a coordinate representation of
`L^G`; its saved rational primal is therefore a feasible point of `L`, not a
different relaxation.

## Proof

The pinned RM(2,5) support is preserved by every element of `G`, so `G`
permutes scopes, supported atoms, normalization equations, containment
equations, and local table coordinates. The singleton objective is also
preserved because `G` fixes the pin and permutes the other 31 coordinates.

Given any feasible point `x` of `L`, define its group average

```text
        x_bar = (1 / |G|) * sum_{g in G} g.x.
```

The feasible region is defined by linear equalities and nonnegativity, so it is
closed under each `g` and under averaging. Thus `x_bar` is feasible and
`G`-invariant. Objective preservation gives `obj(x_bar) = obj(x)`. Hence an
optimum of `L` has an invariant optimum, proving `opt(L) >= opt(L^G)` while
the restriction inclusion gives `opt(L^G) >= opt(L)` for the minimisation
orientation used here. Equality follows.

For an invariant table, every supported atom in one orbit has one common mass.
The normalization and containment equations can likewise be averaged over
the stabilizer of a representative scope and containment pair. Enumerating
those stabilizer orbits gives exactly one quotient variable or row per orbit.
The coefficient of a quotient row is the number of original equations in the
corresponding orbit that contain that variable. Therefore lifting a quotient
assignment by assigning its orbit value to every member gives a feasible
invariant point, and averaging any full point gives the reverse map.

The implementation independently reconstructs the pinned support, scope
orbits, stabilizer closures, variable orbits, row orbits, and coefficients.
The code is evidence for the finite enumeration and its exact arithmetic; it
is not a proof-assistant formalisation of this theorem. The full trust chain
and its remaining boundary are recorded in
[`REFEREE_RESPONSE_2026_10_20.md`](../REFEREE_RESPONSE_2026_10_20.md).
