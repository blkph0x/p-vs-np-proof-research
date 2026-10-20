"""Independent replay of the bounded hidden-affine experiment.

This file deliberately does not import ``engine.py``.  It rebuilds the XOR
chain clauses, enumerates the projection, checks the even-parity relation, and
recomputes the saved work counters.
"""

from __future__ import annotations

import json
import hashlib
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xor3(left: int, right: int, out: int) -> tuple[tuple[int, ...], ...]:
    def lit(variable: int, positive: bool) -> int:
        return variable + 1 if positive else -(variable + 1)
    return (
        (lit(left, False), lit(right, False), lit(out, False)),
        (lit(left, True), lit(right, True), lit(out, False)),
        (lit(left, True), lit(right, False), lit(out, True)),
        (lit(left, False), lit(right, True), lit(out, True)),
    )


def chain(shared_count: int, permutation: tuple[int, ...]) -> tuple[tuple[tuple[int, ...], ...], tuple[int, ...]]:
    previous = permutation[0]
    next_variable = shared_count
    clauses: list[tuple[int, ...]] = []
    local: list[int] = []
    for shared in permutation[1:]:
        helper = next_variable
        next_variable += 1
        local.append(helper)
        clauses.extend(xor3(previous, shared, helper))
        previous = helper
    clauses.append((-(previous + 1),))
    return tuple(clauses), tuple(local)


def sat(clauses: tuple[tuple[int, ...], ...], assignment: dict[int, bool]) -> bool:
    return all(any((assignment[abs(lit) - 1] if lit > 0 else not assignment[abs(lit) - 1])
                   for lit in clause) for clause in clauses)


def projection(clauses, shared, local):
    out = []
    for smask in range(1 << len(shared)):
        found = False
        for lmask in range(1 << len(local)):
            assignment = {
                variable: bool(smask & (1 << index))
                for index, variable in enumerate(shared)
            }
            assignment.update({
                variable: bool(lmask & (1 << index))
                for index, variable in enumerate(local)
            })
            if sat(clauses, assignment):
                found = True
                break
        out.append(int(found))
    return tuple(out)


def expected(shared_count: int) -> tuple[int, ...]:
    return tuple(int(mask.bit_count() % 2 == 0) for mask in range(1 << shared_count))


def main() -> None:
    payload = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "representation_discovery_hidden_xor_v1"
    assert payload["status"] == "EXACT_BOUNDED_EXPERIMENT"
    assert payload["source_sha256"] == {
        "engine.py": sha256(HERE / "engine.py"),
        "run_experiment.py": sha256(HERE / "run_experiment.py"),
    }
    rows = payload["records"]
    assert len(rows) == 10
    for row in rows:
        count = int(row["shared_count"])
        permutation = tuple(int(value) for value in row["permutation"])
        assert tuple(sorted(permutation)) == tuple(range(count))
        clauses, local = chain(count, permutation)
        actual = projection(clauses, tuple(range(count)), local)
        assert list(actual) == row["projected_bits"]
        assert actual == expected(count)
        assert len(clauses) == row["clause_count"]
        assert len(local) == row["local_count"] == count - 1
        bit_width = max(1, (count - 1).bit_length())
        assert row["representation_bits"] == 8 + count * bit_width + 1
        projection_work = (1 << (count + len(local))) * len(clauses)
        candidate_work = (1 << count) * (2 * ((1 << count) - 1) + 1)
        assert row["verification_work"] == projection_work
        assert row["discovery_work"] == projection_work + candidate_work
    print(json.dumps({"independent_checks_passed": True, "records": len(rows)}))


if __name__ == "__main__":
    main()
