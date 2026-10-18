"""Replay saved original-input proofs; independently expand the small field controls."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
from itertools import product
import json
from math import isqrt, prod
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read(relative):
    return json.loads((HERE / relative).read_text(encoding="utf-8"))


def main():
    source_references = 0

    def hashes(mapping, base=HERE):
        nonlocal source_references
        for name, digest in mapping.items():
            path = base / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
            source_references += 1

    residue = module("audit_residue", "coefficient_residue_lab/coefficient_residue.py")
    interval = module("audit_interval", "interval_coefficient_lab/intervals.py")
    structure = module("audit_structure", "coefficient_structure_lab/structure.py")
    packing = module("audit_packing", "packed_cost_exact_matching/packing.py")
    result = {}

    data = read("coefficient_residue_lab/RESULTS.json")
    hashes(data["source_sha256"], HERE / "coefficient_residue_lab")
    exact = unknown = witnesses = 0
    for case in data["cases"]:
        for query in case["queries"]:
            claim = query["result"]
            if claim["status"] == "EXACT":
                check = residue.verify_coefficient_proof(case["choices"], case["target"], claim["certificate"],
                                                         modulus=query["modulus"], **data["verification_limits"])
                assert check["valid"]
                assert claim["target_coefficient"] == claim["certificate"]["target_coefficient"]
                assert claim["attainable"] == (claim["target_coefficient"] > 0)
                exact += 1
                if claim["witness"] is not None:
                    assert residue.verify_choice_witness(case["choices"], case["target"], claim["witness"],
                                                         modulus=query["modulus"])["valid"]
                    witnesses += 1
            else:
                assert claim["status"] == "UNKNOWN"
                assert all(claim[key] is None for key in ("target_coefficient", "attainable", "certificate", "witness"))
                unknown += 1
    result["residue"] = {"exact_proofs": exact, "unknown": unknown, "original_choice_witnesses": witnesses}

    data = read("coefficient_isolation_lab/RESULTS.json")
    hashes(data["source_sha256_before"], HERE / "coefficient_isolation_lab")
    assert data["source_sha256_before"] == data["source_sha256_after"]
    for case in data["packed_controls"]:
        request = case["request"]
        counts = Counter(sum(pair[b] for pair, b in zip(request["choices"], bits))
                         for bits in product((0, 1), repeat=len(request["choices"])))
        assert counts[request["target"]] == case["expected_count"]
        assert case["packed"]["coefficient"] == case["sparse"]["coefficient"] == case["expected_count"]
    ladder = data["large_degree_special_case"]
    pairs = ladder["request"]["choices"]
    assert pairs == [[0, 1 << i] for i in range(len(pairs))]
    assert 0 <= ladder["request"]["target"] < 1 << len(pairs)
    assert ladder["binary_ladder"]["coefficient"] == 1
    assert ladder["packed"]["status"] == ladder["sparse"]["status"] == "UNKNOWN"
    field_cases = field_evaluations = 0
    for case in data["filters"]:
        request, claim = case["request"], case["result"]
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(encoded).hexdigest() == case["request_sha256"]
        choices, target = request["choices"], request["target"]
        counts = Counter(sum(pair[b] for pair, b in zip(choices, bits))
                         for bits in product((0, 1), repeat=len(choices)))
        assert sorted(counts.items()) == [tuple(row) for row in case["original_coefficients"]]
        p, order, omega = request["p"], request["order"], request["omega"]
        assert p >= 2 and all(p % d for d in range(2, isqrt(p)+1))
        assert pow(omega, order, p) == 1 and all(pow(omega, d, p) != 1 for d in range(1, order))
        folded = sum(count for weight, count in counts.items() if (weight-target) % order == 0)
        assert folded == case["folded_integer_count"]
        assert counts[target] == case["target_count"]
        assert len(claim["evaluations"]) == order
        weighted_total = 0
        for j, row in enumerate(claim["evaluations"]):
            point = pow(omega, j, p)
            value = sum(count*pow(point, weight, p) for weight, count in counts.items()) % p
            weighted = value*pow(omega, (-j*target) % order, p) % p
            assert row == {"index": j, "point": point, "value": value, "weighted_value": weighted}
            weighted_total += weighted
            field_evaluations += 1
        assert weighted_total*pow(order, -1, p) % p == claim["filter_residue"] == folded % p
        if "exact_coefficient" in claim:
            assert claim["exact_coefficient"] == counts[target]
        if "exact_folded_count" in claim:
            assert claim["exact_folded_count"] == folded
        if claim["coefficient_decision"] == "POSITIVE":
            assert counts[target] > 0
        elif claim["coefficient_decision"] == "ZERO":
            assert counts[target] == 0
        else:
            assert claim["coefficient_decision"] == "UNKNOWN"
        field_cases += 1
    crt = data["verified_same_count_CRT"]
    sources = {case["name"]: case for case in data["filters"]}
    selected = [sources[name] for name in crt["source_filter_names"]]
    assert all(case["request"]["choices"] == selected[0]["request"]["choices"] and
               case["request"]["target"] == selected[0]["request"]["target"] and case["result"]["alias_free"]
               for case in selected)
    assert crt["congruences"] == [[case["request"]["p"], case["result"]["filter_residue"]] for case in selected]
    assert prod(m for m, _ in crt["congruences"]) > crt["count_bound"] >= selected[0]["target_count"]
    assert crt["result"]["coefficient"] == selected[0]["target_count"]
    result["isolation"] = {"independently_expanded_filter_requests": field_cases,
                           "exact_evaluation_rows": field_evaluations, "same_original_count_CRT": True,
                           "independent_packed_controls": len(data["packed_controls"]),
                           "binary_ladder_identity_checked": True}

    data = read("coefficient_structure_lab/RESULTS.json")
    hashes(data["source_sha256"], HERE / "coefficient_structure_lab")
    exact = unknown = matching = 0
    for case in data["controls"]:
        encoding = case["original_encoding"]
        n, clauses, pairs, target = (encoding[key] for key in ("n", "clauses", "choice_weights", "target"))
        assert packing.verify_encoding(n, clauses, encoding)
        claim = case["result"]
        if claim["status"] == "EXACT":
            check = structure.verify_structure(n, clauses, pairs, target, claim, order=case["external_order"], **case["limits"])
            assert check["valid"] and check["coefficient"] == case["independent_expected_coefficient"]
            exact += 1
        else:
            assert claim["status"] == "UNKNOWN" and claim["coefficient"] is None and claim["positive"] is None
            unknown += 1
        solution = case["known_original_solution"]
        if solution is not None:
            assert packing.satisfied(n, clauses, solution["assignment"])
            check = packing.verify_matching(encoding, solution["matching_edge_ids"])
            assert check["valid"] and check["choice_bits"] == solution["choice_bits"]
            matching += 1
    result["structure"] = {"saved_exact_proofs": exact, "unknown": unknown,
                           "original_solution_witnesses": matching,
                           "note": "630 other small generated cases are reproducible through the frozen runner; their certificates are not stored here."}

    data = read("interval_coefficient_lab/RESULTS.json")
    hashes(data["source_sha256"])
    exact = unknown = modular = matching = 0
    for case in data["cases"]:
        proof = case["proof"]
        check = interval.verify(case["choices"], case["target"], proof)
        if proof["status"] == "EXACT":
            assert check["status"] == "VERIFIED" and check["feasible"] == case["reference_feasible"]
            exact += 1
        else:
            assert check["status"] == "UNKNOWN" and "feasible" not in proof
            unknown += 1
        for witness in case.get("separate_modular_witnesses", []):
            bits = witness["bits"]
            assert len(bits) == len(case["choices"]) and all(type(b) is int and b in (0, 1) for b in bits)
            weight = sum(pair[b] for pair, b in zip(case["choices"], bits))
            assert weight == witness["actual_weight"] != case["target"]
            assert (weight-case["target"]) % witness["modulus"] == 0
            modular += 1
        if case["family"] == "packed_sat":
            assert packing.verify_encoding(case["n"], case["clauses"], case["encoding"])
            assert case["choices"] == case["encoding"]["choice_weights"] and case["target"] == case["encoding"]["target"]
            for key in ("original_matching_witness", "interval_matching_witness"):
                if key in case:
                    assert packing.verify_matching(case["encoding"], case[key])["valid"]
                    matching += 1
    result["interval"] = {"exact_proofs": exact, "unknown": unknown,
                          "separate_modular_witnesses": modular, "original_matching_witnesses": matching}

    data = read("ALGEBRAIC_CROSSCHECK.json")
    hashes(data["source_sha256"])
    for case in data["cases"]:
        check = structure.verify_structure(case["n"], case["clauses"], case["choices"], case["target"],
                                           case["structure_proof"], order=case["order"])
        assert check["valid"] and check["coefficient"] == case["original_reference_count"]
    result["same_request_crosscheck"] = {"exact_proofs": len(data["cases"]), **data["summary"]}
    result["source_references_matched"] = source_references
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    result["all_checks_passed"] = True
    (HERE / "ALGEBRAIC_ARTIFACT_AUDIT.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
