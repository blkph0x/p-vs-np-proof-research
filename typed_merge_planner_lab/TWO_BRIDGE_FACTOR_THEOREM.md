# Two bridges cross the Horn/affine boundary

Let `E(x,y,w)` be the positive exact-one relation

    E = {100, 010, 001}.

The one-bridge exhaustive search found no Horn/affine factorization. With two
shared existential Boolean bridges `z0,z1`, the boundary changes: every one of
the four factor assignments and scope orientations has an exact factorization.

The complete search enumerates every relation on three and four bits directly
from AND-closure or minority-closure. Its four searches have these results:

| orientation | factor counts | pairs | distinct projections | E pairs |
| --- | ---: | ---: | ---: | ---: |
| Horn(3), affine(4) | 122 × 308 | 37,576 | 252 | 8 |
| affine(3), Horn(4) | 52 × 4,960 | 257,920 | 230 | 2 |
| Horn(4), affine(3) | 4,960 × 52 | 257,920 | 230 | 2 |
| affine(4), Horn(3) | 308 × 122 | 37,576 | 252 | 8 |

An explicit witness uses the `ONE_LEFT` layout:

    H(x,z0,z1) = {000, 110, 001}
    A(y,w,z0,z1) = {0100, 0010, 1001, 1111}.

`H` is Horn: it is equivalently `x = z0` together with
`x -> not z1`. `A` is affine, with equations

    y xor z1 = 0,
    w xor z0 xor z1 = 1.

If `x=1`, `H` forces `(z0,z1)=(1,0)`, and `A` forces `(y,w)=(0,0)`.
If `x=0`, the two choices `(z0,z1)=(0,0)` and `(0,1)` produce respectively
`(y,w)=(0,1)` and `(1,0)`. Therefore

    exists z0,z1 . H(x,z0,z1) and A(y,w,z0,z1)

is exactly `E(x,y,w)`.

This gives an immediate complexity consequence. Replace every positive
exact-one clause by this fixed Horn constraint, this fixed affine constraint,
and two fresh bridge variables. The resulting mixed Horn+affine satisfiability
problem is NP-hard; it is in NP because a full assignment checks both
constraints. Thus a planner that treats two-bridge Horn/affine composition as a
uniformly easy operation would already solve positive 1-in-3 SAT.

The two orientations are

    L(x,z0,z1) AND R(y,w,z0,z1),
    L(x,y,z0,z1) AND R(w,z0,z1),

and each orientation is run with both assignments of the Horn and affine
factor. The result is constructive and route-specific. It does not show that
three or more bridges are necessary in every encoding, and it does not rule
out a general SAT algorithm, a different tractable language, or a
representation whose bridge discovery has a separate polynomial guarantee.
The saved artifact and independent replay bind all counts, the witness, and
source hashes.

Together with the complete one-bridge rejection, this proves that the minimum
number of shared existential bits in this two-factor Horn/affine architecture
is exactly two for positive exact-one.

The companion width theorem shows that applying this gadget clause by clause
preserves the original exact-one primal graph's pathwidth within an additive
two. Thus the local NP-hardness reduction does not hide a large structural
width blow-up or a width collapse; its remaining difficulty is the global
interaction of the original clauses.
