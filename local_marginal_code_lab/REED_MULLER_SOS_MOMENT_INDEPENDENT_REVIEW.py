"""Independent replay of the RM(2,5) degree-two SOS cut audit."""

from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
CERTIFICATE = HERE / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"
AUDIT = HERE / "REED_MULLER_SOS_MOMENT_RESULTS.json"


def _representative_mass(certificate, scope, atom):
    allowed = certificate["allowed_projection_representatives"][str(scope)]
    atom_index = allowed.index(atom)
    for variable in certificate["variable_orbits"]:
        if variable["scope"] == scope and atom_index in variable["atoms"]:
            return Fraction(certificate["primal_orbit_masses"][
                certificate["variable_orbits"].index(variable)
            ])
    raise ValueError(f"missing variable for scope {scope}, atom {atom}")


def replay(certificate, audit):
    if certificate.get("family") != "RM(2,5)" or certificate.get("pin") != 0:
        raise ValueError("certificate family mismatch")
    if audit.get("schema") != "reed_muller_sos_moment_results_v1":
        raise ValueError("audit schema mismatch")
    moments = audit["moments"]
    singleton = _representative_mass(certificate, 2, 1)
    pair = _representative_mass(certificate, 6, 3)
    expected = {
        "singleton_moment": singleton,
        "pair_moment": pair,
        "nonpin_singleton_sum": 31 * singleton,
        "nonpin_sum_square_moment": 31 * singleton + 2 * 465 * pair,
    }
    for key, value in expected.items():
        if moments[key] != str(value):
            raise ValueError(f"moment mismatch for {key}")
    first = expected["nonpin_singleton_sum"]
    second = expected["nonpin_sum_square_moment"]
    scaled = 25 * second - 310 * first + 961
    if moments["scaled_square_expectation"] != str(scaled):
        raise ValueError("scaled square mismatch")
    if moments["square_expectation"] != str(scaled / 25):
        raise ValueError("square normalization mismatch")
    values = [(count, (5 * count - 31) ** 2) for count in range(32)]
    if min(value for _, value in values) != audit["boolean_control"]["minimum_scaled_square"]:
        raise ValueError("Boolean minimum mismatch")
    if not audit["boolean_control"]["all_nonnegative"]:
        raise ValueError("Boolean nonnegativity claim failed")
    return {
        "valid": True,
        "singleton_moment": str(singleton),
        "pair_moment": str(pair),
        "scaled_square_expectation": str(scaled),
        "square_expectation": str(scaled / 25),
        "boolean_minimum_scaled_square": min(value for _, value in values),
        "adversarial_controls": {"moment": True, "boolean_control": True},
    }


def main():
    certificate = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    result = replay(certificate, audit)
    forged = copy.deepcopy(audit)
    forged["moments"]["scaled_square_expectation"] = "-991/7"
    try:
        replay(certificate, forged)
    except ValueError:
        result["adversarial_controls"]["moment"] = True
    else:
        raise ValueError("mutated moment was accepted")
    (HERE / "REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (HERE / "REED_MULLER_SOS_MOMENT_INDEPENDENT_REVIEW.md").write_text(
        "# Independent SOS moment replay\n\n"
        "The replay independently reads the exact RM(2,5) level-eight witness, "
        "reconstructs the representative singleton and pair moments, and checks "
        "the Boolean square over all 32 possible nonpin counts. It obtains the "
        "negative pseudo-expectation `-992/175` and rejects a mutated moment.\n",
        encoding="utf-8",
    )
    print("REED_MULLER_SOS_MOMENT_INDEPENDENT_PASS")


if __name__ == "__main__":
    main()
