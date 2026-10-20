"""Generate the bounded hidden-affine representation experiment."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

from engine import records, reorder_gadget_blocks, rename_variables, xor_chain
from gaussian_baseline import recover_xor_relation
from nonlinear_control import classify

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    for row in records():
        chain = xor_chain(row.shared_count, row.permutation)
        baseline = recover_xor_relation(tuple(chain["clauses"]), tuple(chain["shared"]))
        rows.append({
            "shared_count": row.shared_count,
            "permutation": list(row.permutation),
            "clause_count": row.clause_count,
            "local_count": row.local_count,
            "encoded_representation_bits": row.encoded_representation_bits,
            "enumeration_discovery_work": row.enumeration_discovery_work,
            "exhaustive_replay_work": row.exhaustive_replay_work,
            "projected_bits": list(row.projected_bits),
            "linear_algebra_baseline": {
                "status": baseline.status,
                "support": list(baseline.support),
                "rhs": baseline.rhs,
                "work": baseline.work,
                "gadget_count": baseline.gadget_count,
            },
        })
    control_chain = xor_chain(5)
    renamed = rename_variables(control_chain,
                               {index: 8 - index for index in range(9)})
    controls = {
        "reordered_gadgets": reorder_gadget_blocks(control_chain),
        "duplicated_gadget": reorder_gadget_blocks(control_chain, duplicate_block=0),
        "renamed_all_variables": renamed,
    }
    control_rows = {}
    for name, chain in controls.items():
        baseline = recover_xor_relation(tuple(chain["clauses"]), tuple(chain["shared"]))
        control_rows[name] = {
            "clause_count": len(chain["clauses"]),
            "shared": list(chain["shared"]),
            "status": baseline.status,
            "support": list(baseline.support),
            "rhs": baseline.rhs,
            "work": baseline.work,
        }
    payload = {
        "schema": "representation_discovery_hidden_xor_v1",
        "status": "EXACT_BOUNDED_EXPERIMENT",
        "model": {
            "representation": "one even-parity XOR equation on the shared variables",
            "encoding": "existential XOR chain in 3-CNF with one helper per prefix",
            "discovery": "exhaustive projection followed by all nonempty XOR supports and both RHS values",
            "verification": "independent exhaustive projection replay",
            "representation_size_note": "encoded_representation_bits is the size of this label encoding, not a minimum over representations",
            "discovery_cost_note": "enumeration_discovery_work and exhaustive_replay_work are exact charges for the declared procedures, not lower bounds for other algorithms",
            "shared_range": [3, 7],
            "operation_formulas": {
                "local_count": "m - 1",
                "clause_count": "4m - 3",
                "encoded_representation_bits": "9 + m*ceil(log2(m))",
                "exhaustive_replay_work": "(4m - 3)*2^(2m - 1)",
                "candidate_search_work": "(2^(m + 1) - 1)*2^m",
                "enumeration_discovery_work": "(4m - 3)*2^(2m - 1) + (2^(m + 1) - 1)*2^m",
            },
        },
        "source_sha256": {
            "engine.py": sha256(HERE / "engine.py"),
            "run_experiment.py": sha256(HERE / "run_experiment.py"),
            "gaussian_baseline.py": sha256(HERE / "gaussian_baseline.py"),
        },
        "records": rows,
        "controls": control_rows,
        "nonlinear_control": classify(),
        "interpretation": (
            "The projected representation remains one XOR equation while the bounded "
            "projection-based enumeration work grows with the hidden helper variables. "
            "A separate GF(2) baseline recovers the same relation without projection, "
            "so the enumeration cost is algorithm-specific evidence rather than an "
            "intrinsic discovery lower bound."
        ),
    }
    (HERE / "RESULTS.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(rows), "status": payload["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
