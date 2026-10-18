"""Certified arbitrary-terminal labelled T-joins, exponential in terminal count.

After certified lifted shortest paths, a subset DP pairs terminals and allocates
XOR labels. The empty subset uses the separate Eulerian label closure, allowing
disconnected cycle corrections. None is exact infinity, never a numeric sentinel.
"""
from __future__ import annotations

from time import perf_counter

from labelled_tables import build_tables, load_verified_tables, verify_tables


DEFAULT_LIMITS = {"max_states": 4096, "max_total_states": 1_000_000,
                  "max_relaxations": 1_000_000, "max_dp_states": 65536,
                  "max_dp_transitions": 1_000_000, "max_verification_arcs": 10_000_000}


class _VerificationLimit(Exception):
    pass


def _checked_tables(n, edges, p, certificate, state_cap, arc_cap):
    try:
        return load_verified_tables(n, edges, p, certificate,
                                    verification_state_limit=state_cap, verification_arc_limit=arc_cap)
    except ValueError:
        # Preserve the distinction between invalid evidence and an exhausted checker.
        checked = verify_tables(n, edges, p, certificate,
                                verification_state_limit=state_cap, verification_arc_limit=arc_cap)
        if checked['status'] == 'UNKNOWN':
            raise _VerificationLimit('; '.join(checked['errors']))
        raise


def validate_request(n, edges, p, terminals, target):
    if type(n) is not int or n < 0 or type(p) is not int or p < 0:
        raise ValueError("n and p must be nonnegative integers")
    if type(target) is not int or target < 0 or target.bit_length() > p:
        raise ValueError("target must be a p-bit label")
    edges = tuple(tuple(edge) for edge in edges)
    for edge in edges:
        if len(edge) != 4 or any(type(x) is not int for x in edge):
            raise ValueError("edges require integer (u,v,label,weight) fields")
        u, v, label, weight = edge
        if not (0 <= u < n and 0 <= v < n) or label < 0 or label.bit_length() > p or weight < 0:
            raise ValueError("invalid endpoint, label or nonnegative weight")
    terminals = tuple(terminals)
    if any(type(v) is not int or not 0 <= v < n for v in terminals) or len(set(terminals)) != len(terminals):
        raise ValueError("terminals must be distinct valid vertices")
    return edges, tuple(sorted(terminals))


def properties(edges, word):
    boundary, label, weight = set(), 0, 0
    for j, (u, v, edge_label, edge_weight) in enumerate(edges):
        if word >> j & 1:
            boundary.symmetric_difference_update((u,))
            boundary.symmetric_difference_update((v,))
            label ^= edge_label
            weight += edge_weight
    return tuple(sorted(boundary)), label, weight


def _limits(given):
    limits = dict(DEFAULT_LIMITS)
    if given is not None:
        if not isinstance(given, dict) or set(given) - set(limits):
            raise ValueError("unknown work limit")
        limits.update(given)
    if any(type(v) is not int or v < 0 for v in limits.values()):
        raise ValueError("limits must be nonnegative integers")
    return limits


def _dp_size_fits(t, p, cap):
    exponent = p + max(0, t - 1)
    return cap > 0 and exponent < cap.bit_length()


def _graph_caps(limits):
    return {key: limits[key] for key in ("max_states", "max_total_states", "max_relaxations")}


def solve_tjoin(n, edges, p, *, terminals=(), target=0, limits=None):
    """Exact unweighted/weighted label-constrained T-join, permitting empty support.

    DP cost is O(2**len(terminals) * len(terminals) * 2**(2*p)); it is not
    polynomial for arbitrary terminal counts. All edge weights are integers.
    Caps apply to one solve. A stopped solve returns no optimality claim.
    """
    started = perf_counter()
    edges, terminals = validate_request(n, edges, p, terminals, target)
    limits = _limits(limits)
    result = {"schema": "certified_labelled_tjoin_v1", "n": n, "p": p,
              "terminals": list(terminals), "target": target, "limits": limits,
              "status": "UNKNOWN", "weight": None, "word": None,
              "tables": None, "dp_layers": [], "dp_transitions": 0,
              "stop_reason": None, "proof_kind": None}
    if len(terminals) % 2:
        result.update(status="EXACT", proof_kind="ODD_TERMINAL_COUNT")
    elif not _dp_size_fits(len(terminals), p, limits["max_dp_states"]):
        result["stop_reason"] = "DP_STATE_LIMIT"
    elif (n * (1 << p) * sum(1 if e[0] == e[1] else 2 for e in edges)
          + (1 << p) * ((1 << p) - 1)) > limits["max_verification_arcs"]:
        # The checker scans arcs out of unreachable states too; search work alone
        # cannot bound its cost. This conservative bound is separate and explicit.
        result["stop_reason"] = "VERIFICATION_ARC_LIMIT"
    else:
        built = build_tables(n, edges, p, **_graph_caps(limits))
        result["table_build_stats"] = built.get("stats", {})
        if built["status"] != "EXACT":
            result["stop_reason"] = "TABLE_LIMIT"
            result["table_stop_reason"] = built.get("reason")
        else:
            result["tables"] = built["certificate"]
            tables = _checked_tables(n, edges, p, built["certificate"],
                                     limits["max_total_states"], limits["max_verification_arcs"])
            k, t = 1 << p, len(terminals)
            values = {0: [tables.eulerian_join(z)["weight"] for z in range(k)]}
            choices = {}
            result["dp_layers"].append({"mask": 0, "costs": values[0]})
            for mask in range(1, 1 << t):
                if mask.bit_count() % 2:
                    continue
                needed = (mask.bit_count() - 1) * k * k
                if result["dp_transitions"] + needed > limits["max_dp_transitions"]:
                    result["stop_reason"] = "DP_TRANSITION_LIMIT"
                    break
                v_index = (mask & -mask).bit_length() - 1
                v = terminals[v_index]
                costs, chosen = [], []
                for label in range(k):
                    best = None
                    for w_index in range(v_index + 1, t):
                        if not mask >> w_index & 1:
                            continue
                        submask = mask ^ (1 << v_index) ^ (1 << w_index)
                        for path_label in range(k):
                            path_cost = tables.lift_distance(v, terminals[w_index], path_label)
                            rest = values[submask][label ^ path_label]
                            if path_cost is not None and rest is not None:
                                candidate = path_cost + rest, w_index, path_label
                                if best is None or candidate < best:
                                    best = candidate
                    costs.append(best[0] if best else None)
                    chosen.append(best[1:] if best else None)
                values[mask], choices[mask] = costs, chosen
                result["dp_transitions"] += needed
                result["dp_layers"].append({"mask": mask, "costs": costs})
            else:
                full = (1 << t) - 1
                optimum = values[full][target]
                word = None
                if optimum is not None:
                    mask, label, word = full, target, 0
                    while mask:
                        v_index = (mask & -mask).bit_length() - 1
                        w_index, path_label = choices[mask][label]
                        word ^= tables.lift_word(terminals[v_index], terminals[w_index], path_label)
                        mask ^= (1 << v_index) ^ (1 << w_index)
                        label ^= path_label
                    word ^= tables.eulerian_join(label)["word"]
                    if properties(edges, word) != (terminals, target, optimum):
                        raise ArithmeticError("DP reconstruction differs from exact original optimum")
                result.update(status="EXACT", proof_kind="SUBSET_DP", weight=optimum, word=word)
    result["solve_seconds"] = perf_counter() - started
    verify_started = perf_counter()
    checked = verify_tjoin(n, edges, p, result, terminals=terminals, target=target,
                           verification_state_limit=max(limits["max_total_states"], limits["max_dp_states"]),
                           verification_arc_limit=limits["max_verification_arcs"],
                           verification_dp_transitions=limits["max_dp_transitions"])
    if not checked["valid"]:
        raise ArithmeticError(checked)
    result["verification"] = checked
    result["verification_seconds"] = perf_counter() - verify_started
    return result


def verify_tjoin(n, edges, p, result, *, terminals=(), target=0,
                 verification_state_limit=1_000_000, verification_arc_limit=10_000_000,
                 verification_dp_transitions=10_000_000):
    """Verify lifted graph proofs, every DP recurrence, and the original support."""
    try:
        edges, terminals = validate_request(n, edges, p, terminals, target)
        if any(type(cap) is not int or cap < 0 for cap in
               (verification_state_limit, verification_arc_limit, verification_dp_transitions)):
            raise ValueError("verification caps must be nonnegative integers")
        if not isinstance(result, dict) or result.get("schema") != "certified_labelled_tjoin_v1":
            raise ValueError("wrong schema")
        for key, expected in (("n", n), ("p", p), ("target", target)):
            if type(result.get(key)) is not int or result[key] != expected:
                raise ValueError("requested problem mismatch")
        reported = result.get("terminals")
        if not isinstance(reported, list) or any(type(v) is not int for v in reported) or reported != list(terminals):
            raise ValueError("terminal set mismatch")
        _limits(result["limits"])
        if result.get("status") == "UNKNOWN":
            if result.get("weight") is not None or result.get("word") is not None or result.get("proof_kind") is not None:
                raise ValueError("UNKNOWN cannot claim an optimum or proof")
            # Abstention makes no mathematical claim about omitted DP/table states.
            return {"valid": True, "status": "UNKNOWN", "errors": [], "weight": None}
        if result.get("status") != "EXACT" or result.get("stop_reason") is not None:
            raise ValueError("invalid completion status")
        if result.get("proof_kind") == "ODD_TERMINAL_COUNT":
            if len(terminals) % 2 != 1 or result.get("weight") is not None or result.get("word") is not None:
                raise ValueError("invalid odd-cardinality infeasibility proof")
            return {"valid": True, "status": "EXACT", "errors": [], "weight": None}
        if result.get("proof_kind") != "SUBSET_DP" or len(terminals) % 2:
            raise ValueError("invalid DP proof kind")
        if not _dp_size_fits(len(terminals), p, verification_state_limit):
            return {"valid": False, "status": "UNKNOWN", "errors": [], "reason": "VERIFICATION_STATE_LIMIT"}
        tables = _checked_tables(n, edges, p, result["tables"],
                                 verification_state_limit, verification_arc_limit)
        k, t = 1 << p, len(terminals)
        layers = result["dp_layers"]
        masks = [mask for mask in range(1 << t) if mask.bit_count() % 2 == 0]
        if not isinstance(layers, list) or len(layers) != len(masks):
            raise ValueError("incomplete DP state coverage")
        values, transitions = {}, 0
        for mask, layer in zip(masks, layers):
            if not isinstance(layer, dict) or type(layer.get("mask")) is not int or layer["mask"] != mask:
                raise ValueError("missing or reordered DP mask")
            costs = layer.get("costs")
            if not isinstance(costs, list) or len(costs) != k or any(x is not None and (type(x) is not int or x < 0) for x in costs):
                raise ValueError("invalid DP costs")
            if not mask:
                expected = [tables.eulerian_join(z)["weight"] for z in range(k)]
            else:
                transitions += (mask.bit_count() - 1) * k * k
                if transitions > verification_dp_transitions:
                    return {"valid": False, "status": "UNKNOWN", "errors": [], "reason": "VERIFICATION_TRANSITION_LIMIT"}
                v_index = (mask & -mask).bit_length() - 1
                expected = [None] * k
                for w_index in range(t):
                    if w_index == v_index or not mask >> w_index & 1:
                        continue
                    submask = mask ^ (1 << v_index) ^ (1 << w_index)
                    for path_label in range(k):
                        left = tables.lift_distance(terminals[v_index], terminals[w_index], path_label)
                        if left is None:
                            continue
                        for rest_label, right in enumerate(values[submask]):
                            if right is None:
                                continue
                            label, candidate = path_label ^ rest_label, left + right
                            if expected[label] is None or candidate < expected[label]:
                                expected[label] = candidate
            if costs != expected:
                raise ValueError("DP minimum recurrence failed")
            values[mask] = costs
        if type(result.get("dp_transitions")) is not int or result["dp_transitions"] != transitions:
            raise ValueError("DP operation count mismatch")
        optimum = values[(1 << t) - 1][target]
        if result.get("weight") != optimum or (optimum is not None and type(result["weight"]) is not int):
            raise ValueError("aggregate optimum mismatch")
        word = result.get("word")
        if optimum is None:
            if word is not None:
                raise ValueError("infeasible result contains a word")
        elif type(word) is not int or word < 0 or word.bit_length() > len(edges) or properties(edges, word) != (terminals, target, optimum):
            raise ValueError("word fails original boundary, label or weight")
        return {"valid": True, "status": "EXACT", "errors": [], "weight": optimum,
                "dp_states_verified": len(layers) * k, "dp_transitions_verified": transitions}
    except _VerificationLimit as exc:
        return {"valid": False, "status": "UNKNOWN", "errors": [str(exc)], "reason": "TABLE_VERIFICATION_LIMIT"}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def solve_nonempty(n, edges, p, *, terminals=(), target=0, limits=None, max_pin_cases=256):
    """Require nonempty support. Only the empty/zero request needs edge pinning."""
    edges, terminals = validate_request(n, edges, p, terminals, target)
    if type(max_pin_cases) is not int or max_pin_cases < 0:
        raise ValueError("max_pin_cases must be a nonnegative integer")
    limits = _limits(limits)
    if terminals or target:
        direct = solve_tjoin(n, edges, p, terminals=terminals, target=target, limits=limits)
        result = {"schema": "certified_nonempty_labelled_tjoin_v1", "mode": "DIRECT", "direct": direct}
        result.update(status=direct["status"], weight=direct["weight"], upper_bound=direct["weight"], word=direct["word"])
    else:
        cases, best = [], None
        for pin, (u, v, label, weight) in enumerate(edges[:max_pin_cases]):
            remaining = edges[:pin] + edges[pin + 1:]
            residual = solve_tjoin(n, remaining, p, terminals=() if u == v else (u, v), target=label, limits=limits)
            cases.append({"pin": pin, "residual": residual})
            if residual["weight"] is not None:
                local = residual["word"]
                low = local & ((1 << pin) - 1)
                word = low | ((local >> pin) << (pin + 1)) | (1 << pin)
                candidate = weight + residual["weight"], word
                if best is None or candidate < best:
                    best = candidate
        complete = len(cases) == len(edges) and all(c["residual"]["status"] == "EXACT" for c in cases)
        result = {"schema": "certified_nonempty_labelled_tjoin_v1", "mode": "EDGE_PINS",
                  "cases": cases, "max_pin_cases": max_pin_cases,
                  "status": "EXACT" if complete else "UNKNOWN",
                  "weight": best[0] if best and complete else None,
                  "upper_bound": best[0] if best else None, "word": best[1] if best else None}
    checked = verify_nonempty(n, edges, p, result, terminals=terminals, target=target,
                              verification_state_limit=max(limits["max_total_states"], limits["max_dp_states"]),
                              verification_arc_limit=limits["max_verification_arcs"],
                              verification_dp_transitions=limits["max_dp_transitions"])
    if not checked["valid"]:
        raise ArithmeticError(checked)
    result["verification"] = checked
    return result


def verify_nonempty(n, edges, p, result, *, terminals=(), target=0, **verification_limits):
    """Check each complete pin optimum; partial coverage establishes only a bound."""
    try:
        edges, terminals = validate_request(n, edges, p, terminals, target)
        if set(verification_limits) - {'verification_state_limit', 'verification_arc_limit', 'verification_dp_transitions'}:
            raise ValueError('unknown verification limit')
        if any(type(cap) is not int or cap < 0 for cap in verification_limits.values()):
            raise ValueError('verification caps must be nonnegative integers')
        if not isinstance(result, dict) or result.get("schema") != "certified_nonempty_labelled_tjoin_v1":
            raise ValueError("wrong nonempty schema")
        if terminals or target:
            if result.get("mode") != "DIRECT":
                raise ValueError("wrong nonempty mode")
            direct = result["direct"]
            checked = verify_tjoin(n, edges, p, direct, terminals=terminals, target=target, **verification_limits)
            if not checked["valid"]:
                if checked["status"] == "UNKNOWN":
                    return checked
                raise ValueError("direct certificate rejected")
            for key in ("status", "weight", "word"):
                if result.get(key) != direct[key] or (key != "status" and direct[key] is not None and type(result[key]) is not int):
                    raise ValueError("direct aggregate mismatch")
            if result.get("upper_bound") != direct["weight"] or (direct["weight"] is not None and type(result["upper_bound"]) is not int):
                raise ValueError("direct upper bound mismatch")
            return {"valid": True, "status": result["status"], "errors": []}
        if result.get("mode") != "EDGE_PINS":
            raise ValueError("zero request requires pin coverage")
        cap = result["max_pin_cases"]
        if type(cap) is not int or cap < 0:
            raise ValueError("bad pin limit")
        cases = result["cases"]
        if not isinstance(cases, list) or len(cases) != min(len(edges), cap):
            raise ValueError("pin prefix coverage mismatch")
        best, all_exact = None, True
        for pin, case in enumerate(cases):
            if not isinstance(case, dict) or type(case.get("pin")) is not int or case["pin"] != pin:
                raise ValueError("duplicate, missing or reordered pin")
            u, v, label, weight = edges[pin]
            residual = case["residual"]
            checked = verify_tjoin(n, edges[:pin] + edges[pin + 1:], p, residual,
                                   terminals=() if u == v else (u, v), target=label, **verification_limits)
            if not checked["valid"]:
                if checked["status"] == "UNKNOWN":
                    return checked
                raise ValueError("residual certificate rejected")
            all_exact &= checked["status"] == "EXACT"
            if residual["weight"] is not None:
                local = residual["word"]
                word = (local & ((1 << pin) - 1)) | ((local >> pin) << (pin + 1)) | (1 << pin)
                candidate = weight + residual["weight"], word
                if properties(edges, word) != ((), 0, candidate[0]):
                    raise ValueError("pinned original witness failed")
                if best is None or candidate < best:
                    best = candidate
        complete = len(cases) == len(edges) and all_exact
        expected = {"status": "EXACT" if complete else "UNKNOWN",
                    "weight": best[0] if best and complete else None,
                    "upper_bound": best[0] if best else None, "word": best[1] if best else None}
        for key, value in expected.items():
            if result.get(key) != value or (key != "status" and value is not None and type(result[key]) is not int):
                raise ValueError("nonempty aggregate mismatch")
        return {"valid": True, "status": expected["status"], "errors": [], "pins_verified": len(cases)}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}
