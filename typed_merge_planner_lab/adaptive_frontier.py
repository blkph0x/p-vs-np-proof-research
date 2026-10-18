"""Proof-producing SAT solver that composes exact order discovery and frontier DP.

The order search is deliberately bounded by ``max_order_variables``.  Within
that bound the solver is exact for arbitrary finite Boolean relations; above it
it returns ``UNKNOWN`` rather than hiding exponential order-discovery work.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from mixed_order_discovery import discover
from mixed_relation_dp import Constraint, solve as frontier_solve


HERE = Path(__file__).resolve().parent


def primal_graph(n: int, constraints: tuple[Constraint, ...]) -> tuple[int, ...]:
    """Return the constraint primal graph as one adjacency bitset per variable."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    adjacency = [0] * n
    for constraint in constraints:
        scope = tuple(constraint.scope)
        if len(set(scope)) != len(scope):
            raise ValueError("constraint scope repeats a variable")
        if any(v < 0 or v >= n for v in scope):
            raise ValueError("constraint variable outside range")
        for i, left in enumerate(scope):
            for right in scope[i + 1:]:
                adjacency[left] |= 1 << right
                adjacency[right] |= 1 << left
    return tuple(adjacency)


def solve(n: int, constraints: tuple[Constraint, ...], *,
          max_order_variables: int = 12) -> dict[str, object]:
    """Solve a finite relation instance using an exact small-order pipeline.

    For ``n <= max_order_variables``, minimum vertex-separation order discovery
    and frontier DP are both exhaustive and the result is SAT or UNSAT.  For a
    larger instance the result is UNKNOWN with the complete graph construction
    recorded, so the cap cannot be mistaken for a complexity theorem.
    """
    if max_order_variables < 0:
        raise ValueError("max_order_variables must be nonnegative")
    constraints = tuple(constraints)
    adjacency = primal_graph(n, constraints)
    graph_certificate = {"n": n, "adjacency": list(adjacency)}
    if n > max_order_variables:
        return {"status": "UNKNOWN", "sat": None, "reason": "ORDER_DISCOVERY_CAP",
                "max_order_variables": max_order_variables,
                "certificate": {"graph": graph_certificate,
                                 "order": None, "width": None,
                                 "order_search": None, "frontier": None}}

    order_search = discover(adjacency)
    order = tuple(order_search["order"])
    frontier = frontier_solve(n, constraints, order)
    certificate = {"graph": graph_certificate,
                   "order": list(order),
                   "width": order_search["width"],
                   "order_search": order_search,
                   "frontier": frontier["certificate"]}
    return {"status": frontier["status"], "sat": frontier["sat"],
            "width": order_search["width"], "order": list(order),
            "max_states": frontier["max_states"],
            "order_search": order_search, "certificate": certificate}


def source_hashes() -> dict[str, str]:
    names = ("adaptive_frontier.py", "run_adaptive_frontier.py",
             "ADAPTIVE_FRONTIER_THEOREM.md", "ADAPTIVE_FRONTIER_REVIEW.py",
             "test_adaptive_frontier.py")
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in names}
