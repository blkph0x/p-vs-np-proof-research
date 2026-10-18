"""Budgeted search for recursive Horn/affine backdoor decision trees."""
from __future__ import annotations

from itertools import product

import backdoor_solver as native
import engine


def _target_tag(target: str) -> str:
    if target == "HORN":
        return "AND"
    if target == "AFFINE":
        return "MIN"
    raise ValueError("target must be HORN or AFFINE")


def _residual(constraints, assignment):
    return tuple(native.restrict(c, assignment) for c in constraints)


def _target_obstruction(residual, tag):
    for index, constraint in enumerate(residual):
        signature = sorted(engine.relation_signature(constraint.relation,
                                                     len(constraint.scope)))
        if constraint.relation and tag not in signature:
            return {"constraint": index, "scope": list(constraint.scope),
                    "signature": signature}
    return None


def solve_recursive(n: int, constraints: tuple[native.Constraint, ...], target: str,
                    max_depth: int, *, max_nodes: int = 10000) -> dict[str, object]:
    """Search all bounded branching choices, charging every search node.

    A SAT result needs one checked witness.  An UNSAT result requires both
    children of every internal node to be UNSAT.  Any unexplored or capped
    branch keeps the top-level result UNKNOWN.
    """
    if type(max_depth) is not int or max_depth < 0:
        raise ValueError("max_depth must be a nonnegative integer")
    if type(max_nodes) is not int or max_nodes <= 0:
        raise ValueError("max_nodes must be a positive integer")
    constraints = tuple(constraints)
    backdoor_solver_validate = getattr(native, "_validate")
    backdoor_solver_validate(n, constraints, ())
    tag = _target_tag(target)
    ledger = {"nodes": 0, "candidate_trials": 0, "max_nodes": max_nodes,
              "max_depth": max_depth}

    def search(assignment: dict[int, int], depth: int):
        if ledger["nodes"] >= max_nodes:
            return {"status": "UNKNOWN", "reason": "NODE_LIMIT"}
        ledger["nodes"] += 1
        residual = _residual(constraints, assignment)
        obstruction = _target_obstruction(residual, tag)
        if obstruction is None:
            if target == "HORN":
                sat, witness = native.solve_horn(n, residual)
            else:
                sat, witness = native.solve_affine(n, residual)
            node = {"kind": "NATIVE", "assignment": dict(assignment),
                    "status": "SAT" if sat else "UNSAT",
                    "residual_signatures": [
                        sorted(engine.relation_signature(c.relation, len(c.scope)))
                        for c in residual]}
            if sat:
                full = list(witness or ())
                for variable, bit in assignment.items():
                    full[variable] = bit
                candidate = tuple(full)
                if not native._check_witness(n, constraints, candidate):
                    raise AssertionError("recursive native witness failed original check")
                node["witness"] = list(candidate)
                return {"status": "SAT", "node": node, "witness": list(candidate)}
            return {"status": "UNSAT", "node": node}
        if depth == 0:
            return {"status": "UNKNOWN", "reason": "DEPTH_LIMIT",
                    "node": {"kind": "CAP", "assignment": dict(assignment),
                             "obstruction": obstruction}}

        # A variable outside this obstruction cannot change its relation, so
        # branching there would waste one level.  Trying every local variable
        # makes the search complete for decision trees of the requested depth.
        for variable in obstruction["scope"]:
            ledger["candidate_trials"] += 1
            children = []
            for bit in (0, 1):
                child = search({**assignment, variable: bit}, depth - 1)
                children.append(child)
                if child["status"] == "SAT":
                    node = {"kind": "BRANCH", "variable": variable,
                            "assignment": dict(assignment), "children": children}
                    return {"status": "SAT", "node": node,
                            "witness": child["witness"]}
                if child["status"] == "UNKNOWN":
                    break
            if len(children) == 2 and all(child["status"] == "UNSAT" for child in children):
                node = {"kind": "BRANCH", "variable": variable,
                        "assignment": dict(assignment), "children": children}
                return {"status": "UNSAT", "node": node}
        return {"status": "UNKNOWN", "reason": "NO_DECISION_TREE_WITHIN_BUDGET",
                "node": {"kind": "CAP", "assignment": dict(assignment),
                         "obstruction": obstruction}}

    result = search({}, max_depth)
    return {"status": result["status"], "target": target,
            "max_depth": max_depth, "max_nodes": max_nodes,
            "ledger": ledger, "tree": result.get("node"),
            "witness": result.get("witness"),
            "reason": result.get("reason")}
