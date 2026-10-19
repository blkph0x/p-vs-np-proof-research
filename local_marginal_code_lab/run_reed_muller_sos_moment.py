"""Audit a degree-two SOS cut against the exact RM(2,5) level-eight witness."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from reed_muller_full_level8 import allowed, build_model, canonicalize, pts


ROOT = Path(__file__).resolve().parent
CERTIFICATE = ROOT / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
OUT = ROOT / "REED_MULLER_SOS_MOMENT_RESULTS.json"


def _variable_index(certificate, model):
    result = {}
    for index, variable in enumerate(certificate["variable_orbits"]):
        atoms = allowed(variable["scope"])
        for atom_index in variable["atoms"]:
            result[(variable["scope"], atoms[atom_index])] = index
    expected = sum(
        len(allowed(mask))
        for masks in model["scope_reps"].values()
        for mask in masks
    )
    if len(result) != expected:
        raise ValueError("variable map is not a partition")
    return result


def _atom_variable(mask, atom, variable_index):
    canonical, mapping = canonicalize(mask)[:2]
    canonical_positions = {point: index for index, point in enumerate(pts(canonical))}
    canonical_atom = 0
    for index, point in enumerate(pts(mask)):
        if atom >> index & 1:
            canonical_atom |= 1 << canonical_positions[mapping[point]]
    return variable_index[(canonical, canonical_atom)]


def _moments(certificate, model):
    variable_index = _variable_index(certificate, model)
    masses = tuple(Fraction(value) for value in certificate["primal_orbit_masses"])

    def mass(mask, atom):
        return masses[_atom_variable(mask, atom, variable_index)]

    singleton = {point: mass(1 << point, 1) for point in range(1, 32)}
    pair = {
        (left, right): mass((1 << left) | (1 << right), 3)
        for left in range(1, 32)
        for right in range(left + 1, 32)
    }
    if len(set(singleton.values())) != 1 or len(set(pair.values())) != 1:
        raise ValueError("the saved witness is not GL(5,2)-symmetric")
    first = sum(singleton.values())
    second = first + 2 * sum(pair.values())
    square_scaled = 25 * second - 310 * first + 961
    return {
        "singleton_moment": str(singleton[1]),
        "pair_moment": str(pair[(1, 2)]),
        "nonpin_singleton_sum": str(first),
        "nonpin_sum_square_moment": str(second),
        "scaled_square_expectation": str(square_scaled),
        "square_expectation": str(square_scaled / 25),
        "singleton_count": len(singleton),
        "pair_count": len(pair),
    }


def _boolean_control():
    values = [(count, (5 * count - 31) ** 2) for count in range(32)]
    return {
        "minimum_scaled_square": min(value for _, value in values),
        "minimum_attaining_counts": [count for count, value in values if value == min(v for _, v in values)],
        "all_nonnegative": all(value >= 0 for _, value in values),
        "checked_counts": len(values),
    }


def main() -> None:
    certificate = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    model = build_model()
    moments = _moments(certificate, model)
    expected = {
        "singleton_moment": "1/5",
        "pair_moment": "1/35",
        "nonpin_singleton_sum": "31/5",
        "nonpin_sum_square_moment": "1147/35",
        "scaled_square_expectation": "-992/7",
        "square_expectation": "-992/175",
    }
    for key, value in expected.items():
        if moments[key] != value:
            raise ValueError(f"unexpected exact moment: {key}={moments[key]}")
    boolean_control = _boolean_control()
    if not boolean_control["all_nonnegative"] or boolean_control["minimum_scaled_square"] != 1:
        raise ValueError("Boolean square control failed")
    payload = {
        "schema": "reed_muller_sos_moment_results_v1",
        "family": "RM(2,5)",
        "pin": 0,
        "source_certificate": "REED_MULLER_LEVEL_D_FULL_RESULTS.json",
        "polynomial": "(5*t - 31)^2 where t=sum_{p != 0} x_p",
        "validity_scope": "every Boolean assignment, independent of the RM code",
        "moments": moments,
        "boolean_control": boolean_control,
        "cut_status": "CUT_FOUND",
        "interpretation": (
            "The exact level-eight local-marginal witness violates a valid degree-two "
            "sum-of-squares inequality. This identifies a missing global moment constraint; "
            "it is not a P-versus-NP result."
        ),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("REED_MULLER_SOS_MOMENT_PASS")
    print("scaled_square_expectation=-992/7 square_expectation=-992/175")


if __name__ == "__main__":
    main()
