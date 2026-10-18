import json
from datetime import datetime, timezone
from pathlib import Path

from circuit_order import build_edge_or_circuit, source_lower_bound


CASES = (
    ("path_6", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]),
    ("star_6", 6, [(0, i) for i in range(1, 6)]),
    ("cycle_6", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]),
    ("bipartite_3_2", 5, [(u, v) for u in range(3) for v in (3, 4)]),
    ("complete_4", 4, [(u, v) for u in range(4) for v in range(u + 1, 4)]),
)


def main():
    rows = []
    for name, n, edges in CASES:
        circuit = build_edge_or_circuit(n, edges)
        result = source_lower_bound(circuit)
        rows.append({
            "name": name,
            "source_vertices": n,
            "source_edges": len(edges),
            "circuit_variables": circuit["vertices"],
            "circuit_clauses": len(circuit["clauses"]),
            "all_ones_sat": True,
            "source_width": result["source"]["width"],
            "full_width": result["full"]["width"],
            "width_gap": result["full"]["width"] - result["source"]["width"],
            "extended_width": result["extended_width"],
            "additive_upper_bound_holds": result["additive_upper_bound_holds"],
            "source_states": result["source"]["state_count"],
            "full_states": result["full"]["state_count"],
            "lower_bound_holds": result["lower_bound_holds"],
            "source_order": result["source"]["order"],
            "full_order": result["full"]["order"],
            "extended_order": result["extended_order"],
        })
    output = {
        "format": "circuit-source-primal-lower-bound-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "all_lower_bounds_hold": all(row["lower_bound_holds"] for row in rows),
        "all_additive_upper_bounds_hold": all(row["additive_upper_bound_holds"] for row in rows),
        "all_controls_trivially_satisfiable": all(row["all_ones_sat"] for row in rows),
        "scope": "exact small controls; lower-bound bridge only, no P-versus-NP claim",
    }
    Path("RESULTS.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"status": "CIRCUIT_ORDER_BOUND_PASS",
                      "cases": len(rows),
                      "max_source_width": max(row["source_width"] for row in rows),
                      "max_full_width": max(row["full_width"] for row in rows),
                      "max_gap": max(row["width_gap"] for row in rows)}))


if __name__ == "__main__":
    main()
