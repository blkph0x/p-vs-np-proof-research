"""Finite exact controls for OR matching thresholds and scalar composition.

The graph oracle enumerates original edge subsets. Trade verification uses
external Boolean labels and exact integer/rational features, never a fitted
score. No general matching reduction or SAT algorithm is implemented here.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from time import perf_counter


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _rational(value):
    if type(value) not in (int, Fraction):
        raise ValueError("costs and features must be exact integers or Fractions")
    return Fraction(value)


def _json_number(value):
    value = _rational(value)
    return value.numerator if value.denominator == 1 else {
        "numerator": value.numerator, "denominator": value.denominator}


def build_or_gadget(k):
    """Pair i consists of vertices 2*i,2*i+1; deletion means literal true."""
    _integer(k, "k", 1)
    if k > 5:
        raise ValueError("this finite control is capped at five pairs")
    return {"k": k, "vertices": 2 * k, "terminals": list(range(2 * k)),
            "edges": [[2 * i, 2 * i + 1, 1] for i in range(k)],
            "cutoff": k - 1}


def reference_signature(n, edges, terminals, *, max_vertices=10,
                        max_checks=1_000_000):
    """Exact deletion signature by independent edge-subset enumeration.

    For each boundary mask, directly check edge endpoints and exact coverage
    of the surviving original vertices. Signed rational weights are allowed.
    Resource refusal raises ValueError before any exponential loop; no partial
    signature is returned. A check is one (boundary mask, edge subset) pair.
    """
    _integer(n, "n")
    _integer(max_vertices, "max_vertices")
    _integer(max_checks, "max_checks", 1)
    if n > max_vertices:
        raise ValueError("reference vertex cap exceeded")
    if type(edges) not in (list, tuple) or type(terminals) not in (list, tuple):
        raise ValueError("edges and terminals must be lists or tuples")
    if any(type(v) is not int or not 0 <= v < n for v in terminals):
        raise ValueError("invalid terminal")
    if len(set(terminals)) != len(terminals):
        raise ValueError("duplicate terminal")
    exponent = len(edges) + len(terminals)
    if exponent >= max_checks.bit_length() or (1 << exponent) > max_checks:
        raise ValueError("reference edge-subset check cap exceeded")
    normalized = []
    for edge in edges:
        if type(edge) not in (list, tuple) or len(edge) != 3:
            raise ValueError("edges must be (u,v,weight)")
        u, v, weight = edge
        if type(u) is not int or type(v) is not int or not 0 <= u < v < n:
            raise ValueError("invalid edge endpoints; loops are not allowed")
        normalized.append((u, v, _rational(weight)))
    states = []
    checks = 0
    all_vertices = set(range(n))
    for mask in range(1 << len(terminals)):
        removed = {v for i, v in enumerate(terminals) if mask >> i & 1}
        required = all_vertices - removed
        best, witness, count = None, None, 0
        for subset in range(1 << len(normalized)):
            checks += 1
            covered, chosen, cost, valid = set(), [], Fraction(0), True
            for edge_id, (u, v, weight) in enumerate(normalized):
                if subset >> edge_id & 1:
                    if u in removed or v in removed or u in covered or v in covered:
                        valid = False
                        break
                    covered.update((u, v))
                    chosen.append(edge_id)
                    cost += weight
            if valid and covered == required:
                count += 1
                if best is None or cost < best:
                    best, witness = cost, chosen
        states.append({"deleted_mask": mask, "feasible": best is not None,
                       "minimum_cost": best, "matching_count": count,
                       "witness_edge_ids": witness})
    return {"status": "EXACT", "states": states,
            "edge_subset_checks": checks, "physical_states": len(states)}


def or_control(k):
    """Compare every physical state with the explicit OR theorem."""
    graph = build_or_gadget(k)
    reference = reference_signature(graph["vertices"], graph["edges"],
                                    graph["terminals"])
    states, mismatches = [], []
    for state in reference["states"]:
        mask = state["deleted_mask"]
        pair_masks = [(mask >> (2 * i)) & 3 for i in range(k)]
        valid_pairs = all(pair in (0, 3) for pair in pair_masks)
        deleted_pairs = sum(pair == 3 for pair in pair_masks)
        expected_cost = k - deleted_pairs if valid_pairs else None
        accepted = (state["minimum_cost"] is not None and
                    state["minimum_cost"] <= graph["cutoff"])
        expected_accepted = valid_pairs and deleted_pairs >= 1
        if (state["minimum_cost"] != expected_cost or
                accepted != expected_accepted or
                state["matching_count"] != int(valid_pairs)):
            mismatches.append(mask)
        states.append({**state, "minimum_cost": None if state["minimum_cost"] is None
                       else _json_number(state["minimum_cost"]),
                       "valid_pairs": valid_pairs, "deleted_pairs": deleted_pairs,
                       "accepted": accepted})
    return {**graph, "states": states, "all_states_verified": not mismatches,
            "mismatches": mismatches,
            "physical_states": reference["physical_states"],
            "edge_subset_checks": reference["edge_subset_checks"],
            "feasible_states": sum(s["feasible"] for s in states),
            "accepted_states": sum(s["accepted"] for s in states),
            "invalid_physical_states": sum(not s["valid_pairs"] for s in states)}


def aggregation_control():
    """Logical budget calculation, without assuming any variable-wire gadget."""
    rows = []
    for x, y in product((0, 1), repeat=2):
        counts = [x, 1 - x, x + y]
        costs = [1 - counts[0], 1 - counts[1], 2 - counts[2]]
        rows.append({"assignment": [x, y], "true_literal_counts": counts,
                     "costs": costs, "total_cost": sum(costs),
                     "formula_satisfied": all(c >= 1 for c in counts),
                     "sum_threshold_accepted": sum(costs) <= 1})
    return {"formula": "(x) AND (NOT x) AND (x OR y)",
            "clause_sizes": [1, 1, 2], "clause_cutoffs": [0, 0, 1],
            "summed_cutoff": 1, "rows": rows,
            "formula_satisfiable": any(r["formula_satisfied"] for r in rows),
            "false_accepts": [r["assignment"] for r in rows
                              if r["sum_threshold_accepted"] and
                              not r["formula_satisfied"]]}


def _external_data(truth_table, features):
    if type(truth_table) not in (list, tuple) or type(features) not in (list, tuple):
        raise ValueError("truth table and features must be lists or tuples")
    if not 0 < len(truth_table) <= 4096 or len(features) != len(truth_table):
        raise ValueError("invalid or oversized truth table")
    if any(type(label) is not bool for label in truth_table):
        raise ValueError("truth labels must be Boolean")
    if any(type(row) not in (list, tuple) for row in features):
        raise ValueError("feature rows must be lists or tuples")
    dimension = len(features[0])
    if dimension > 128 or any(len(row) != dimension for row in features):
        raise ValueError("inconsistent or oversized feature dimension")
    normalized = [tuple(_rational(value) for value in row) for row in features]
    # Binary canonical encoding avoids Python's decimal-string digit guard for
    # legitimate large integers. Every magnitude has an eight-byte byte-length
    # prefix; numerator signs, row labels and the matrix dimensions are explicit.
    binding = sha256(b"threshold-feature-trade-input-v2\0")

    def unsigned(value):
        encoded = value.to_bytes((value.bit_length() + 7) // 8, "big")
        binding.update(len(encoded).to_bytes(8, "big"))
        binding.update(encoded)

    unsigned(len(truth_table))
    unsigned(dimension)
    for label, row in zip(truth_table, normalized):
        binding.update(b"\x01" if label else b"\x00")
        for value in row:
            binding.update(b"\x01" if value.numerator < 0 else b"\x00")
            unsigned(abs(value.numerator))
            unsigned(value.denominator)
    return normalized, binding.hexdigest()


def make_trade_certificate(truth_table, features, accepted_indices, rejected_indices):
    """Construct an equal-mass multiset trade; reject a false proposed trade."""
    _, digest = _external_data(truth_table, features)
    certificate = {"kind": "equal_mass_feature_trade_v1", "input_sha256": digest,
                   "accepted_indices": list(accepted_indices),
                   "rejected_indices": list(rejected_indices)}
    verdict = verify_trade_certificate(truth_table, features, certificate)
    if not verdict["valid"]:
        raise ValueError("invalid proposed trade: " + "; ".join(verdict["errors"]))
    return certificate


def verify_trade_certificate(truth_table, features, certificate):
    """Check input binding, original labels, equal mass and exact feature sums.

    A valid result proves impossibility of correctly classifying ALL supplied
    rows by c + w.feature <= K, even for arbitrary real c,w,K. The executable
    feature values themselves are exact integers or rationals. Repeated row
    indices are allowed and count as repeated multiset members.
    """
    try:
        rows, digest = _external_data(truth_table, features)
        if type(certificate) is not dict:
            raise ValueError("certificate must be a dictionary")
        if set(certificate) != {"kind", "input_sha256", "accepted_indices", "rejected_indices"}:
            raise ValueError("invalid certificate fields")
        if certificate["kind"] != "equal_mass_feature_trade_v1":
            raise ValueError("unsupported certificate kind")
        if certificate["input_sha256"] != digest:
            raise ValueError("certificate is bound to a different truth table or features")
        accepted, rejected = certificate["accepted_indices"], certificate["rejected_indices"]
        if type(accepted) not in (list, tuple) or type(rejected) not in (list, tuple):
            raise ValueError("trade sides must be lists or tuples")
        if not 0 < len(accepted) == len(rejected) <= 4096:
            raise ValueError("trade sides must have equal positive bounded mass")
        for indices, label in ((accepted, True), (rejected, False)):
            for index in indices:
                if type(index) is not int or not 0 <= index < len(rows):
                    raise ValueError("invalid trade row index")
                if truth_table[index] is not label:
                    raise ValueError("trade member has the wrong original truth label")
        left = [sum((rows[i][j] for i in accepted), Fraction(0))
                for j in range(len(rows[0]))]
        right = [sum((rows[i][j] for i in rejected), Fraction(0))
                 for j in range(len(rows[0]))]
        if left != right:
            raise ValueError("trade feature sums are unequal")
        return {"valid": True, "status": "VERIFIED", "errors": [],
                "mass_per_side": len(accepted), "feature_dimension": len(left),
                "common_feature_sum": [_json_number(v) for v in left],
                "input_sha256": digest}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def trade_control():
    assignments = list(product((0, 1), repeat=4))
    truth = [bool((a or b) and (c or d)) for a, b, c, d in assignments]
    accepted = [assignments.index((1, 0, 1, 0)), assignments.index((0, 1, 0, 1))]
    rejected = [assignments.index((1, 1, 0, 0)), assignments.index((0, 0, 1, 1))]
    cert = make_trade_certificate(truth, assignments, accepted, rejected)
    nonlinear_features = [[int(a or b), int(c or d)] for a, b, c, d in assignments]
    nonlinear_predictions = [-sum(row) <= -2 for row in nonlinear_features]
    return {"formula": "(a OR b) AND (c OR d)", "variable_order": ["a", "b", "c", "d"],
            "assignments": [list(row) for row in assignments], "truth_table": truth,
            "features": [list(row) for row in assignments], "certificate": cert,
            "verification": verify_trade_certificate(truth, assignments, cert),
            "nonlinear_feature_positive_control": {
                "features": nonlinear_features, "weights": [-1, -1], "offset": 0,
                "cutoff": -2, "all_rows_correct": nonlinear_predictions == truth,
                "meaning": "Clause-satisfaction features change the score class; no matching realization is claimed."}}


def run_experiments():
    here = Path(__file__).resolve().parent
    source_names = ("threshold_controls.py", "test_threshold_controls.py", "THEOREM.md")
    before = {name: sha256((here / name).read_bytes()).hexdigest() for name in source_names}
    started = perf_counter()
    controls = [or_control(k) for k in range(1, 6)]
    aggregation, trade = aggregation_control(), trade_control()
    if not all(c["all_states_verified"] for c in controls) or not trade["verification"]["valid"]:
        raise AssertionError("a claimed control failed independent verification")
    after = {name: sha256((here / name).read_bytes()).hexdigest() for name in source_names}
    brief = here.parent / "NEXT_RESEARCH_BRIEF.md"
    return {"scope": "Finite exact matching controls and a universal affine-score trade; no SAT decision reduction is excluded merely by all-input classification failure.",
            "or_controls": controls, "aggregation_counterexample": aggregation,
            "affine_trade": trade,
            "totals": {"or_graphs": len(controls),
                       "physical_states": sum(c["physical_states"] for c in controls),
                       "edge_subset_checks": sum(c["edge_subset_checks"] for c in controls),
                       "aggregation_assignments": len(aggregation["rows"]),
                       "trade_truth_table_rows": len(trade["truth_table"])},
            "elapsed_seconds": perf_counter() - started, "source_sha256": before,
            "source_unchanged_during_run": before == after,
            "research_brief_sha256": sha256(brief.read_bytes()).hexdigest(),
            "research_brief_note": "The earlier paired AND exclusion concerns a gate relation including its output, not the input-only conjunction predicate."}


if __name__ == "__main__":
    result = run_experiments()
    destination = Path(__file__).with_name("RESULTS.json")
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"saved": str(destination), "totals": result["totals"],
                      "source_unchanged_during_run": result["source_unchanged_during_run"]}))
