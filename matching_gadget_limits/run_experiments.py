"""Reproduce bounded exact support checks; all-size claims are proved separately."""
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
import platform
import random
from time import perf_counter

from matching_boundary import (
    alternating_exchange, bipartite_cost_example, boundary_signature,
    encoded_and, even_delta_audit, threshold_support_audit, valid_domain,
)


ROOT = Path(__file__).resolve().parent
SEED = 2026101811
SOURCES = ("matching_boundary.py", "test_matching_boundary.py", "run_experiments.py", "THEOREM.md")


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def record(n, edges, terminals):
    signature = boundary_signature(n, edges, terminals)
    request = {"n": n, "edges": [list(edge) for edge in edges], "terminals": list(terminals)}
    return {"request": request,
            "request_sha256": hashlib.sha256(json.dumps(request, separators=(",", ":"), sort_keys=True).encode()).hexdigest(),
            "feasible_deleted_sets": sorted(signature),
            "signature": [{"deleted": state, **value} for state, value in sorted(signature.items())],
            "even_delta_check": even_delta_audit(signature, len(terminals))}


def exhaustive_simple_graphs():
    started = perf_counter()
    graphs = relations = empty = flips = 0
    per_n = []
    for n in range(6):
        possible = list(combinations(range(n), 2))
        count = 1 << len(possible)
        for graph_mask in range(count):
            graphs += 1
            edges = [(u, v, 0) for j, (u, v) in enumerate(possible) if graph_mask >> j & 1]
            for terminal_count in range(n + 1):
                relations += 1
                terminals = tuple(range(terminal_count))
                signature = boundary_signature(n, edges, terminals)
                if not signature:
                    empty += 1
                    continue
                audit = even_delta_audit(signature, terminal_count)
                if not audit["is_even_delta_matroid"] or audit["parities"] != [n % 2]:
                    raise ArithmeticError("a nonempty matching boundary relation violated even exchange")
                A, B = min(signature), max(signature)
                for e in range(terminal_count):
                    if (A ^ B) >> e & 1:
                        alternating_exchange(n, edges, terminals, A, B, e,
                                             signature[A]["matching"], signature[B]["matching"])
                        flips += 1
        per_n.append({"vertices": n, "graphs": count, "terminal_prefixes_per_graph": n + 1})
    return {"graph_count": graphs, "boundary_relations": relations,
            "empty_relations": empty, "nonempty_relations": relations - empty,
            "all_nonempty_relations_even_delta": True,
            "alternating_path_certificates_checked": flips,
            "all_simultaneous_flips_and_cost_conservation_verified": True,
            "per_n": per_n, "seconds": perf_counter() - started}


def weighted_checks():
    rng = random.Random(SEED)
    started = perf_counter()
    count = nonempty = zero_supports = minimum_supports = threshold_supports = 0
    for index in range(200):
        n = rng.randrange(2, 9)
        terminals = tuple(range(rng.randrange(n + 1)))
        signed = [(u, v, rng.randrange(-3, 6)) for u, v in combinations(range(n), 2)
                  if rng.random() < 0.45]
        for nonnegative in (False, True):
            edges = [(u, v, abs(w) if nonnegative else w) for u, v, w in signed]
            signature = boundary_signature(n, edges, terminals)
            count += 1
            if not signature:
                continue
            nonempty += 1
            minimum = min(value["cost"] for value in signature.values())
            minimizers = {state for state, value in signature.items() if value["cost"] == minimum}
            if not even_delta_audit(minimizers, len(terminals))["is_even_delta_matroid"]:
                raise ArithmeticError("global optimum support violated exchange")
            minimum_supports += 1
            for cutoff in sorted({value["cost"] for value in signature.values()}):
                support = {state for state, value in signature.items() if value["cost"] <= cutoff}
                if not threshold_support_audit(support, len(terminals))["passes_necessary_threshold_conditions"]:
                    raise ArithmeticError("a signed weighted threshold violated two-sided exchange")
                threshold_supports += 1
            if nonnegative:
                zeros = {state for state, value in signature.items() if value["cost"] == 0}
                zero_graph = set(boundary_signature(n, [e for e in edges if e[2] == 0], terminals))
                if zeros != zero_graph or (zeros and not even_delta_audit(zeros, len(terminals))["is_even_delta_matroid"]):
                    raise ArithmeticError("nonnegative zero-edge support identity failed")
                zero_supports += bool(zeros)
    return {"seed": SEED, "weighted_requests": count, "nonempty_signatures": nonempty,
            "global_minimum_supports_checked": minimum_supports,
            "distinct_threshold_supports_checked": threshold_supports,
            "all_threshold_supports_pass_two_sided_exchange": True,
            "nonempty_nonnegative_zero_supports_checked": zero_supports,
            "all_checks_passed": True, "seconds": perf_counter() - started}


def explicit_examples():
    cross = [(0, 5, 0), (1, 2, 0), (3, 4, 0)]
    validity = [(0, 1, 0), (2, 3, 0), (4, 5, 0)]
    copy = record(6, cross, range(6))
    copy["valid_domain"] = valid_domain(3)
    copy["valid_domain_intersection"] = sorted(set(copy["feasible_deleted_sets"]) & set(valid_domain(3)))
    copy_signature = boundary_signature(6, cross, range(6))
    copy["exchange_escape_certificate"] = alternating_exchange(6, cross, range(6), 0, 63, 0,
                          copy_signature[0]["matching"], copy_signature[63]["matching"])
    positive = record(6, bipartite_cost_example([1, 2, 3, 4]), range(4))
    positive["threshold"] = 5
    positive["threshold_support"] = [row["deleted"] for row in positive["signature"] if row["cost"] <= 5]
    positive["threshold_audit"] = even_delta_audit(positive["threshold_support"], 4)
    positive["two_sided_threshold_audit"] = threshold_support_audit(positive["threshold_support"], 4)
    signed = record(6, bipartite_cost_example([1, -1, 2, -2]), range(4))
    signed["zero_support"] = [row["deleted"] for row in signed["signature"] if row["cost"] == 0]
    signed["zero_audit"] = even_delta_audit(signed["zero_support"], 4)
    promised_and = record(6, [(0, 4, 0), (1, 5, 0), (2, 4, 0), (3, 5, 0), (0, 3, 0)], range(6))
    promised_and["valid_domain"] = valid_domain(3)
    promised_and["valid_domain_intersection"] = sorted(set(promised_and["feasible_deleted_sets"]) & set(valid_domain(3)))
    if promised_and["valid_domain_intersection"] != sorted(encoded_and(2)):
        raise ArithmeticError("promised-domain AND control does not implement its stated truth table")
    return {"exact_three_copy_relation": {"feasible_deleted_sets": [0, 63],
                                          "audit": even_delta_audit([0, 63], 6),
                                          "threshold_audit": threshold_support_audit([0, 63], 6)},
            "encoded_AND_relations": [{"inputs": k, "relation": encoded_and(k),
                                        "audit": even_delta_audit(encoded_and(k), 2 * (k + 1)),
                                        "threshold_audit": threshold_support_audit(encoded_and(k), 2 * (k + 1))}
                                       for k in (2, 3)],
            "promised_domain_copy": copy, "promised_domain_AND": promised_and,
            "validity_gadget": record(6, validity, range(6)),
            "naive_edge_union": record(6, cross + validity, range(6)),
            "positive_threshold_counterexample": positive,
            "signed_zero_counterexample": signed}


def main():
    started = perf_counter()
    before = hashes()
    data = {"schema": "matching_boundary_gadget_audit_v2", "started_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "exact_integer_arithmetic": True,
            "all_size_impossibility_source": "THEOREM.md, not finite graph enumeration",
            "universal_matching_reduction_impossibility_claimed": False,
            "exhaustive_graphs": exhaustive_simple_graphs(),
            "weighted_checks": weighted_checks(), "examples": explicit_examples()}
    after = hashes()
    if before != after:
        raise RuntimeError("source changed during experiment")
    data["source_sha256"] = after
    data["sources_unchanged_during_run"] = True
    data["seconds"] = perf_counter() - started
    (ROOT / "RESULTS.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    graph, weighted = data["exhaustive_graphs"], data["weighted_checks"]
    text = ("# Matching-gadget boundary experiments\n\n"
            f"All checks passed on {graph['graph_count']:,} labelled simple graphs with at most five vertices, "
            f"using every terminal-prefix size: {graph['boundary_relations']:,} boundary relations, "
            f"of which {graph['nonempty_relations']:,} were nonempty. Every nonempty relation had fixed "
            f"vertex parity and satisfied even symmetric exchange. The empty relations are not called delta-matroids.\n\n"
            f"Replayed {graph['alternating_path_certificates_checked']:,} explicit alternating-path flips, "
            "checking both resulting perfect matchings and exact cost conservation. A terminal prefix of "
            "every size covers arbitrary terminal placements up to relabelling because all labelled graphs are enumerated.\n\n"
            f"An additional {weighted['weighted_requests']} seeded weighted requests used signed and "
            f"nonnegative integer weights. All {weighted['global_minimum_supports_checked']} nonempty "
            "global-minimum supports passed exchange. Nonnegative zero-optimum support always agreed "
            "exactly with the feasible support of the zero-edge subgraph.\n\n"
            f"Every one of {weighted['distinct_threshold_supports_checked']} distinct nonempty cost-cutoff "
            "supports passed the weaker two-sided exchange condition. This condition holds for arbitrary "
            "signed costs and any common threshold, and still excludes exact paired copy and AND. "
            "It does not assert that threshold supports are delta-matroids.\n\n"
            "The saved examples include ordinary and two-sided exchange failures for exact paired copy "
            "and AND, six-vertex promised-domain copy and AND gadgets, a valid-pair gadget, the failure "
            "of naive edge-union to enforce relation intersection, a positive-threshold counterexample "
            "to ordinary exchange that passes two-sided exchange, and a signed-zero-level "
            "counterexample. Every graph signature includes exact costs and matching witnesses.\n\n"
            "Run `python -m unittest test_matching_boundary.py` and `python run_experiments.py` here to "
            "reproduce the unit tests and this bounded experiment. The JSON records input and source "
            f"hashes. Seed {SEED}; Python {data['python']}; measured experiment time {data['seconds']:.6f}s.\n\n"
            "The all-size statements follow from the alternating-path proof in THEOREM.md. Finite "
            "enumeration alone would not exclude larger gadgets. No impossibility of general matching "
            "reductions or conclusion about P versus NP is claimed.\n")
    (ROOT / "RESULTS.md").write_text(text, encoding="utf-8")
    print(json.dumps({"graphs": graph["graph_count"], "relations": graph["boundary_relations"],
                      "flip_certificates": graph["alternating_path_certificates_checked"],
                      "weighted_requests": weighted["weighted_requests"],
                      "threshold_supports": weighted["distinct_threshold_supports_checked"],
                      "seconds": data["seconds"]}))


if __name__ == "__main__":
    main()
