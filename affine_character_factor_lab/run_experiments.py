"""Reproducible saved controls for the affine-character factor experiment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from engine import (paired_or_blocks, solve, solve_components, verify,
                    verify_components, direct_count)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_one(name, n, blocks, rows, rhs, expected=None, caps=None, direct=False):
    start = time.perf_counter()
    result = solve(n, blocks, rows, rhs, caps)
    elapsed = time.perf_counter() - start
    record = {"name": name, "n": n, "blocks": len(blocks), "equation_rows": len(rows),
              "status": result["status"], "elapsed_seconds": elapsed}
    if "reason" in result:
        record["reason"] = result["reason"]
    if result["status"] == "EXACT":
        checked = verify(n, blocks, rows, rhs, result, caps)
        record["verification"] = checked["status"]
        record["verification_valid"] = checked["valid"]
        record["value"] = result["value"]
        record["rank"] = result.get("rank")
        record["characters"] = result.get("stats", {}).get("characters")
        record["producer_work"] = result.get("stats", {}).get("work")
        record["verifier_work"] = checked.get("stats", {}).get("work")
        if expected is not None:
            record["expected"] = [expected, 1]
            record["expected_matches"] = result["value"] == [expected, 1]
        if direct:
            oracle = direct_count(n, blocks, rows, rhs)
            record["direct_count"] = oracle
            record["direct_matches"] = result["value"] == [oracle, 1]
    return record


def random_crosscheck():
    rng = random.Random(8128)
    cases = exact = direct_ok = certificate_ok = 0
    for n in range(11):
        for _ in range(20):
            blocks = [{"id": f"b{i}", "scope": [i], "factors":
                       [{"id": f"f{i}", "scope": [i],
                         "table": [rng.randint(-2, 2), rng.randint(-2, 2)]}]}
                      for i in range(n)]
            rows = [rng.randrange(1 << n) for _ in range(rng.randrange(0, min(5, n + 1)))]
            rhs = [rng.randrange(2) for _ in rows]
            result = solve(n, blocks, rows, rhs)
            cases += 1
            if result["status"] != "EXACT":
                continue
            exact += 1
            oracle = direct_count(n, blocks, rows, rhs)
            direct_ok += result["value"] == [oracle, 1]
            certificate_ok += verify(n, blocks, rows, rhs, result)["valid"]
    return {"seed": 8128, "cases": cases, "exact": exact,
            "direct_matches": direct_ok, "certificate_matches": certificate_ok}


def component_control(name, m, mode, expected, caps=None):
    n, blocks, equations, rhs = paired_or_blocks(m, mode)
    result = solve_components(n, blocks, equations, rhs, caps)
    row = {"name": name, "mode": mode, "m": m, "status": result["status"]}
    if result["status"] == "EXACT":
        checked = verify_components(n, blocks, equations, rhs, result, caps)
        row.update({"value": result["value"], "expected": [expected, 1],
                    "expected_matches": result["value"] == [expected, 1],
                    "verification": checked["status"],
                    "verification_valid": checked["valid"],
                    "component_count": result["component_count"],
                    "component_characters": result["stats"]["component_characters"]})
    else:
        row["reason"] = result.get("reason")
    return row


def main():
    rows = []
    for m in [1, 2, 4, 8, 16, 32, 64, 96, 128]:
        n, blocks, equations, rhs = paired_or_blocks(m, "global")
        expected = (3 ** m + (-1) ** m) // 2
        rows.append(run_one(f"global_even_or_{m}", n, blocks, equations, rhs,
                            expected=expected, direct=m <= 6))
    for m in [0, 1, 4, 16, 64, 128]:
        n, blocks, equations, rhs = paired_or_blocks(m, "none")
        rows.append(run_one(f"uncoupled_or_{m}", n, blocks, equations, rhs,
                            expected=3 ** m, direct=m <= 6))
    for m in [1, 2, 4, 8, 12, 14]:
        n, blocks, equations, rhs = paired_or_blocks(m, "local")
        rows.append(run_one(f"local_parities_rank_{m}", n, blocks, equations, rhs,
                            expected=1, direct=m <= 6))
    # This is an intentional UNKNOWN control: local parity rank is the
    # character parameter, and the capped run reaches the charged work limit.
    n, blocks, equations, rhs = paired_or_blocks(16, "local")
    rows.append(run_one("local_parities_rank_16_capped", n, blocks, equations, rhs,
                        expected=1, caps={"max_work": 100_000}))
    # Mutation control is saved as a verifier failure without changing the
    # producer's original result.
    n, blocks, equations, rhs = paired_or_blocks(4, "global")
    result = solve(n, blocks, equations, rhs)
    result["characters"][0]["term"] += 1
    bad = verify(n, blocks, equations, rhs, result)
    rows.append({"name": "mutated_certificate", "status": bad["status"],
                 "verification_valid": bad["valid"], "errors": bad["errors"]})
    component_rows = []
    for m in [1, 4, 16, 64, 128]:
        n, blocks, equations, rhs = paired_or_blocks(m, "local")
        component_rows.append(component_control(f"split_local_{m}", m, "local", 1))
    for m in [1, 8, 128]:
        expected = (3 ** m + (-1) ** m) // 2
        component_rows.append(component_control(f"split_global_{m}", m, "global", expected))
    for m in [1, 4, 8, 12]:
        component_rows.append(component_control(f"connected_rank_{m}", m, "connected", 1))
    component_rows.append(component_control("connected_rank_16_capped", 16, "connected", 1,
                                             {"max_work": 100_000}))
    payload = {
        "schema": "affine_character_factor_experiment_v1",
        "interpretation": "Exact factorized counting for disjoint local factors plus affine coupling; rank is an explicit parameter and no unrestricted SAT claim follows.",
        "records": rows,
        "component_controls": component_rows,
        "random_crosscheck": random_crosscheck(),
        "source_hashes": {name: sha(HERE / name) for name in ["engine.py", "test_engine.py", "run_experiments.py"]},
    }
    (HERE / "RESULTS.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "EXPERIMENTS_WRITTEN", "records": len(rows),
                      "exact": sum(r.get("status") == "EXACT" for r in rows),
                      "unknown": sum(r.get("status") == "UNKNOWN" for r in rows),
                      "invalid_controls": sum(r.get("status") == "INVALID" for r in rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
