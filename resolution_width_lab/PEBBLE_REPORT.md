# Pebble-game width bridge

This report records the finite resolution-width result for the standard
PHP(5,4) CNF: 20 variables, 5 positive four-literal pigeon clauses, and 70
negative binary exclusivity clauses (75 clauses total).

The method is the Boolean existential pebble-game characterization of
resolution width from Atserias and Dalmau, *A Combinatorial Characterization of
Resolution Width*, Theorem 2:

<https://www.cs.upc.edu/~atserias/papers/width/ccc03.pdf>

For width `w`, Spoiler wins the `(w+1)`-pebble game exactly when a width-`w`
resolution refutation exists. A Duplicator position is a partial assignment
that does not falsify an input clause. A winning family is closed under every
restriction and gives at least one legal truth-value extension for every new
variable while a pebble is free.

`pebble.py` enumerates all positions up to the requested pebble count and
computes the greatest family satisfying those two conditions. Each round
removes positions that fail a projection or extension check. The complete
round trace and the digest of the final family are saved in
`PEBBLE_RESULTS.json`. `review_pebble.py` uses a separate tuple-state replay;
its result is saved in `PEBBLE_REVIEW.json`.

| instance | pebbles | initial positions | final positions | rounds | result |
| --- | ---: | ---: | ---: | ---: | --- |
| unit contradiction | 2 | 1 | 0 | 1 | Spoiler wins |
| all assignments, 3 variables | 4 | 19 | 0 | 3 | Spoiler wins |
| PHP(4,3) | 4 | 5,758 | 0 | 12 | Spoiler wins |
| PHP(5,4) | 4 | 54,471 | 54,471 | 0 | Duplicator wins |
| PHP(5,4) | 5 | 279,815 | 0 | 22 | Spoiler wins |

The 5-pebble PHP(5,4) result is an exhaustive finite certificate for a
width-4 resolution refutation. The independent bounded-width closure already
has a complete width-3 fixed point with 2,230 clauses and no empty clause, so
there is no width-3 refutation. The exact minimum resolution width of this
encoding is therefore **4**. The earlier indexed and bit-mask width-4 runs
stopped at explicit candidate caps; the pebble certificate explains that
those runs stopped before reaching an existing width-4 refutation.

This is a finite proof-complexity result for one encoding. The position count
is exponential in the number of variables, and the result says nothing about
a polynomial-time algorithm for general SAT or about the truth of P versus
NP.
