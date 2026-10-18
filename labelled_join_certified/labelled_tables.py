"""Certified labelled shortest-path tables for zero/two-terminal graph joins.

Edges are (u, v, label, nonnegative_integer_weight); their positions are stable
edge IDs. This module implements the reviewed LABELLED_JOIN_DESIGN.md, for
integer weights only. Its independent verifier uses local certificate checks,
not shortest-path search. Explicit caps return UNKNOWN, never a partial optimum.
"""
from __future__ import annotations

from hashlib import sha256
from heapq import heappop, heappush
from pathlib import Path
from time import perf_counter


FORMAT = "labelled-join-tables-v1"
_TOKEN = object()


class _Limit(Exception):
    pass


def _natural(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _prepare(n, edges, p):
    _natural(n, "n")
    _natural(p, "p")
    try:
        edges = tuple(edges)
    except TypeError as exc:
        raise ValueError("edges must be an iterable of four-field records") from exc
    normalized = []
    for edge in edges:
        if type(edge) not in (list, tuple) or len(edge) != 4:
            raise ValueError("each edge must be (u,v,label,weight)")
        u, v, label, weight = edge
        if any(type(value) is not int for value in edge):
            raise ValueError("edge fields must be integers, excluding bool")
        if not 0 <= u < n or not 0 <= v < n:
            raise ValueError("edge endpoint outside graph")
        if label < 0 or label.bit_length() > p or weight < 0:
            raise ValueError("invalid label or negative weight")
        normalized.append((u, v, label, weight))
    return tuple(normalized)


def _input_hash(n, edges, p):
    digest = sha256(b"labelled-join-input-v1\0")
    for value in (n, p, len(edges)):
        data = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    for edge in edges:
        for value in edge:
            data = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
    return digest.hexdigest()


def _dimensions(n, p, max_states, max_total_states):
    # Guard before shifting: a hostile p such as 10**9 must not allocate 2**p.
    label_cap = min(max_states, max_total_states)
    if label_cap == 0 or p >= label_cap.bit_length():
        raise _Limit("state cap excludes the label-space table")
    labels = 1 << p
    per_source = n * labels
    total = n * per_source + labels
    if max(labels, per_source) > max_states:
        raise _Limit("per-table state cap exceeded")
    if total > max_total_states:
        raise _Limit("total certificate state cap exceeded")
    return labels, per_source, total


def _search(size, source, neighbors, stats, max_relaxations, phase):
    dist, parent, depth = [None] * size, [None] * size, [None] * size
    stats["allocated_states"] += size
    stats["searches_started"] += 1
    dist[source], depth[source] = 0, 0
    queue = [(0, source)]
    stats["heap_pushes"] += 1
    while queue:
        distance, state = heappop(queue)
        stats["heap_pops"] += 1
        if distance != dist[state]:
            continue
        for destination, edge_id, weight in neighbors(state):
            if stats["relaxations"] >= max_relaxations:
                raise _Limit("relaxation cap exceeded")
            stats["relaxations"] += 1
            stats[phase + "_relaxations"] += 1
            candidate = distance + weight
            if dist[destination] is None or candidate < dist[destination]:
                dist[destination] = candidate
                parent[destination] = [state, edge_id]
                depth[destination] = depth[state] + 1
                heappush(queue, (candidate, destination))
                stats["heap_pushes"] += 1
    stats["searches_completed"] += 1
    return {"dist": dist, "parent": parent, "depth": depth}


def build_tables(n, edges, p, *, max_states=4096, max_total_states=1000000,
                 max_relaxations=1000000):
    """Return EXACT with certificate, or UNKNOWN with no certificate on a cap.

    max_states bounds max(n*2**p, 2**p); max_total_states bounds n*n*2**p+2**p.
    The latter counts path-table states, each with three fields; closed-cost
    arrays and adjacency require additional O(2**p+n+m) storage. Every directed
    arc attempted by a search counts against max_relaxations, before processing.
    Input validation/setup, allocation, heaps and closed minima are counted
    separately in stats. Invalid inputs or limits raise ValueError.
    """
    start = perf_counter()
    edges = _prepare(n, edges, p)
    for name, value in (("max_states", max_states), ("max_total_states", max_total_states),
                        ("max_relaxations", max_relaxations)):
        _natural(value, name)
    stats = {"input_edges": len(edges), "input_fields_checked": 2 + 4 * len(edges),
             "allocated_states": 0, "searches_started": 0, "searches_completed": 0,
             "relaxations": 0, "lift_relaxations": 0, "label_relaxations": 0,
             "heap_pushes": 0, "heap_pops": 0, "closed_candidates": 0,
             "adjacency_entries": 0}
    input_hash = _input_hash(n, edges, p)
    provenance = {"algorithm": FORMAT, "input_sha256": input_hash,
                  "module_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    limits = {"max_states": max_states, "max_total_states": max_total_states,
              "max_relaxations": max_relaxations}
    try:
        labels, per_source, total = _dimensions(n, p, max_states, max_total_states)
        stats.update(label_states=labels, lift_states_per_source=per_source,
                     required_total_states=total)
        adjacency = [[] for _ in range(n)]
        for edge_id, (u, v, label, weight) in enumerate(edges):
            adjacency[u].append((v, edge_id, label, weight))
            if u != v:
                adjacency[v].append((u, edge_id, label, weight))
        stats["adjacency_entries"] = sum(map(len, adjacency))

        def lift_neighbors(state):
            vertex, label = divmod(state, labels)
            for other, edge_id, edge_label, weight in adjacency[vertex]:
                yield other * labels + (label ^ edge_label), edge_id, weight

        lifted = [_search(per_source, vertex * labels, lift_neighbors, stats,
                          max_relaxations, "lift") for vertex in range(n)]
        closed_cost, closed_source = [None] * labels, [None] * labels
        closed_cost[0] = 0
        for label in range(1, labels):
            for vertex in range(n):
                stats["closed_candidates"] += 1
                distance = lifted[vertex]["dist"][vertex * labels + label]
                if distance is not None and (closed_cost[label] is None or distance < closed_cost[label]):
                    closed_cost[label], closed_source[label] = distance, vertex
        finite_steps = tuple((label, cost) for label, cost in enumerate(closed_cost)
                             if label and cost is not None)

        def label_neighbors(state):
            for label, cost in finite_steps:
                yield state ^ label, label, cost

        eulerian = _search(labels, 0, label_neighbors, stats, max_relaxations, "label")
        certificate = {"format": FORMAT, "n": n, "p": p, "edge_hash": input_hash,
                       "lift": lifted, "closed_cost": closed_cost,
                       "closed_source": closed_source, "eulerian": eulerian}
        stats["elapsed_seconds"] = perf_counter() - start
        return {"status": "EXACT", "certificate": certificate, "stats": stats,
                "limits": limits, "provenance": provenance, "reason": None}
    except _Limit as exc:
        stats["elapsed_seconds"] = perf_counter() - start
        return {"status": "UNKNOWN", "certificate": None, "stats": stats,
                "limits": limits, "provenance": provenance, "reason": str(exc)}


def _array(value, size, name):
    if type(value) not in (list, tuple) or len(value) != size:
        raise ValueError(f"{name} has wrong shape")
    return value


def _table_shape(table, size, root, stats):
    if type(table) is not dict or set(table) != {"dist", "parent", "depth"}:
        raise ValueError("path table has invalid fields")
    dist = _array(table["dist"], size, "distance array")
    parent = _array(table["parent"], size, "parent array")
    depth = _array(table["depth"], size, "depth array")
    for state in range(size):
        stats["state_checks"] += 1
        if dist[state] is None:
            if parent[state] is not None or depth[state] is not None:
                raise ValueError("unreachable state has predecessor or depth")
            continue
        if type(dist[state]) is not int or dist[state] < 0:
            raise ValueError("distance must be a nonnegative integer or None")
        if type(depth[state]) is not int or not 0 <= depth[state] < size:
            raise ValueError("invalid predecessor depth")
        if state == root:
            if dist[state] != 0 or depth[state] != 0 or parent[state] is not None:
                raise ValueError("source must have distance/depth zero and no predecessor")
        else:
            pointer = _array(parent[state], 2, "predecessor")
            if any(type(value) is not int for value in pointer) or not 0 <= pointer[0] < size:
                raise ValueError("invalid predecessor indices")
            if depth[state] == 0:
                raise ValueError("only the source can have depth zero")
    if dist[root] != 0:
        raise ValueError("source is unreachable")
    return dist, parent, depth


def _bellman(dist, source, destination, weight, stats, arc_limit):
    if stats["arc_checks"] >= arc_limit:
        raise _Limit("verification arc cap exceeded")
    stats["arc_checks"] += 1
    if dist[source] is not None:
        if dist[destination] is None:
            raise ValueError("claimed reachable set is not closed under arcs")
        if dist[destination] > dist[source] + weight:
            raise ValueError("Bellman inequality violated")


def verify_tables(n, edges, p, certificate, *, verification_state_limit=1000000,
                  verification_arc_limit=10000000):
    """Independently verify all arcs and rooted predecessor paths; no Dijkstra.

    Return {'valid':bool, 'status':EXACT/INVALID/UNKNOWN, 'errors':[], 'stats':...}.
    UNKNOWN means a verifier resource cap prevented validation. State budget
    covers n*n*2**p+2**p before any exponential allocation. Arc budget counts
    every Bellman arc including arcs out of unreachable states; parent checks
    and closed-minimum comparisons are counted separately. Extra/missing schema
    fields, malformed inputs and graph mismatch fail closed as INVALID.
    """
    start = perf_counter()
    stats = {"state_checks": 0, "parent_checks": 0, "arc_checks": 0,
             "closed_comparisons": 0}
    try:
        edges = _prepare(n, edges, p)
        _natural(verification_state_limit, "verification_state_limit")
        _natural(verification_arc_limit, "verification_arc_limit")
        labels, per_source, total = _dimensions(n, p, verification_state_limit,
                                               verification_state_limit)
        stats["required_total_states"] = total
        fields = {"format", "n", "p", "edge_hash", "lift", "closed_cost", "closed_source", "eulerian"}
        if type(certificate) is not dict or set(certificate) != fields:
            raise ValueError("certificate has invalid fields")
        if certificate["format"] != FORMAT or type(certificate["n"]) is not int or type(certificate["p"]) is not int:
            raise ValueError("invalid certificate format or dimensions")
        if certificate["n"] != n or certificate["p"] != p or certificate["edge_hash"] != _input_hash(n, edges, p):
            raise ValueError("certificate does not match supplied graph")
        lifted = _array(certificate["lift"], n, "lift sources")
        for vertex, table in enumerate(lifted):
            dist, parent, depth = _table_shape(table, per_source, vertex * labels, stats)
            for state, pointer in enumerate(parent):
                if pointer is None:
                    continue
                stats["parent_checks"] += 1
                previous, edge_id = pointer
                if not 0 <= edge_id < len(edges) or dist[previous] is None:
                    raise ValueError("invalid lifted predecessor edge or unreachable parent")
                a, b, edge_label, weight = edges[edge_id]
                prior_vertex, prior_label = divmod(previous, labels)
                current_vertex, current_label = divmod(state, labels)
                if not ((prior_vertex == a and current_vertex == b) or (prior_vertex == b and current_vertex == a)):
                    raise ValueError("predecessor edge has wrong endpoints")
                if current_label != prior_label ^ edge_label:
                    raise ValueError("predecessor edge has wrong label")
                if dist[state] != dist[previous] + weight or depth[state] != depth[previous] + 1:
                    raise ValueError("predecessor does not realize a rooted shortest path")
            for u, v, edge_label, weight in edges:
                for label in range(labels):
                    a, b = u * labels + label, v * labels + (label ^ edge_label)
                    _bellman(dist, a, b, weight, stats, verification_arc_limit)
                    if u != v:
                        _bellman(dist, b, a, weight, stats, verification_arc_limit)
        closed = _array(certificate["closed_cost"], labels, "closed costs")
        sources = _array(certificate["closed_source"], labels, "closed sources")
        if type(closed[0]) is not int or closed[0] != 0 or sources[0] is not None:
            raise ValueError("label-zero closed walk must be the empty walk")
        for label in range(1, labels):
            best = None
            for vertex in range(n):
                stats["closed_comparisons"] += 1
                candidate = lifted[vertex]["dist"][vertex * labels + label]
                if candidate is not None and (best is None or candidate < best):
                    best = candidate
            if closed[label] is not None and type(closed[label]) is not int:
                raise ValueError("closed cost must be integer or None")
            if closed[label] != best:
                raise ValueError("closed cost is not the minimum over every base source")
            if best is None:
                if sources[label] is not None:
                    raise ValueError("unreachable closed walk has a source")
            elif type(sources[label]) is not int or not 0 <= sources[label] < n:
                raise ValueError("invalid realizing closed-walk source")
            elif lifted[sources[label]]["dist"][sources[label] * labels + label] != best:
                raise ValueError("closed-walk source does not realize its cost")
        dist, parent, depth = _table_shape(certificate["eulerian"], labels, 0, stats)
        for state, pointer in enumerate(parent):
            if pointer is None:
                continue
            stats["parent_checks"] += 1
            previous, step = pointer
            if not 0 < step < labels or closed[step] is None or dist[previous] is None:
                raise ValueError("invalid label-space predecessor")
            if state != previous ^ step or dist[state] != dist[previous] + closed[step] or depth[state] != depth[previous] + 1:
                raise ValueError("label predecessor does not realize a rooted shortest path")
        finite_steps = tuple((step, cost) for step, cost in enumerate(closed)
                             if step and cost is not None)
        for state in range(labels):
            for step, cost in finite_steps:
                _bellman(dist, state, state ^ step, cost, stats, verification_arc_limit)
        result = {"valid": True, "status": "EXACT", "errors": [], "stats": stats}
    except _Limit as exc:
        result = {"valid": False, "status": "UNKNOWN", "errors": [str(exc)], "stats": stats}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        result = {"valid": False, "status": "INVALID", "errors": [str(exc)], "stats": stats}
    stats["elapsed_seconds"] = perf_counter() - start
    return result


def _freeze_table(table):
    return (tuple(table["dist"]),
            tuple(None if value is None else tuple(value) for value in table["parent"]),
            tuple(table["depth"]))


def _thaw_table(table):
    return {"dist": list(table[0]), "parent": [None if value is None else list(value) for value in table[1]],
            "depth": list(table[2])}


class VerifiedTables:
    """Immutable table snapshot created only by load_verified_tables.

    Query witnesses use original edge-ID bitmasks. Individual lifted walk XORs
    may cost less than their walk distances; only final Eulerian/pair optima
    have equality. Zero-boundary label-zero permits the empty edge set.
    """
    __slots__ = ("n", "p", "edges", "_labels", "_lift", "_closed", "_sources", "_eulerian", "_hash")

    def __init__(self, token, n, edges, p, certificate):
        if token is not _TOKEN:
            raise ValueError("use load_verified_tables to construct verified tables")
        for name, value in (("n", n), ("p", p), ("edges", edges), ("_labels", 1 << p),
                            ("_lift", tuple(_freeze_table(t) for t in certificate["lift"])),
                            ("_closed", tuple(certificate["closed_cost"])),
                            ("_sources", tuple(certificate["closed_source"])),
                            ("_eulerian", _freeze_table(certificate["eulerian"])),
                            ("_hash", certificate["edge_hash"])):
            object.__setattr__(self, name, value)

    def __setattr__(self, name, value):
        raise AttributeError("verified tables are immutable")

    @property
    def certificate(self):
        return self.as_certificate()

    def as_certificate(self):
        return {"format": FORMAT, "n": self.n, "p": self.p, "edge_hash": self._hash,
                "lift": [_thaw_table(table) for table in self._lift],
                "closed_cost": list(self._closed), "closed_source": list(self._sources),
                "eulerian": _thaw_table(self._eulerian)}

    def _label(self, target):
        if type(target) is not int or not 0 <= target < self._labels:
            raise ValueError("target label outside label space")

    def _vertex(self, vertex):
        if type(vertex) is not int or not 0 <= vertex < self.n:
            raise ValueError("vertex outside graph")

    def lift_distance(self, source, destination, label):
        self._vertex(source)
        self._vertex(destination)
        self._label(label)
        return self._lift[source][0][destination * self._labels + label]

    def lift_word(self, source, destination, label):
        if self.lift_distance(source, destination, label) is None:
            return None
        state, root = destination * self._labels + label, source * self._labels
        word, parents = 0, self._lift[source][1]
        while state != root:
            state, edge_id = parents[state]
            word ^= 1 << edge_id
        return word

    def eulerian_join(self, target):
        self._label(target)
        weight = self._eulerian[0][target]
        if weight is None:
            return {"status": "EXACT", "weight": None, "word": None}
        state, word = target, 0
        while state:
            previous, step = self._eulerian[1][state]
            source = self._sources[step]
            word ^= self.lift_word(source, source, step)
            state = previous
        self._check_word(word, 0, target, weight)
        return {"status": "EXACT", "weight": weight, "word": word}

    def pair_join(self, u, v, target):
        self._vertex(u)
        self._vertex(v)
        self._label(target)
        if u == v:
            raise ValueError("pair_join requires two distinct terminals")
        best = None
        for label in range(self._labels):
            distance = self._lift[u][0][v * self._labels + label]
            correction = self._eulerian[0][target ^ label]
            if distance is not None and correction is not None:
                candidate = distance + correction, label
                if best is None or candidate < best:
                    best = candidate
        if best is None:
            return {"status": "EXACT", "weight": None, "word": None}
        weight, label = best
        word = self.lift_word(u, v, label) ^ self.eulerian_join(target ^ label)["word"]
        self._check_word(word, (1 << u) ^ (1 << v), target, weight)
        return {"status": "EXACT", "weight": weight, "word": word}

    def _check_word(self, word, boundary, target, weight):
        actual_boundary = actual_label = actual_weight = 0
        for edge_id, (u, v, label, cost) in enumerate(self.edges):
            if word >> edge_id & 1:
                actual_boundary ^= (1 << u) ^ (1 << v)
                actual_label ^= label
                actual_weight += cost
        if (actual_boundary, actual_label, actual_weight) != (boundary, target, weight):
            raise ArithmeticError("verified optimum reconstruction invariant failed")


def load_verified_tables(n, edges, p, certificate, *, verification_state_limit=1000000,
                         verification_arc_limit=10000000):
    """Validate once and freeze an isolated snapshot for repeated queries.

    Validation errors and verifier resource exhaustion raise ValueError; inspect
    verify_tables directly when INVALID versus UNKNOWN needs to be preserved.
    """
    edges = _prepare(n, edges, p)
    checked = verify_tables(n, edges, p, certificate,
                            verification_state_limit=verification_state_limit,
                            verification_arc_limit=verification_arc_limit)
    if not checked["valid"]:
        raise ValueError(checked["status"] + ": " + "; ".join(checked["errors"]))
    return VerifiedTables(_TOKEN, n, edges, p, certificate)
