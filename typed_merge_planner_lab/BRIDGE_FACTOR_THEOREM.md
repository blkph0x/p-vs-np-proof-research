# Exhaustive one-bridge Horn/affine obstruction

Let `E(a,b,c)` be the positive exact-one relation

    E = {100, 010, 001}.

Its positive constraint-satisfaction problem is positive 1-in-3 SAT, an
NP-complete problem. Test whether a single auxiliary Boolean bridge `z` can
split this relation into two bounded factors, with one factor arbitrary Horn
(AND-closed) and the other arbitrary affine (minority-closed).

There are two scope orientations:

    L(a,b,z) AND R(c,z),
    L(a,z) AND R(b,c,z),

and either factor may be the Horn factor. The exhaustive search enumerates
every relation on two or three bits, tests the defining closure directly, and
projects every factor pair over `z`.

The exact counts are:

| orientation | factor counts | pairs | distinct projections | E pairs |
| --- | ---: | ---: | ---: | ---: |
| Horn(3), affine(2) | 122 × 12 | 1,464 | 170 | 0 |
| affine(3), Horn(2) | 52 × 14 | 728 | 88 | 0 |
| Horn(2), affine(3) | 14 × 52 | 728 | 88 | 0 |
| affine(2), Horn(3) | 12 × 122 | 1,464 | 170 | 0 |

Thus no one-bridge factorization in this complete finite family represents
`E`. The two scope orientations and factor swaps exhaust the placement of one
bridge between a two-variable side and a one-variable side, up to permutation
of the symmetric exact-one variables.

This is a bounded composition obstruction. It does not rule out two or more
bridges; in fact the companion
`TWO_BRIDGE_FACTOR_THEOREM.md` gives an explicit two-bridge factorization.
Different tractable languages, non-primitive-positive encodings, promises, and
general SAT algorithms remain outside both finite searches. The saved artifact
and an independent replay bind every enumerated relation and source hash.
