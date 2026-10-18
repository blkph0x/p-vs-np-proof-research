# A precise obstruction to direct-terminal min-cut parity gadgets

2026-10-18. This is an established graph-representability restriction, with a
self-contained proof and finite controls. No novelty or P-versus-NP claim is
made. The primary reference is Kolmogorov and Zabih, *What Energy Functions
Can Be Minimized via Graph Cuts?* (2004): Definition 3.1 permits auxiliary
vertices and additive constants, and Section 6 gives a necessary regularity
condition. [Author-hosted paper](https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf).

## Model and theorem

Take any finite directed graph with nonnegative capacities, fixed source s
and sink t, one designated vertex for each Boolean input x_i, and any number
of free auxiliary Boolean vertices y. Zero means the source side; one means
the sink side. Define the terminal energy by

    f(x) = c + min_y Cut(x,y),

for any constant c. Undirected nonnegative edges are included by replacing
each with two opposite arcs. Capacities may be arbitrary finite nonnegative
reals; the executable controls use exact integers and rationals.

**Theorem.** Every such terminal energy is submodular:

    f(x) + f(x') >= f(x AND x') + f(x OR x').

**Proof.** An arc u->v contributes w(1-z_u)z_v. Its two-variable table has
values (0,w,0,0) in order (00,01,10,11), so its submodularity inequality is
0<=w. Fixing the source/sink yields constants or unary terms, which satisfy
the lattice inequality with equality. Nonnegative sums therefore make the
full cut energy F(x,y) submodular.

More generally, partial minimization preserves submodularity. Choose auxiliary
minimizers a for x and b for x'; they exist because the graph is finite. Then

    f(x)+f(x')-2c
      = F(x,a)+F(x',b)
      >= F(x AND x', a AND b)+F(x OR x', a OR b)
      >= f(x AND x')+f(x OR x')-2c.

Thus adding any number of free auxiliary vertices cannot remove the
inequality. Parallel arcs and zero capacities cause no exception.

## Three-bit parity is excluded

Let M>0, and require cost zero on even triples and cost M on odd triples.
Take x=110 and x'=101. Both costs are zero, but their meet is 100 and their
join is 111, both with cost M. Submodularity would require 0>=2M, impossible.

The odd-parity version also fails: x=100 and x'=010 have zero cost, whereas
their meet 000 and join 110 each cost M. Complementing any fixed subset of
the three input bits merely changes the desired parity by the parity of the
complement mask. Hence neither version becomes representable by choosing
fixed input polarities. Input permutations, additive constants, and unary
terms do not repair the violated inequality. This concerns one direct input
bit per terminal, with optional fixed polarity.

The zero set gives a slightly stronger statement: minimizers of a submodular
function are closed under meet and join. The same pairs therefore exclude
any energy that assigns a common minimum to exactly the desired parity
triples and strictly larger costs to all other triples, even if the positive
penalties are unequal. A uniform approximation to the 0/M truth table must
have maximum absolute error at least M/2, since the four-entry inequality
otherwise still fails.

## What this does not exclude

One-hot encodings and externally restricted validity domains change the
model. The valid encodings need not be closed under meet and join, so the
displayed logical-input argument does not automatically transfer. For a
concrete control, encode a bit a as (a,1-a) and b as (b,1-b). A unit undirected
cut edge between a and 1-b is submodular on all four encoded vertices, but
restricts to [a=b], a nonsubmodular function of the two logical bits. This
does not enforce the one-hot validity domain in an unconstrained cut or
construct a three-bit parity reduction. A proposed reduction must supply
that missing validity, decoding, and objective argument.

Perfect matching is another distinct model. Take zero-cost K4 with three
port vertices and one internal vertex. Input bit one means its port is
already matched outside and is deleted from the internal matching problem.
The remaining complete graph has a perfect matching exactly when an even
number of ports were deleted. Thus this simple gadget realizes even-parity
*feasibility*, with internal minimum cost zero when feasible. The matching
counts are three at input 000 and one at each weight-two input; no equal
counting signature is asserted. This explicitly prevents interpreting the
cut obstruction as a blanket prohibition on graph parity gadgets.

A matching parity gadget alone does not prove that arbitrary instances can
be composed while preserving variable consistency, nonzero semantics, and
the original additive cost. Those are separate required equivalences. The
theorem also says nothing against T-joins, labelled joins, global matching
algorithms, nonlinear decoding maps, or arbitrary decision reductions. It
rules out the stated direct-terminal cut truth-table representation, not
general polynomial algorithms and not P=NP.

## Reproducible finite controls

`validate_gadgets.py` enumerates all directed graphs with zero to three input
terminals, zero to two auxiliaries, at most three useful arcs, and capacity
one or two on each present arc. It omits constant/zero-contribution arcs;
it does **not** enumerate all graphs of those dimensions with arbitrary
edge counts or capacities. All auxiliary assignments are evaluated directly.

The audit passed for 60,988 graphs, 1,466,473 full cut assignments, and
3,164,719 terminal-pair submodularity checks. It also verifies all eight input
complement masks for each parity target, the K4 matching feasibility table,
and the restricted one-hot example. Six unit tests passed, including exact
rational capacities, directed-cut conventions, and malformed inputs.
`RESULTS.json` records the exact counts and the validation source hash.

Run from this directory:

    python -m unittest -v test_gadgets
    python validate_gadgets.py

These finite controls support the proof and guard against model confusion;
they do not supply the general theorem by enumeration.
