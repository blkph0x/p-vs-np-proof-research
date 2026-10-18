# Rank-five exhaustive oracle

The companion `rank5_exact.cpp` searches every ordered basis of
`F_2^5`.  At recursion depth `k` it has selected independent rows
`u_1,...,u_k`; the next row is chosen outside their span.  Therefore every
terminal tuple is an ordered basis, and every ordered basis appears once.  The
number of terminal tuples is

`(32-1)(32-2)(32-4)(32-8)(32-16) = 9,999,360 = |GL(5,2)|`.

For each basis the program transforms every original column `c` by
`(u_i · c)_i`, then computes:

* count-first objective `(q, excess, total)`, where `q` is the number of
  columns of Hamming weight greater than two;
* rank-first objective `(p, q, excess, total)`, where `p` is the binary rank of
  those exceptional columns.

The four saved inputs in `RANK5_RESULTS.json` all report the full group count
and are replayed by `rank5_driver.py` with independent Python arithmetic.  On
the first input, the count-first optimum has `(q,p)=(2,2)` and the rank-first
optimum has `(q,p)=(4,1)`.  Feeding those two certified transforms to the
native syndrome solver gives state counts 4 and 2, respectively, with the same
minimum distance 2.

This is a finite exact oracle for four rank-five representations.  The group
size is `2^(25+O(5))`, and the search is not a polynomial-time universal basis
discovery procedure.  It supplies a larger downstream-aware control; it does
not resolve P versus NP.
