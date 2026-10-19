# Tseitin expander scaling report

Each row is an odd-charge Tseitin contradiction on a connected cubic
graph. The local parity constraints are encoded as 3-CNF, and the
saved result is a complete first-UIP CDCL resolution trace replayed by
`INDEPENDENT_REVIEW.py`.

| graph | vertices | edge variables | clauses | decisions | conflicts | resolution steps | seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cube_3_regular | 8 | 12 | 32 | 23 | 24 | 147 | 0.006165 |
| petersen_3_regular | 10 | 15 | 40 | 47 | 48 | 347 | 0.019129 |
| heawood_3_regular | 14 | 21 | 56 | 127 | 128 | 1243 | 0.100960 |
| cyclic_bipartite_16 | 16 | 24 | 64 | 159 | 160 | 1787 | 0.163184 |
| mobius_ladder_6 | 6 | 9 | 24 | 15 | 16 | 75 | 0.002729 |
| mobius_ladder_8 | 8 | 12 | 32 | 31 | 32 | 187 | 0.007689 |
| mobius_ladder_10 | 10 | 15 | 40 | 63 | 64 | 443 | 0.021651 |
| mobius_ladder_12 | 12 | 18 | 48 | 127 | 128 | 1019 | 0.060084 |
| mobius_ladder_14 | 14 | 21 | 56 | 255 | 256 | 2299 | 0.176073 |
| mobius_ladder_16 | 16 | 24 | 64 | 511 | 512 | 5115 | 0.572485 |
| mobius_ladder_18 | 18 | 27 | 72 | 1023 | 1024 | 11259 | 1.932619 |
| mobius_ladder_20 | 20 | 30 | 80 | 2047 | 2048 | 24571 | 6.935537 |

The odd-charge certificate is an exact XOR argument: every edge
variable occurs at two vertices, so summing all vertex equations
cancels every variable while leaving total charge one. This proves
unsatisfiability of each encoded CNF independently of the CDCL trace.

[Ben-Sasson and Wigderson](https://people.inf.ethz.ch/emo/SatSem05/Papers/BensassonWidgerson01.pdf)'s width-size tradeoff, together with graph
expansion, supplies the literature boundary for asymptotic resolution
lower bounds on Tseitin contradictions. These finite rows measure one
solver and do not reprove that theorem, lower-bound every SAT algorithm,
or resolve P versus NP.

The Möbius-ladder rows are a deterministic scaling control for this
specific CDCL implementation. Their observed conflict counts are
reported as measurements; no all-size formula for those counts is
claimed, and the family is not asserted here to be a uniform expander
family.

The companion `EXPANSION_RESULTS.json` records the exact open-neighborhood
profile through half-size vertex sets for all twelve graphs. Its separate
replay checks every subset and rebuilds the named graph family. This is
finite graph evidence, not a resolution lower bound or an asymptotic
expander theorem.
