# Affinity of an existential CNF projection

Status: written all-input proof with independently rebuilt finite regression
checks. **Novelty is not established.** This is an elementary classification
using standard closure and quantified-SAT facts, not a separation of complexity
classes or evidence that P versus NP has been resolved.

## Input, convention, and statement

An instance is a Boolean CNF `F(x,y)` together with explicit disjoint lists of
visible variables `x=(x_1,...,x_m)` and existential variables
`y=(y_1,...,y_l)`. The lists cover every literal. Input length includes the
lists, clauses, and binary variable labels; it is at least `m+l`. Width is
not supplied by a succinct exponential-length declaration.

Let `R_F={x : exists y F(x,y)}`. Define `AFFINE-PROJECTION` to accept exactly
when `R_F` is a **nonempty affine coset** over `F_2`. Empty relations are
rejected. Empty variable lists, empty conjunctions, and empty clauses have
their usual Boolean meanings.

**Theorem.** When visible width is part of the input, `AFFINE-PROJECTION`
is `Pi_2^P`-complete under deterministic polynomial-time many-one reductions.
Hardness holds for formulas with at most five literals per clause, even
under a promise that the projection contains zero and has full affine hull.

The promise concerns the projection, not a supplied solution. The membership
proof applies without the promise. No such classification is asserted here
for a fixed visible width.

## Closure characterization

A nonempty subset `R` of `F_2^m` is affine exactly when
`a XOR b XOR c in R` for every `a,b,c in R`.
This is the standard affine-closure characterization, appearing in
[Schaefer (1978), Lemma 3.1A](https://www.khoury.northeastern.edu/home/lieber/courses/csg260/f06/materials/papers/max-sat/p216-schaefer.pdf).

For completeness, choose `r in R` and translate: `W=R+r`. Then `0 in W`.
If ternary closure holds, applying it to `r+u,r+v,r` shows `u+v in W`
for all `u,v in W`. A set containing zero and closed under addition is a
linear subspace over `F_2`, so `R=r+W`. Conversely, adding three members of
a coset returns a member of that coset. Including nonemptiness is essential:
the empty set satisfies the closure condition vacuously.

## Membership in Pi_2^P

Use the following single universal-existential predicate:

```text
forall x1,x2,x3,y1,y2,y3
exists x0,y0,z:

  F(x0,y0) AND
  (NOT F(x1,y1) OR NOT F(x2,y2) OR NOT F(x3,y3)
                    OR F(x1 XOR x2 XOR x3,z)).
```

All blocks have length polynomial in the explicit input, and the matrix is
evaluated in polynomial bit time. If the relation is a nonempty affine coset,
choose any `(x0,y0)` satisfying `F`; whenever the three antecedent
assignments satisfy `F`, closure supplies a suitable `z`. Conversely, the
first conjunct forces a member of `R_F`, and applying the predicate to
witnesses for any three members establishes closure. Even a zero-length
universal block has one assignment, so it cannot vacuously bypass
nonemptiness. This proves membership.

The predicate need not be CNF to use the quantified definition of the
complexity class. Polynomial-time predicate evaluation is sufficient.

## Hardness by two guard bits

Start from a true-or-false quantified 3CNF instance
`Q = forall u exists v phi(u,v)`. This decision language is
`Pi_2^P`-complete; see the alternation and normal-form statements in
[Hemaspaandra (2004), section 2.3](https://arxiv.org/pdf/cs/0406006).
Introduce visible bits `a,b` and construct

```text
F_Q(a,b,u,v) = AND over clauses C of phi: (NOT a OR NOT b OR C).
```

Project only `v`. The resulting relation contains every `(a,b,u)` with
`(a,b) != (1,1)`. A point `(1,1,u)` belongs exactly when
`exists v phi(u,v)`. Therefore:

* If `Q` is true, the projection is the full cube and is affine.
* If `Q` is false, choose `u0` with no existential witness. The three
  present points `(0,0,u0),(1,0,u0),(0,1,u0)` have XOR
  `(1,1,u0)`, which is absent. The projection is not affine.

The relation always contains zero and every coordinate unit vector: the
guard-bit units use `u=0`, and each `u` unit uses `a=b=0`.
Consequently its affine hull is the full cube. These statements also cover
zero source widths. Empty source conjunctions produce the full cube;
an empty source clause forbids precisely the `a=b=1` slice.

The map adds two variables and two literal occurrences per source clause.
Renumbering and writing labels costs polynomial bit time in the explicit
input length; a three-literal clause becomes a five-literal clause.
This establishes the claimed many-one hardness and completes the proof.

## Semantic verification is a separate task

Let `A(x)` be an explicitly supplied system of XOR equations. Deciding
`R_F={x:A(x)}` is also `Pi_2^P`-complete. The upper bound follows from

```text
forall x,y exists z:
    (NOT F(x,y) OR A(x)) AND (NOT A(x) OR F(x,z)).
```

The first conjunct gives one inclusion, the second the other. Both sides
allow empty sets in this equality problem. Hardness already holds when
`A` has no equations and therefore specifies the full cube: equality is
exactly `forall x exists y F(x,y)`. The guard construction above additionally
preserves the nonempty, zero-containing promise.

Every affine subset has a system of at most `m` independent equations,
using `O(m^2)` bits in a dense encoding. Thus short *output descriptions*
do not, by themselves, supply short *proofs of semantic equality*.

This is a classification of deciding equality from the two descriptions.
It does not say that checking every supplied proof is hard. A polynomial-time
proof checker may require long proofs on some inputs. Nor does the theorem
establish superpolynomial time unconditionally: a polynomial-time algorithm
for this complete problem would imply `P=NP` (and collapse PH), and no
separation is proved here. A promise-only procedure permitted to return
anything on non-affine inputs is not classified by this theorem.

## Direct comparison with earlier mathematics

| Source | Input and conclusion | Difference from this note |
| --- | --- | --- |
| Schaefer (1978), Lemma 3.1A | Affinity characterized by ternary XOR closure. | The closure criterion is inherited; the note supplies an explicit quantified membership predicate. |
| [Creignou (1998), *Complexity versus stability for classes of propositional formulas*](https://www.sciencedirect.com/science/article/pii/S002001909800163X) | Ordinary CNF semantic equivalence to some XOR-CNF is coNP-complete. The publisher abstract explicitly reports this. | No existential projection in that stated result. XOR-CNF may be inconsistent, so its affine convention includes the empty relation. Do not apply this coNP label to our nonempty version without another argument. |
| [Boehler, Creignou, Reith and Vollmer (2004), Definition 3.1 and Theorem 3.4](https://www.researchgate.net/publication/237654012_Playing_with_Boolean_Blocks_Part_II_Constraint_Satisfaction_Problems1) | Co-clone membership for ordinary formula-defined relations; includes the affine co-clone and credits Creignou's earlier theorem. | Tuple evaluation there is polynomial-time. Membership in a projected CNF relation is existential. The ordinary-formula theorem does not directly classify this encoding. |
| Hemaspaandra (2004), section 2.3 | Completeness of alternation-bounded quantified Boolean formulas, including the required true forall-exists 3CNF language. | The hardness source and complexity-class framework are inherited. The two-guard map is proved explicitly above. |

The comparison establishes the input distinction, **not novelty**. Semantic
affinity recognition is an established subject. The precise quantified
classification may already appear elsewhere or be considered an immediate
corollary. No original contribution or publication readiness is asserted.
Schaefer's PDF was inaccessible directly during this review; the indexed
primary text and the self-contained proof above support the stated lemma.
Creignou's abstract and the later author-uploaded theorem were accessible.

## Finite evidence and trust boundary

Run from this directory on Python 3.10 or later, with no additional
dependencies (the repository CI selects Python 3.12):

```text
python review_quantified_boundary.py
python -m unittest -v test_quantified_boundary.py test_lab.py
```

These commands check the committed artifact. To regenerate it separately,
run `python quantified_boundary.py` and inspect the diff.

The campaign covers all 512 subsets of the nine non-tautological clauses on
two variables, **including the empty clause**, for all three universal/local
splits: 1,536 inputs, of which 113 are true and 1,423 false. Eight additional
examples cover empty widths, witness dependence on universal assignments,
tautologies, duplicates, and missing fibers. The deterministic campaign digest
binds the complete reconstructed record stream in the declared order.

The producer evaluates every source and lifted assignment and tests affinity
using rank versus cardinality. The separate reviewer imports no producer
code, regenerates the cases and guarded clauses, enumerates Boolean tuples,
and checks translated closure. Tests compare the rank criterion against
direct ternary closure on all 256 relations on three bits. Eight corruption
controls invoke the complete replay and require rejection. A separate
source-bound record check names the failing field. These programs can still
share an erroneous mathematical specification; this is not proof-assistant
certification.

The recorded 30,720 campaign formula evaluations count full truth-assignment
checks, not runtime, literal inspections, or bit operations. The experiment
is exhaustive and exponential in source width. Its default cap returns
`UNKNOWN_CAP` without an affinity answer; an unknown record cannot pass the
exact verifier. The all-input theorem is the written argument above, not an
extrapolation from these tests.

The repaired structural-chain baseline is a different, restricted algorithm.
Its efficient recovery on recognized XOR encodings is compatible with this
unrestricted hardness classification. Its legacy `EXACT_AFFINE` status
means an exact XOR equation, including a possible inconsistent zero-support
equation; the recognition problem defined here explicitly rejects empty
cosets. Affinity of existential support also says nothing about whether
different visible assignments have the same number of hidden witnesses.
No transfer theorem to arbitrary SAT algorithms has been supplied.
