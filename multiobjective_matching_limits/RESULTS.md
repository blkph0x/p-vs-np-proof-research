# Simultaneous matching-bound validation

Eight unit tests passed in 0.058 seconds. The experiment checked:

| Check | Count |
| --- | ---: |
| Formulas | 740 |
| Exhaustive normalized formulas on at most three variables, at most two distinct clauses | 434 |
| Seeded raw formulas, including repeated literals, tautologies, and empty clauses | 300 |
| Named SAT/UNSAT and boundary controls | 6 |
| Original truth assignments evaluated | 6,558 |
| Generic graph perfect matchings checked | 6,595 |
| Exact clause-cost values checked | 15,576 |

The test suite additionally checked all 231 unordered pairs, allowing repetition, of raw clauses of length at most two on two variables. A separate edge-subset oracle enumerated the graph matchings for those cases. Other tests cover the two cycle states, positive/negative literal signs, the empty graph, the empty-clause obstruction, JSON replay, malformed witnesses and costs, explicit enumeration limits, and exact arithmetic with a 15,001-bit integer.

The saved named controls include a satisfiable three-clause formula, contradictory unit clauses, and all eight distinct-variable ternary clauses on three variables. The last formula is unsatisfiable: every assignment violates exactly one bound. For every matching, however, the sum of clause costs is 12 and the sum of bounds is 16, so the single unweighted sum inequality accepts it. This establishes a concrete aggregation failure; it does not classify every possible scalar encoding.

`RESULTS.json` stores the original graph and all cost rows, bounds, assignments, matching edge IDs and exact verification outcomes for the named cases. It also records hashes of the producer, tests and theorem and confirms they stayed unchanged during the run. The primary source page is preserved separately in `KARP_PAGE_95.png`; the original URL and bibliographic citation are in `THEOREM.md`.

The finite checks support the reduction and the explicit examples. The proof establishes NP-completeness with 0/1 weights and bounds at most two on disjoint four-cycles. It concerns polynomially many simultaneous bounds and leaves ordinary unconstrained matching easy. No fixed-number strong-hardness claim or P-versus-NP resolution is made.
