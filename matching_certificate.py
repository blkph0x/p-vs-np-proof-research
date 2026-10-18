"""Extract and independently check an integer matching primal/dual certificate.

NetworkX supplies the blossom algorithm. A temporary per-thread profile observer
copies its final dual variables without modifying the algorithm or installation.
Every returned certificate is checked by a separate weak-duality implementation.
Unsupported internals fail closed. Only integer vertex labels and weights are used.
"""
from __future__ import annotations

import hashlib
import inspect
import sys


def verify_matching_certificate(vertices, edges, certificate):
    """Maximum-weight matching LP certificate, with all numbers doubled exactly.

    Edge inequalities: y_u+y_v+2 sum_{B contains u,v} z_B >= 2 w_uv.
    Objective: sum_v y_v + sum_B (|B|-1)z_B = 2 weight(matching).
    Here y_v=2u_v and z_B are nonnegative; B is any odd vertex set.
    Feasibility and equality prove global optimality by weak duality alone.
    """
    try:
        vertices = tuple(vertices)
        if any(type(v) is not int for v in vertices) or len(set(vertices)) != len(vertices):
            raise ValueError("vertices must be distinct integer labels")
        vertex_set = set(vertices)
        weights = {}
        for u, v, weight in edges:
            if type(u) is not int or type(v) is not int or u not in vertex_set or v not in vertex_set or u == v:
                raise ValueError("invalid edge endpoint")
            if type(weight) is not int:
                raise ValueError("edge weights must be integers")
            key = tuple(sorted((u, v)))
            if key in weights:
                raise ValueError("parallel metric edges are not allowed")
            weights[key] = weight
        if not isinstance(certificate, dict) or certificate.get("schema") != "integer_matching_dual_v1":
            raise ValueError("invalid certificate schema")
        dual = {}
        for row in certificate["vertex_duals"]:
            vertex, value = row["vertex"], row["twice_value"]
            if type(vertex) is not int or vertex not in vertex_set or vertex in dual:
                raise ValueError("invalid vertex dual label")
            if type(value) is not int or value < 0:
                raise ValueError("vertex duals must be nonnegative integers")
            dual[vertex] = value
        if set(dual) != vertex_set:
            raise ValueError("missing vertex dual")
        odd_sets = []
        seen_sets = set()
        for row in certificate["odd_set_duals"]:
            members, value = tuple(row["vertices"]), row["value"]
            if any(type(v) is not int or v not in vertex_set for v in members):
                raise ValueError("invalid odd-set vertex")
            members_set = frozenset(members)
            if len(members_set) != len(members) or len(members) < 3 or not len(members) % 2:
                raise ValueError("dual sets must be distinct-vertex odd sets of size at least three")
            if members_set in seen_sets:
                raise ValueError("duplicate odd dual set")
            if type(value) is not int or value < 0:
                raise ValueError("odd-set duals must be nonnegative integers")
            seen_sets.add(members_set)
            odd_sets.append((members_set, value))
        covered = set()
        matching_weight = 0
        for u, v in certificate["matching"]:
            if type(u) is not int or type(v) is not int or u == v or u in covered or v in covered:
                raise ValueError("invalid matching incidence")
            key = tuple(sorted((u, v)))
            if key not in weights:
                raise ValueError("matching uses nonexistent edge")
            covered.update((u, v))
            matching_weight += weights[key]
        for (u, v), weight in weights.items():
            lhs = dual[u] + dual[v] + 2 * sum(value for members, value in odd_sets if u in members and v in members)
            if lhs < 2 * weight:
                raise ValueError("infeasible matching dual edge inequality")
        dual_objective = sum(dual.values()) + sum((len(members) - 1) * value for members, value in odd_sets)
        if dual_objective != 2 * matching_weight:
            raise ValueError("primal and dual objectives differ")
        return {"valid": True, "errors": [], "matching_weight": matching_weight,
                "twice_dual_objective": dual_objective, "perfect": covered == vertex_set,
                "matched_vertices": len(covered)}
    except (KeyError, TypeError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)]}


def certified_maximum_weight_matching(vertices, edges):
    """Run exact blossom, export its dual, then require independent verification."""
    import networkx as nx
    import networkx.algorithms.matching as nx_matching

    vertices, edges = tuple(vertices), tuple(edges)
    if not vertices:
        certificate = {"schema": "integer_matching_dual_v1", "matching": [],
                       "vertex_duals": [], "odd_set_duals": []}
        verification = verify_matching_certificate(vertices, edges, certificate)
        if not verification["valid"]:
            raise ValueError(verification["errors"])
        return certificate
    graph = nx.Graph()
    graph.add_nodes_from(vertices)
    graph.add_weighted_edges_from(edges)
    source_file = inspect.getsourcefile(nx_matching)
    captured = {}

    def observe(frame, event, arg):
        if event != "return" or frame.f_code.co_filename != source_file or frame.f_code.co_name != "max_weight_matching":
            return
        local = frame.f_locals
        if "dualvar" not in local or "blossomdual" not in local:
            return
        if local.get("maxcardinality"):
            raise RuntimeError("cardinality-offset duals are not accepted")
        captured["vertex_duals"] = [{"vertex": v, "twice_value": value}
                                    for v, value in sorted(local["dualvar"].items())]
        captured["odd_set_duals"] = sorted(
            [{"vertices": sorted(blossom.leaves()), "value": value}
             for blossom, value in local["blossomdual"].items() if value],
            key=lambda row: row["vertices"])

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        matching = nx.max_weight_matching(graph, maxcardinality=False, weight="weight")
    finally:
        sys.setprofile(previous)
    if not captured:
        raise RuntimeError("installed NetworkX does not expose the expected final blossom duals")
    certificate = {"schema": "integer_matching_dual_v1",
                   "matching": sorted([sorted(pair) for pair in matching]), **captured,
                   "producer": {"networkx": nx.__version__,
                                "source_sha256": hashlib.sha256(inspect.getsource(nx_matching.max_weight_matching).encode()).hexdigest()}}
    checked = verify_matching_certificate(vertices, edges, certificate)
    if not checked["valid"]:
        raise ArithmeticError(f"matching optimality certificate rejected: {checked['errors']}")
    return certificate
