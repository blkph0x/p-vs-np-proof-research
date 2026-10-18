"""Independent exact replay of the RM(1,3) level-four LP dual certificate.

This checker deliberately rebuilds the code, every supported local atom, and
the full local-marginal equality system from scratch.  It does not invoke an
LP solver and does not import the certificate-producing modules.
"""

from __future__ import annotations

import json
from fractions import Fraction
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "REED_MULLER_LEVEL_D_DUAL.json"
RESULTS = ROOT / "REED_MULLER_LEVEL_D_RESULTS.json"
REVIEW = ROOT / "REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.json"
REVIEW_MD = ROOT / "REED_MULLER_LEVEL_D_INDEPENDENT_REVIEW.md"


def monomial_row(mask: int) -> int:
    """Evaluate one degree-at-most-one monomial on F_2^3."""
    return sum(1 << point for point in range(8) if point & mask == mask)


def generator_rows() -> tuple[int, ...]:
    return tuple(monomial_row(mask) for mask in range(8) if mask.bit_count() <= 1)


def codewords(rows: tuple[int, ...]) -> tuple[int, ...]:
    words = [0]
    for row in rows:
        words += [word ^ row for word in tuple(words)]
    return tuple(sorted(words))


def model_data(level: int = 4, pin: int = 0) -> dict:
    rows = generator_rows()
    words = codewords(rows)
    pinned = tuple(word for word in words if word >> pin & 1)
    scopes: list[tuple[int, ...]] = []
    supported: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
    variables: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for size in range(level + 1):
        for scope in combinations(range(8), size):
            scope = tuple(scope)
            values = sorted(
                {tuple((word >> coordinate) & 1 for coordinate in scope) for word in pinned}
            )
            scopes.append(scope)
            supported[scope] = values
            variables.extend((scope, value) for value in values)
    return {
        "rows": rows,
        "words": words,
        "pinned": pinned,
        "scopes": scopes,
        "supported": supported,
        "variables": variables,
        "index": {variable: index for index, variable in enumerate(variables)},
    }


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def replay_certificate(certificate: dict) -> dict:
    if certificate.get("schema") != "rm1_level4_local_dual_v1":
        raise ValueError("invalid certificate schema")
    expected = {
        "family": "RM(1,3)",
        "pin": 0,
        "level": 4,
        "n": 8,
        "distance": 4,
        "variable_count": 982,
        "scope_count": 163,
        "equality_row_count": 2544,
        "dual_objective": "4",
        "objective_definition": "sum singleton one-marginals",
        "nonnegative_reduced_costs": True,
        "zero_slack_variables": 981,
    }
    for key, value in expected.items():
        if certificate.get(key) != value:
            raise ValueError(f"certificate field mismatch: {key}")

    data = model_data()
    scopes = data["scopes"]
    supported = data["supported"]
    variables = data["variables"]
    index = data["index"]
    if len(scopes) != certificate["scope_count"]:
        raise ValueError("scope count mismatch")
    if len(variables) != certificate["variable_count"]:
        raise ValueError("variable count mismatch")
    equality_rows = len(scopes) + sum(
        sum(
            len(supported[tuple(coordinate for coordinate in scope if coordinate != drop)])
            for drop in scope
        )
        for scope in scopes
    )
    if equality_rows != certificate["equality_row_count"]:
        raise ValueError("equality-row count mismatch")

    coefficients = [Fraction(0) for _ in variables]
    entries = certificate.get("entries")
    if not isinstance(entries, list) or len(entries) != 113:
        raise ValueError("dual entry count mismatch")
    dual_objective = Fraction(0)
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("malformed dual entry")
        multiplier = Fraction(_integer(entry.get("multiplier"), "multiplier"))
        kind = entry.get("kind")
        scope = tuple(entry.get("scope", ()))
        if scope not in supported:
            raise ValueError("dual entry references an unsupported scope")
        if kind == "norm":
            if set(entry) != {"kind", "scope", "multiplier"}:
                raise ValueError("malformed normalization row")
            dual_objective += multiplier
            for assignment in supported[scope]:
                coefficients[index[(scope, assignment)]] += multiplier
            continue
        if kind != "marg":
            raise ValueError("unknown dual row kind")
        if set(entry) != {"kind", "scope", "drop", "assignment", "multiplier"}:
            raise ValueError("malformed marginal row")
        drop = _integer(entry.get("drop"), "drop")
        if drop not in scope:
            raise ValueError("marginal row drops a missing coordinate")
        position = scope.index(drop)
        parent = tuple(coordinate for coordinate in scope if coordinate != drop)
        assignment = tuple(entry.get("assignment", ()))
        if assignment not in supported[parent]:
            raise ValueError("marginal row references an unsupported assignment")
        coefficients[index[(parent, assignment)]] += multiplier
        for child in supported[scope]:
            projected = tuple(value for offset, value in enumerate(child) if offset != position)
            if projected == assignment:
                coefficients[index[(scope, child)]] -= multiplier

    if dual_objective != Fraction(4):
        raise ValueError("dual objective mismatch")
    reduced_cost_slacks = []
    for variable, coefficient in zip(variables, coefficients):
        scope, assignment = variable
        objective_coefficient = (
            1 if len(scope) == 1 and assignment == (1,) else 0
        )
        slack = Fraction(objective_coefficient) - coefficient
        if slack < 0:
            raise ValueError(f"negative reduced-cost slack for {variable}")
        reduced_cost_slacks.append(slack)
    if max(reduced_cost_slacks) != Fraction(4):
        raise ValueError("reduced-cost slack maximum mismatch")
    if sum(slack == 0 for slack in reduced_cost_slacks) != certificate["zero_slack_variables"]:
        raise ValueError("zero-slack count mismatch")

    witness = 15  # x_0 + x_1 + x_2 + x_3 = 1 on the four low-order points.
    if witness not in data["words"] or not witness >> 0 & 1 or witness.bit_count() != 4:
        raise ValueError("integer witness mismatch")
    if any((left & right).bit_count() % 2 for left in data["rows"] for right in data["rows"]):
        raise ValueError("generator is not self-orthogonal")
    dual_rows = tuple(word for word in data["words"] if word)
    if any((word & witness).bit_count() % 2 for word in dual_rows):
        raise ValueError("witness violates a dual parity check")
    for scope in scopes:
        projection = tuple((witness >> coordinate) & 1 for coordinate in scope)
        if projection not in supported[scope]:
            raise ValueError("witness projection is not supported")

    return {
        "status": "VERIFIED",
        "valid": True,
        "family": "RM(1,3)",
        "pin": 0,
        "level": 4,
        "scope_count": len(scopes),
        "variable_count": len(variables),
        "equality_row_count": certificate["equality_row_count"],
        "dual_entry_count": len(entries),
        "dual_lower_bound": "4",
        "primal_witness_word": witness,
        "primal_witness_weight": witness.bit_count(),
        "combined_relaxation_optimum": "4",
    }


def main() -> None:
    certificate = json.loads(INPUT.read_text(encoding="utf-8"))
    verification = replay_certificate(certificate)
    RESULTS.write_text(
        json.dumps(
            {
                "schema": "reed_muller_level_d_results_v1",
                "description": "Exact level-four local-marginal dual certificate for pinned RM(1,3).",
                "records": [{"status": "FOUND", "certificate": certificate, "verification": verification}],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    REVIEW.write_text(
        json.dumps(
            {
                "schema": "reed_muller_level_d_independent_review_v1",
                "valid": True,
                "records": [verification],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    REVIEW_MD.write_text(
        "# Independent review\n\n"
        "This replay rebuilds the RM(1,3) code, all 163 scopes through level four, "
        "all 982 supported local atoms, and the 2,544 equality rows without an LP "
        "solver. It checks all 113 integer dual multipliers exactly and verifies "
        "the weight-four pinned primal witness.\n",
        encoding="utf-8",
    )
    print("VERIFIED_INDEPENDENT_REED_MULLER_LEVEL_D")
    print(
        f"scopes={verification['scope_count']} variables={verification['variable_count']} "
        f"dual_entries={verification['dual_entry_count']} optimum={verification['combined_relaxation_optimum']}"
    )


if __name__ == "__main__":
    main()
