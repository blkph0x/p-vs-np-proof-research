# Fixed-width affinity of existential CNF projections

Status: complete written proof with independently implemented finite controls.
This is not proof-assistant verification. **Novelty is UNKNOWN.** The result
classifies a restricted input family; it is not a complexity-class separation
or a polynomial-time SAT algorithm.

## Decision problem and exact convention

Fix an integer `k>=1` once and for all. An input is a Boolean CNF `F(x,y)`
with exactly `k` visible variables `x` and an explicitly listed, disjoint
set of hidden variables `y`. Every literal belongs to one of these lists.
Input length includes the lists, clauses, and binary labels, so is at least
the number of variables. Unused variables, empty conjunctions, and empty
clauses have their ordinary meanings.

Let `R_F={x in F_2^k : exists y F(x,y)}`. The language `AFF_k` accepts
exactly when `R_F` is a **nonempty affine coset**. In particular, it rejects
the empty relation. There is no promise of nonemptiness, affinity, known
dimension, or a supplied witness.

**Theorem.** For every fixed `k>=1`, `AFF_k` is complete for `BH_(2k-1)`
under deterministic polynomial-time many-one reductions.
For `k=0`, the same nonempty-affinity problem is NP-complete.

| Fixed visible width | Classification |
| ---: | --- |
| 0 | NP-complete |
| 1 | NP-complete |
| 2 | BH3-complete |
| 3 | BH5-complete |
| 4 | BH7-complete |
| k>=1 | BH_(2k-1)-complete |

These are completeness statements, not claims that consecutive Boolean
hierarchy levels are distinct.

## Boolean-hierarchy convention and inherited framework

Use the standard nested-difference definition

```text
BH1 = NP
BH_(d+1) = { A \ B : A in NP and B in BH_d }.
```

Here `BH2=DP`; it is not the second level of the polynomial hierarchy.
The definition and standard complete languages appear in Richard Chang,
[*Bounded Queries, Approximations and the Boolean Hierarchy* (1999),
Section 2, Definition 1 and the discussion preceding Definition 3,
printed page 3 / PDF page 4](https://userpages.cs.umbc.edu/chang/papers/bqabh/npfsat.pdf).
That primary author manuscript treats constant levels as nested differences
of NP languages. We use that framework and give both reductions below.

For fixed `d`, every language in `BH_d` can be written

```text
A1 \ (A2 \ (... \ Ad)),    Ai in NP.
```

The sets need not initially be nested. Put
`Yi=A1 intersect ... intersect Ai`. These sets are in NP and satisfy
`Y1 superset ... superset Yd`. For each input, the nested difference
accepts exactly when its longest initial sequence of true `Ai` predicates
has odd length. This is also the maximum true `Yi` index, with maximum
zero when no predicate is true. Hence the nested difference is unchanged.

The corresponding nested-difference SAT language is `BH_d`-complete:
replace each NP predicate by its polynomial-time reduction to SAT. On
arbitrary CNFs `G1,...,Gd`, it accepts when

```text
SAT(G1) AND NOT (SAT(G2) AND NOT (... SAT(Gd)))
```

is true. Every source tuple is allowed. Later satisfiable formulas after
the first unsatisfiable one do not affect this expression.

The existing [variable-width theorem](../COMPLEXITY_THEOREM.md) classifies
the unrestricted-width problem as Pi2P-complete. The earlier
[fixed-width report](../REPORT.md) proves SAT and SAT--UNSAT hardness
and a constant nonadaptive-query upper bound. The present proof completes
the fixed-width classification. It does not replace the variable-width
quantified argument. No priority claim is made for this application of the
established Boolean-hierarchy framework.

## A finite alternating-chain lemma

For a subset `S` of `F_2^k`, let `a(S)` be one if `S` is nonempty affine,
and zero otherwise. Consider a strict inclusion chain

```text
S1 proper-subset S2 proper-subset ... proper-subset Sj
```

whose values alternate `1,0,1,0,...`. Every set in such a chain is nonempty.

Two consecutive affine stages have strictly increasing affine dimension:
one contains a nonaffine intermediate set and is properly contained in
the next affine stage. There cannot be a nonaffine intermediate set inside
an affine line, because its nonempty subsets have one or two points and
are affine. Thus, if the first affine stage is a singleton, the second
has dimension at least two. Otherwise the first has dimension at least one.
After that, dimensions increase by at least one each time.

Consequently the number of affine stages is at most `k`. If there are
`k` affine stages, the last has dimension `k` and is the full cube, so
no further stage is possible. A chain ending nonaffine therefore has at
most `k-1` affine stages. Every alternating chain has length at most
`2k-1`. For `k=1`, the only nonaffine subset is empty, so the same bound
is one.

The bound is attained. Let `H_d=span(e1,...,ed)`. For `k>=2`, use

```text
R0 = empty
R1 = {0}
R2 = {0,e1,e2}
R3 = H2
R_(2d-2) = H_(d-1) union {ed},    d=3,...,k
R_(2d-1) = H_d,                  d=3,...,k.
```

The three-point set is nonaffine. The other even stages have
`2^(d-1)+1` points, which is not a power of two, and so are nonaffine.
Every odd stage is affine. The final stage is the full cube.
For `k=1`, take `R0=empty` and `R1=F_2`.

Refining a strict chain into single-point insertions preserves at least
its stated changes of affinity. Conversely, retaining just the changes
along any such refined chain gives an alternating chain. Thus maximum
alternating length also equals the maximum number of changes along
single-point insertion paths from the empty set, as used in the finite DP.

## Membership in BH_(2k-1)

For an input CNF and an integer `1<=j<=2k-1`, let `L_j` assert that
`R_F` contains an alternating chain of length `j` as above.

Each `L_j` is an NP language **for fixed k**. A certificate explicitly
lists the chain's subsets and, for each listed visible point, a hidden
assignment satisfying the original CNF. At most `(2k-1)2^k` points need
such witnesses; this is a constant depending on the fixed language.
Inclusion and each subset's affinity can be checked directly on its
constant-size truth table. The verifier does not need to prove that a
listed subset is all of `R_F`.

The languages are nested: `L_(j+1)` implies `L_j` by deleting the last
stage. Let `t` be the maximum true index, or zero if none is true.
If `R_F` is empty, `t=0`. Otherwise a singleton gives `t>=1`.
In a longest chain, its last set must have the same affinity value as
`R_F`: if the values differed, appending `R_F` would be a strict,
longer alternating chain. Hence `R_F` is nonempty affine exactly when
`t` is odd.

The chain lemma gives `t<=2k-1`. Therefore

```text
AFF_k = L1 \ (L2 \ (... \ L_(2k-1))).
```

This proves membership in the stated Boolean-hierarchy level.
For `k=0`, the visible cube contains one empty tuple. Its projection is
nonempty affine exactly when the original CNF is satisfiable.

## Total many-one hardness reduction

Let `d=2k-1` and start with arbitrary source CNFs `G1,...,Gd` for the
nested-difference SAT language. Rename their hidden variable sets
disjointly. Define the satisfiability predicates

```text
Phi_i = G1 AND ... AND Gi.
```

Because the variable blocks are disjoint, `Phi_i` is satisfiable exactly
when the first `i` source formulas are each satisfiable. These predicates
are nested regardless of the source truth pattern.

Use the fixed maximal chain `R0,...,Rd` above. Each visible point `p`
has an entry stage `e(p)=min{i:p in Ri}`. Add one hidden selector `s_p`
for each of the `2^k` visible points and write the following CNF:

1. The clause `OR_p s_p` requires a selected point.
2. For each `p` and each visible coordinate, add the implication
   `s_p => (x_coordinate = p_coordinate)`.
3. For each `p`, each `i<=e(p)`, and each clause `C` of the renamed `Gi`,
   add `NOT s_p OR C`.

No explicit at-most-one selector clauses are needed. Distinct selected
points would require different values of some visible coordinate and
are inconsistent. This observation also covers the single selector at
width zero.

For a fixed visible point `p`, all other selectors must be false and
`s_p` must be true. The remaining constraints are precisely the source
prefix through `e(p)`, plus unrestricted unused variables. Thus

```text
p is in the projection  iff  Phi_(e(p)) is satisfiable.
```

Let `t` be the longest satisfiable source prefix, possibly zero. The
projection is exactly `Rt`. Its nonempty-affinity value is true exactly
when `t` is odd, which is the source nested-difference answer.
This is a total many-one reduction. No SAT oracle is used to construct it
and no promised nesting of the input formulas is assumed.

If the source formulas contain `N` variables, `c` clauses and `ell`
literal occurrences in total, the target has

```text
k + 2^k + N variables,
at most 1 + k*2^k + 2^k*c clauses,
at most 2^k + 2*k*2^k + 2^k*(ell+c) literal occurrences.
```

Writing renamed labels adds the ordinary logarithmic bit cost. Since
`k` is fixed, these bounds are polynomial in the explicit source input.
They are not a uniform polynomial bound when `k` is allowed to grow.
Together with membership, this proves completeness. At widths zero and
one, a single source SAT instance and the same selector construction
give the NP lower bound.

## Scope and consequences

Changing the convention to accept the empty affine relation changes the
language. The proof and code here consistently reject it; they do not
silently import the empty-allowed convention from a different recognizer.
The non-affine-or-empty complement is coBH_(2k-1)-complete for fixed
`k>=1`, by complementing the same many-one reductions.

A deterministic polynomial-time solver for any one of these fixed-width
languages would imply P=NP, because every stated level contains NP.
Conversely P=NP would make all these finite Boolean combinations
polynomial-time decidable. This equivalence supplies no algorithm proving
either possibility and no unconditional superpolynomial lower bound.

In the membership proof, the chain certificate can list exponentially
many visible points as a function of `k`. In the hardness reduction,
there are `2^k` selectors. These facts prevent promotion of this proof
to a fixed Boolean-hierarchy bound for unrestricted width. They are
consistent with the separate Pi2P-completeness theorem.

## Independent finite evidence and reproduction

`chain.py` uses affine rank/cardinality and backward deletion transitions
on the subset lattice. `verify.py` imports no producer and uses translated
binary-XOR closure and forward insertion transitions instead. Both
enumerate every relation at widths zero through four: 65,814 relations,
including 65,812 at widths one through four. The computed maximum depths
are respectively `1,1,3,5,7`; parity is checked at every relation.
The finite computations support, but do not replace, the all-k chain proof.

The SAT-gadget campaign contains 1,060 external originals:

- four zero-visible empty-formula, empty-clause and hidden-variable controls;
- all 512 two-variable CNFs over the nine distinct non-tautological clauses
  (including the empty clause), at visible width one;
- all 512 triples of one-variable CNFs over the empty and two unit clauses,
  at visible width two;
- all 32 arbitrary source truth patterns for five zero-variable CNFs,
  at visible width three.

The independent checker reconstructs the original campaign and every
clause and variable block. It exhausts all assignments of every resulting
gadget, tests the projection by closure, and separately evaluates the
source nested difference. It checks 344,076 full gadget assignments and
5,286 full source assignments. These counters count whole-formula evaluations;
they do not measure literal scans, bit operations, or total runtime.

Tests reject missing or duplicated coverage, changed original inputs,
rebound input hashes, altered clauses, shared variable blocks, false
projection/affinity/depth claims, and malformed types. Empty relations,
empty variable lists, unused variables, and unrestricted source truth
patterns are explicit controls. The implementation bounds its enumeration
to visible width four and at most eighteen complete gadget variables;
larger requested experiments raise an error without claiming a decision.
This finite program is not an efficient SAT procedure.

From this directory, verify committed evidence before regenerating:

```text
python verify.py
python -B -m unittest -v test_hierarchy
python -B -O -m unittest -v test_hierarchy
```

To regenerate the certificate, independent replay, and both test transcripts:

```text
python -B run_experiments.py
```

`RESULTS.json` records exact counters, the compressed certificate digest,
test exit statuses, transcript digests, and source hashes before and after
the run. Text hashes decode strict UTF-8, normalize CRLF and lone CR to LF,
and hash the re-encoded text. No other whitespace, Unicode, or BOM
normalization occurs. This binds the saved source across Git newline
conversion; it does not independently certify historical execution time.
The checker replays original semantic claims rather than treating a matching
hash or a producer status as proof.
