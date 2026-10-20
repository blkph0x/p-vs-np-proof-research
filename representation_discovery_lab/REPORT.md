# Hidden-affine representation discovery experiment

This is a bounded experiment for the representation-discovery question.  It
does not claim a lower bound for SAT, an invariant of all algorithms, or a
route to P versus NP.

The family encodes one even-parity equation on `m` shared variables as a chain
of 3-CNF XOR gadgets.  The chain has `m-1` existential helper variables.  The
projected relation therefore has a compact representation consisting of one
XOR support, while the declared discovery procedure must enumerate all shared
and helper assignments before testing every bounded XOR candidate.

The experiment records three model-relative quantities:

```text
D = bits in the discovered one-XOR representation
S = bounded projection work plus candidate-search work
V = independent exhaustive projection replay work
```

`D` grows with the support label width, while `S` and `V` grow with the hidden
helper variables.  Reversing the shared-variable names preserves the projected
relation and all three values, so the control distinguishes semantic hiding by
auxiliary encoding from ordinary renaming.

| shared variables | helpers | clauses | representation bits | discovery work | verification work |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 2 | 9 | 15 | 408 | 288 |
| 4 | 3 | 13 | 17 | 2,160 | 1,664 |
| 5 | 4 | 17 | 24 | 10,720 | 8,704 |
| 6 | 5 | 21 | 27 | 51,136 | 43,008 |
| 7 | 6 | 25 | 30 | 237,440 | 204,800 |

The values are exact operation counts for the declared enumeration model, not
wall-clock timings.  `RESULTS.json` stores both identity and reversed-name
controls.  `independent_review.py` rebuilds the clauses and projection without
importing the producer.

For `m` shared variables the counts have the closed forms

```text
local variables       = m - 1
CNF clauses           = 4m - 3
D                     = 9 + m ceil(log2 m)
V                     = (4m - 3) 2^(2m - 1)
candidate-search work = (2^(m + 1) - 1) 2^m
S                     = V + candidate-search work
```

The first two identities follow from the XOR chain.  The projection enumerates
`2^(m+(m-1))` assignments, and the fixed candidate vocabulary evaluates
`2(2^m-1)+1` candidates on each shared assignment, giving the last three
identities exactly.  Thus this declared procedure has
`D=Theta(m log m)` and `S,V=Theta(m 4^m)`.  The theorem is about the procedure's
charged work; it does not imply that every method for discovering or verifying
the same XOR relation pays that cost.

The result supports a precise, limited statement: a compact projected
representation can coexist with high discovery cost for one explicit
projection-based synthesizer.  It does not show that another solver must first
discover that representation, and it does not establish a superpolynomial
lower bound.  Extending the experiment to a theorem would require a transfer
argument covering a broader algorithm model.
