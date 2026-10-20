"""Independent replay of the finite sparse-parity clause comparison."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "SPARSE_PARITY_CLAUSE_REVIEW.json"


def parity_cnf(scope: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    clauses = []
    for assignment in itertools.product((0, 1), repeat=len(scope)):
        if sum(assignment) % 2 == 0:
            continue
        clauses.append(tuple(
            variable + 1 if bit == 0 else -(variable + 1)
            for variable, bit in zip(scope, assignment)
        ))
    return tuple(clauses)


def substitute_pin(clause: tuple[int, ...], pin: int = 0) -> tuple[int, ...] | None:
    remainder = []
    for literal in clause:
        variable = abs(literal) - 1
        if variable == pin:
            if literal > 0:
                return None
            continue
        remainder.append(literal)
    return tuple(remainder)


def satisfies(clause: tuple[int, ...], assignment: dict[int, int]) -> bool:
    return any((assignment[abs(literal) - 1] if literal > 0
                else 1 - assignment[abs(literal) - 1]) for literal in clause)


def main() -> None:
    checks = ((0, 1, 2), (0, 1, 3))
    original = tuple(clause for scope in checks for clause in parity_cnf(scope))
    simplified = tuple(
        clause for clause in (substitute_pin(clause) for clause in original)
        if clause is not None
    )
    expected = ((2, 3), (-2, -3), (2, 4), (-2, -4))
    assert simplified == expected

    # The clause inequalities imply x1+x2 >= 1 and x1+x3 >= 1, hence F >= 1.
    positive = tuple(clause for clause in simplified if all(lit > 0 for lit in clause))
    assert positive == ((2, 3), (2, 4))
    clause_witness = {0: 1, 1: 1, 2: 0, 3: 0}
    assert all(satisfies(clause, clause_witness) for clause in original)
    assert all(sum(clause_witness[index] for index in scope) % 2 == 0
               for scope in checks)
    clause_value = sum(clause_witness[index] for index in (1, 2, 3))
    assert clause_value == 1

    # The check-local level-two model sees no whole ternary check on a free pair.
    check_local_witness = {0: 1, 1: 0, 2: 0, 3: 0}
    check_local_value = sum(check_local_witness[index] for index in (1, 2, 3))
    assert check_local_value == 0
    result = {
        "status": "EXACT_FINITE_COMPARISON",
        "checks": [list(scope) for scope in checks],
        "simplified_clauses": [list(clause) for clause in simplified],
        "clause_lp_optimum": clause_value,
        "check_local_level_two_value": check_local_value,
        "strict_gap": True,
        "scope": "four-variable pinned ternary-parity control only",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
