"""Retained small original-input campaign for certified affine-hull recovery."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from affine_hull import recover

HERE = Path(__file__).resolve().parent


def xor_clauses(a, b, c):
    return [[-v if word & (1 << j) else v for j, v in enumerate((a, b, c))]
            for word in (1, 2, 4, 7)]


def chain(m, rhs=0):
    clauses = []
    previous = 1
    for i in range(1, m):
        helper = m + i
        clauses.extend(xor_clauses(previous, i + 1, helper))
        previous = helper
    clauses.append([previous if rhs else -previous])
    return clauses


def cases():
    result = [
        ("zero_width", 0, 0, [], {}),
        ("empty_zero_width", 0, 0, [[]], {}),
        ("nonaffine_hole", 2, 0, [[-1, -2]], {}),
        ("affine_guard_sat", 1, 1, [[-1, 2]], {}),
        ("affine_guard_unsat", 1, 1, [[-1, 2], [-1, -2]], {}),
        ("nonconstant_hidden_counts", 1, 1, [[1, 2]], {}),
        ("nonzero_offset", 3, 1, [[1], [-2, 3], [2, -3]], {}),
        ("decision_cap", 8, 0, [], {"max_decisions": 0}),
        ("call_cap", 4, 0, [], {"max_calls": 1}),
        ("odd_parity", 3, 2, chain(3, 1), {}),
    ]
    result += [("even_parity_" + str(m), m, m - 1, chain(m), {}) for m in (3, 4, 6, 8)]
    return result


def source_hashes():
    paths = [HERE / name for name in (
        "affine_hull.py", "review_affine_hull.py", "run_affine_hull.py",
        "test_hull_engine.py", "test_hull_certificate.py", "AFFINE_HULL_METHOD.md")]
    paths.append(HERE.parent / "proof_producing_cdcl_lab" / "cdcl.py")
    return {p.relative_to(HERE.parent).as_posix(): hashlib.sha256(
        p.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    ).hexdigest() for p in paths}


def build():
    before = source_hashes()
    rows = [{"name": name, "source": {"visible_width": m, "hidden_width": q, "clauses": clauses},
             "caps": caps, "certificate": recover(m, q, clauses, **caps)}
            for name, m, q, clauses, caps in cases()]
    if source_hashes() != before:
        raise RuntimeError("sources changed during campaign")
    return {"schema": "certified-affine-hull-v1", "hash_scheme": "sha256-utf8-lf-v1",
            "source_sha256": before, "cases": rows,
            "scope": "Exact affine hull only; projection affinity is not checked."}


if __name__ == "__main__":
    result = build()
    (HERE / "HULL_RESULTS.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                           encoding="utf-8")
    for row in result["cases"]:
        cert = row["certificate"]
        print(json.dumps({"name": row["name"], "status": cert["status"],
                          "dimension": cert["dimension"], "calls": len(cert["queries"]),
                          "solver_totals": cert["solver_totals"]}, sort_keys=True))
