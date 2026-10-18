"""Checked normal form for a supplied sparse-column perturbation H = B + UV.

B is a reduced graph-incidence matrix and each supplied column of U also has
weight at most two. Contracting a forest basis of U leaves graph rows, while
rank(U) remaining rows become labels. This discovers no representation of an
arbitrary input matrix. Binary vectors are Python integers; edge coordinates
are unchanged. All arithmetic is over GF(2).
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from time import perf_counter


FORMAT = "sparse-lift-normal-form-v1"


class _Limit(Exception):
    pass


class _Work:
    def __init__(self, limit):
        if type(limit) is not int or limit < 0:
            raise ValueError("work limit must be a nonnegative integer")
        self.limit = limit
        self.count = 0
        self.categories = {}

    def add(self, category, count=1):
        if self.count + count > self.limit:
            raise _Limit("explicit work limit exceeded")
        self.count += count
        self.categories[category] = self.categories.get(category, 0) + count

    def stats(self):
        return {"work_units": self.count, "work_limit": self.limit,
                "categories": dict(self.categories),
                "unit_definition": "input records, set-bit visits, graph/linear-algebra steps; integer operations have polynomial bit cost"}


def _inputs(B_rows, U_columns, V_rows, n, target, work):
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    try:
        B, U, V = tuple(B_rows), tuple(U_columns), tuple(V_rows)
    except TypeError as exc:
        raise ValueError("B rows, U columns and V rows must be iterable") from exc
    r = len(B)
    if len(U) != len(V) or target.bit_length() > r:
        raise ValueError("factor dimensions or target dimension mismatch")
    work.add("input_records", 2 + len(B) + len(U) + len(V))
    for row in B + V:
        if type(row) is not int or row < 0 or row.bit_length() > n:
            raise ValueError("B and V rows must be nonnegative n-bit integers")
    for column in U:
        if type(column) is not int or column < 0 or column.bit_length() > r or column.bit_count() > 2:
            raise ValueError("U columns must be r-bit vectors of weight at most two")
    # Bit-parallel count: columns present twice cannot occur in a third row.
    once = twice = 0
    for row in B:
        work.add("B_column_validation")
        if twice & row:
            raise ValueError("B contains a column of weight greater than two")
        twice |= once & row
        once |= row
    return B, U, V


def _hash(B, U, V, n, target):
    digest = sha256(b"sparse-lift-normal-form-input-v1\0")
    for values in ((n, target), B, U, V):
        digest.update(len(values).to_bytes(8, "big"))
        for value in values:
            encoded = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
    return digest.hexdigest()


def _endpoints(column, ground):
    if column == 0:
        return ground, ground
    first = (column & -column).bit_length() - 1
    remainder = column & (column - 1)
    return first, remainder.bit_length() - 1 if remainder else ground


def _rank(vectors, work):
    basis = {}
    for vector in vectors:
        work.add("rank_vectors")
        while vector:
            work.add("rank_elimination_steps")
            pivot = vector.bit_length() - 1
            if pivot in basis:
                vector ^= basis[pivot]
            else:
                basis[pivot] = vector
                break
    return len(basis)


def build_sparse_lift_normal_form(B_rows, U_columns, V_rows, n, *, target=0,
                                  max_work=1000000):
    """Return EXACT with a normal-form certificate, or UNKNOWN on the work cap.

    Invalid input raises ValueError. Q acts on rows/syndromes, not coordinates:
    certificate['rows'] == QH, transformed_target == Q target. The first
    graph_rows rows have columns of weight <=2, and label_rows == rank(U).
    No column is removed, merged, or reordered.
    """
    started = perf_counter()
    work = _Work(max_work)
    provenance = {"algorithm": FORMAT,
                  "module_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        B, U, V = _inputs(B_rows, U_columns, V_rows, n, target, work)
        r = len(B)
        provenance["input_sha256"] = _hash(B, U, V, n, target)
        parents, sizes = list(range(r + 1)), [1] * (r + 1)

        def find(vertex):
            while parents[vertex] != vertex:
                work.add("union_find_steps")
                parents[vertex] = parents[parents[vertex]]
                vertex = parents[vertex]
            return vertex

        forest = []
        for edge_id, column in enumerate(U):
            work.add("U_columns_scanned")
            a, b = _endpoints(column, r)
            a, b = find(a), find(b)
            if a != b:
                if sizes[a] < sizes[b]:
                    a, b = b, a
                parents[b] = a
                sizes[a] += sizes[b]
                forest.append(edge_id)
        groups = {}
        for vertex in range(r + 1):
            work.add("component_vertices")
            groups.setdefault(find(vertex), []).append(vertex)
        components = sorted(groups.values(), key=lambda group: group[0])
        non_ground = [group for group in components if r not in group]
        representatives = {group[0] for group in non_ground}
        Q = []
        for group in non_ground:
            vector = 0
            for vertex in group:
                work.add("component_indicator_entries")
                vector |= 1 << vertex
            Q.append(vector)
        Q.extend(1 << vertex for vertex in range(r) if vertex not in representatives)
        work.add("unit_completion_rows", r - len(non_ground))
        H = list(B)
        for column, row in zip(U, V):
            while column:
                work.add("outer_product_entries")
                bit = column & -column
                H[bit.bit_length() - 1] ^= row
                column ^= bit
        rows, transformed_target = [], 0
        for i, combination in enumerate(Q):
            work.add("transformed_rows")
            value = 0
            remaining = combination
            while remaining:
                work.add("row_xor_terms")
                bit = remaining & -remaining
                value ^= H[bit.bit_length() - 1]
                remaining ^= bit
            rows.append(value)
            transformed_target |= ((combination & target).bit_count() & 1) << i
        certificate = {"format": FORMAT, "n": n, "r": r,
                       "input_hash": provenance["input_sha256"], "H_rows": H,
                       "row_transform": Q, "rows": rows,
                       "graph_rows": len(non_ground), "label_rows": len(forest),
                       "forest_columns": forest, "components": components,
                       "target": target, "transformed_target": transformed_target}
        result = {"status": "EXACT", "certificate": certificate, "reason": None,
                  "provenance": provenance, "stats": work.stats()}
    except _Limit as exc:
        result = {"status": "UNKNOWN", "certificate": None, "reason": str(exc),
                  "provenance": provenance, "stats": work.stats()}
    result["stats"]["elapsed_seconds"] = perf_counter() - started
    return result


def _vector_list(values, size, bits, name):
    if type(values) not in (list, tuple) or len(values) != size:
        raise ValueError(f"{name} has wrong length")
    if any(type(value) is not int or value < 0 or value.bit_length() > bits for value in values):
        raise ValueError(f"{name} contains an invalid binary vector")
    return values


def verify_sparse_lift_normal_form(B_rows, U_columns, V_rows, n, certificate, *,
                                   target=0, verification_work_limit=1000000):
    """Check the supplied decomposition and normal form independently.

    The verifier uses DFS connectivity, binary ranks, explicit matrix products,
    and column counts. It does not call the producer or trust its forest/graph.
    Return valid/status/errors/stats; UNKNOWN means the verifier cap was reached.
    """
    started = perf_counter()
    work = None
    try:
        work = _Work(verification_work_limit)
        B, U, V = _inputs(B_rows, U_columns, V_rows, n, target, work)
        r = len(B)
        fields = {"format", "n", "r", "input_hash", "H_rows", "row_transform", "rows",
                  "graph_rows", "label_rows", "forest_columns", "components", "target", "transformed_target"}
        if type(certificate) is not dict or set(certificate) != fields:
            raise ValueError("invalid normal-form certificate fields")
        if certificate["format"] != FORMAT or certificate["input_hash"] != _hash(B, U, V, n, target):
            raise ValueError("certificate does not match supplied factorization")
        for key, expected in (("n", n), ("r", r), ("target", target)):
            if type(certificate[key]) is not int or certificate[key] != expected:
                raise ValueError("certificate dimension or target mismatch")
        Q = _vector_list(certificate["row_transform"], r, r, "row transform")
        rows = _vector_list(certificate["rows"], r, n, "transformed rows")
        H = _vector_list(certificate["H_rows"], r, n, "original H rows")
        if _rank(Q, work) != r:
            raise ValueError("row transform is singular")
        p = _rank(U, work)
        if type(certificate["label_rows"]) is not int or certificate["label_rows"] != p:
            raise ValueError("label-row count differs from rank(U)")
        graph_rows = certificate["graph_rows"]
        if type(graph_rows) is not int or graph_rows != r - p:
            raise ValueError("graph-row count is inconsistent")
        expected_H = []
        for i in range(r):
            row = B[i]
            for column, value in zip(U, V):
                work.add("independent_product_terms")
                if column >> i & 1:
                    row ^= value
            expected_H.append(row)
        if list(H) != expected_H:
            raise ValueError("H is not B+UV")
        expected_rows, expected_target = [], 0
        for i, combination in enumerate(Q):
            row = 0
            for j in range(r):
                work.add("independent_transform_terms")
                if combination >> j & 1:
                    row ^= H[j]
            expected_rows.append(row)
            expected_target |= ((combination & target).bit_count() & 1) << i
        if list(rows) != expected_rows:
            raise ValueError("transformed rows are not QH")
        if type(certificate["transformed_target"]) is not int or certificate["transformed_target"] != expected_target:
            raise ValueError("transformed target is not Q target")
        counts = {}
        for row in rows[:graph_rows]:
            remaining = row
            while remaining:
                work.add("graph_column_entries")
                bit = remaining & -remaining
                counts[bit] = counts.get(bit, 0) + 1
                if counts[bit] > 2:
                    raise ValueError("graph part contains a column of weight above two")
                remaining ^= bit
        adjacency = [[] for _ in range(r + 1)]
        for column in U:
            work.add("verification_U_edges")
            a, b = _endpoints(column, r)
            if a != b:
                adjacency[a].append(b)
                adjacency[b].append(a)
        visited, components = set(), []
        for start in range(r + 1):
            if start in visited:
                continue
            visited.add(start)
            queue, group = [start], []
            while queue:
                vertex = queue.pop()
                work.add("dfs_vertices")
                group.append(vertex)
                for neighbor in adjacency[vertex]:
                    work.add("dfs_arcs")
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(sorted(group))
        supplied_components = certificate["components"]
        if type(supplied_components) not in (list, tuple) or any(type(group) not in (list, tuple) for group in supplied_components):
            raise ValueError("invalid component partition")
        if any(type(vertex) is not int for group in supplied_components for vertex in group):
            raise ValueError("component vertices must be integers")
        if [list(group) for group in supplied_components] != components:
            raise ValueError("component partition does not match the U graph")
        expected_top = []
        for group in components:
            if r not in group:
                indicator = 0
                for vertex in group:
                    indicator |= 1 << vertex
                expected_top.append(indicator)
        if list(Q[:graph_rows]) != expected_top:
            raise ValueError("top functionals are not quotient component indicators")
        for combination in Q[:graph_rows]:
            for column in U:
                work.add("annihilator_checks")
                if (combination & column).bit_count() & 1:
                    raise ValueError("graph-row functional does not annihilate U")
        forest = certificate["forest_columns"]
        if type(forest) not in (list, tuple) or len(forest) != p:
            raise ValueError("invalid forest basis size")
        if any(type(index) is not int or not 0 <= index < len(U) for index in forest) or len(set(forest)) != p:
            raise ValueError("invalid or duplicate forest edge IDs")
        if _rank([U[index] for index in forest], work) != p:
            raise ValueError("selected forest columns are not a basis of U")
        result = {"valid": True, "status": "EXACT", "errors": []}
    except _Limit as exc:
        result = {"valid": False, "status": "UNKNOWN", "errors": [str(exc)]}
    except (ValueError, TypeError, IndexError, KeyError, OverflowError) as exc:
        result = {"valid": False, "status": "INVALID", "errors": [str(exc)]}
    result["stats"] = work.stats() if work is not None else {"work_units": 0}
    result["stats"]["elapsed_seconds"] = perf_counter() - started
    return result
