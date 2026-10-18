"""Independent replay of the two-bridge primal-width controls."""
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def clique(adj, vs):
    for i, u in enumerate(vs):
        for v in vs[i + 1:]:
            adj[u] |= 1 << v
            adj[v] |= 1 << u


def graph(clauses, n, transformed):
    total = n + (2 * len(clauses) if transformed else 0)
    adj = [0] * total
    for i, (x, y, w) in enumerate(clauses):
        if transformed:
            z0, z1 = n + 2 * i, n + 2 * i + 1
            clique(adj, (x, z0, z1))
            clique(adj, (y, w, z0, z1))
        else:
            clique(adj, (x, y, w))
    return tuple(adj)


def pw(adj):
    n = len(adj)
    dp = [n + 1] * (1 << n)
    dp[0] = 0
    for subset in range(1, 1 << n):
        boundary = sum(bool(subset >> v & 1 and adj[v] & ~subset)
                        for v in range(n))
        rest, best = subset, n + 1
        while rest:
            bit = rest & -rest
            best = min(best, max(dp[subset ^ bit], boundary))
            rest ^= bit
        dp[subset] = best
    return dp[-1]


def main():
    clauses = tuple(combinations(range(4), 3))
    rows = []
    for mask in range(1 << len(clauses)):
        formula = tuple(clauses[i] for i in range(len(clauses)) if mask >> i & 1)
        before, after = pw(graph(formula, 4, False)), pw(graph(formula, 4, True))
        assert before <= after <= before + 2
        rows.append({"mask": mask, "original_pathwidth": before,
                     "transformed_pathwidth": after})
    artifact = json.loads((HERE / "MIXED_BRIDGE_WIDTH_RESULTS.json").read_text(encoding="utf-8"))
    assert artifact["rows"] == [{"mask": row["mask"], "clause_count": len(tuple(clauses[i] for i in range(len(clauses)) if row["mask"] >> i & 1)),
                                  "original_pathwidth": row["original_pathwidth"],
                                  "transformed_pathwidth": row["transformed_pathwidth"]} for row in rows]
    names = ["mixed_bridge_width.py", "run_mixed_bridge_width.py",
             "MIXED_BRIDGE_WIDTH_THEOREM.md", "MIXED_BRIDGE_WIDTH_REVIEW.py",
             "test_mixed_bridge_width.py"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    result = {"status": "PASS", "formula_count": len(rows),
              "all_bounds_hold": True, "source_hashes_match": True}
    (HERE / "MIXED_BRIDGE_WIDTH_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
