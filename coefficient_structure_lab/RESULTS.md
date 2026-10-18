# Clause-structure coefficient results

Eleven tests passed in 0.544 seconds. The saved experiment completed in 0.494 seconds and compared 630 small original formulas: 430 exhaustive cases and 200 seeded cases. It checked their exact polynomial coefficients against direct logical-assignment/slack enumeration, covering 7,235 logical assignments and 3,162 original product factors. Including the larger named controls, 641 complete elimination certificates were verified.

The 15 saved named queries produced 11 EXACT results and four UNKNOWN results. Nine independently checked original satisfying assignments and exact-weight matching extensions are saved, including the positive cases that exceeded the coefficient solver's budget.

| Original formula/control | Coefficient result | Checked width | Peak bucket assignments | Count arithmetic operations |
| --- | ---: | ---: | ---: | ---: |
| One ternary clause | 10 | 2 | 8 | 22 |
| Same ternary clause repeated | 16 | 2 | 8 | 30 |
| One ternary clause plus unused variable | 20 | 2 | 8 | 24 |
| Shared contradictory unit clauses | 0 | 0 | 2 | 6 |
| Original interval/gcd gap | 0 | 1 | 4 | 16 |
| All eight ternary polarity clauses, UNSAT | 0 | 2 | 8 | 78 |
| 24 disjoint ternary clauses | 10^24 | 2 | 8 | 528 |
| Connected 40-clause chain | 63,591,000,982,758,758,589,317,251,072 | 2 | 8 | 1,036 |
| Binary star, leaves-first order | 513 | 1 | 4 | 74 |
| Binary star, center-first order | UNKNOWN | Budget exceeded | Cap 64 | No count claimed |
| Complete interaction on 16 variables | UNKNOWN | Every order has width 15 | Cap 256 | No count claimed |
| Planted mixed 3CNF, 24 variables/96 clauses | UNKNOWN | Budget exceeded | Cap 256 | No count claimed |
| Planted mixed 3CNF, 32 variables/128 clauses | UNKNOWN | Budget exceeded | Cap 256 | No count claimed |
| Empty product | 1 | 0 | 1 | 0 |
| 256 unused variables | 2^256 | 0 | 2 | 512 |

The older sparse reachable-cost reference returned UNKNOWN at its 4,096-state cap on the eight-clause UNSAT control, the 24 disjoint clauses, the connected 40-clause chain, and both planted large formulas. The structure method certifies the first three; it also remains UNKNOWN on the planted cases. This comparison uses exactly the original saved exponent pairs and target, including shared truth choices and all separate slack bits.

For 24 disjoint ternary clauses, the final sparse support below the target has `(2*(6^24−1)/5)+1` distinct states by the proved digit argument. The structure certificate stores 360 entries and retains the exact multiplicity 10^24. The connected-chain count independently satisfies the transfer recurrence in `THEOREM.md`, so the improvement is not limited to disconnected products.

The count arithmetic column excludes polynomial input validation, exponent binding, hashing, index projection and graph bookkeeping. Those costs and the exact scope of the counters are stated in the theorem. All intermediate counts respect the q+1-bit bound; the 256-unused-variable control reaches it exactly with 257-bit final count.

`RESULTS.json` preserves all original encodings and orders, full exact certificates, honest UNKNOWN outcomes, exact oracles, known matching witnesses, source hashes and source-stability checks. The proof gives a width-parameterized algorithm, not a general small-width guarantee or a resolution of P versus NP.
