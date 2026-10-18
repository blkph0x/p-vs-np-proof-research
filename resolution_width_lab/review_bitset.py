"""Independent tuple-based replay of the bit-mask stress artifact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from review_indexed import all_assignment_clauses, closure, pigeonhole


HERE = Path(__file__).resolve().parent


def digest(path):
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()


def clause_digest(clauses):
    return hashlib.sha256(
        json.dumps(sorted(clauses), separators=(",", ":")).encode()
    ).hexdigest()


def exact_case(name):
    if name.startswith("all_assignments_n"):
        nvars = int(name.rsplit("n", 1)[1])
        return nvars, all_assignment_clauses(nvars)
    if name.startswith("pigeonhole_"):
        pigeons, holes = (int(value) for value in name.removeprefix("pigeonhole_").split("_"))
        return pigeonhole(pigeons, holes)
    raise AssertionError(name)


def main():
    artifact = json.loads((HERE / "BITSET_RESULTS.json").read_text(encoding="utf-8"))
    for relative, expected in artifact["source_sha256"].items():
        assert digest(HERE / relative.split("/", 1)[1]) == expected, relative

    exact_rows = [row for row in artifact["rows"] if row["family"] != "pigeonhole_stress"]
    for row in exact_rows:
        nvars, clauses = exact_case(row["name"])
        status, reason, known, _ = closure(
            nvars, clauses, row["width"], (),
            artifact["caps"]["max_clauses"], artifact["caps"]["max_steps"],
        )
        assert row["reference_match"]
        assert row["status"] == status and row["reason"] == reason
        assert row["closure_size"] == len(known)
        assert row["clause_digest"] == clause_digest(known)

    nvars, clauses = pigeonhole(5, 4)
    stress = [row for row in artifact["rows"] if row["family"] == "pigeonhole_stress"]
    width3 = next(row for row in stress if row["width"] == 3)
    status, reason, known, _ = closure(
        nvars, clauses, 3, (),
        artifact["caps"]["max_clauses"], artifact["caps"]["max_steps"],
    )
    assert status == width3["status"] == "UNKNOWN"
    assert reason == width3["reason"] == "NO_WIDTH_W_REFUTATION"
    assert len(known) == width3["closure_size"]
    assert clause_digest(known) == width3["clause_digest"]

    width4 = next(row for row in stress if row["width"] == 4)
    status, reason, _, stats = closure(
        nvars, clauses, 4, tuple(sorted(known)),
        artifact["caps"]["max_clauses"], 100_000,
    )
    assert status == "UNKNOWN" and reason == "STEP_CAP"
    assert stats["candidate_steps"] > 100_000
    assert width4["status"] == "UNKNOWN" and width4["reason"] == "STEP_CAP"
    output = {"status": "PASS", "exact_rows_replayed": len(exact_rows),
              "stress_width3_match": True, "stress_cap_control": True,
              "source_hashes_match": True}
    (HERE / "BITSET_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
