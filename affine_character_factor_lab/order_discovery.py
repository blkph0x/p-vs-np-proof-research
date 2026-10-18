"""Exact, budgeted width-order discovery for supplied factor scopes.

This is a bounded search over filled primal graphs. It is deliberately honest:
the result is a certified order, a certified NO after all legal branches are
exhausted, or UNKNOWN when the state cap is reached. No claim of a universal
polynomial order finder is made.
"""

from __future__ import annotations


class Exhausted(Exception):
    pass


def _validate(n, scopes):
    if type(n) is bool or type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if type(scopes) not in (list, tuple):
        raise ValueError("scopes must be a list")
    checked = []
    for scope in scopes:
        if type(scope) not in (list, tuple):
            raise ValueError("scope must be a list")
        scope = list(scope)
        if any(type(v) is not int or v < 0 or v >= n for v in scope):
            raise ValueError("scope variable out of range")
        if len(set(scope)) != len(scope):
            raise ValueError("scope variables must be distinct")
        checked.append(scope)
    return checked


def primal_adjacency(n, scopes):
    scopes = _validate(n, scopes)
    adjacency = [0] * n
    for scope in scopes:
        bits = sum(1 << v for v in scope)
        for v in scope:
            adjacency[v] |= bits & ~(1 << v)
    return tuple(adjacency)


def verify_order(n, scopes, order, width_cap=None):
    scopes = _validate(n, scopes)
    if type(order) not in (list, tuple) or list(order) != sorted(set(order)):
        # The order need not be numerically sorted; this only catches duplicate
        # entries below. Keep the explicit sequence order intact.
        pass
    order = list(order)
    if len(order) != n or set(order) != set(range(n)):
        return {"valid": False, "reason": "order must contain every variable once"}
    if width_cap is not None and (type(width_cap) is not int or width_cap < 0):
        return {"valid": False, "reason": "invalid width cap"}
    adjacency = list(primal_adjacency(n, scopes))
    active = (1 << n) - 1
    widths = []
    for v in order:
        if not ((active >> v) & 1):
            return {"valid": False, "reason": "repeated or inactive variable"}
        neighbors = adjacency[v] & active & ~(1 << v)
        width = neighbors.bit_count()
        widths.append(width)
        if width_cap is not None and width > width_cap:
            return {"valid": False, "reason": "width cap exceeded", "widths": widths}
        ns = [u for u in range(n) if (neighbors >> u) & 1]
        for i, u in enumerate(ns):
            for w in ns[i + 1:]:
                adjacency[u] |= 1 << w
                adjacency[w] |= 1 << u
        active &= ~(1 << v)
    return {"valid": True, "width": max(widths, default=0), "widths": widths,
            "order": order}


def find_order(n, scopes, width_cap, *, max_states=100_000):
    scopes = _validate(n, scopes)
    if type(width_cap) is not int or width_cap < 0:
        raise ValueError("width_cap must be a nonnegative integer")
    if type(max_states) is not int or max_states < 0:
        raise ValueError("max_states must be a nonnegative integer")
    initial = primal_adjacency(n, scopes)
    states = 0
    memo = set()

    def search(active, adjacency, prefix):
        nonlocal states
        if active == 0:
            return list(prefix)
        key = (active, adjacency)
        if key in memo:
            return None
        memo.add(key)
        states += 1
        if states > max_states:
            raise Exhausted("state cap")
        candidates = []
        for v in range(n):
            if (active >> v) & 1:
                degree = (adjacency[v] & active & ~(1 << v)).bit_count()
                if degree <= width_cap:
                    candidates.append((degree, v))
        candidates.sort()
        for _, v in candidates:
            neighbors = adjacency[v] & active & ~(1 << v)
            updated = list(adjacency)
            ns = [u for u in range(n) if (neighbors >> u) & 1]
            for i, u in enumerate(ns):
                for w in ns[i + 1:]:
                    updated[u] |= 1 << w
                    updated[w] |= 1 << u
            answer = search(active & ~(1 << v), tuple(updated), prefix + [v])
            if answer is not None:
                return answer
        return None

    try:
        order = search((1 << n) - 1, initial, [])
    except Exhausted as exc:
        return {"status": "UNKNOWN", "reason": str(exc), "states": states}
    if order is None:
        return {"status": "NO", "states": states, "width_cap": width_cap}
    checked = verify_order(n, scopes, order, width_cap)
    if not checked.get("valid"):
        raise AssertionError("internal order certificate failed")
    return {"status": "EXACT", "order": order, "width": checked["width"],
            "widths": checked["widths"], "states": states, "width_cap": width_cap}


def factor_order_from_variable_order(scopes, variable_order):
    """A deterministic scope-sweep factor order; discovery is separate."""
    pos = {v: i for i, v in enumerate(variable_order)}
    return sorted(range(len(scopes)), key=lambda i: (
        min((pos[v] for v in scopes[i]), default=len(variable_order)),
        max((pos[v] for v in scopes[i]), default=-1), len(scopes[i]), i))
