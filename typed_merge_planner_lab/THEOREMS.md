# Typed merge facts

## Common Schaefer property

For a finite Boolean relation R, let Sig(R) contain any of:
- ZERO if R contains the all-zero tuple;
- ONE if R contains the all-one tuple;
- AND if R is closed under coordinatewise conjunction;
- OR if R is closed under coordinatewise disjunction;
- MAJ if R is closed under coordinatewise majority;
- MIN if R is closed under coordinatewise minority/xor-of-three.

If a finite constraint language Gamma has any one property common to every relation in
Gamma, Schaefer's dichotomy places SAT(Gamma) in P.

If none of the six properties is common to all relations, SAT(Gamma) is NP-complete.

Therefore for two exact bounded relations R,S the intersection

    Sig(R) intersect Sig(S)

is an exact pairwise tractability test in Schaefer's Boolean framework.

This statement concerns **unpinned** SAT over the fixed finite language. It is
not sufficient for the partial-assignment extension queries used by boundary DP.
For those queries the language also contains the unary relations {0} and {1}.
Their common Schaefer signature is exactly {AND, OR, MAJ, MIN}; ZERO and ONE
validity therefore cannot certify an extension oracle. The optional
`allow_pins=True` classifier applies this stronger test. The native planner
already used these four operation tags; it now explicitly filters constant
validity tags out of conditional-message merges as well.

Primary reference: Schaefer, *The Complexity of Satisfiability Problems* (1978),
Section 2 explicitly distinguishes SAT from SAT with constants and excludes
the constant-valid cases for the latter:
https://www.khoury.northeastern.edu/home/lieber/courses/csg260/f06/materials/papers/max-sat/p216-schaefer.pdf

## Minimal explicit obstruction: one pin can expose NP-completeness

Let R(a,b,c) mean a+b=c in ordinary integer arithmetic on Boolean arguments:

    R = {000, 011, 101}.

It is ZERO-valid and has no other Schaefer property. Witnesses are:
- 011 AND 101 = 001, outside R;
- 011 OR 101 = 111, outside R;
- majority(000,011,101) = 001, outside R;
- minority(000,011,101) = 110, outside R.

For each positive exactly-one clause on a,b,c introduce a fresh s and use

    R(a,b,s) AND R(s,c,t).

Existentially eliminating s gives a+b+c=t. Share the same t across all clauses.
At t=0 the all-zero assignment satisfies the whole instance. At t=1 it is
exactly the original positive 1-in-3 SAT instance, an NP-complete problem by
Schaefer. Thus deciding extension under a single pin is NP-complete even though
unpinned satisfiability is trivial and the projected boundary has only one bit.
Complementing all coordinates gives the corresponding ONE-valid obstruction.

The obstruction is minimal in arity and tuple count: every Boolean relation of
arity at most two is majority-closed. For three binary tuples, their coordinate
majority is one of those tuples (some pair agrees in each of at most two
coordinates, and the agreeing pairs share an index). Every relation with at
most two tuples is minority-closed, since among any three selected tuples two
are equal and cancel under XOR. Hence at least three coordinates and three
tuples are necessary to lose all four pin-preserving polymorphisms.

## Closure through a merge

AND, OR, majority and minority are polymorphisms.

Relations preserved by a polymorphism remain preserved under conjunction and existential
quantification / primitive-positive definition.

Hence if two child boundary relations share one such polymorphism, their exact merged and
projected parent relation stays in that tractable class.

ZERO/ONE validity is also preserved by conjunction and existential projection whenever the
distinguished all-zero/all-one assignment extends through the local variables in the
declared relation language.

This last preservation statement is semantic only. It gives neither an
arbitrary-pinning extension algorithm nor a tractable boundary-message type.

## Horn projection: semantic closure does not bound flat CNF size

For m>=1 consider the Horn formula on boundary a_i,b_i,z and local y_i:

    F_m = AND_i ((a_i -> y_i) AND (b_i -> y_i))
          AND ((y_1 AND ... AND y_m) -> z).

It has 2m+1 clauses and O(m) literal occurrences. Its existential projection is

    P_m = ((AND_i (a_i OR b_i)) -> z).

Necessity follows because every y_i is forced true when each pair contains a
true bit. Sufficiency follows by choosing y_i=a_i OR b_i. Distributing P_m
gives 2^m Horn clauses, one for every choice c_i in {a_i,b_i}:

    (c_1 AND ... AND c_m) -> z.

Every CNF over only the boundary variables equivalent to P_m needs at least
2^m clauses, even if its clauses are not required to be Horn. Consider the 2^m
false assignments with z=0 and exactly one true bit in each pair. If one clause
were false on two distinct such assignments, it would also be false on their
coordinatewise meet: any positive literal is false in both, and any negative
literal has its variable true in both. That meet has a pair 00 and therefore
satisfies P_m. Such a clause cannot belong to an equivalent CNF. Each clause
can therefore exclude at most one of the 2^m designated false assignments.

This is a representation lower bound, not a Horn solving lower bound. A safe
native message may retain `exists y . F_m` with private auxiliary variables.
Its size remains linear, arbitrary boundary pins are units, and extension is
Horn satisfiability. Conjoining two such messages requires alpha-renaming
private variables; it then remains an existential Horn formula of additive
size. This gives the precise representation contract for the planner's Horn
closed merges. A promise to emit a polynomial-size auxiliary-free Horn CNF
would be false. The current planner models costs and does not itself perform
that symbolic compilation.

## Explicit bridge

For an arbitrary merge whose child-interface union contains k Boolean variables, enumerate
all 2^k assignments and compute the exact merged/projection relation.

This is polynomial whenever 2^k is bounded by a declared polynomial in the total input
size.

## Extension quotient bridge

If an exact extension-equivalence quotient contains q representatives and all required
transition/compatibility tests are polynomial, then replacing raw assignments by the q
classes gives polynomial merge work whenever q is polynomially bounded.

## Hard native pairs

AFFINE + CARDINALITY contains the binary-code minimum-distance decision problem:

    Hx=0
    1 <= |x| <= k.

Thus unrestricted exact combination is NP-hard.

The project now has an explicit fixed Horn+Affine encoding of positive exact-one:
two shared bridge variables suffice, even though one does not. Replacing every
positive 1-in-3 clause by that pair of fixed constraints proves that the mixed
Horn+Affine language is NP-complete despite polynomial component solvers. The
saved two-bridge theorem gives the exact tuples and the exhaustive relation
counts; it does not claim that every larger composition is equally simple.
