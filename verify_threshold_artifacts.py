"""Check current provenance and replay saved threshold-phase evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads((HERE/path).read_text(encoding="utf-8"))


def main():
    checks = []
    labs = ("threshold_composition_lab", "saturated_clause_limits",
            "multiobjective_matching_limits", "packed_cost_exact_matching")
    saved = {lab: read(lab+"/RESULTS.json") for lab in labs}
    for lab, data in saved.items():
        mapping = data.get("source_sha256", data.get("source_sha256_after"))
        for name, expected in mapping.items():
            path = HERE/name if "/" in name else HERE/lab/name
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            checks.append({"path": path.relative_to(HERE).as_posix(), "matches": actual == expected,
                           "origin": lab+"/RESULTS.json", "sha256": actual})
    for name, expected in read("THRESHOLD_TEST_SUMMARY.json")["implementation_sha256"].items():
        actual = hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        checks.append({"path": name, "matches": actual == expected,
                       "origin": "THRESHOLD_TEST_SUMMARY.json", "sha256": actual})
    brief_hash = hashlib.sha256((HERE/"NEXT_RESEARCH_BRIEF.md").read_bytes()).hexdigest()
    checks.append({"path": "NEXT_RESEARCH_BRIEF.md", "matches": brief_hash == saved[labs[0]]["research_brief_sha256"],
                   "origin": labs[0]+"/RESULTS.json", "sha256": brief_hash})
    if not all(c["matches"] for c in checks):
        raise ArithmeticError("saved source hash is stale")

    sys.path.insert(0, str(HERE/labs[0]))
    from threshold_controls import verify_trade_certificate
    trade = saved[labs[0]]["affine_trade"]
    if not verify_trade_certificate(trade["truth_table"], trade["features"], trade["certificate"])["valid"]:
        raise ArithmeticError("saved feature trade failed")
    or_states = 0
    for graph in saved[labs[0]]["or_controls"]:
        k = graph["k"]
        if graph["edges"] != [[2*i, 2*i+1, 1] for i in range(k)] or graph["vertices"] != 2*k:
            raise ArithmeticError("unexpected OR graph")
        if [s["deleted_mask"] for s in graph["states"]] != list(range(1 << (2*k))):
            raise ArithmeticError("incomplete boundary states")
        for state in graph["states"]:
            pairs = [(state["deleted_mask"] >> (2*i)) & 3 for i in range(k)]
            valid = all(p in (0, 3) for p in pairs)
            expected = k-sum(p == 3 for p in pairs) if valid else None
            if state["minimum_cost"] != expected or state["feasible"] != valid:
                raise ArithmeticError("saved OR cost disagrees with independent component proof")
            if valid and state["witness_edge_ids"] != [i for i, p in enumerate(pairs) if p == 0]:
                raise ArithmeticError("saved OR witness incorrect")
            or_states += 1

    sys.path.insert(0, str(HERE/"matching_gadget_limits"))
    from matching_boundary import verify_matching as verify_boundary
    saturated_witnesses = 0
    for graph in saved[labs[1]]["promised_saturated_gadgets"]:
        r = graph["request"]
        for row in graph["signature"]:
            if not verify_boundary(r["n"], r["edges"], r["terminals"], row["deleted"], row["matching"]):
                raise ArithmeticError("saved saturation matching failed")
            if sum(r["edges"][i][2] for i in row["matching"]) != row["cost"]:
                raise ArithmeticError("saved saturation cost failed")
            saturated_witnesses += 1

    sys.path.insert(0, str(HERE/labs[2]))
    from clause_bounds import check_instance_matching, cnf_value
    bounded_witnesses = 0
    for case in saved[labs[2]]["controls"]:
        instance = case["instance"]
        for witness in case["witnesses"]:
            check = check_instance_matching(instance, witness["matching"])
            if check != witness["verification"]:
                raise ArithmeticError("saved simultaneous-bound result changed")
            request = instance["request"]
            if check["valid"] != cnf_value(request["variable_count"], request["clauses"], witness["assignment"]):
                raise ArithmeticError("saved bounded matching disagrees with original CNF")
            bounded_witnesses += 1

    sys.path.insert(0, str(HERE/labs[3]))
    from run_experiments import replay
    packed = replay(saved[labs[3]]["cases"])
    result = {"checked_utc": datetime.now(timezone.utc).isoformat(), "all_source_hashes_match": True,
              "source_references": len(checks), "checks": checks, "feature_trade_valid": True,
              "OR_boundary_states_replayed": or_states, "saturation_matching_witnesses_replayed": saturated_witnesses,
              "bounded_matching_witnesses_replayed": bounded_witnesses, "packed_replay": packed,
              "scope": "Stored evidence and current-source binding; no new optimization search.",
              "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/"THRESHOLD_ARTIFACT_AUDIT.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}))


if __name__ == "__main__":
    main()
