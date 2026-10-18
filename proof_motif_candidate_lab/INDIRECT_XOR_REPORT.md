# Hidden XOR pair audit

This audit closes one narrow gap in the proof-motif miner: parity encoded through
auxiliary variables rather than a direct four-clause relation on the final
support.

An exact three-variable parity block certifies an equation
`x_a XOR x_b XOR x_c = r`. If two verified blocks share exactly one variable,
XORing the two equations cancels that variable and yields a four-variable
equation on the symmetric difference of the supports. The implementation emits
both source block certificates and the cancelled variable, then checks the
derived implication by exhaustive assignments to the four visible variables.

The saved positive fixture contains two blocks sharing variable `3`. Their
equations are

```text
x_0 XOR x_1 XOR x_3 = 0
x_3 XOR x_2 XOR x_0 = 1
```

so the derived relation is `x_0 XOR x_1 XOR x_2 XOR x_3 = 1`. The independent
review reconstructs the local blocks from clauses and obtains exactly the same
candidate. A one-literal mutation destroys the local parity certificate, and a
disjoint pair produces no candidate.

This is a polynomial bounded discovery pass over explicit clauses: local
three-variable grouping is linear after hashing, and the pair join is quadratic
in the number of verified blocks in the worst case. It is not a complete
auxiliary-variable eliminator. Longer chains, exponentially many XOR spans,
ambiguous encodings, and arbitrary semantic macro discovery remain outside the
scope. The result therefore strengthens a scoped miner while leaving general
SAT and P versus NP unresolved.

Run:

```text
python run_indirect_xor.py
python review_indirect_xor.py
```

