"""Exact syndrome compression of exceptional columns, with replayable evidence.

The exceptional coordinates are DISJOINT from the graph coordinates. This is
not a solver for an arbitrary low-rank perturbation of a graphic matrix.
Complexity is O(q*2**p) plus at most 2**p+1 polynomial graph calls, where p is
the rank of the q exceptional columns. Exponential worst cases remain.
"""
from __future__ import annotations

from time import perf_counter

from native_coset_solver import (
    _prepare, _rank, _syndrome, _transformed_target, _verify_branch,
    minimum_tjoin, shortest_nonempty_cycle,
)


def _request(original, target, require_nonzero):
    if type(target) is not int or target < 0 or target.bit_length() > len(original):
        raise ValueError("target must be an original-row bitmask")
    if type(require_nonzero) is not bool:
        raise ValueError("require_nonzero must be Boolean")


def _specifications(nonempty, target, require_nonzero):
    """One cheapest exceptional word per syndrome; zero needs two possibilities."""
    yield 0, 0, bool(require_nonzero and target == 0)
    for syndrome in sorted(nonempty):
        if syndrome or (require_nonzero and target == 0):
            yield syndrome, nonempty[syndrome][1], False


def solve_rank_native(check_rows, n, *, row_transform=None, target=0,
                      require_nonzero=True, max_states=256,
                      max_dp_transitions=1_000_000, max_graph_calls=257):
    """Solve Hx=target, with explicit independent state/transition/graph caps.

    A state limit is checked before the potentially exponential DP allocation.
    A partial DP does not certify missing syndromes. A partial graph pass keeps
    only witnessed upper bounds. EXACT requires every DP layer and graph case.
    """
    for cap in (max_states, max_dp_transitions, max_graph_calls):
        if type(cap) is not int or cap < 0:
            raise ValueError("work caps must be nonnegative integers")
    started = perf_counter()
    original, transform, columns, exceptional, edges, vertices = _prepare(check_rows, n, row_transform)
    _request(original, target, require_nonzero)
    rhs = _transformed_target(target, transform)
    rank = _rank(columns[j] for j in exceptional)
    state_count = 1 << rank
    layers, transitions, processed = [[]], 0, 0
    nonempty = {}
    stop_reason = None
    if state_count > max_states:
        stop_reason = "STATE_LIMIT"
    else:
        for coordinate in exceptional:
            needed = len(nonempty) + 1
            if transitions + needed > max_dp_transitions:
                stop_reason = "DP_LIMIT"
                break
            column, bit = columns[coordinate], 1 << coordinate
            updated = dict(nonempty)
            candidate = (1, bit)
            if column not in updated or candidate < updated[column]:
                updated[column] = candidate
            for syndrome, (cost, word) in nonempty.items():
                next_syndrome = syndrome ^ column
                candidate = (cost + 1, word | bit)
                if next_syndrome not in updated or candidate < updated[next_syndrome]:
                    updated[next_syndrome] = candidate
            nonempty = updated
            transitions += needed
            processed += 1
            layers.append([[s, value[0]] for s, value in sorted(nonempty.items())])
    dp_complete = stop_reason is None and processed == len(exceptional)
    witnesses = [[s, cost, word] for s, (cost, word) in sorted(nonempty.items())] if dp_complete else []
    stats = {"bfs_calls": 0, "adjacency_visits": 0, "matching_calls": 0, "metric_edges": 0}
    specifications = list(_specifications(nonempty, target, require_nonzero)) if dp_complete else []
    branches, best = [], None
    for syndrome, fixed, need_cycle in specifications[:max_graph_calls]:
        branch_target = rhs ^ syndrome
        graph = (shortest_nonempty_cycle(vertices, edges, stats) if need_cycle
                 else minimum_tjoin(vertices, edges, branch_target, stats))
        branches.append({"exception_syndrome": syndrome, "exception_word": fixed,
                         "nonzero_graph_required": need_cycle, "graph": graph})
        if graph.get("word") is not None:
            word = fixed | graph["word"]
            candidate = word.bit_count(), word
            if best is None or candidate < best:
                best = candidate
    complete = dp_complete and len(branches) == len(specifications)
    if dp_complete and not complete:
        stop_reason = "GRAPH_LIMIT"
    result = {"schema": "rank_native_minweight_v1", "n": n,
              "target": target, "require_nonzero": require_nonzero,
              "row_transform": list(transform), "exceptional_coordinates": list(exceptional),
              "exception_rank": rank, "state_count": state_count,
              "limits": {"max_states": max_states, "max_dp_transitions": max_dp_transitions,
                         "max_graph_calls": max_graph_calls},
              "dp_layers": layers, "dp_transitions": transitions, "dp_complete": dp_complete,
              "exception_witnesses": witnesses, "graph_case_count": len(specifications) if dp_complete else None,
              "branches": branches, "status": "EXACT" if complete else "UNKNOWN",
              "stop_reason": stop_reason, "distance": best[0] if best and complete else None,
              "upper_bound": best[0] if best else None, "word": best[1] if best else None,
              "stats": stats, "solve_seconds": perf_counter() - started}
    verify_started = perf_counter()
    verification = verify_rank_native(original, n, result, target=target, require_nonzero=require_nonzero)
    result["verification_seconds"] = perf_counter() - verify_started
    if not verification["valid"]:
        raise ArithmeticError(verification)
    result["verification"] = verification
    return result


def verify_rank_native(check_rows, n, result, *, target=0, require_nonzero=True):
    """Check every Bellman layer, final witnesses and graph optimality evidence.

    DP verification recomputes scalar costs, not the producer's chosen paths.
    Graph matching duals and cycle evidence use the existing independent checker.
    The caller supplies the original problem; result metadata cannot replace it.
    """
    try:
        if not isinstance(result, dict) or result.get("schema") != "rank_native_minweight_v1":
            raise ValueError("wrong schema")
        original, transform, columns, exceptional, edges, vertices = _prepare(check_rows, n, result["row_transform"])
        _request(original, target, require_nonzero)
        for key, value in (("n", n), ("target", target)):
            if type(result.get(key)) is not int or result[key] != value:
                raise ValueError("problem metadata mismatch")
        if type(result.get("require_nonzero")) is not bool or result["require_nonzero"] != require_nonzero:
            raise ValueError("nonzero condition mismatch")
        reported = result["exceptional_coordinates"]
        if not isinstance(reported, list) or any(type(j) is not int for j in reported) or reported != list(exceptional):
            raise ValueError("exception indices mismatch")
        rank = _rank(columns[j] for j in exceptional)
        for key, value in (("exception_rank", rank), ("state_count", 1 << rank)):
            if type(result.get(key)) is not int or result[key] != value:
                raise ValueError("rank or state count mismatch")
        limits = result["limits"]
        if not isinstance(limits, dict) or set(limits) != {"max_states", "max_dp_transitions", "max_graph_calls"}:
            raise ValueError("invalid work limits")
        if any(type(v) is not int or v < 0 for v in limits.values()):
            raise ValueError("invalid work limits")
        layers = result["dp_layers"]
        if not isinstance(layers, list) or not layers or layers[0] != [] or len(layers) > len(exceptional) + 1:
            raise ValueError("invalid DP layer list")
        costs, transitions = {}, 0
        for i, layer in enumerate(layers[1:]):
            if not isinstance(layer, list) or any(not isinstance(entry, list) or len(entry) != 2
                    or any(type(v) is not int for v in entry) for entry in layer):
                raise ValueError("malformed DP layer")
            column = columns[exceptional[i]]
            expected = dict(costs)
            expected[column] = min(expected.get(column, n + 1), 1)
            for syndrome, cost in costs.items():
                next_syndrome = syndrome ^ column
                expected[next_syndrome] = min(expected.get(next_syndrome, n + 1), cost + 1)
            transitions += len(costs) + 1
            if layer != [[s, cost] for s, cost in sorted(expected.items())]:
                raise ValueError("DP Bellman recurrence failed")
            costs = expected
        if type(result.get("dp_transitions")) is not int or result["dp_transitions"] != transitions:
            raise ValueError("DP operation count mismatch")
        if transitions > limits["max_dp_transitions"]:
            raise ValueError("DP budget exceeded")
        stopped_on_states = (1 << rank) > limits["max_states"]
        if stopped_on_states and len(layers) != 1:
            raise ValueError("DP allocated after state budget failure")
        dp_complete = not stopped_on_states and len(layers) == len(exceptional) + 1
        if type(result.get("dp_complete")) is not bool or result["dp_complete"] != dp_complete:
            raise ValueError("DP completeness mismatch")
        if not dp_complete and not stopped_on_states and transitions + len(costs) + 1 <= limits["max_dp_transitions"]:
            raise ValueError("DP stopped before its stated budget")
        witnesses = result["exception_witnesses"]
        nonempty = {}
        if dp_complete:
            if not isinstance(witnesses, list) or len(witnesses) != len(costs):
                raise ValueError("missing final DP witnesses")
            mask = sum(1 << j for j in exceptional)
            for expected_syndrome, entry in zip(sorted(costs), witnesses):
                if not isinstance(entry, list) or len(entry) != 3 or any(type(v) is not int for v in entry):
                    raise ValueError("malformed DP witness")
                syndrome, cost, word = entry
                if syndrome != expected_syndrome or cost != costs[syndrome] or word <= 0 or word & ~mask:
                    raise ValueError("invalid final exceptional witness")
                if word.bit_count() != cost or _syndrome(columns, word) != syndrome:
                    raise ValueError("exceptional witness does not realize DP cost")
                nonempty[syndrome] = cost, word
        elif witnesses != []:
            raise ValueError("partial DP must not claim complete witnesses")
        specs = list(_specifications(nonempty, target, require_nonzero)) if dp_complete else []
        expected_cases = len(specs) if dp_complete else None
        if result.get("graph_case_count") != expected_cases or (dp_complete and type(result["graph_case_count"]) is not int):
            raise ValueError("graph case count mismatch")
        branches = result["branches"]
        if not isinstance(branches, list) or len(branches) != min(len(specs), limits["max_graph_calls"]):
            raise ValueError("graph case coverage mismatch")
        best, rhs = None, _transformed_target(target, transform)
        for branch, (syndrome, fixed, need_cycle) in zip(branches, specs):
            if not isinstance(branch, dict):
                raise ValueError("malformed graph case")
            if type(branch.get("exception_syndrome")) is not int or branch["exception_syndrome"] != syndrome:
                raise ValueError("graph case syndrome mismatch")
            if type(branch.get("exception_word")) is not int or branch["exception_word"] != fixed:
                raise ValueError("graph case witness mismatch")
            if type(branch.get("nonzero_graph_required")) is not bool or branch["nonzero_graph_required"] != need_cycle:
                raise ValueError("graph nonzero condition mismatch")
            graph = branch["graph"]
            optimum = _verify_branch(columns, edges, vertices, rhs ^ syndrome, graph, need_cycle)
            if optimum is not None:
                word = fixed | graph["word"]
                actual_rhs = sum(((row & word).bit_count() % 2) << i for i, row in enumerate(original))
                if actual_rhs != target or (require_nonzero and not word):
                    raise ValueError("word fails original equations")
                candidate = word.bit_count(), word
                if best is None or candidate < best:
                    best = candidate
        complete = dp_complete and len(branches) == len(specs)
        status = "EXACT" if complete else "UNKNOWN"
        reason = None if complete else ("STATE_LIMIT" if stopped_on_states else "DP_LIMIT" if not dp_complete else "GRAPH_LIMIT")
        expected_values = {"distance": best[0] if best and complete else None,
                           "upper_bound": best[0] if best else None, "word": best[1] if best else None}
        for key, value in expected_values.items():
            if result.get(key) != value or (value is not None and type(result[key]) is not int):
                raise ValueError("aggregate optimum or witness mismatch")
        if result.get("status") != status or result.get("stop_reason") != reason:
            raise ValueError("unsupported completion claim")
        return {"valid": True, "errors": [], "status": status,
                "dp_layers_verified": len(layers), "graph_cases_verified": len(branches),
                "distance": expected_values["distance"], "upper_bound": expected_values["upper_bound"]}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"valid": False, "errors": [str(exc)]}
