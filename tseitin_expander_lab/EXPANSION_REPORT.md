# Tseitin exact expansion profiles

For each connected cubic graph, this artifact enumerates every nonempty
vertex subset through size floor(n/2). It records both the open
neighborhood `N(S)` and the external neighborhood `N(S)\S`, with the
exact ratio at every subset size, the global minimum, and an explicit
lexicographically first witness. `review_expansion_profile.py` rebuilds
the graph family and recomputes every value independently.

| graph | vertices | open epsilon | external epsilon | subsets checked |
| --- | ---: | ---: | ---: | ---: |
| cube_3_regular | 8 | 1/1 | 3/4 | 162 |
| petersen_3_regular | 10 | 3/2 | 4/5 | 637 |
| heawood_3_regular | 14 | 1/1 | 5/7 | 9907 |
| cyclic_bipartite_16 | 16 | 1/1 | 5/8 | 39202 |
| mobius_ladder_6 | 6 | 1/1 | 1/1 | 41 |
| mobius_ladder_8 | 8 | 3/2 | 3/4 | 162 |
| mobius_ladder_10 | 10 | 1/1 | 4/5 | 637 |
| mobius_ladder_12 | 12 | 4/3 | 2/3 | 2509 |
| mobius_ladder_14 | 14 | 1/1 | 4/7 | 9907 |
| mobius_ladder_16 | 16 | 5/4 | 1/2 | 39202 |
| mobius_ladder_18 | 18 | 1/1 | 4/9 | 155381 |
| mobius_ladder_20 | 20 | 6/5 | 2/5 | 616665 |

This is an exact finite graph certificate. The external ratios make the
boundary explicit: the saved Möbius-ladder values decline to 2/5 at
20 vertices, so these rows are not evidence for a standard uniform
external-expander family. The profile is recorded alongside the
proof-producing CDCL measurements; no resolution lower bound or
P-versus-NP conclusion is inferred from these ratios alone.
