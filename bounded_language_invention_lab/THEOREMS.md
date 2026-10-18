# Fixed-Width Language Invention Theorem

Let K,L be fixed nonnegative integers.

Consider any collection of CNF proof fragments F. Each fragment has:
- at most K declared boundary variables x;
- at most L local variables y;
- an arbitrary explicit list of clauses over x union y.

Define its boundary relation

    R_F(x) := exists y F(x,y).

## Exact extraction

Enumerate all 2^K boundary assignments and all 2^L local assignments.

For each boundary assignment, mark it accepted iff at least one local assignment satisfies
all clauses.

This computes the complete truth table of R_F in

    O(2^(K+L) |F|)

literal/clause evaluation work.

For fixed K,L this is polynomial in the explicit fragment size.

## Canonicalization under variable permutation

To identify isomorphic uses of the same k-ary relation, the prototype evaluates the truth
table under every one of k! boundary-variable permutations and chooses the lexicographically
smallest table.

This costs

    O(k! 2^k)

relation evaluations.

For fixed K this is again a constant-factor polynomial procedure.

## Completeness of the dynamic vocabulary

There are exactly

    2^(2^k)

Boolean relations of arity k.

Therefore the number of Boolean relations of arity at most K is the finite constant

    sum_{k=0}^K 2^(2^k).

The registry can assign a unique relation symbol to every canonical relation it encounters.

Hence, for fixed K,L, the dynamic relation language is complete for **all** possible
boundary semantics of such fragments; it is not restricted to a predefined motif library.

## Exact relation certificate

The canonical truth table is the authoritative semantic certificate of the invented
relation symbol.

Any optimized implementation—ANF, affine equation, symmetric weight table, coordinate
quotient, or synthesized circuit—is admitted only after exact equality with the certified
truth table is checked over all 2^k boundary assignments.

## Coordinate quotient

Given an exact k-variable truth table, the prototype additionally computes:
- variables on which the relation is independent;
- variables fixed to constants on all satisfying tuples;
- pairs/classes whose XOR is constant on all satisfying tuples.

These properties are decidable by direct truth-table scanning in polynomial time in 2^k.

Substituting those dependencies gives an exact lower-arity quotient relation, again checked
on every complete boundary assignment.

## Limitation

The theorem is parameterized by fixed K,L.

If K grows, the 2^K truth table and current K! permutation canonicalizer are not polynomial
in K.

Thus the theorem establishes complete dynamic language invention for bounded interfaces,
not for unrestricted SAT interfaces.
