"""Explicit failure of one ordinary-matching gluing of promised NOT gadgets.

Large-cycle matching existence is established by a directly checked witness,
not by a matching optimizer. Enumeration is limited to the six-vertex local
gadget and at most 4096 Boolean assignments. No universal reduction claim.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from time import perf_counter


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def build_cycle(k):
    """Vertex 6*i+j is local vertex j of gadget i; edges have stable list IDs."""
    _positive_integer(k, "k")
    edges, local_edge_ids = [], []
    for i in range(k):
        local = []
        for internal in (4, 5):
            for terminal in range(4):
                local.append(len(edges))
                edges.append([6 * i + terminal, 6 * i + internal])
        local_edge_ids.append(local)
    wire_edge_ids = []
    for i in range(k):
        wire = []
        for rail in (0, 1):
            wire.append(len(edges))
            endpoints = (6 * i + 2 + rail, 6 * ((i + 1) % k) + rail)
            edges.append(sorted(endpoints))
        wire_edge_ids.append(wire)
    return {"k": k, "vertices": 6 * k, "edges": edges,
            "local_edge_ids": local_edge_ids, "wire_edge_ids": wire_edge_ids}


def verify_matching(n, edges, matching, *, removed=()):
    """Independent edge-membership and exact vertex-coverage checker."""
    try:
        if type(n) is not int or n < 0:
            raise ValueError("invalid vertex count")
        edges, matching, removed = tuple(edges), tuple(matching), tuple(removed)
        for edge in edges:
            if type(edge) not in (list, tuple) or len(edge) != 2:
                raise ValueError("malformed graph edge")
            u, v = edge
            if type(u) is not int or type(v) is not int or not 0 <= u < v < n:
                raise ValueError("invalid graph endpoints")
        if any(type(v) is not int or not 0 <= v < n for v in removed) or len(set(removed)) != len(removed):
            raise ValueError("invalid removed vertices")
        omitted = set(removed)
        covered = set()
        for edge_id in matching:
            if type(edge_id) is not int or not 0 <= edge_id < len(edges):
                raise ValueError("invalid matching edge ID")
            u, v = edges[edge_id]
            if u in omitted or v in omitted or u in covered or v in covered:
                raise ValueError("matching touches a removed or already covered vertex")
            covered.update((u, v))
        if covered != set(range(n)) - omitted:
            raise ValueError("matching does not cover every required vertex")
        return {"valid": True, "matching_edges": len(matching), "covered_vertices": len(covered)}
    except (ValueError, TypeError, IndexError) as exc:
        return {"valid": False, "reason": str(exc)}


def local_signature():
    """Exhaust all sixteen deletion states of the fixed six-vertex gadget."""
    edges = [[terminal, internal] for internal in (4, 5) for terminal in range(4)]
    states = []
    for deleted in range(16):
        removed = [v for v in range(4) if deleted >> v & 1]
        matching_size, remainder = divmod(6 - len(removed), 2)
        witnesses = []
        if not remainder:
            for matching in combinations(range(8), matching_size):
                if verify_matching(6, edges, matching, removed=removed)["valid"]:
                    witnesses.append(list(matching))
        states.append({"deleted_mask": deleted, "feasible": bool(witnesses),
                       "matching_count": len(witnesses), "witness": witnesses[0] if witnesses else None})
    return {"vertices": 6, "edges": edges, "states": states,
            "feasible_masks": [state["deleted_mask"] for state in states if state["feasible"]],
            "promised_masks": [0, 3, 12, 15],
            "promised_feasible_masks": [state["deleted_mask"] for state in states
                                         if state["feasible"] and state["deleted_mask"] in (0, 3, 12, 15)]}


def _assignment(k, assignment):
    _positive_integer(k, "k")
    if type(assignment) is not int or assignment < 0 or assignment.bit_length() > k:
        raise ValueError("assignment must be a k-bit integer")


def boolean_satisfies(k, assignment):
    _assignment(k, assignment)
    return all(((assignment >> i) ^ (assignment >> ((i + 1) % k))) & 1 for i in range(k))


def enumerate_boolean_assignments(k, *, max_assignments=4096):
    _positive_integer(k, "k")
    if type(max_assignments) is not int or max_assignments < 1:
        raise ValueError("max_assignments must be a positive integer")
    if k >= max_assignments.bit_length():
        raise ValueError("Boolean enumeration budget exceeded")
    return {"assignments_checked": 1 << k,
            "satisfying_assignments": [word for word in range(1 << k) if boolean_satisfies(k, word)]}


def partial_rail_matching(graph):
    """Select rail zero on every wire and local edges (1,4),(3,5)."""
    matching = []
    for i in range(graph["k"]):
        matching.extend((graph["wire_edge_ids"][i][0],
                         graph["local_edge_ids"][i][1], graph["local_edge_ids"][i][7]))
    return sorted(matching)


def boolean_extension(graph, assignment):
    """Extend every satisfying assignment; x_i is gadget i's left-port bit.

    Wire i connects gadget i's right port to gadget i+1's left port, so both
    rails are chosen exactly when x_(i+1)=1. Remaining local terminals match
    to the two mandatory internal vertices.
    """
    k = graph["k"]
    if not boolean_satisfies(k, assignment):
        raise ValueError("assignment does not satisfy the cycle of NOT constraints")
    matching = []
    for i in range(k):
        if assignment >> ((i + 1) % k) & 1:
            matching.extend(graph["wire_edge_ids"][i])
        if assignment >> i & 1:
            matching.extend((graph["local_edge_ids"][i][2], graph["local_edge_ids"][i][7]))
        else:
            matching.extend((graph["local_edge_ids"][i][0], graph["local_edge_ids"][i][5]))
    matching.sort()
    if not verify_matching(graph["vertices"], graph["edges"], matching)["valid"]:
        raise ArithmeticError("Boolean extension did not produce a perfect matching")
    return matching


def boundary_states(graph, matching):
    """Read external occupancy; wire masks 1/2 violate the paired-port domain."""
    checked = verify_matching(graph["vertices"], graph["edges"], matching)
    if not checked["valid"]:
        raise ValueError(checked["reason"])
    selected = set(matching)
    wire_masks = [sum((edge_id in selected) << rail for rail, edge_id in enumerate(wire))
                  for wire in graph["wire_edge_ids"]]
    deleted_masks = []
    for i in range(graph["k"]):
        left = wire_masks[(i - 1) % graph["k"]]
        right = wire_masks[i]
        deleted_masks.append(left | (right << 2))
    invalid = [i for i, mask in enumerate(wire_masks) if mask not in (0, 3)]
    assignment = None
    if not invalid:
        assignment = sum((wire_masks[(i - 1) % graph["k"]] == 3) << i for i in range(graph["k"]))
        if not boolean_satisfies(graph["k"], assignment):
            raise ArithmeticError("fully valid matching ports failed the local NOT relation")
    return {"wire_masks": wire_masks, "local_deleted_masks": deleted_masks,
            "invalid_wires": invalid, "all_ports_valid": not invalid, "decoded_assignment": assignment}


def _source_hashes(directory):
    return {name: sha256((directory / name).read_bytes()).hexdigest()
            for name in ("not_cycle.py", "test_not_cycle.py")}


def run_experiments():
    directory = Path(__file__).resolve().parent
    before, started = _source_hashes(directory), perf_counter()
    local = local_signature()
    if local["feasible_masks"] != [3, 5, 6, 9, 10, 12] or local["promised_feasible_masks"] != [3, 12]:
        raise ArithmeticError("local NOT truth table differs from the proved signature")
    cases = []
    for k in (3, 4, 5, 7, 11):
        graph = build_cycle(k)
        matching = partial_rail_matching(graph)
        checked = verify_matching(graph["vertices"], graph["edges"], matching)
        if not checked["valid"]:
            raise ArithmeticError("explicit partial-rail witness failed coverage")
        states = boundary_states(graph, matching)
        if states["wire_masks"] != [1] * k or states["local_deleted_masks"] != [5] * k:
            raise ArithmeticError("partial-wire occupancy differs from the proved construction")
        boolean = enumerate_boolean_assignments(k)
        extensions = []
        for assignment in boolean["satisfying_assignments"]:
            extension = boolean_extension(graph, assignment)
            extension_states = boundary_states(graph, extension)
            if not extension_states["all_ports_valid"] or extension_states["decoded_assignment"] != assignment:
                raise ArithmeticError("Boolean extension did not preserve the logical assignment")
            extensions.append({"assignment": assignment, "matching_edge_ids": extension,
                               "matching_verified": True, "boundary_states": extension_states})
        if len(extensions) != (0 if k % 2 else 2):
            raise ArithmeticError("exhaustive Boolean cycle result disagrees with parity")
        graph_hash = sha256(json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        cases.append({"k": k, "graph": graph, "graph_sha256": graph_hash,
                      "matching_edge_ids": matching, "matching_verification": checked,
                      "boundary_states": states, "boolean": boolean,
                      "boolean_extensions": extensions,
                      "false_positive_for_boolean_feasibility": not bool(extensions)})
    after = _source_hashes(directory)
    if before != after:
        raise RuntimeError("source changed during the experiment")
    result = {"schema": "promised_NOT_matching_cycle_control_v1", "local_gadget": local,
              "cases": cases, "source_sha256": before, "source_unchanged_during_run": True,
              "summary": {"cycles": len(cases), "false_positives": 4, "even_positive_controls": 1,
                          "boolean_assignments_checked": sum(case["boolean"]["assignments_checked"] for case in cases),
                          "explicit_matchings_verified": sum(1 + len(case["boolean_extensions"]) for case in cases),
                          "largest_graph_vertices": max(case["graph"]["vertices"] for case in cases),
                          "general_matching_optimizer_used": False},
              "elapsed_seconds": perf_counter() - started}
    (directory / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_experiments()
    print(json.dumps(result["summary"]))
