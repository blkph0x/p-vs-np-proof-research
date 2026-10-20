"""Write the exact affine-overlap RM(2,5) boundary certificate."""

from __future__ import annotations

import json
from pathlib import Path

from reed_muller_affine_overlap import build_quotient, exact_certificate_values, generators, verify_quotient


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_RESULTS.json"


def encode_row(row):
    if row[0] == "normalization":
        return {"kind": "normalization", "scope": list(row[1])}
    return {
        "kind": "consistency",
        "parent": list(row[1]),
        "child": list(row[2]),
        "child_atom": row[3],
    }


def main() -> None:
    model = build_quotient()
    primal, dual = exact_certificate_values()
    verification = verify_quotient(model, primal, dual)
    payload = {
        "schema": "reed_muller_level_d_affine_overlap_results_v1",
        "description": (
            "Exact symmetry-quotient certificate for affine RM(2,5) scopes "
            "with shared 4-flat, line, and singleton marginals."
        ),
        "family": "RM(2,5)",
        "pin": 0,
        "selected_scope_sizes": [8, 4, 2, 1],
        "scope_counts": {str(size): len(model["scopes"][size]) for size in (8, 4, 2, 1)},
        "variable_orbit_count": len(model["variable_orbits"]),
        "row_orbit_count": len(model["row_orbits"]),
        "generator_count": len(generators()),
        "affine_flat_span_rank": model["affine_flat_span_rank"],
        "variable_orbits": [
            {
                "representative_scope": list(model["variable_keys"][orbit[0]][0]),
                "representative_atom": model["variable_keys"][orbit[0]][1],
                "orbit_size": len(orbit),
                "mass": str(primal[index]),
            }
            for index, orbit in enumerate(model["variable_orbits"])
        ],
        "row_orbits": [
            {"representative": encode_row(model["row_representatives"][index]), "orbit_size": len(orbit)}
            for index, orbit in enumerate(model["row_orbits"])
        ],
        "quotient_matrix": [
            {str(index): coefficient for index, coefficient in sorted(row.items())}
            for row in model["matrix"]
        ],
        "rhs": [str(value) for value in model["rhs"]],
        "objective": [str(value) for value in model["objective"]],
        "primal_orbit_masses": [str(value) for value in primal],
        "dual_row_values": [str(value) for value in dual],
        "objective_convention": "nonpin_weight",
        "selected_model_optimum": "31/5",
        "selected_model_total_optimum": "36/5",
        "integer_pinned_optimum": "7",
        "integer_pinned_nonpin_optimum": "7",
        "integer_pinned_total_optimum": "8",
        "selected_model_integrality_ratio": "35/31",
        "selected_model_total_integrality_ratio": "10/9",
        "full_level_8_lower_bound": "31/5",
        "full_level_8_status": "UNRESOLVED",
        "verification": verification,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("REED_MULLER_AFFINE_OVERLAP_PASS")
    print("selected_model_optimum=31/5 full_level_8_status=UNRESOLVED")


if __name__ == "__main__":
    main()
