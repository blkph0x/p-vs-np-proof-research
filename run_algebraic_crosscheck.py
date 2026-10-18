"""Compare interval membership and certified clause contraction on identical inputs."""
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "coefficient_structure_lab"))
import structure


def local_slack_count(clause, assignment):
    false_count = sum(bool((assignment >> (abs(lit)-1)) & 1) != (lit > 0) for lit in clause)
    return sum(false_count+sum(slacks) == len(clause)-1
               for slacks in product((0, 1), repeat=len(clause)-1))


def original_count(n, clauses):
    if n <= 6:
        count = 0
        for assignment in range(1 << n):
            extensions = 1
            for clause in clauses:
                extensions *= local_slack_count(clause, assignment)
            count += extensions
        return count, "original Boolean enumeration and local slack enumeration"
    assert n == 3*len(clauses)
    assert clauses == [[3*j+1, 3*j+2, 3*j+3] for j in range(len(clauses))]
    one_clause = sum(local_slack_count([1, 2, 3], assignment) for assignment in range(8))
    return one_clause**len(clauses), "verified disjoint original clause components"


def main():
    sources = [Path(__file__).resolve(), HERE / "interval_coefficient_lab" / "RESULTS.json",
               HERE / "coefficient_structure_lab" / "structure.py"]
    hashes = {path.relative_to(HERE).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    inputs = json.loads(sources[1].read_text(encoding="utf-8"))
    rows = []
    for case in inputs["cases"]:
        if case["family"] != "packed_sat":
            continue
        n, clauses = case["n"], case["clauses"]
        order = list(range(n))
        proof = structure.solve_structure(n, clauses, case["choices"], case["target"], order=order)
        check = structure.verify_structure(n, clauses, case["choices"], case["target"], proof, order=order)
        reference, method = original_count(n, clauses)
        assert proof["status"] == "EXACT" and check["valid"] and check["coefficient"] == reference
        assert (reference > 0) == case["reference_feasible"]
        rows.append({"name": case["name"], "n": n, "clauses": clauses,
                     "choices": case["choices"], "target": case["target"], "order": order,
                     "interval_status": case["proof"]["status"], "original_reference_count": reference,
                     "reference_method": method, "structure_proof": proof, "verification": check})
    assert hashes == {path.relative_to(HERE).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": hashes,
              "summary": {"same_original_requests": len(rows), "exact_structure_proofs": len(rows),
                          "interval_unknown_resolved": sum(row["interval_status"] == "UNKNOWN" for row in rows),
                          "positive_counts": sum(row["original_reference_count"] > 0 for row in rows),
                          "zero_counts": sum(row["original_reference_count"] == 0 for row in rows)},
              "scope": "Finite comparison on identical inputs; no general small-width or polynomial solver claim.",
              "cases": rows}
    (HERE / "ALGEBRAIC_CROSSCHECK.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
