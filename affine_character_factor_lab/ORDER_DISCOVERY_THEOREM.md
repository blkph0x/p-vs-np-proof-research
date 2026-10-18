# Capped width-order discovery

The order finder works on the primal graph of supplied factor scopes. A
variable elimination step removes (v), records its current live-neighbor
count, and fills those neighbors into a clique. A recursive branch is legal at
width (k) exactly when that count is at most (k). The search memoizes the
filled graph and active-variable mask.

For an `EXACT` result, the returned order is independently replayed and every
step's width is checked. A `NO` result means every legal branch under the
specified width was exhausted. A state cap returns `UNKNOWN` without an order;
it is never treated as a width lower bound. The search is intentionally a
budgeted exact procedure and carries no claim of polynomial worst-case order
discovery. The known difficulty of finding minimum-width decompositions remains
part of the problem rather than being hidden behind a heuristic.

The factor-order adapter sorts original factor scopes by their first and last
positions in a certified variable order. It is a deterministic bridge for the
weighted affine DAG, not a proof that this factor order is optimal.

Saved controls find width-three orders for the cumulative-parity chain at 8,
32 and 128 blocks; the resulting factor orders drive exact weighted-DAG
certificates. A complete graph has no width-two order, a cycle has no width-one
order, and a deliberately capped path search returns `UNKNOWN`. These controls
separate a verified decomposition certificate from a failed or budget-limited
search.
