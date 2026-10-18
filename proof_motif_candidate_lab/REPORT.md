# Proof-Motif Candidate Discovery Lab

**Status:** Executed research prototype. No proof of P=NP or P!=NP.

## What changed

The previous interpolant portfolio could choose among XOR/PB/literal/CNF candidates once
those candidates existed.

This lab attacks the missing step: **candidate discovery without benchmark-family labels**.

The miner receives only:
- clauses / proof leaves;
- resolution structure that it constructs or is given;
- trusted theory certificates;
- recurrence of verified proof motifs.

Structural similarity may propose a candidate, but only an exact proof/certificate checker
may authorize it.

## Motif vocabulary implemented

### Equality quotient

Detect both binary directions

    not x OR y
    x OR not y

and union them into verified equivalence classes.

One-way implications are not accepted as equality.

### AMO / PB

Build the graph of all-negative binary clauses. A connected component is admitted as
at-most-one only when it is a complete clique, giving every pairwise conflict clause.

A near-clique missing one edge is rejected.

### XOR3

Group ternary clauses by exact support. Four full-width clauses are accepted as parity only
when the four excluded assignments have one common parity.

Same-support/same-count non-parity truth tables are rejected.

### ITE

Group width-4 clauses by exact support and test all constant-many role permutations against

    z = ite(c,a,b).

Only the exact eight-clause truth-table relation is accepted.

### OR -> unit proof macro

For a positive clause

    r OR x_2 OR ... OR x_w

and every spoke

    r OR not x_i,

the miner builds and replays the resolution chain proving the unit `(r)`.

It then canonicalizes the ancestor proof under variable renaming. Repeated normalized
signatures are counted as reusable proof motifs.

## Positive scaling

The 256-block XOR fixture was recovered as 256 exact XOR blocks.

The repeated Hall/implication family was mined up to 1,024 groups. The largest actual
proof-fusion run in the package has:

    groups                         = 256
    group width                    = 8
    proof log entries              = 4097
    source clauses visible to miner= 2048
    OR->unit macros rediscovered   = 256
    common proof-signature reuse   = 256
    derived source units           = 256
    receiver theory certificate   = AFFINE
    automatically proposed object = XOR_INTERPOLANT.

The miner is not told that the benchmark is "Hall + parity". It discovers the unit-producing
proof motifs from the source clauses, then consumes the verified affine receiver row.

## Source-driven candidate catalog

Verified source motifs become typed facts:
- equality relation;
- PB at-most-one;
- XOR relation;
- ITE gate;
- derived Boolean unit.

An unrelated receiver assignment can then test which typed facts it falsifies.

The mixed corpus contains all motif types simultaneously. It produced 49
verified candidates; two closed the supplied receiver assignment, and the declared
description-cost selector chose XOR.

## Adversarial controls

The lab includes:
- incomplete AMO cliques;
- one-way fake equivalences;
- 200 ternary same-support/same-count non-parity blocks;
- 150 four-variable same-support/same-count non-ITE blocks;
- repeated proof families with 10 deliberately broken spokes;
- forged/untrusted affine certificates;
- valid but non-contradictory affine/PB certificates;
- XOR and ITE blocks with one defining clause removed.

All exact semantic decoys were rejected. In the 100-group repeated-proof control, exactly
90 intact OR macros were admitted.

This does **not** establish a meaningful statistical false-positive rate on arbitrary SAT
instances; the controls are constructed adversarial fixtures.

## Actual proof-log integration

The package includes the earlier proof-producing affine+matching fusion engine.

From that real proof log:
1. Hall and equality proof lemmas are extracted as the source corpus.
2. Repeated OR->unit proof motifs are rediscovered.
3. Their heads become verified source facts.
4. The receiver's affine proof certificate is independently read from the trusted GF(2)
   theory row.
5. The miner computes the parity of the derived units.
6. Because it contradicts the receiver row, an XOR interpolant is proposed.

Flipping the affine certificate's RHS without adding that row to the trusted theory database
causes the proposal to be rejected.

## Complexity of the current implementation

All implemented discovery passes are polynomial in the explicit proof/clause input:

- binary-equivalence indexing: polynomial / near-linear hashing;
- fixed-arity XOR and ITE grouping: linear grouping plus constant-size truth-table tests;
- AMO clique certification: polynomial in its binary conflict graph;
- OR-collapse search: clause hashing plus O(w^2) work per width-w positive clause in the
  current implementation;
- normalized subproof hashing: linear in the visited subproof;
- trusted affine/PB receiver-certificate checks: polynomial.

There is no SAT-equivalence oracle hidden inside the miner.

## Relation to current SAT work

This direction is close in spirit to SAT 2026 work on globally factoring XOR and ITE gates
from learned clauses using Extended Resolution. The objective here is different: mined
structure becomes a candidate **communication/interpolant language** as well as a possible
proof macro.

## What remains hard

The current vocabulary is intentionally small and exact.

It will miss:
- XOR/circuit structure encoded indirectly through auxiliaries;
- optimized ITE encodings not present as direct truth-table blocks;
- large semantic macros with no local syntactic witness;
- relations requiring high-dimensional or global discovery;
- useful candidates whose discovery is itself NP-hard.

Therefore this lab closes the "benchmark labels" loophole for several important motifs,
but it does not prove that the candidate portfolio is complete.

The next serious target is **adaptive vocabulary growth**:
mine repeated residual proof fragments, synthesize a bounded candidate relation from the
fragment, and demand an independently checkable semantic certificate before adding a new
candidate language.


## Classical feasible-interpolation hard control

The permanent control suite now includes small instances of the standard
**clique-vs-coloring** interpolation template.

Shared variables describe graph edges.

- A uses local selector variables to assert that the graph contains a k-clique.
- B uses local coloring variables to assert that the graph is (k-1)-colorable.

The A/B conjunction is inconsistent because a k-clique needs k distinct colors.

For the small instances n<=6 used here, separation was checked directly over every graph
assignment.

The current motif vocabulary was then run independently on A and B.

Results:
- it produced no candidate whose support lies entirely in the shared graph-edge variables;
- for k=4 it did rediscover local B-side color AMO constraints;
- those local PB macros did not become shared interpolants.

This is the intended hard outcome.

Clique-coloring formulas are a classical feasible-interpolation lower-bound template in
proof complexity. The tiny instances here do **not** reproduce the asymptotic circuit/proof
lower bounds. Their role is to verify that local motif mining does not falsely claim that a
compact shared explanation has been found.

So the candidate miner now has both:
- positive cases where proof motifs expose the right shared language;
- a standard interpolation template where the current vocabulary genuinely stalls.
