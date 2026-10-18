# Recursive Schaefer backdoor search

The supplied-backdoor solver assumes that a variable set is already known.
This follow-up searches for a bounded decision tree instead. At a node, if all
restricted relations share the requested Horn or affine closure, the native
solver closes the node. Otherwise the search branches on every variable in a
non-target relation and recursively tries both values. A SAT result contains a
checked witness from one branch; an UNSAT result requires both children to be
UNSAT. Exhausted depth, node budget, or unsuccessful candidate choices produce
`UNKNOWN`.

For depth `t` and `n` variables, exhaustive candidate selection has a worst-case
search factor bounded by `sum_{i<=t} (n 2)^i` before the native polynomial leaf
work. The implementation records node and candidate counts and applies a hard
node cap. This is a bounded discovery algorithm, not a polynomial universal
backdoor finder. A small recursive tree is an input-sensitive certificate, and
failure to find one within the cap is not a lower bound.

The exact-one controls show the intended boundary: a positive exact-one
relation is not affine at the root, but one variable assignment makes each
branch affine, so depth one proves SAT or UNSAT for the saved instances. A
zero-depth call returns `UNKNOWN` instead of silently enumerating the original
hard relation.
