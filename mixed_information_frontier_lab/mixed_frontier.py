"""Exact future-equivalence frontiers for small mixed Boolean bundles.

The analyzer is deliberately exponential in the number of variables.  It is a
research oracle: a prefix is represented by the complete truth vector of its
possible suffixes, so equal vectors are exactly future-equivalent prefixes.
"""

from __future__ import annotations

from hashlib import sha256
import json
from math import prod
from pathlib import Path


KINDS = {"parity", "cardinality", "clause"}


def _scope_mask(scope):
    return sum(1 << i for i in scope)


def validate(n, constraints):
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if type(constraints) not in (list, tuple):
        raise ValueError("constraint list required")
    checked = []
    for item in constraints:
        if type(item) is not dict or item.get("kind") not in KINDS:
            raise ValueError("unknown constraint")
        kind = item["kind"]
        if kind == "parity":
            scope = list(item.get("scope", ()))
            rhs = item.get("rhs")
            if type(rhs) is not int or rhs not in (0, 1):
                raise ValueError("parity rhs")
            if any(type(i) is not int or not 0 <= i < n for i in scope):
                raise ValueError("parity scope")
            if len(set(scope)) != len(scope):
                raise ValueError("duplicate parity variable")
            checked.append({"kind": kind, "scope": scope, "rhs": rhs})
        elif kind == "cardinality":
            scope = list(item.get("scope", ()))
            target = item.get("target")
            op = item.get("op", "eq")
            if any(type(i) is not int or not 0 <= i < n for i in scope):
                raise ValueError("cardinality scope")
            if len(set(scope)) != len(scope) or type(target) is not int:
                raise ValueError("cardinality arguments")
            if op not in ("eq", "le") or not 0 <= target <= len(scope):
                raise ValueError("cardinality target")
            checked.append({"kind": kind, "scope": scope, "op": op, "target": target})
        else:
            literals = list(item.get("literals", ()))
            if not literals or any(type(x) is not int or x == 0 or abs(x) > n for x in literals):
                raise ValueError("clause literals")
            if len({abs(x) for x in literals}) != len(literals):
                raise ValueError("duplicate clause variable")
            checked.append({"kind": kind, "literals": literals})
    return checked


def satisfies(n, constraints, assignment):
    """Evaluate the original bundle on one full bit assignment."""
    for item in constraints:
        if item["kind"] == "parity":
            if sum((assignment >> i) & 1 for i in item["scope"]) % 2 != item["rhs"]:
                return False
        elif item["kind"] == "cardinality":
            count = sum((assignment >> i) & 1 for i in item["scope"])
            if item["op"] == "eq" and count != item["target"]:
                return False
            if item["op"] == "le" and count > item["target"]:
                return False
        else:
            if not any(((assignment >> (abs(lit) - 1)) & 1) == (lit > 0)
                       for lit in item["literals"]):
                return False
    return True


def local_state(n, item, prefix, cut):
    """The obvious local summary exposed by a prefix at a cut."""
    if item["kind"] == "parity":
        return sum((prefix >> i) & 1 for i in item["scope"] if i < cut) % 2
    if item["kind"] == "cardinality":
        return sum((prefix >> i) & 1 for i in item["scope"] if i < cut)
    hit = any((lit > 0 and ((prefix >> (lit - 1)) & 1))
              or (lit < 0 and not ((prefix >> (-lit - 1)) & 1))
              for lit in item["literals"] if abs(lit) <= cut)
    return 1 if hit else 0


def analyze_cut(n, constraints, cut):
    """Return exact residual classes and local-product accounting at one cut."""
    constraints = validate(n, constraints)
    if type(cut) is not int or not 0 <= cut <= n:
        raise ValueError("invalid cut")
    suffix_width = n - cut
    residuals = {}
    tuple_to_prefixes = {}
    local_values = [set() for _ in constraints]
    for prefix in range(1 << cut):
        signature = 0
        for suffix in range(1 << suffix_width):
            assignment = prefix | (suffix << cut)
            if satisfies(n, constraints, assignment):
                signature |= 1 << suffix
        if signature == 0:
            continue
        residuals.setdefault(signature, []).append(prefix)
        state = tuple(local_state(n, item, prefix, cut) for item in constraints)
        tuple_to_prefixes.setdefault(state, []).append(prefix)
        for index, item in enumerate(constraints):
            local_values[index].add(state[index])
    state_counts = [len(values) for values in local_values]
    return {
        "n": n,
        "cut": cut,
        "suffix_assignments": 1 << suffix_width,
        "prefix_assignments": 1 << cut,
        "live_prefixes": sum(map(len, residuals.values())),
        "future_classes": len(residuals),
        "future_class_sizes": sorted(map(len, residuals.values())),
        "local_state_counts": state_counts,
        "naive_product_states": prod(state_counts) if state_counts else 1,
        "reachable_local_product_states": len(tuple_to_prefixes),
        "residuals": {str(key): values for key, values in sorted(residuals.items())},
    }


def source_hashes(paths):
    return {str(path.name): sha256(path.read_bytes()).hexdigest() for path in paths}


def jsonable_constraints(constraints):
    return json.loads(json.dumps(constraints, sort_keys=True))
