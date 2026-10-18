"""Exact small controls for common-cost OR saturation; no solver-core modifications."""
from datetime import datetime, timezone
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import platform
from time import perf_counter

from saturated_clause import (
    boundary_signature, encoded_or, even_delta_audit, exact_or_exchange_witness,
    raw_or_graph, saturated_or_graph, threshold_support_audit, valid_domain,
)

ROOT = Path(__file__).resolve().parent
SOURCES = {name: ROOT / name for name in
           ("saturated_clause.py", "test_saturated_clause.py", "run_experiments.py", "THEOREM.md")}
SOURCES["matching_gadget_limits/matching_boundary.py"] = ROOT.parent / "matching_gadget_limits/matching_boundary.py"


def source_hashes():
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in SOURCES.items()}


def graph_record(request, k):
    signature = boundary_signature(**request)
    valid = valid_domain(k)
    return {"request": request,
            "request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "signature": [{"deleted": state, **row} for state, row in sorted(signature.items())],
            "valid_domain": valid,
            "valid_costs": [{"deleted": state, "true_literals": state.bit_count() // 2,
                             "cost": signature[state]["cost"]} for state in valid],
            "invalid_feasible_states": sorted(set(signature) - set(valid)),
            "zero_support_audit": even_delta_audit([s for s, row in signature.items() if row["cost"] == 0], 2 * k)}


def exhaust_four_vertex_weights():
    edges = list(combinations(range(4), 2))
    count = candidates = 0
    for weights in product((None, -1, 0, 1), repeat=len(edges)):
        graph = [(u, v, w) for (u, v), w in zip(edges, weights) if w is not None]
        signature = boundary_signature(4, graph, range(4))
        count += 1
        if 3 not in signature or 12 not in signature:
            continue
        # Equality of the three accepted adjusted costs forces the pair offsets below.
        pair_offset_0, pair_offset_1 = signature[12]["cost"], signature[3]["cost"]
        common = pair_offset_0 + pair_offset_1
        assert signature[15]["cost"] == 0
        assert signature[3]["cost"] + pair_offset_0 == common
        assert signature[12]["cost"] + pair_offset_1 == common
        assert signature[0]["cost"] <= common
        candidates += 1
    return {"labelled_graph_weight_assignments": count,
            "edge_choices": ["absent", -1, 0, 1],
            "graphs_with_both_required_pair_states": candidates,
            "all_forced_modular_offsets_accept_false_at_cost_at_most_common": True,
            "all_size_minimality_source": "THEOREM.md proof; bounded enumeration alone is not an impossibility proof"}


def main():
    started, before = perf_counter(), source_hashes()
    saturated = [graph_record(saturated_or_graph(k), k) for k in (1, 2, 3)]
    for record in saturated:
        assert all(row["cost"] == int(row["deleted"] == 0) for row in record["valid_costs"])
        assert record["zero_support_audit"]["is_even_delta_matroid"]
    raw = []
    for k in range(1, 5):
        record = graph_record(raw_or_graph(k), k)
        support = [row["deleted"] for row in record["signature"] if row["cost"] <= k - 1]
        assert support == encoded_or(k)
        record["threshold"] = k - 1
        record["threshold_support"] = support
        record["threshold_audit"] = threshold_support_audit(support, 2 * k)
        raw.append(record)
    data = {"schema": "saturated_clause_limits_v1", "started_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "exact_integer_arithmetic": True,
            "status": "PROVED_SCOPED_OBSTRUCTION_AND_CONSTRUCTIVE_PROMISED_CONTROL",
            "universal_reduction_or_P_versus_NP_result_claimed": False,
            "exact_flat_OR_exchange_witnesses": [exact_or_exchange_witness(k) for k in range(2, 7)],
            "raw_threshold_gadgets": raw, "promised_saturated_gadgets": saturated,
            "four_vertex_exhaustion": exhaust_four_vertex_weights(),
            "search_status": "No unresolved search claim: explicit witnesses supplied; larger-arity minimum graph size uninvestigated",
            "two_clause_compensation": {"clause_true_literal_counts": [0, 2], "raw_cost_sum": 2,
                                        "sum_of_clause_thresholds": 2, "unsatisfied_clauses": 1,
                                        "saturated_penalty_sum": 1}}
    after = source_hashes()
    assert before == after
    data.update(source_sha256_before=before, source_sha256_after=after,
                sources_unchanged_during_run=True, seconds=perf_counter() - started)
    (ROOT / "RESULTS.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    text = ("# Common-cost clause saturation checks\n\n"
            "The exact flat OR relation fails ordinary even exchange for every arity at least two, "
            "as proved in THEOREM.md. Signed weights, modular terminal offsets and extra internal "
            "vertices do not permit that exact relation to be the global-minimum boundary support.\n\n"
            "A constructive positive control does implement flat OR on the promised paired domain: "
            "the all-false state costs one and every other valid state costs zero. Full signatures "
            "and matching witnesses are saved for arities one, two and three (2, 6 and 10 vertices). "
            "The all-size construction has 4k−2 vertices. Its invalid zero-cost states remain explicit.\n\n"
            "The two-input control uses six vertices, the minimum under these four-terminal deletion "
            "semantics, including signed costs and modular terminal offsets. The lower bound is "
            "proved algebraically. A supplemental enumeration checked all 4,096 simple four-vertex "
            "graphs with each edge absent or weighted −1, 0 or 1; in all 2,304 graphs supporting "
            "the required pair states, the forced common-cost offsets also allowed the false state.\n\n"
            "Raw disjoint-pair threshold controls were checked for arities one through four. Their "
            "score rewards additional true literals; the saved two-clause example shows how these "
            "rewards can conceal an unsatisfied clause when thresholds are simply added. Scalar "
            "saturation fixes that numerical truth table, but a complete reduction still needs "
            "correct interface composition and exclusion of invalid encodings.\n\n"
            "Run `python -m unittest test_saturated_clause.py -v` and `python run_experiments.py` "
            "in this folder. The JSON includes requests, matching witnesses, and before/after "
            f"source hashes. Python {data['python']}; measured experiment time {data['seconds']:.6f}s. "
            "No general impossibility of matching reductions or conclusion about P versus NP is claimed.\n")
    (ROOT / "RESULTS.md").write_text(text, encoding="utf-8")
    print(json.dumps({"saturated_gadgets": len(saturated), "raw_gadgets": len(raw),
                      "weighted_graphs": data["four_vertex_exhaustion"]["labelled_graph_weight_assignments"],
                      "seconds": data["seconds"]}))


if __name__ == "__main__":
    main()
