# Tseitin expander scaling report

Each row is an odd-charge Tseitin contradiction on a connected cubic
graph. The local parity constraints are encoded as 3-CNF, and the
saved result is a complete first-UIP CDCL resolution trace replayed by
`INDEPENDENT_REVIEW.py`.

| graph | vertices | edge variables | clauses | decisions | conflicts | resolution steps | seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cube_3_regular | 8 | 12 | 32 | 23 | 24 | 147 | 0.006204 |
| petersen_3_regular | 10 | 15 | 40 | 47 | 48 | 347 | 0.019124 |
| heawood_3_regular | 14 | 21 | 56 | 127 | 128 | 1243 | 0.100807 |
| cyclic_bipartite_16 | 16 | 24 | 64 | 159 | 160 | 1787 | 0.164227 |

The odd-charge certificate is an exact XOR argument: every edge
variable occurs at two vertices, so summing all vertex equations
cancels every variable while leaving total charge one. This proves
unsatisfiability of each encoded CNF independently of the CDCL trace.

[Ben-Sasson and Wigderson](https://people.inf.ethz.ch/emo/SatSem05/Papers/BensassonWidgerson01.pdf)'s width-size tradeoff, together with graph
expansion, supplies the literature boundary for asymptotic resolution
lower bounds on Tseitin contradictions. These finite rows measure one
solver and do not reprove that theorem, lower-bound every SAT algorithm,
or resolve P versus NP.
