"""Independent replay of exact order discovery and saved orders."""
from hashlib import sha256
import json
from itertools import combinations
from pathlib import Path


HERE = Path(__file__).resolve().parent


def boundary(adj, subset):
    return sum(bool(subset >> v & 1 and adj[v] & ~subset)
               for v in range(len(adj)))


def discover(adj):
    n = len(adj)
    if not n:
        return {"width": 0, "order": [], "subsets": 1, "transitions": 0}
    dp = [n + 1] * (1 << n)
    choice = [-1] * (1 << n)
    dp[0] = 0
    values = [boundary(adj, s) for s in range(1 << n)]
    transitions = 0
    for s in range(1, 1 << n):
        rest, best, pick = s, n + 1, -1
        while rest:
            bit = rest & -rest
            prev = s ^ bit
            value = max(dp[prev], values[s])
            transitions += 1
            if value < best:
                best, pick = value, bit.bit_length() - 1
            rest ^= bit
        dp[s], choice[s] = best, pick
    s, reverse = (1 << n) - 1, []
    while s:
        v = choice[s]
        reverse.append(v)
        s ^= 1 << v
    return {"width": dp[-1], "order": list(reversed(reverse)),
            "subsets": 1 << n, "transitions": transitions}


def main():
    artifact = json.loads((HERE / "MIXED_ORDER_DISCOVERY_RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "MIXED_ORDER_DISCOVERY_CERTIFICATES.json").read_text(encoding="utf-8"))
    triples = tuple(combinations(range(4), 3))
    rows = []
    for mask in range(16):
        clauses = tuple(triples[i] for i in range(4) if mask >> i & 1)
        n = 4 + 2 * len(clauses)
        adj = [0] * n
        for i, (x, y, w) in enumerate(clauses):
            z0, z1 = 4 + 2 * i, 4 + 2 * i + 1
            for scope in ((x, z0, z1), (y, w, z0, z1)):
                for a, u in enumerate(scope):
                    for v in scope[a + 1:]:
                        adj[u] |= 1 << v
                        adj[v] |= 1 << u
        result = discover(tuple(adj))
        cert = certificates[mask]
        assert cert == {"mask": mask, "adjacency": list(adj),
                        "order": result["order"], "width": result["width"]}
        assert artifact["rows"][mask]["order"] == result["order"]
        assert artifact["rows"][mask]["width"] == result["width"]
        rows.append(result)
    assert artifact["all_orders_optimal"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    result = {"status": "PASS", "formula_count": len(rows),
              "orders_match": True, "source_hashes_match": True}
    (HERE / "MIXED_ORDER_DISCOVERY_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
