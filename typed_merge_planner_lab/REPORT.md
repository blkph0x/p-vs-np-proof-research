# Typed Merge-Compatibility Planner

**Status:** Executed research prototype. No proof of P=NP or P!=NP.

## Main change

The project no longer treats "interface complexity" as one scalar.

Every message/region now has a **type**, and every merge is classified by both:

1. the semantic languages of its children;
2. the amount of shared information exposed at that particular decomposition cut.

The planner distinguishes four cases:

    POLY_CLOSED
        the languages share a tractable closure invariant;

    EXPLICIT_TT_BRIDGE
        the language pair may be hard/unknown in general, but this particular Boolean
        interface is small enough to enumerate exactly;

    EXTENSION_QUOTIENT
        raw Boolean width is large, but a certified polynomial-size extension-equivalence
        quotient exists;

    HARD_BARRIER / UNKNOWN
        no currently justified polynomial combination route.

This makes theory-combination complexity a first-class part of decomposition search.

## 1. Automatic Schaefer classifier for bounded relations

For an explicit Boolean relation, the engine checks six classical Schaefer conditions:

    ZERO-valid
    ONE-valid
    AND/Horn closure
    OR/dual-Horn closure
    majority/bijunctive closure
    minority/affine closure.

Examples recovered exactly:

| relation | discovered signature |
|---|---|
| implication | AND;MAJ;ONE;OR;ZERO |
| equality | AND;MAJ;MIN;ONE;OR;ZERO |
| even parity 3 | MIN;ZERO |
| odd parity 3 | MIN;ONE |
| AMO3 | AND;MAJ;ZERO |
| EXACT1-3 | (none) |
| NAE3 | (none) |

For two exact finite Boolean relations:
- if their signatures share any Schaefer tractability condition, conjunctions of constraints
  from that fixed language remain in a polynomial SAT class;
- if the common signature is empty, Schaefer's dichotomy classifies the resulting fixed
  relation language as NP-complete.

For example:
- even and odd parity share `MIN`, so their union remains affine;
- EXACT1-3 has no tractable Schaefer signature, and repeated EXACT1-3 is the familiar
  NP-complete positive 1-in-3 language.

One subtle but useful result is that implication + even parity share ZERO-validity: all-zero
satisfies both languages, so that specific fixed-language combination is trivially
satisfiable.

## 2. Native theory combination graph

For large native theories we use guaranteed language metadata rather than enumerating truth
tables.

Current guaranteed closed types:

    HORN       -> AND
    DUALHORN   -> OR
    BIJUNCTIVE -> MAJ
    AFFINE     -> MIN.

Known hard edges currently recorded:

    HORN + AFFINE
        hard in general / outside one Schaefer tractable class;

    AFFINE + CARDINALITY
        contains binary-code minimum-distance decision.

Pairs without a theorem are deliberately marked `UNKNOWN_GENERAL`; the planner does not
silently declare them easy or hard.

## 3. Decomposition can turn a hard pair into a tiny bridge

The central controlled fixture contains four regions:

    H0: HORN on private H variables + 3 shared bits
    H1: HORN on the same private H variables
    A0: AFFINE on private A variables + the same 3 shared bits
    A1: AFFINE on the same private A variables.

Take 1,024 private variables on each side.

### Bad merge order

Merge H0 directly with A0 first.

The child boundaries expose both large private blocks plus the shared bits.

Since HORN+AFFINE is a hard-in-general pair and the explicit interface is far beyond the
polynomial truth-table budget, the declared tree has **no justified polynomial merge**.

### Good merge order

Merge

    H0 with H1

inside Horn first, and

    A0 with A1

inside affine first.

Both merges are polynomial regardless of their large internal boundaries because each
language is closed under its native operation.

After existentially eliminating the private variables, the two surviving messages share only

    3 Boolean bits.

The final hard Horn/Affine interaction is then handled by an exact

    2^3 = 8-state

truth-table bridge.

At private width 1024:

    structural input proxy       = 4106
    exact planner found route    = True
    exact max explicit width     = 3
    greedy max explicit width    = 3
    bad declared tree feasible   = False
    good declared tree feasible  = True.

So decomposition is now optimizing **where difficult theories are allowed to meet**.

## 4. Current bridge decisions

The bridge assessor reproduces several earlier experiments in one typed framework:

| scenario | merge | raw width | route |
|---|---|---:|---|
| matching + affine small | MATCHING × AFFINE | 3 | EXPLICIT_TT_BRIDGE |
| counting wide quotient | CARD × CARD | 2048 | EXTENSION_QUOTIENT (2049 states) |
| affine + cardinality | AFFINE × CARD | 40 | HARD_BARRIER |
| Horn + affine small | HORN × AFFINE | 3 | EXPLICIT_TT_BRIDGE |
| Horn + affine wide | HORN × AFFINE | 40 | HARD_BARRIER |
| affine + affine wide | AFFINE × AFFINE | 4096 | NATIVE_CLOSED |

The matching+affine row is not hypothetical: it corresponds to the automatically abstracted
permutation+XOR fixture, where the actual region boundary is three bits. The typed planner
therefore authorizes an eight-state exact bridge even though no general polynomial
MATCHING+AFFINE combination theorem is assumed.

## 4.5. One bridge is not enough for a canonical hard relation

The new exhaustive bridge audit targets the positive exact-one relation
`{100,010,001}`, whose constraint problem is NP-complete. It enumerates every
Horn relation on two or three bits and every affine relation on two or three
bits, then projects every pair through one existential bridge variable.

Both scope orientations and both factor assignments are covered. The four
searches inspect 1,464, 728, 728 and 1,464 factor pairs respectively; none
projects to exact-one. An independent implementation reproduces all counts and
binds the saved source hashes in `BRIDGE_FACTOR_REVIEW.json`.

This closes only the one-bridge Horn/affine pattern. More bridges, other native
languages, promises and non-primitive-positive encodings remain open.

## 4.6. Two bridges are already expressive enough

The next exhaustive search enumerates every Horn and affine relation on three
and four bits and projects every pair over two shared bridge bits. The four
orientations inspect 37,576, 257,920, 257,920 and 37,576 factor pairs. Exact-one
appears 8, 2, 2 and 8 times respectively; an independent replay reproduces the
counts and the saved witness.

One explicit factorization is

    H(x,z0,z1) = {000,110,001}
    A(y,w,z0,z1) = {0100,0010,1001,1111}.

`H` is Horn (`x=z0` and `x -> not z1`). `A` is affine
(`y xor z1 = 0` and `w xor z0 xor z1 = 1`). Eliminating `z0,z1` gives exactly
`{100,010,001}`. Replacing every positive exact-one clause with these two fixed
constraints and two fresh bridges proves that the mixed Horn+affine CSP is
NP-hard (and it is in NP).

This reverses the one-bridge result: the obstruction is a sharp bridge-budget
boundary, not evidence that mixed Horn/affine composition is impossible. A
planner must charge bridge discovery and the resulting global auxiliary
interaction; treating two-bridge composition as uniformly cheap would already
solve positive 1-in-3 SAT.

## 4.7. The local gadget does not remove global width

The fixed two-bridge replacement also has a structural width audit. For every
four-variable exact-one clause family, the transformed primal graph has exact
pathwidth between the original width and the original width plus two. The
independent replay checks all 16 formulas.

The all-size reason is graph-theoretic. Contracting the edge from the first
clause variable to its first bridge recovers the original clause triangle, so
the original primal graph is a minor of the transformed graph. Conversely, a
path decomposition of the original graph contains every clause triangle in a
bag; adjoining that clause's two bridge vertices in a fresh bag raises width by
at most two. Thus

    pathwidth(original) <= pathwidth(transformed)
                         <= pathwidth(original) + 2.

The factorization can make each local relation tractable, but it cannot erase
the global order-discovery problem represented by the original clause graph.
See `MIXED_BRIDGE_WIDTH_THEOREM.md` and its source-bound replay.

## 4.8. Proof-producing mixed-relation solver

The new relation-level frontier solver accepts arbitrary explicitly listed
Boolean relations and a supplied variable order. It records every boundary,
state and accepted transition, and the independent reviewer reconstructs the
same certificate without importing the solver. Its state bound is `2^w` per
cut, where `w` is the supplied boundary width.

All 16 four-variable positive exact-one reductions were solved through their
Horn/affine factors and matched direct brute-force satisfiability. This is a
useful positive algorithm for the parameterized class, while the width theorem
shows why it is not a uniform polynomial solver: the bridge gadget preserves
the original global width up to two.

## 4.9. Exact order discovery is now charged explicitly

The order oracle reconstructs a minimum-width variable order by subset dynamic
programming. Its recurrence is independently replayed, and the resulting order
is fed into the proof-producing relation DP. All 16 exact-one reductions retain
matching optimal widths, saved orders, subset counts and transition counts.

The oracle uses `O(n 2^n)` subset transitions and is deliberately labelled an
audit algorithm. The complete-graph control reaches width five on six variables
and evaluates all `2^6` subsets. This makes the missing global step visible:
local relation factorization, frontier solving and order discovery are three
separate costs.

## 5. Exact audit planner vs scalable greedy planner

The package contains two planners:

- an exponential subset DP for <=10 regions, used only as an audit oracle;
- a polynomial greedy merger used as the scalable proposal heuristic.

The Horn/Affine helper family is easy enough that both find the same width-3 route.

But the greedy heuristic is not complete.

A seven-region control was found after 180 random fixtures where:

    exact planner:
        cost               = 109
        max explicit width = 5

    greedy planner:
        no legal route under the same polynomial bridge budget.

The exact plan uses only explicit bridges of width <=5 plus one bijunctive closed merge.

This is the typed-theory analogue of the decomposition local minima found earlier:
automatic region discovery and a correct combination graph still do not make global
planning trivial.

## 6. What is theorem vs implementation

### Mathematical/theory-backed

- Schaefer classification of finite Boolean relation languages.
- Closure of a common polymorphism under conjunction / primitive-positive projection.
- Gaussian/affine, Horn, dual-Horn and bijunctive self-combination.
- NP-hardness of arbitrary AFFINE+CARDINALITY via minimum distance.
- The earlier explicit Horn+Affine NP-hard interaction.
- Exact truth-table bridge cost 2^k.
- Polynomiality of a supplied polynomial-size extension quotient.

### Implemented polynomial logic

- relation-signature inference for bounded truth tables;
- native pair knowledge base;
- exact bridge-budget check;
- greedy typed merge planner.

### Audit-only exponential logic

- exact subset planner over all merge trees for small region counts.

## 7. Strongest formulation reached

A merge is cheap only when the **typed conjunction/projection operation** is cheap.

Thus a potential universal theorem needs more than small messages and more than tractable
leaves.

It would need a polynomial-size decomposition such that every internal merge satisfies at
least one of:

1. both children share a tractable closure language;
2. the explicit shared Boolean interface is O(log n) / otherwise polynomially enumerable;
3. a polynomial-size extension-equivalence quotient is certified;
4. the hard language interaction has a polynomially bounded FPT/backdoor parameter;
5. a stronger native/global theory has a polynomial proof-producing combination procedure.

The current planner now checks the first three cases explicitly and marks known hard
violations instead of hiding them.

No theorem currently says arbitrary SAT always admits such a merge tree.
