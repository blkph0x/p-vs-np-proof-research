"""Independent exact replay of the RM(2,5) candidate-cut separation scan."""
from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
FULL = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
WITNESS = HERE / "REED_MULLER_SOS_SEVEN_CUT_RESULTS.json"
SCAN = HERE / "REED_MULLER_SOS_CANDIDATE_SCAN_RESULTS.json"
REVIEW_JSON = HERE / "REED_MULLER_SOS_CANDIDATE_SCAN_INDEPENDENT_REVIEW.json"
REVIEW_MD = HERE / "REED_MULLER_SOS_CANDIDATE_SCAN_INDEPENDENT_REVIEW.md"
_MOMENT_CACHE: tuple[Fraction, ...] | None = None


def _points(mask: int) -> tuple[int, ...]:
    return tuple(point for point in range(32) if mask >> point & 1)


def _rank(vectors: tuple[int, ...]) -> int:
    basis: list[int] = []
    for value in vectors:
        for pivot in basis:
            value = min(value, value ^ pivot)
        if value:
            basis.append(value)
            basis.sort(reverse=True)
    return len(basis)


def _canonicalize(mask: int) -> tuple[int, dict[int, int]]:
    points = _points(mask)
    nonzero = tuple(point for point in points if point)
    rank = _rank(nonzero)
    if rank == 0:
        return mask, {0: 0}
    best: int | None = None
    best_mapping: dict[int, int] | None = None
    for basis in itertools.combinations(nonzero, rank):
        if _rank(basis) != rank:
            continue
        for ordered in itertools.permutations(basis):
            coordinates: dict[int, int] = {0: 0}
            for index, vector in enumerate(ordered):
                for value, image in list(coordinates.items()):
                    coordinates[value ^ vector] = image | (1 << index)
            image = sum(1 << coordinates[point] for point in points)
            if best is None or image < best:
                best = image
                best_mapping = {point: coordinates[point] for point in points}
    if best is None or best_mapping is None:
        raise ValueError("failed to canonicalize scope")
    return best, best_mapping


def _moments(source: dict, witness: dict) -> tuple[Fraction, ...]:
    global _MOMENT_CACHE
    if _MOMENT_CACHE is not None:
        return _MOMENT_CACHE
    index: dict[tuple[int, int], int] = {}
    for variable, orbit in enumerate(source["variable_orbits"]):
        scope = int(orbit["scope"])
        support = [int(value) for value in source["allowed_projection_representatives"][str(scope)]]
        for atom in orbit["atoms"]:
            index[(scope, support[int(atom)])] = variable

    def variable_for(mask: int, atom: int) -> int:
        canonical, mapping = _canonicalize(mask)
        positions = {point: i for i, point in enumerate(_points(canonical))}
        canonical_atom = 0
        for i, point in enumerate(_points(mask)):
            if atom >> i & 1:
                canonical_atom |= 1 << positions[mapping[point]]
        return index[(canonical, canonical_atom)]

    masses = [Fraction(value) for value in witness["primal_orbit_masses"]]
    moments = [Fraction(1)]
    for k in range(1, 6):
        total = Fraction(0)
        for combination in itertools.combinations(range(1, 32), k):
            mask = sum(1 << point for point in combination)
            total += masses[variable_for(mask, (1 << k) - 1)]
        moments.append(total)
    _MOMENT_CACHE = tuple(moments)
    return _MOMENT_CACHE


def _multiply(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return tuple(result)


def _value(polynomial: tuple[int, ...], t: int) -> int:
    return sum(coefficient * t**power for power, coefficient in enumerate(polynomial))


def _family() -> list[tuple[str, tuple[int, ...], list[str]]]:
    base: list[tuple[str, tuple[int, ...], list[str]]] = []
    for root in range(32):
        base.append((f"square_{root}", (root * root, -2 * root, 1), [f"square_{root}"]))
    for root in range(31):
        base.append((f"adjacent_{root}_{root + 1}",
                     (root * (root + 1), -(2 * root + 1), 1),
                     [f"adjacent_{root}_{root + 1}"]))
    base.append(("boundary_0_31", (0, 31, -1), ["boundary_0_31"]))
    family = list(base)
    for (left_name, left, _), (right_name, right, _) in itertools.combinations_with_replacement(base, 2):
        polynomial = _multiply(left, right)
        if len(polynomial) <= 6:
            family.append((f"{left_name}*{right_name}", polynomial,
                           [left_name, right_name]))
    return family


def _expectation(polynomial: tuple[int, ...], moments: tuple[Fraction, ...]) -> Fraction:
    values = [_value(polynomial, t) for t in range(32)]
    differences = values[:]
    coefficients: list[int] = []
    while differences:
        coefficients.append(differences[0])
        differences = [differences[i + 1] - differences[i]
                       for i in range(len(differences) - 1)]
    return sum(Fraction(coefficients[index]) * moments[index]
               for index in range(len(polynomial)))


def replay(source: dict, witness: dict, scan: dict) -> dict[str, object]:
    if scan.get("schema") != "reed_muller_sos_candidate_scan_results_v1":
        raise ValueError("candidate scan schema mismatch")
    if scan.get("status") != "SEPARATION_ONLY":
        raise ValueError("candidate scan must remain separation-only")
    if scan.get("family") != "RM(2,5)" or scan.get("pin") != 0:
        raise ValueError("candidate scan family or pin mismatch")
    expected_hashes = {FULL.name: hashlib.sha256(FULL.read_bytes()).hexdigest(),
                       WITNESS.name: hashlib.sha256(WITNESS.read_bytes()).hexdigest()}
    if scan.get("source_sha256") != expected_hashes:
        raise ValueError("candidate scan source hash mismatch")
    moments = _moments(source, witness)
    family = _family()
    evaluated: list[dict[str, object]] = []
    for name, polynomial, factors in family:
        if not all(_value(polynomial, t) >= 0 for t in range(32)):
            raise ValueError(f"invalid nonnegative-domain candidate: {name}")
        evaluated.append({"name": name, "polynomial": list(polynomial),
                          "factors": factors,
                          "degree": len(polynomial) - 1,
                          "expectation": str(_expectation(polynomial, moments))})
    evaluated.sort(key=lambda row: (Fraction(row["expectation"]), str(row["name"])))
    negative = [row for row in evaluated if Fraction(row["expectation"]) < 0]
    selected = negative[0]
    if scan.get("candidate_count") != len(evaluated):
        raise ValueError("candidate count mismatch")
    if scan.get("negative_candidate_count") != len(negative):
        raise ValueError("negative candidate count mismatch")
    if scan.get("moments_binomial_basis") != [str(value) for value in moments]:
        raise ValueError("moment vector mismatch")
    if scan.get("selected_candidate") != selected:
        raise ValueError("selected candidate mismatch")
    if scan.get("top_negative_candidates") != negative[:20]:
        raise ValueError("negative candidate ranking mismatch")
    return {"valid": True, "status": scan["status"],
            "candidate_count": len(evaluated),
            "negative_candidate_count": len(negative),
            "selected_candidate": selected,
            "scope": scan["scope"]}


def main() -> None:
    source = json.loads(FULL.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS.read_text(encoding="utf-8"))
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    result = replay(source, witness, scan)
    REVIEW_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REVIEW_MD.write_text(
        "# Independent RM(2,5) candidate-cut review\n\n"
        "The independent exact replay recomputed the binomial moments, rebuilt the "
        "candidate family, and confirmed separation of the saved seven-cut witness.\n\n"
        f"- candidates checked: `{result['candidate_count']}`\n"
        f"- negative candidates: `{result['negative_candidate_count']}`\n"
        f"- selected candidate: `{result['selected_candidate']['name']}`\n"
        f"- exact expectation: `{result['selected_candidate']['expectation']}`\n\n"
        "This is a separation-only artifact. It does not certify the optimum after "
        "adding the candidate cut.\n", encoding="utf-8")
    print("REED_MULLER_SOS_CANDIDATE_SCAN_INDEPENDENT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
