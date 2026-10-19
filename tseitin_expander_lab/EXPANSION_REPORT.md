# Tseitin exact expansion profiles

For each connected cubic graph, this artifact enumerates every nonempty
vertex subset through size floor(n/2). `N(S)` is the open neighborhood
of `S`, and the saved ratio is `|N(S)|/|S|`. The profile records the
minimum at every subset size, the global minimum, and an explicit
lexicographically first witness. `review_expansion_profile.py` rebuilds
the graph family and recomputes every value independently.

| graph | vertices | global epsilon | global witness size | subsets checked |
| --- | ---: | ---: | ---: | ---: |
| cube_3_regular | 8 | 1/1 | 4 | 162 |
| petersen_3_regular | 10 | 3/2 | 4 | 637 |
| heawood_3_regular | 14 | 1/1 | 7 | 9907 |
| cyclic_bipartite_16 | 16 | 1/1 | 8 | 39202 |
| mobius_ladder_6 | 6 | 1/1 | 3 | 41 |
| mobius_ladder_8 | 8 | 3/2 | 4 | 162 |
| mobius_ladder_10 | 10 | 1/1 | 5 | 637 |
| mobius_ladder_12 | 12 | 4/3 | 6 | 2509 |
| mobius_ladder_14 | 14 | 1/1 | 7 | 9907 |
| mobius_ladder_16 | 16 | 5/4 | 8 | 39202 |
| mobius_ladder_18 | 18 | 1/1 | 9 | 155381 |
| mobius_ladder_20 | 20 | 6/5 | 10 | 616665 |

This is an exact finite graph certificate, not a claim that the saved
Möbius ladders form a uniform expander family. The profile is recorded
to make the graph property visible alongside the proof-producing CDCL
measurements. No resolution lower bound or P-versus-NP conclusion is
inferred from these ratios alone.
