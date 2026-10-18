# Independent review of packed exact-weight matching

**Conclusion:** no correctness defect found in the reviewed theorem, encoder, bounded dynamic program or recurrence verifier. The construction correctly reduces width-at-most-three SAT to perfect matching with an exact binary-encoded total weight. It does not make ordinary minimum-weight matching decide SAT. All 11 current unit tests passed; the additional independent checks below passed as well.

Only this review file was written. The initial mathematical/code review was followed by a review of the completed experiment runner, stricter embedded-clause validation, and a disk replay of the final 34 cases. The final source snapshot is recorded below.

## Mathematical checks

For a clause of width k in {1,2,3}, its false-literal count lies in [0,k]. Its k−1 independent binary slack bits attain every integer in [0,k−1]. Equality to k−1 is therefore extendible exactly when the clause is satisfied. The combined count is at most 2k−1<=5, so base six prevents carries in every clause digit. Positional uniqueness proves both directions without an approximation or an unproved inverse operation.

Each Boolean choice is represented by a disjoint four-cycle with precisely two perfect matchings. Its two sums are the specified choice weights. A variable's one cycle contributes to all its clause digits, preserving consistency. The graph has 4(n+sum_j(k_j−1)) vertices and equally many edges. Every individual weight is below 6^m, and hence has at most 3m bits; the target does too. Polynomial bit length must not be confused with a polynomial numerical target.

The exact-weight problem is in NP: a matching and its exact sum have a polynomial verification. Together with the demonstrated reduction from width-at-most-three SAT, this proves NP-completeness even for the produced disjoint-cycle graphs. This is the arbitrary binary-weight equality problem, not ordinary optimization and not the special red/blue edge-count problem. The primary source's main theorem includes the width-at-most-three satisfiability problem as item 11 on printed page 95. [Karp, *Reducibility Among Combinatorial Problems*](https://www2.seas.gwu.edu/~simhaweb/champalg/tsp/papers/KarpOriginal.pdf).

For (x) AND (NOT x) AND (y OR z), the choice weights are (1,6),(36,0),(36,0),(0,36), target 36. Direct expansion gives exactly {1,6,37,42,73,78,109,114}. Thus both minimum-at-most-target and target-between-extremes tests accept incorrectly. The theorem's concrete counterexample is accurate.

## Executable checks and limits

`verify_encoding(n, clauses, encoding)` separately reconstructs the truth-choice costs, slack choices, target and cycle graph from the external original formula. This is an important binding step. `verify_matching` alone checks the data stored inside its supplied encoding and does not replace external-formula binding. A complete experiment or consumer should call `verify_encoding` first, then use `verify_choices` and, for a positive result, `verify_matching`.

The DP recurrence is exact: each prefix set contains precisely all attainable costs at most W. Removing greater costs is sound because every later cost is nonnegative. Witness reconstruction follows a certified predecessor in the saved layer. The verifier independently recomputes every recurrence, checks sorted unique integer states, the original-choice hash, the final decision, witness sum and reported work counts. A verifier transition-cap exhaustion returns UNKNOWN rather than accepting an incomplete proof. A solver cap exhaustion likewise returns UNKNOWN without a feasibility conclusion.

All arithmetic uses Python integers. Hashing uses length-prefixed binary integer encodings, including a test beyond 15,000 bits, and does not depend on decimal conversion or floating point. The transition cap counts recurrence transitions, not every machine instruction, byte allocation, certificate parsing step or big-integer operation. The state cap bounds a layer's cardinality; retaining all layers still uses space proportional to their total size and integer bit lengths. These are bounded reference controls, not a general polynomial or hardware-memory guarantee.

The stated polynomial graph-size argument assumes the theorem's preliminary removal of unused variable IDs and renumbering. `encode` does not itself perform that normalization: it creates one cycle per supplied n, including unused variables. Thus an enormous binary header n with few actual literals must be normalized before invoking the encoder to obtain the claimed bound in actual formula text length. This does not invalidate the mathematical reduction or the normalized experiments, but is a real interface precondition.

## Independent finite checks

The supplied 11 tests passed. Additional checks used all lists of zero through three choice pairs, each pair in {0,1,2}^2, and every target from zero through eight: **7,380 exact membership requests**. Independent enumeration of all Boolean choices agreed in every case. Each certificate was accepted with its exact reported transition count; reducing a positive transition budget by one produced UNKNOWN. The same requests were also run with state budget target mod 4 and transition budget target mod 5: 33 completed EXACT, all correctly, and 7,347 returned UNKNOWN without a feasibility field.

A separate seeded sample of **50 four-variable formulas** used zero through four clauses of width one through three and independently evaluated all original assignments. Enumerating **7,808 complete truth/slack choice words** reproduced exactly the satisfying assignments, and every positive encoding extension and matching replay passed. Seed: 70918. Formula generation sampled distinct variables per clause and independent signs, using Python 3.10.10's `random.Random`.

The exhaustive DP check can be reproduced from this folder with:

```python
from itertools import product
from packing import solve_choices, verify_choices
count = exact_capped = unknown_capped = 0
for size in range(4):
    for choices in product(list(product(range(3), repeat=2)), repeat=size):
        possible = {sum(p[b] for p,b in zip(choices,bits))
                    for bits in product((0,1), repeat=size)}
        for target in range(9):
            result = solve_choices(choices,target,max_states=100,max_transitions=1000)
            assert result['status']=='EXACT'
            assert result['feasible'] == (target in possible)
            assert verify_choices(choices,target,result,
                                  max_transitions=result['transitions'])['valid']
            if result['transitions']:
                assert verify_choices(choices,target,result,
                        max_transitions=result['transitions']-1)['status']=='UNKNOWN'
            limited = solve_choices(choices,target,
                        max_states=target%4,max_transitions=target%5)
            if limited['status']=='EXACT':
                exact_capped += 1
                assert limited['feasible'] == (target in possible)
            else:
                unknown_capped += 1
                assert 'feasible' not in limited
            count += 1
assert (count,exact_capped,unknown_capped)==(7380,33,7347)
```

The reviewed files were unchanged during these independent checks. Initial SHA-256 snapshot for the 7,380-request audit:

| File | SHA-256 |
|:---|:---|
| packing.py | 2ea788a7cbcef08858f84418acf9e00cda988f36e7d8eec10c4f7405093f8aa4 |
| test_packing.py | 7f061ac66402cf569ccbf3a01147da2d6002eb8e951e3c2360b8883de02cb337 |
| THEOREM.md | 11db830ad320390fdde1c5ea69cf9252f3550fa644a34388fc49759c6ad0d3e1 |

## Final runner and saved-result review

The subsequent source change validates the embedded clause metadata through the same strict formula validator, rejecting Boolean values masquerading as integer literals. Its regression is included in the current 11-test suite; all 11 passed again. The encoder mathematics and DP recurrence were unchanged, so the 7,380-case run was not needlessly repeated.

The completed `run_experiments.py` binds each graph to its external original formula before solving or replaying it. Original-assignment enumeration is capped at eight variables; larger examples supply and check an explicit satisfying assignment instead. All 34 inputs use compact variable numbering, satisfying the preprocessing scope stated above. The runner compares completed DP decisions to the independent formula reference and never labels an exhausted DP as infeasible.

The saved RESULTS.json was loaded from disk. Its source hashes matched the actual files. Replay verified **30 exact DP certificates, four UNKNOWN records with no feasibility conclusion, and 87 original-graph matching witnesses** across 34 cases. The reviewer additionally recomputed every saved small-formula truth table, checked every larger supplied assignment directly against its clauses, recomputed all ordinary minima/maxima from the independent cycle choices, and checked agreement of every exact DP decision with its formula reference. All 34 passed. The four capped examples have explicit satisfying assignments; their UNKNOWN status describes only this DP's work limit.

Final reviewed SHA-256 snapshot, matching the saved experiment:

| File | SHA-256 |
|:---|:---|
| packing.py | 1d60ffd5bf25a2cacdb08e5cf0287432135fe8134c6ca531c497e054ede30fbe |
| test_packing.py | 750091130860ebeb3a75a4b67b41164ec1e6ef0ebed9b63b3fad840320961da3 |
| run_experiments.py | 30f37a67592b42e4702826fac12b3250440b80f99d95ea0057e4aa95902d3640 |
| THEOREM.md | 11db830ad320390fdde1c5ea69cf9252f3550fa644a34388fc49759c6ad0d3e1 |

Finite checks supplement the proof and examine the implementation. They do not establish general polynomial solvability or a complexity-class separation.
