# Compact ITE motif audit

The proof-motif miner previously accepted the direct full-width CNF for
`z = ite(c,a,b)`, which has eight width-four clauses. This audit adds the exact
four-clause 3-CNF encoding:

```text
(~c OR ~a OR z)   (~c OR a OR ~z)
( c OR ~b OR z)   ( c OR b OR ~z)
```

For every candidate group, the recognizer enumerates the constant 24 role
permutations on its four-variable support and accepts only when the clauses'
truth table is exactly the ITE relation. The emitted certificate records the
roles and all four source clause indices. The independent reviewer reconstructs
the groups and truth tables without importing the recognizer.

The positive artifact contains two exact gates. A one-literal mutation and a
same-support decoy with one wrong clause are both rejected. Grouping is
polynomial in the explicit clause list; role testing is constant-size. This
recognizes a useful compact encoding but does not discover arbitrary circuits,
auxiliary definitions, or a complete candidate language, so it does not imply
a polynomial-time algorithm for general SAT.

Run:

```text
python run_indirect_ite.py
python review_indirect_ite.py
```

