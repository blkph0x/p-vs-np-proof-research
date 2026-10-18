# Semantic clutter: width is not semantic hardness

For each `n`, the formula is `z AND NOT z` together with every positive
2-clause `(x_i OR x_j)` on a clique of `n` otherwise irrelevant variables.
Unit propagation sees the contradiction immediately, while the primal
clique forces a large variable boundary under every order.

| clique variables | total variables | clauses | resolution width | minimum frontier width | row-order width |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2 | 2 | 1 | 0 | 0 |
| 2 | 3 | 3 | 1 | 1 | 1 |
| 3 | 4 | 5 | 1 | 2 | 2 |
| 4 | 5 | 8 | 1 | 3 | 3 |
| 5 | 6 | 12 | 1 | 4 | 4 |
| 6 | 7 | 17 | 1 | 5 | 5 |
| 7 | 8 | 23 | 1 | 6 | 6 |
| 8 | 9 | 30 | 1 | 7 | 7 |

The width-zero closure has no refutation and width one derives the empty
clause from the two unit axioms. The independent order recurrence finds
minimum boundary `n-1`; the displayed order reaches that value. Removing
either unit makes the remaining positive clique satisfiable by setting all
clique variables true, so the contradiction is a real semantic core rather
than a hidden claim about the clique clauses.

This is a preprocessing warning. It does not make frontier width useless
after sound simplification, and it does not prove that arbitrary semantic
simplification is polynomial. A general solver must charge the discovery
and removal of such irrelevant structure.
