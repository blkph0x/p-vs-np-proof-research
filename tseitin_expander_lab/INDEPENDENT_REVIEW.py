"""Independent replay of Tseitin encoding, parity certificates, and CDCL traces."""
from __future__ import annotations

from hashlib import sha256
import json
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def normalize(clause):
    values = {int(literal) for literal in clause}
    assert 0 not in values
    if any(-literal in values for literal in values):
        return None
    return tuple(sorted(values, key=lambda literal: (abs(literal), literal < 0)))


def resolve(left, right, pivot):
    positive = pivot + 1
    left_set, right_set = set(left), set(right)
    if positive in left_set and -positive in right_set:
        result = (left_set - {positive}) | (right_set - {-positive})
    elif -positive in left_set and positive in right_set:
        result = (left_set - {-positive}) | (right_set - {positive})
    else:
        raise AssertionError((left, right, pivot))
    return normalize(result)


def edges_and_incidence(n, edges):
    checked = set()
    for raw_u, raw_v in edges:
        u, v = int(raw_u), int(raw_v)
        assert 0 <= u < n and 0 <= v < n and u != v
        if u > v:
            u, v = v, u
        assert (u, v) not in checked
        checked.add((u, v))
    normalized = tuple(sorted(checked))
    incidence = [[] for _ in range(n)]
    for index, (u, v) in enumerate(normalized, start=1):
        incidence[u].append(index)
        incidence[v].append(index)
    return normalized, tuple(tuple(row) for row in incidence)


def expected_cnf(n, edges, charges):
    normalized, incidence = edges_and_incidence(n, edges)
    assert len(charges) == n and all(int(value) in (0, 1) for value in charges)
    clauses = []
    for vertex, variables in enumerate(incidence):
        target = int(charges[vertex])
        for bits in product((0, 1), repeat=len(variables)):
            if sum(bits) % 2 == target:
                continue
            clauses.append(tuple(-variable if bit else variable
                                 for variable, bit in zip(variables, bits)))
    return len(normalized), tuple(clauses)


def parity_record(n, edges, charges):
    normalized, incidence = edges_and_incidence(n, edges)
    counts = [0] * len(normalized)
    for variables in incidence:
        for variable in variables:
            counts[variable - 1] += 1
    total = sum(int(value) for value in charges) % 2
    return {
        "edge_occurrences": counts,
        "every_edge_occurs_twice": all(count == 2 for count in counts),
        "charge_sum_mod2": total,
        "odd_charge": total == 1,
        "parity_proves_unsat": all(count == 2 for count in counts) and total == 1,
    }


def replay_result(nvars, clauses, result):
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
    assert resolution_steps > 0
    return True


def main():
    artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "CERTIFICATES.json").read_text(encoding="utf-8"))
    assert artifact["all_cases_unsat"]
    assert len(certificates) == len(artifact["rows"]) == 4
    for saved, row in zip(certificates, artifact["rows"]):
        nvars, clauses = expected_cnf(saved["vertices"], saved["edges"], saved["charges"])
        assert nvars == saved["nvars"]
        assert [list(clause) for clause in clauses] == saved["clauses"]
        assert parity_record(saved["vertices"], saved["edges"], saved["charges"]) == saved["parity"]
        assert saved["parity"]["parity_proves_unsat"]
        assert replay_result(saved["nvars"], saved["clauses"], saved["result"])
        assert row["status"] == "UNSAT"
        assert row["proof_events"] == len(saved["result"]["proof"])
        assert row["stats"] == saved["result"]["stats"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "case_count": len(certificates),
              "parity_certificates_match": True, "proofs_match": True,
              "source_hashes_match": True}
    (HERE / "INDEPENDENT_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output))


if __name__ == "__main__":
    main()
