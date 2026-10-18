"""Independent verification of the dense 3-CNF Fourier-spectrum artifact."""

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def clauses_for(n):
    """Independent reconstruction of the four-clause forcing gadget."""
    clauses = []
    for i in range(n):
        x, a, b = i + 1, n + i + 1, 2 * n + i + 1
        clauses.extend(((x, a, b), (x, a, -b),
                        (x, -a, b), (x, -a, -b)))
    return tuple(clauses)


def cyclic_clauses_for(n):
    """Independently reconstruct the distinct-variable cyclic family."""
    if n < 3:
        raise ValueError("n must be at least 3")
    clauses = []
    for i in range(n):
        x = i + 1
        a = ((i + 1) % n) + 1
        b = ((i + 2) % n) + 1
        clauses.extend(((x, a, b), (x, a, -b),
                        (x, -a, b), (x, -a, -b)))
    return tuple(clauses)


def cyclic_target_clauses_for(n, target):
    """Independently reconstruct the unique-model family for any target."""
    if n < 3 or not 0 <= target < (1 << n):
        raise ValueError("invalid target family parameters")
    clauses = []
    for i in range(n):
        x = i + 1
        a = ((i + 1) % n) + 1
        b = ((i + 2) % n) + 1
        forced = x if ((target >> i) & 1) else -x
        clauses.extend(((forced, a, b), (forced, a, -b),
                        (forced, -a, b), (forced, -a, -b)))
    return tuple(clauses)


def literal_true(literal, assignment):
    bit = (assignment >> (abs(literal) - 1)) & 1
    return bool(bit) if literal > 0 else not bool(bit)


def truth_table(n):
    variables = 3 * n
    clauses = clauses_for(n)
    return [int(all(any(literal_true(lit, assignment) for lit in clause)
                   for clause in clauses))
            for assignment in range(1 << variables)]


def cyclic_truth_table(n):
    clauses = cyclic_clauses_for(n)
    return [int(all(any(literal_true(lit, assignment) for lit in clause)
                   for clause in clauses))
            for assignment in range(1 << n)]


def independent_fwht(values):
    out = list(values)
    width = 1
    while width < len(out):
        for start in range(0, len(out), 2 * width):
            for offset in range(width):
                left = out[start + offset]
                right = out[start + offset + width]
                out[start + offset] = left + right
                out[start + offset + width] = left - right
        width *= 2
    return out


def independent_modular_fwht(values, prime):
    out = [value % prime for value in values]
    width = 1
    while width < len(out):
        for start in range(0, len(out), 2 * width):
            for offset in range(width):
                left = out[start + offset]
                right = out[start + offset + width]
                out[start + offset] = (left + right) % prime
                out[start + offset + width] = (left - right) % prime
        width *= 2
    return out


def verify():
    artifact = json.loads((ROOT / "RESULTS.json").read_text())
    assert artifact["all_checks_passed"]
    assert artifact["brute_force_rows"]
    for row in artifact["brute_force_rows"]:
        n = row["n"]
        variables = 3 * n
        clauses = clauses_for(n)
        assert len(clauses) == 4 * n
        assert all(len(clause) == 3 and len({abs(x) for x in clause}) == 3
                   for clause in clauses)
        spectrum = tuple(Fraction(value, 1 << variables)
                         for value in independent_fwht(truth_table(n)))
        assert sum(value != 0 for value in spectrum) == 1 << n
        helper_mask = ((1 << (2 * n)) - 1) << n if n else 0
        for subset in range(min(1 << variables, 128)):
            if subset & helper_mask:
                expected = Fraction(0)
            else:
                sign = -1 if subset.bit_count() & 1 else 1
                expected = Fraction(sign, 1 << n)
            assert spectrum[subset] == expected
    for row in artifact["analytic_rows"]:
        n = row["n"]
        assert row["analytic_nonzero_coefficients"] == 1 << n
        assert Fraction(row["coefficient_magnitude"]) == Fraction(1, 1 << n)
    for row in artifact["cyclic_brute_force_rows"]:
        n = row["n"]
        clauses = cyclic_clauses_for(n)
        assert len(clauses) == 4 * n
        assert all(len(clause) == 3 and len({abs(x) for x in clause}) == 3
                   for clause in clauses)
        values = cyclic_truth_table(n)
        assert sum(values) == 1
        assert values[-1] == 1
        spectrum = tuple(Fraction(value, 1 << n)
                         for value in independent_fwht(values))
        assert sum(value != 0 for value in spectrum) == 1 << n
        for subset, value in enumerate(spectrum):
            expected = Fraction(-1 if subset.bit_count() & 1 else 1, 1 << n)
            assert value == expected
    for row in artifact["cyclic_analytic_rows"]:
        n = row["n"]
        assert row["variables"] == n
        assert row["clauses"] == 4 * n
        assert row["analytic_nonzero_coefficients"] == 1 << n
        assert row["unique_satisfying_assignment"] == (1 << n) - 1
        assert Fraction(row["coefficient_magnitude"]) == Fraction(1, 1 << n)
    for row in artifact["cyclic_modular_rows"]:
        n, prime = row["n"], row["prime"]
        clauses = cyclic_clauses_for(n)
        values = cyclic_truth_table(n)
        inverse = pow(pow(2, n, prime), -1, prime)
        spectrum = tuple((value * inverse) % prime
                         for value in independent_modular_fwht(values, prime))
        assert sum(value != 0 for value in spectrum) == 1 << n
        assert row["modular_support"] == 1 << n
        assert all(value == ((-1 if mask.bit_count() & 1 else 1) * inverse) % prime
                   for mask, value in enumerate(spectrum))
    for row in artifact["cyclic_target_span_rows"]:
        n = row["n"]
        assert row["target_count"] == 1 << n
        assert row["indicator_span_dimension"] == 1 << n
        assert row["clauses_per_target"] == 4 * n
        assert row["field_independent"]
        # For every target, independently verify that the satisfying indicator
        # is the corresponding standard basis vector.  The resulting identity
        # matrix has rank 2^n over every field.
        for target in range(1 << n):
            clauses = cyclic_target_clauses_for(n, target)
            assert len(clauses) == 4 * n
            assert all(len(clause) == 3 and len({abs(x) for x in clause}) == 3
                       for clause in clauses)
            models = [assignment for assignment in range(1 << n)
                      if all(any(literal_true(lit, assignment) for lit in clause)
                             for clause in clauses)]
            assert models == [target]
    return {"independent_checks_passed": True,
            "analytic_rows": len(artifact["analytic_rows"]),
            "brute_force_rows": len(artifact["brute_force_rows"]),
            "cyclic_analytic_rows": len(artifact["cyclic_analytic_rows"]),
            "cyclic_brute_force_rows": len(artifact["cyclic_brute_force_rows"]),
            "cyclic_modular_rows": len(artifact["cyclic_modular_rows"]),
            "cyclic_target_span_rows": len(artifact["cyclic_target_span_rows"])}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
