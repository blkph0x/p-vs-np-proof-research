# Non-graphic internally 4-connected high-width controls

Each saved matrix is a full-rank binary column representation with the seven
columns `1,2,3,4,5,6,7` in its first three rows. Those columns are all seven
nonzero vectors of `GF(2)^3`, so their restriction is the Fano matroid `F7`.

`F7` is not graphic. A simple graphic matroid of rank three is represented by
a loopless graph with four vertices after deleting isolated components, and it
has at most `binomial(4,2)=6` distinct edges. `F7` is simple, has rank three,
and has seven elements. Graphic matroids are closed under restriction, so any
matroid containing this restriction is non-graphic.

For a binary column matroid, the connectivity function is

    lambda(S) = rank(S) + rank(E-S) - rank(E).

The C++ audit enumerates every unordered nontrivial cut for `n=18,20,22,24,26`.
It rejects every 1-separation and every 3-separation of order two, and it
rejects every order-three separation whose smaller side has more than three
elements. A three-element order-three side is permitted only when it is a
triangle or triad. Therefore the saved matrices are internally 4-connected
under the standard binary-matroid definition.

Every variable ordering has a prefix of exactly `floor(n/2)` coordinates.
The minimum audited connectivity among those balanced cuts is consequently a
lower bound on every trellis/pathwidth ordering. The saved minimum-distance
values are computed by complete enumeration of all `2^rank-1` nonzero messages.

This is an adversarial family for the current representation route: it is
non-graphic, internally 4-connected, and has a certified high-width cut while
retaining an explicit non-graphic certificate. It is not a lower bound for
minimum distance, SAT, or P versus NP; no native polynomial algorithm is
claimed for these controls.
