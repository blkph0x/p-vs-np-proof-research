"""Independent verifier for the proof-complexity scaling certificates."""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def normalize(clause):
    values = {int(lit) for lit in clause}
    assert 0 not in values
    if any(-lit in values for lit in values):
        return None
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def resolve(left, right, pivot):
    positive = pivot + 1
    a, b = set(left), set(right)
    if positive in a and -positive in b:
        result = (a - {positive}) | (b - {-positive})
    elif -positive in a and positive in b:
        result = (a - {-positive}) | (b - {positive})
    else:
        raise AssertionError((left, right, pivot))
    return normalize(result)


def all_assignment_clauses(nvars):
    return tuple(
        tuple((variable + 1) if not bit else -(variable + 1)
              for variable, bit in enumerate(bits))
        for bits in product((0, 1), repeat=nvars)
    )


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [
        tuple(variable(pigeon, hole) for hole in range(holes))
        for pigeon in range(pigeons)
    ]
    clauses += [
        (-variable(pigeon, left), -variable(pigeon, right))
        for pigeon in range(pigeons)
        for left, right in combinations(range(holes), 2)
    ]
    clauses += [
        (-variable(left, hole), -variable(right, hole))
        for hole in range(holes)
        for left, right in combinations(range(pigeons), 2)
    ]
    return pigeons * holes, tuple(clauses)


def expected_clauses(saved):
    if saved["family"] == "all_assignments":
        return saved["nvars"], all_assignment_clauses(saved["parameter"])
    if saved["family"] == "pigeonhole":
        return pigeonhole(saved["pigeons"], saved["holes"])
    raise AssertionError(saved)


def direct_all_assignment(nvars, clauses):
    for assignment in product((False, True), repeat=nvars):
        if all(any(assignment[abs(lit) - 1] == (lit > 0)
                   for lit in clause) for clause in clauses):
            return True
    return False


def pigeonhole_is_unsat(pigeons, holes):
    # Every pigeon clause chooses at least one hole, and the pair clauses
    # enforce at most one. Hole-pair clauses then make those choices injective.
    return pigeons > holes


def replay(nvars, clauses, result):
    database = [normalize(clause) for clause in clauses]
    assert all(clause is not None for clause in database)
    learned_count = 0
    resolution_steps = 0
    learned_literals = 0
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
                resolution_steps += 1
            assert current == tuple(event["clause"])
            database.append(current)
            learned_count += 1
            learned_literals += len(current)
        elif event["kind"] == "terminal-empty":
            current = tuple(event["from_conflict"])
            assert current in database
            for step in event["derivation"]:
                assert tuple(step["left"]) == current
                right = tuple(step["right"])
                assert right in database
                current = resolve(current, right, int(step["pivot"]))
                assert current == tuple(step["result"])
                resolution_steps += 1
            assert current == ()
        else:
            raise AssertionError(event)
    assert result["status"] == "UNSAT"
    assert any(event["kind"] == "terminal-empty" for event in result["proof"])
    assert result["clauses"] == [list(clause) for clause in database]
    stats = result["stats"]
    assert stats["conflicts"] == len(result["proof"])
    assert stats["learned_clauses"] == learned_count
    assert stats["learned_literals"] == learned_literals
    assert stats["resolution_steps"] == resolution_steps
    assert len(result["proof"]) > 0
    return True


def expected_all_assignment_stats(nvars):
    half = 2 ** (nvars - 1)
    return {"decisions": half - 1, "conflicts": half,
            "learned_clauses": half - 1, "resolution_steps": 2 ** nvars - 1}


def main():
    artifact = json.loads((HERE / "SCALING_RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads(
        (HERE / "SCALING_CERTIFICATES.json").read_text(encoding="utf-8")
    )
    for saved, row in zip(certificates, artifact["rows"]):
        nvars, clauses = expected_clauses(saved)
        assert nvars == saved["nvars"]
        assert [list(clause) for clause in clauses] == saved["clauses"]
        assert replay(saved["nvars"], saved["clauses"], saved["result"])
        if saved["family"] == "all_assignments":
            assert direct_all_assignment(saved["nvars"], saved["clauses"]) is False
            expected = expected_all_assignment_stats(saved["parameter"])
            for key, value in expected.items():
                assert saved["result"]["stats"][key] == value
        else:
            assert pigeonhole_is_unsat(saved["pigeons"], saved["holes"])
        assert row["proof_events"] == len(saved["result"]["proof"])
        assert row["status"] == "UNSAT"
        assert row["elapsed_seconds"] > 0
    assert artifact["all_cases_unsat"]
    for name, digest in artifact["source_sha256"].items():
        path = ROOT / name
        assert sha256(path.read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "case_count": len(certificates),
              "proofs_match": True, "scaling_laws_match": True,
              "source_hashes_match": True}
    (HERE / "SCALING_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output))


if __name__ == "__main__":
    main()
