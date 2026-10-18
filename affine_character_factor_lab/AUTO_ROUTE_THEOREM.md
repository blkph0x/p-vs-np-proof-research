# Automatic bounded-width route

The automatic route composes three separately checked steps:

1. Convert the original factor scopes to a primal graph.
2. Search filled graphs for an order of width at most (k), with a state cap.
3. Convert the verified variable order to a deterministic factor order, run the
   weighted affine DAG, and replay its full certificate.

The route returns `EXACT` only when all three steps succeed. An exhausted order
search returns `UNKNOWN`; an exhausted weighted solver also returns `UNKNOWN`;
neither is interpreted as UNSAT. A complete search that exhausts every legal
branch returns `NO` for the supplied width bound. The weighted DAG's own
certificate verifier independently checks every original factor occurrence and
every marginal/product record.

For the cumulative-parity chain, the route discovers width three and returns a
verified count of one through 128 blocks. A complete interaction has no width
two order, and a deliberately state-capped path search returns `UNKNOWN`. These
are parameterized guarantees for supplied scopes and caps. They do not provide
a polynomial algorithm for finding a suitable width on arbitrary SAT inputs,
and they do not resolve P versus NP.
