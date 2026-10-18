"""Independent replay and arithmetic review of saved character controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine import (paired_or_blocks, solve, solve_components, verify,
                    verify_components, direct_count)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_for(name):
    m = int(re.search(r"_(\d+)(?:_capped)?$", name).group(1))
    if name.startswith("global_even_or_"):
        return (3 ** m + (-1) ** m) // 2, "global"
    if name.startswith("uncoupled_or_"):
        return 3 ** m, "none"
    if name.startswith("local_parities_rank_"):
        return 1, "local"
    raise AssertionError(name)


def random_replay():
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
            assert result["status"] == "EXACT"
            exact += 1
            oracle = direct_count(n, blocks, rows, rhs)
            direct_ok += result["value"] == [oracle, 1]
            certificate_ok += verify(n, blocks, rows, rhs, result)["valid"]
    return {"seed": 8128, "cases": cases, "exact": exact,
            "direct_matches": direct_ok, "certificate_matches": certificate_ok}


def component_replay():
    checks = []
    for m in [1, 4, 16, 64, 128]:
        n, blocks, rows, rhs = paired_or_blocks(m, "local")
        result = solve_components(n, blocks, rows, rhs)
        assert result["status"] == "EXACT" and result["value"] == [1, 1]
        assert result["component_count"] == m
        assert verify_components(n, blocks, rows, rhs, result)["valid"]
        checks.append(("local", m, result["stats"]["component_characters"]))
    for m in [1, 8, 128]:
        n, blocks, rows, rhs = paired_or_blocks(m, "global")
        expected = (3 ** m + (-1) ** m) // 2
        result = solve_components(n, blocks, rows, rhs)
        assert result["status"] == "EXACT" and result["value"] == [expected, 1]
        assert result["component_count"] == 1
        assert verify_components(n, blocks, rows, rhs, result)["valid"]
        checks.append(("global", m, result["stats"]["component_characters"]))
    for m in [1, 4, 8, 12]:
        n, blocks, rows, rhs = paired_or_blocks(m, "connected")
        result = solve_components(n, blocks, rows, rhs)
        assert result["status"] == "EXACT" and result["value"] == [1, 1]
        assert result["component_count"] == 1
        assert result["stats"]["component_characters"] == [1 << m]
        assert verify_components(n, blocks, rows, rhs, result)["valid"]
        checks.append(("connected", m, result["stats"]["component_characters"]))
    n, blocks, rows, rhs = paired_or_blocks(16, "connected")
    capped = solve_components(n, blocks, rows, rhs, {"max_work": 100_000})
    assert capped["status"] == "UNKNOWN" and "value" not in capped
    return checks


def main():
    data = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    records = data["records"]
    assert len(records) == 23
    exact = [r for r in records if r.get("status") == "EXACT"]
    unknown = [r for r in records if r.get("status") == "UNKNOWN"]
    invalid = [r for r in records if r.get("status") == "INVALID"]
    assert len(exact) == 21 and len(unknown) == 1 and len(invalid) == 1
    random_result = random_replay()
    assert data["random_crosscheck"] == random_result
    assert random_result == {"seed": 8128, "cases": 220, "exact": 220,
                             "direct_matches": 220, "certificate_matches": 220}
    component_result = component_replay()
    saved_components = data["component_controls"]
    assert len(saved_components) == 13
    assert sum(row["status"] == "EXACT" for row in saved_components) == 12
    assert sum(row["status"] == "UNKNOWN" for row in saved_components) == 1
    assert saved_components[-1]["name"] == "connected_rank_16_capped"
    replayed = 0
    for row in exact:
        if row["name"] == "mutated_certificate":
            continue
        expected, mode = expected_for(row["name"])
        m = int(re.search(r"_(\d+)(?:_capped)?$", row["name"]).group(1))
        n, blocks, equations, rhs = paired_or_blocks(m, mode)
        result = solve(n, blocks, equations, rhs)
        assert result["status"] == "EXACT"
        assert result["value"] == [expected, 1]
        checked = verify(n, blocks, equations, rhs, result)
        assert checked["valid"] and checked["status"] == "VERIFIED"
        if m <= 6:
            assert direct_count(n, blocks, equations, rhs) == expected
        assert row.get("expected_matches") is True
        assert row.get("verification_valid") is True
        replayed += 1
    capped = unknown[0]
    assert capped["name"] == "local_parities_rank_16_capped"
    assert capped.get("reason") == "work cap"
    assert "value" not in capped
    assert invalid[0]["name"] == "mutated_certificate"
    assert invalid[0]["verification_valid"] is False
    for name, recorded in data["source_hashes"].items():
        assert recorded == sha(HERE / name), name
    review = {
        "status": "VERIFIED_INDEPENDENT_CHARACTER_REVIEW",
        "records": len(records), "exact": len(exact), "unknown": len(unknown),
        "invalid_controls": len(invalid), "exact_replayed": replayed,
        "global_rank_128_value": next(r["value"] for r in exact if r["name"] == "global_even_or_128"),
        "local_rank_14_characters": next(r["characters"] for r in exact if r["name"] == "local_parities_rank_14"),
        "source_hashes_match": True,
        "random_crosscheck": random_result,
        "component_controls": len(saved_components),
        "component_replay": component_result,
    }
    (HERE / "INDEPENDENT_REVIEW.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (HERE / "INDEPENDENT_REVIEW.md").write_text(
        "# Independent review\n\n"
        "The saved character-factor experiment was replayed from its original "
        "family constructors. All 21 exact rows were independently recomputed "
        "and verified; small rows also matched direct assignment enumeration. "
        "The rank-16 control remained UNKNOWN at its explicit work cap and had "
        "no value. The deliberately mutated certificate was rejected. Source "
        "hashes matched the saved provenance. A deterministic 220-case random "
        "cross-check also matched a separate direct enumerator and the checker "
        "in every exact case. The component replay split independent local "
        "parities into rank-one pieces and retained the connected rank barrier.\n\n"
        "This review confirms the restricted identity and certificate plumbing; "
        "it makes no claim about unrestricted SAT or P versus NP.\n",
        encoding="utf-8")
    print(json.dumps(review, sort_keys=True))


if __name__ == "__main__":
    main()
