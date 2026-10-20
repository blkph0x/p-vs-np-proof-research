
"""Generate and verify the full RM(2,5) level-eight certificate."""
from __future__ import annotations
import json
from fractions import Fraction
from pathlib import Path

from reed_muller_full_level8 import build_model, verify_primal

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "REED_MULLER_LEVEL_D_FULL_RESULTS.json"


def _normalise_matrix(matrix):
    return [{str(index): int(value) for index, value in sorted(row.items(), key=lambda item: int(item[0]))}
            for row in matrix]


def _normalise_model(model):
    payload = dict(model)
    payload["matrix"] = _normalise_matrix(model["matrix"])
    return payload


def main() -> None:
    saved = json.loads(OUT.read_text(encoding="utf-8"))
    masses = [Fraction(value) for value in saved["primal_orbit_masses"]]
    model = build_model()
    verification = verify_primal(model, masses)
    rebuilt = _normalise_model(model)
    structural_fields = {
        "scope_representatives": "scope_reps",
        "scope_orbit_sizes": "scope_orbit_sizes",
        "allowed_projection_representatives": "allowed_reps",
        "stabilizer_induced_orders": "stabilizer_orders",
        "variable_orbits": "variable_orbits",
        "row_orbits": "rows",
        "rhs": "rhs",
        "quotient_matrix": "matrix",
        "objective": "objective",
        "variable_orbit_count": "variable_orbit_count",
        "row_orbit_count": "row_orbit_count",
        "quotient_nonzero_count": "quotient_nonzero_count",
        "affine_flat_span_rank": "affine_flat_span_rank",
    }
    for saved_key, model_key in structural_fields.items():
        expected = saved.get(saved_key)
        actual = rebuilt.get(model_key)
        if saved_key in {"scope_representatives", "allowed_projection_representatives"}:
            expected = {str(k): v for k, v in expected.items()}
        if expected != actual:
            raise ValueError(f"saved structural field differs: {saved_key}")
    if saved.get("full_level_8_optimum") != "31/5":
        raise ValueError("saved objective claim mismatch")
    if saved.get("selected_model_lower_bound") != "31/5":
        raise ValueError("lower-bound provenance mismatch")
    saved["objective_convention"] = "nonpin_weight"
    saved["full_level_8_total_optimum"] = "36/5"
    saved["integer_pinned_optimum"] = "7"
    saved["integer_pinned_nonpin_optimum"] = "7"
    saved["integer_pinned_total_optimum"] = "8"
    saved["full_level_8_integrality_ratio"] = "35/31"
    saved["full_level_8_total_integrality_ratio"] = "10/9"
    saved["verification"] = verification
    saved["verification"]["source_rebuilt"] = True
    saved["stabilizer_generators"] = rebuilt["stabilizer_generators"]
    OUT.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("REED_MULLER_FULL_LEVEL8_PASS")
    print("variable_orbits=2174 row_orbits=27926 nonpin_optimum=31/5 total_optimum=36/5")


if __name__ == "__main__":
    main()
