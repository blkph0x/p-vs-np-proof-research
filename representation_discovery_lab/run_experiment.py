"""Generate the bounded hidden-affine representation experiment."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

from engine import records, xor_chain

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    for row in records():
        rows.append({
            "shared_count": row.shared_count,
            "permutation": list(row.permutation),
            "clause_count": row.clause_count,
            "local_count": row.local_count,
            "representation_bits": row.representation_bits,
            "discovery_work": row.discovery_work,
            "verification_work": row.verification_work,
            "projected_bits": list(row.projected_bits),
        })
    payload = {
        "schema": "representation_discovery_hidden_xor_v1",
        "status": "EXACT_BOUNDED_EXPERIMENT",
        "model": {
            "representation": "one even-parity XOR equation on the shared variables",
            "encoding": "existential XOR chain in 3-CNF with one helper per prefix",
            "discovery": "exhaustive projection followed by all nonempty XOR supports and both RHS values",
            "verification": "independent exhaustive projection replay",
            "shared_range": [3, 7],
        },
        "source_sha256": {
            "engine.py": sha256(HERE / "engine.py"),
            "run_experiment.py": sha256(HERE / "run_experiment.py"),
        },
        "records": rows,
        "interpretation": (
            "The projected representation remains one XOR equation while the bounded "
            "projection-based discovery work grows with the hidden helper variables. "
            "This is evidence about the declared discovery model only, not a lower bound "
            "on SAT or on arbitrary representation algorithms."
        ),
    }
    (HERE / "RESULTS.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(rows), "status": payload["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
