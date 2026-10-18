"""Certified minweight for parity checks with few non-incidence columns.

Columns of weight zero/one/two are graph loops/ground edges/ordinary edges.
Other columns are fixed by explicit bounded branching. Each remaining affine
coset is a minimum T-join, with an independently checked matching LP dual.
The zero branch instead uses a shortest nonempty cycle. This is a parameterized
route, not a polynomial algorithm for arbitrary binary codes.
"""
from __future__ import annotations

from collections import deque
from time import perf_counter

from matching_certificate import certified_maximum_weight_matching, verify_matching_certificate


def _rank(values):
    basis = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


def _prepare(check_rows, n, row_transform=None):
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    original = tuple(check_rows)
    if any(type(row) is not int or row < 0 or row.bit_length() > n for row in original):
        raise ValueError("parity checks must be nonnegative n-bit integers")
    r = len(original)
    transform = tuple(1 << i for i in range(r)) if row_transform is None else tuple(row_transform)
    if len(transform) != r or any(type(row) is not int or row < 0 or row.bit_length() > r for row in transform) or _rank(transform) != r:
        raise ValueError("row_transform must be an invertible square binary matrix")
    rows = []
    for combination in transform:
        row = 0
        for i, original_row in enumerate(original):
            if combination >> i & 1:
                row ^= original_row
        rows.append(row)
    columns = [0] * n
    for i, row in enumerate(rows):
        while row:
            bit = row & -row
            columns[bit.bit_length() - 1] |= 1 << i
            row ^= bit
    columns = tuple(columns)
    exceptional = tuple(j for j, column in enumerate(columns) if column.bit_count() > 2)
    edges = []
    for j, column in enumerate(columns):
        if column.bit_count() > 2:
            continue
        endpoints = []
        while column:
            bit = column & -column
            endpoints.append(bit.bit_length() - 1)
            column ^= bit
        if len(endpoints) == 0:
            edges.append((r, r, j))
        elif len(endpoints) == 1:
            edges.append((endpoints[0], r, j))
        elif len(endpoints) == 2:
            edges.append((*endpoints, j))
    return original, transform, columns, exceptional, edges, r + 1


def _adjacency(vertex_count, edges):
    adjacency = [[] for _ in range(vertex_count)]
    for u, v, coordinate in edges:
        adjacency[u].append((v, coordinate))
        if u != v:
            adjacency[v].append((u, coordinate))
    return adjacency


def _bfs(adjacency, source, banned_edge=None, stats=None):
    distances = [-1] * len(adjacency)
    parents = [None] * len(adjacency)
    distances[source] = 0
    queue = deque([source])
    if stats is not None:
        stats["bfs_calls"] += 1
    while queue:
        u = queue.popleft()
        for v, coordinate in adjacency[u]:
            if stats is not None:
                stats["adjacency_visits"] += 1
            if coordinate == banned_edge or distances[v] >= 0:
                continue
            distances[v] = distances[u] + 1
            parents[v] = u, coordinate
            queue.append(v)
    return distances, parents


def _path_word(parents, source, destination):
    word = 0
    while destination != source:
        parent, coordinate = parents[destination]
        word ^= 1 << coordinate
        destination = parent
    return word


def _syndrome(columns, word):
    value = 0
    while word:
        bit = word & -word
        value ^= columns[bit.bit_length() - 1]
        word ^= bit
    return value


def _transformed_target(target, transform):
    return sum(((row & target).bit_count() % 2) << i for i, row in enumerate(transform))


def _terminals(target, vertex_count):
    terminals = [i for i in range(vertex_count - 1) if target >> i & 1]
    if len(terminals) % 2:
        terminals.append(vertex_count - 1)
    return terminals


def shortest_nonempty_cycle(vertex_count, edges, stats=None):
    """Exact multigraph girth by edge deletion and shortest paths, with a word."""
    adjacency = _adjacency(vertex_count, edges)
    best = None
    seen_pairs = {}
    for u, v, coordinate in edges:
        if u == v:
            return {"kind": "CYCLE", "weight": 1, "word": 1 << coordinate}
    for u, v, coordinate in edges:
        pair = tuple(sorted((u, v)))
        if pair in seen_pairs:
            return {"kind": "CYCLE", "weight": 2, "word": (1 << coordinate) | (1 << seen_pairs[pair])}
        seen_pairs[pair] = coordinate
    for u, v, coordinate in edges:
        distances, parents = _bfs(adjacency, u, coordinate, stats)
        if distances[v] < 0:
            continue
        candidate = distances[v] + 1, _path_word(parents, u, v) | (1 << coordinate)
        if best is None or candidate < best:
            best = candidate
            if best[0] == 3:  # no loops or parallel edges remain
                break
    return {"kind": "CYCLE", "weight": best[0] if best else None, "word": best[1] if best else None}


def _independent_girth(vertex_count, edges):
    """Verifier uses BFS rooted at every vertex, rather than deleting each edge."""
    adjacency = _adjacency(vertex_count, edges)
    best = None
    for source in range(vertex_count):
        distances, parent_edge = [-1] * vertex_count, [-1] * vertex_count
        distances[source] = 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, coordinate in adjacency[u]:
                if distances[v] < 0:
                    distances[v] = distances[u] + 1
                    parent_edge[v] = coordinate
                    queue.append(v)
                elif coordinate != parent_edge[u] and coordinate != parent_edge[v]:
                    length = distances[u] + distances[v] + 1
                    best = length if best is None else min(best, length)
    return best


def minimum_tjoin(vertex_count, edges, target, stats=None):
    """Minimum unweighted T-join with complete integer matching dual evidence."""
    adjacency = _adjacency(vertex_count, edges)
    terminals = _terminals(target, vertex_count)
    if not terminals:
        return {"kind": "TJOIN", "word": 0, "weight": 0, "matching_certificate": None}
    distances_by_source, parents_by_source = {}, {}
    for source in terminals:
        distances, parents = _bfs(adjacency, source, stats=stats)
        component = [v for v, distance in enumerate(distances) if distance >= 0]
        if len(set(component) & set(terminals)) % 2:
            return {"kind": "INFEASIBLE", "odd_component": component}
        distances_by_source[source] = distances
        parents_by_source[source] = parents
    metric = [(u, v, distances_by_source[u][v]) for i, u in enumerate(terminals)
              for v in terminals[i + 1:] if distances_by_source[u][v] >= 0]
    scale = max(distance for _, _, distance in metric) + 1
    weighted_edges = [(u, v, scale - distance) for u, v, distance in metric]
    if stats is not None:
        stats["matching_calls"] += 1
        stats["metric_edges"] += len(metric)
    certificate = certified_maximum_weight_matching(terminals, weighted_edges)
    checked = verify_matching_certificate(terminals, weighted_edges, certificate)
    if not checked["valid"] or not checked["perfect"]:
        raise ArithmeticError("T-join matching is not certified perfect")
    word = 0
    for u, v in certificate["matching"]:
        word ^= _path_word(parents_by_source[u], u, v)
    weight = len(terminals) // 2 * scale - checked["matching_weight"]
    if word.bit_count() != weight:
        raise ArithmeticError("matching/path reconstruction weight mismatch")
    return {"kind": "TJOIN", "word": word, "weight": weight,
            "matching_certificate": certificate}


def _verify_branch(columns, edges, vertex_count, target, branch, nonzero_required):
    adjacency = _adjacency(vertex_count, edges)
    graph_mask = sum(1 << coordinate for _, _, coordinate in edges)
    terminals = _terminals(target, vertex_count)
    if not isinstance(branch, dict):
        raise ValueError("branch must be an object")
    if branch.get("kind") == "INFEASIBLE":
        component = branch["odd_component"]
        if not isinstance(component, (tuple, list)) or any(type(v) is not int or not 0 <= v < vertex_count for v in component):
            raise ValueError("invalid infeasibility component")
        subset = set(component)
        if len(subset) != len(component) or len(subset & set(terminals)) % 2 != 1:
            raise ValueError("infeasibility component has no odd terminal obstruction")
        if any((u in subset) != (v in subset) for u, v, _ in edges):
            raise ValueError("infeasibility set has graph edges leaving it")
        return None
    if branch.get("weight") is not None and (type(branch["weight"]) is not int or branch["weight"] < 0):
        raise ValueError("branch weight must be a nonnegative integer or None")
    if nonzero_required:
        if branch.get("kind") != "CYCLE" or target:
            raise ValueError("zero exceptional assignment requires a cycle certificate")
        optimum = _independent_girth(vertex_count, edges)
    else:
        if branch.get("kind") != "TJOIN":
            raise ValueError("nonzero exceptional assignment requires T-join evidence")
        if not terminals:
            optimum = 0
        else:
            distances = {u: _bfs(adjacency, u)[0] for u in terminals}
            if any(sum(distances[u][v] >= 0 for v in terminals) % 2 for u in terminals):
                raise ValueError("claimed feasible T-join has an odd terminal component")
            metric = [(u, v, distances[u][v]) for i, u in enumerate(terminals)
                      for v in terminals[i + 1:] if distances[u][v] >= 0]
            scale = max(distance for _, _, distance in metric) + 1
            checked = verify_matching_certificate(terminals, [(u, v, scale - d) for u, v, d in metric], branch["matching_certificate"])
            if not checked["valid"] or not checked["perfect"]:
                raise ValueError("matching certificate rejected")
            optimum = len(terminals) // 2 * scale - checked["matching_weight"]
    if branch.get("weight") != optimum:
        raise ValueError("branch optimum differs from independently checked optimum")
    word = branch.get("word")
    if optimum is None:
        if word is not None:
            raise ValueError("infeasible nonzero branch has a word")
        return None
    if type(word) is not int or word < 0 or word & ~graph_mask or word.bit_count() != optimum:
        raise ValueError("invalid graph word or weight")
    if _syndrome(columns, word) != target or (nonzero_required and not word):
        raise ValueError("graph word violates syndrome or nonzero requirement")
    return optimum


def verify_native_result(check_rows, n, result, *, target=0, require_nonzero=True):
    """Replay all branch certificates and reject unsupported optimality claims."""
    try:
        if not isinstance(result, dict) or result.get("schema") != "native_coset_minweight_v1":
            raise ValueError("invalid result schema")
        for field in ("distance", "upper_bound", "word"):
            value = result.get(field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{field} must be a nonnegative integer or None")
        original, transform, columns, exceptional, edges, vertex_count = _prepare(check_rows, n, result["row_transform"])
        if type(target) is not int or target < 0 or target.bit_length() > len(original) or type(require_nonzero) is not bool:
            raise ValueError("invalid requested target or nonzero condition")
        if result.get("target") != target or result.get("require_nonzero") != require_nonzero:
            raise ValueError("certificate does not match the requested affine problem")
        reported_exceptions = result["exceptional_coordinates"]
        if not isinstance(reported_exceptions, list) or any(type(j) is not int for j in reported_exceptions):
            raise ValueError("exceptional coordinates must be integer indices")
        if reported_exceptions != list(exceptional) or type(result["n"]) is not int or result["n"] != n:
            raise ValueError("representation metadata mismatch")
        original_target = result["target"]
        require_nonzero = result["require_nonzero"]
        if type(original_target) is not int or original_target < 0 or original_target.bit_length() > len(original):
            raise ValueError("invalid original target")
        if type(require_nonzero) is not bool:
            raise ValueError("require_nonzero must be Boolean")
        transformed_rhs = _transformed_target(original_target, transform)
        branch_count = 1 << len(exceptional)
        if type(result.get("dimension")) is not int or result["dimension"] != n - _rank(original):
            raise ValueError("dimension metadata mismatch")
        if type(result.get("branch_count")) is not int or result["branch_count"] != branch_count:
            raise ValueError("branch-count metadata mismatch")
        branches = result["branches"]
        if not isinstance(branches, list) or len(branches) > branch_count:
            raise ValueError("invalid branch list")
        best = None
        for assignment, branch in enumerate(branches):
            if branch.get("assignment") != assignment or type(branch.get("assignment")) is not int:
                raise ValueError("missing, duplicated or out-of-order assignment")
            fixed = sum(1 << coordinate for i, coordinate in enumerate(exceptional) if assignment >> i & 1)
            target = transformed_rhs ^ _syndrome(columns, fixed)
            need_cycle = require_nonzero and not fixed and not target
            weight = _verify_branch(columns, edges, vertex_count, target, branch, need_cycle)
            if weight is not None:
                word = fixed | branch["word"]
                candidate = word.bit_count(), word
                actual_rhs = sum(((row & word).bit_count() % 2) << i for i, row in enumerate(original))
                if actual_rhs != original_target or (require_nonzero and not word):
                    raise ValueError("reconstructed word violates original code")
                if best is None or candidate < best:
                    best = candidate
        expected_status = "EXACT" if len(branches) == branch_count else "UNKNOWN"
        if result.get("status") != expected_status:
            raise ValueError("completeness/status mismatch")
        expected_upper = best[0] if best else None
        if result.get("upper_bound") != expected_upper or result.get("word") != (best[1] if best else None):
            raise ValueError("aggregate upper-bound witness mismatch")
        if result.get("distance") != (expected_upper if expected_status == "EXACT" else None):
            raise ValueError("unsupported exact distance claim")
        return {"valid": True, "errors": [], "status": expected_status, "branches_verified": len(branches),
                "distance": result["distance"], "upper_bound": expected_upper}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"valid": False, "errors": [str(exc)]}


def solve_native(check_rows, n, *, row_transform=None, max_branches=256,
                 target=0, require_nonzero=True):
    """Minweight Hx=target; exact iff all exceptional assignments finish.

    target is a row-index bitmask in the ORIGINAL check basis. Defaults solve
    homogeneous nonzero minimum distance. Set require_nonzero=False for ordinary
    affine minimum weight, permitting the zero solution when target is zero.
    """
    if type(max_branches) is not int or max_branches < 0:
        raise ValueError("max_branches must be a nonnegative integer")
    started = perf_counter()
    original, transform, columns, exceptional, edges, vertex_count = _prepare(check_rows, n, row_transform)
    if type(target) is not int or target < 0 or target.bit_length() > len(original):
        raise ValueError("target must be a nonnegative bitmask of the original check rows")
    if type(require_nonzero) is not bool:
        raise ValueError("require_nonzero must be Boolean")
    transformed_rhs = _transformed_target(target, transform)
    stats = {"bfs_calls": 0, "adjacency_visits": 0, "matching_calls": 0, "metric_edges": 0}
    branches, best = [], None
    for assignment in range(min(1 << len(exceptional), max_branches)):
        fixed = sum(1 << coordinate for i, coordinate in enumerate(exceptional) if assignment >> i & 1)
        branch_target = transformed_rhs ^ _syndrome(columns, fixed)
        need_cycle = require_nonzero and not fixed and not branch_target
        branch = (shortest_nonempty_cycle(vertex_count, edges, stats) if need_cycle
                  else minimum_tjoin(vertex_count, edges, branch_target, stats))
        branch["assignment"] = assignment
        branches.append(branch)
        if branch.get("word") is not None:
            word = fixed | branch["word"]
            candidate = word.bit_count(), word
            if best is None or candidate < best:
                best = candidate
    complete = len(branches) == 1 << len(exceptional)
    result = {"schema": "native_coset_minweight_v1", "n": n, "dimension": n - _rank(original),
              "target": target, "require_nonzero": require_nonzero,
              "row_transform": list(transform), "exceptional_coordinates": list(exceptional),
              "branch_count": 1 << len(exceptional), "max_branches": max_branches,
              "status": "EXACT" if complete else "UNKNOWN", "branches": branches,
              "distance": best[0] if best and complete else None,
              "upper_bound": best[0] if best else None, "word": best[1] if best else None,
              "stats": stats, "solve_seconds": perf_counter() - started}
    verify_started = perf_counter()
    verification = verify_native_result(original, n, result, target=target, require_nonzero=require_nonzero)
    result["verification_seconds"] = perf_counter() - verify_started
    if not verification["valid"]:
        raise ArithmeticError(f"native result certificate rejected: {verification['errors']}")
    result["verification"] = verification
    return result
