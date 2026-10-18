# Proof width, CDCL traces, and frontier-state growth

Every row below is reconstructed by `review_frontier.py`. CDCL fields
come from the separately replayed proof-producing scaling certificates.

## All-assignment family

| n | input literals | frontier width | retained states | CDCL conflicts | resolution steps |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2 | 0 | 1 | 1 | 1 |
| 2 | 8 | 1 | 3 | 2 | 3 |
| 3 | 24 | 2 | 7 | 4 | 7 |
| 4 | 64 | 3 | 15 | 8 | 15 |
| 5 | 160 | 4 | 31 | 16 | 31 |
| 6 | 384 | 5 | 63 | 32 | 63 |
| 7 | 896 | 6 | 127 | 64 | 127 |

## Pigeonhole family

| holes | input literals | frontier width | retained states | CDCL conflicts | resolution steps |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 1 | 2 | 1 | 2 |
| 2 | 24 | 4 | 12 | 2 | 10 |
| 3 | 72 | 9 | 60 | 6 | 42 |
| 4 | 160 | 16 | 324 | 18 | 164 |
| 5 | 300 | 25 | 2005 | 50 | 590 |
| 6 | 504 | 36 | 14268 | 130 | 1962 |
| 7 | 784 | 49 | 115416 | 322 | 6104 |

The all-assignment input is already exponential in `n`; its exact count
identities are controls, not input-length lower bounds. The pigeonhole
inputs are polynomial in the hole parameter and have a direct injection
contradiction. The table still measures one supplied variable order and
one deterministic resolution-based CDCL implementation. It is evidence
for adversarial scaling, not a lower bound for every SAT algorithm.
