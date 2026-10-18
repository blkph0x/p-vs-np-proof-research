"""Independently replay the dense-U coverage-count artifact."""
from hashlib import sha256
import json
from pathlib import Path

import perturbation_coverage as coverage


HERE = Path(__file__).resolve().parent
CASES = [(128, 64, 7), (256, 128, 16), (512, 256, 27), (16, 8, 12)]


def _digest(value):
    data = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    return sha256(data).hexdigest()


def _independent_record(n, r, p):
    choices = 1 + r + r * (r - 1) // 2
    fixed_upper = choices ** n * (1 << (p * (r + n)))
    fixed_lower = 1 << (r * (n - r))
    all_upper = sum(
        (1 + rows + rows * (rows - 1) // 2) ** n
        * (1 << (p * (rows + n)))
        for rows in range(n + 1)
    )
    all_lower = 1 << ((n // 2) * (n - n // 2))
    largest = -1
    candidate = 0
    while sum(
        (1 + rows + rows * (rows - 1) // 2) ** n
        * (1 << (candidate * (rows + n)))
        for rows in range(n + 1)
    ) < all_lower:
        largest = candidate
        candidate += 1
    return {
        "n": n,
        "r": r,
        "p": p,
        "representation_upper_bound_bit_length": fixed_upper.bit_length(),
        "representation_upper_bound_sha256": _digest(fixed_upper),
        "systematic_rowspace_lower_bound_bit_length": fixed_lower.bit_length(),
        "systematic_rowspace_lower_bound_sha256": _digest(fixed_lower),
        "universal_coverage_excluded": fixed_lower > fixed_upper,
        "all_row_count_upper_bound_bit_length": all_upper.bit_length(),
        "all_row_count_upper_bound_sha256": _digest(all_upper),
        "all_row_count_systematic_lower_bound_bit_length": all_lower.bit_length(),
        "all_row_count_systematic_lower_bound_sha256": _digest(all_lower),
        "universal_coverage_excluded_with_any_row_count": all_lower > all_upper,
        "largest_excluded_label_budget": largest,
    }


def main():
    artifact = json.loads((HERE / "PERTURBATION_COVERAGE_RESULTS.json").read_text(encoding="utf-8"))
    if artifact.get("format") != "dense-u-perturbation-coverage-v1":
        raise AssertionError("wrong artifact format")
    saved_cases = artifact.get("cases")
    expected = [_independent_record(*case) for case in CASES]
    if saved_cases != expected:
        raise AssertionError("saved coverage records do not match independent arithmetic")
    generated = [coverage.bound_record(*case) for case in CASES]
    if generated != expected:
        raise AssertionError("module output differs from independent arithmetic")
    current_sources = {}
    for name in artifact["source_sha256"]:
        current_sources[name] = sha256((HERE / name).read_bytes()).hexdigest()
    if current_sources != artifact["source_sha256"]:
        raise AssertionError("source hash mismatch")
    if [tuple((row["n"], row["r"], row["p"])) for row in saved_cases] != CASES:
        raise AssertionError("case order changed")
    if not all(row["universal_coverage_excluded_with_any_row_count"] for row in saved_cases[:3]):
        raise AssertionError("large-case exclusions missing")
    if saved_cases[3]["universal_coverage_excluded_with_any_row_count"]:
        raise AssertionError("small positive control changed")
    print(json.dumps({
        "status": "PASS",
        "cases": len(saved_cases),
        "source_hashes_match": True,
        "independent_arithmetic_match": True,
    }, indent=2))


if __name__ == "__main__":
    main()
