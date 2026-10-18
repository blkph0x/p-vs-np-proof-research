"""Independent verifier for general-CDCL models, clauses, and resolution traces."""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent


def normalize(clause):
    values = {int(lit) for lit in clause}
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def resolve(left, right, pivot):
    p = pivot + 1
    a, b = set(left), set(right)
    if p in a and -p in b:
        result = (a - {p}) | (b - {-p})
    elif -p in a and p in b:
        result = (a - {-p}) | (b - {p})
    else:
        raise AssertionError((left, right, pivot))
    return normalize(result)


def clause_satisfied(clause, assignment):
    return any(assignment[abs(lit) - 1] == (lit > 0) for lit in clause)


def direct(nvars, clauses):
    return any(all(clause_satisfied(clause, assignment) for clause in clauses)
               for assignment in product((False, True), repeat=nvars))


def replay(nvars, clauses, result):
    database = []
    for clause in clauses:
        canonical = normalize(clause)
        if canonical is not None:
            database.append(canonical)
    for event in result["proof"]:
        if event["kind"] == "learned":
            current = tuple(event["from_conflict"])
            assert current in database
            for step in event["derivation"]:
                assert tuple(step["left"]) == current
                right = tuple(step["right"])
                assert right in database
                current = resolve(current, right, int(step["pivot"]))
                assert current == tuple(step["result"])
            assert current == tuple(event["clause"])
            database.append(current)
        elif event["kind"] == "terminal-empty":
            current = tuple(event["from_conflict"])
            assert current in database
            for step in event["derivation"]:
                assert tuple(step["left"]) == current
                right = tuple(step["right"])
                assert right in database
                current = resolve(current, right, int(step["pivot"]))
                assert current == tuple(step["result"])
            assert current == ()
        else:
            raise AssertionError(event)
    if result["status"] == "SAT":
        model = result["model"]
        assert isinstance(model, dict)
        assignment = tuple(bool(model[str(v)] if str(v) in model else model[v])
                           for v in range(nvars))
        assert all(clause_satisfied(clause, assignment) for clause in clauses)
        assert direct(nvars, clauses)
    elif result["status"] == "UNSAT":
        assert any(event["kind"] == "terminal-empty" for event in result["proof"])
        assert not direct(nvars, clauses)
    else:
        assert result["reason"] in {"DECISION_CAP", "CONFLICT_CAP", "RESOLUTION_CAP"}
    return True


def main():
    artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "CERTIFICATES.json").read_text(encoding="utf-8"))
    for saved in certificates:
        assert replay(saved["nvars"], saved["clauses"], saved["result"])
    assert artifact["all_cases_match_direct"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "case_count": len(certificates),
              "proofs_match": True, "source_hashes_match": True}
    (HERE / "REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
