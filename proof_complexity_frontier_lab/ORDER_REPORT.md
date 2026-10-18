# Exact small-order discovery for pigeonhole frontiers

The subset recurrence exhausts every variable order through 20 variables.
The independent reviewer recomputes the recurrence and every saved order.

| holes | variables | row-major width | exact minimum width |
| ---: | ---: | ---: | ---: |
| 1 | 2 | 1 | 1 |
| 2 | 6 | 4 | 3 |
| 3 | 12 | 9 | 7 |
| 4 | 20 | 16 | 11 |

The row-major h^2 width is not always optimal: the exact controls reduce
it to 1, 3, 7, and 11 for h = 1, 2, 3, and 4. These are finite exact
optima only; no asymptotic formula is inferred from four rows. The order
oracle itself costs 2^n subset states and is not a general polynomial
order-discovery algorithm.
