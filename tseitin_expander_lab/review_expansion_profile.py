"""Independently replay the finite Tseitin expansion profile artifact."""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from math import comb, gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def expected_controls():
    cube = [(i, i ^ (1 << bit)) for i in range(8) for bit in range(3)
            if i < (i ^ (1 << bit))]
    petersen = ([(i, (i + 1) % 5) for i in range(5)] +
                [(5 + i, 5 + ((i + 2) % 5)) for i in range(5)] +
                [(i, 5 + i) for i in range(5)])
    fano_lines = [(0, 1, 3), (1, 2, 4), (2, 3, 5), (3, 4, 6),
                  (4, 5, 0), (5, 6, 1), (6, 0, 2)]
    heawood = [(point, 7 + line) for line, triple in enumerate(fano_lines)
               for point in triple]
    cyclic_bipartite = [(left, 8 + (left + shift) % 8)
                        for left in range(8) for shift in (0, 1, 3)]
    controls = [
        {"name": "cube_3_regular", "n": 8, "edges": cube},
        {"name": "petersen_3_regular", "n": 10, "edges": petersen},
        {"name": "heawood_3_regular", "n": 14, "edges": heawood},
        {"name": "cyclic_bipartite_16", "n": 16, "edges": cyclic_bipartite},
    ]
    for n in range(6, 22, 2):
        cycle = [(vertex, (vertex + 1) % n) for vertex in range(n)]
        opposite = [(vertex, vertex + n // 2) for vertex in range(n // 2)]
        edges = tuple(sorted({tuple(sorted(edge)) for edge in cycle + opposite}))
        controls.append({"name": f"mobius_ladder_{n}", "n": n,
                         "edges": edges, "family": "mobius_ladder"})
    return tuple(controls)


def normalize(n, edges):
    checked = set()
    for raw in edges:
        assert isinstance(raw, (tuple, list)) and len(raw) == 2
        u, v = (int(raw[0]), int(raw[1]))
        assert 0 <= u < n and 0 <= v < n and u != v
        if u > v:
            u, v = v, u
        assert (u, v) not in checked
        checked.add((u, v))
    normalized = tuple(sorted(checked))
    assert all(sum(vertex in edge for edge in normalized) == 3 for vertex in range(n))
    return normalized


def exact_profile(n, edges):
    edges = normalize(n, edges)
    adjacency = [0] * n
    for u, v in edges:
        adjacency[u] |= 1 << v
        adjacency[v] |= 1 << u
    minimum_by_size = []
    global_count = global_size = None
    global_vertices = None
    subsets_checked = 0
    for size in range(1, n // 2 + 1):
        best_count = None
        best_vertices = None
        for chosen in combinations(range(n), size):
            subset = sum(1 << vertex for vertex in chosen)
            neighborhood = 0
            remaining = subset
            while remaining:
                bit = remaining & -remaining
                neighborhood |= adjacency[bit.bit_length() - 1]
                remaining ^= bit
            count = neighborhood.bit_count()
            subsets_checked += 1
            if best_count is None or count < best_count:
                best_count = count
                best_vertices = list(chosen)
            if global_count is None or count * global_size < global_count * size:
                global_count = count
                global_size = size
                global_vertices = list(chosen)
        divisor = gcd(best_count, size)
        minimum_by_size.append({
            "size": size,
            "neighborhood_size": best_count,
            "epsilon_numerator": best_count // divisor,
            "epsilon_denominator": size // divisor,
            "witness": {"vertices": best_vertices,
                        "neighborhood_size": best_count},
        })
    divisor = gcd(global_count, global_size)
    return {
        "half_size": n // 2,
        "epsilon_numerator": global_count // divisor,
        "epsilon_denominator": global_size // divisor,
        "witness": {"vertices": global_vertices,
                    "neighborhood_size": global_count},
        "minimum_by_size": minimum_by_size,
        "subsets_checked": subsets_checked,
        "maximum_degree": max(map(int.bit_count, adjacency)),
    }


def main():
    artifact = json.loads((HERE / "EXPANSION_RESULTS.json").read_text(encoding="utf-8"))
    assert artifact["all_profiles_exact"]
    controls = expected_controls()
    assert len(artifact["rows"]) == len(controls) == 12
    for saved, expected in zip(artifact["rows"], controls):
        assert saved["name"] == expected["name"]
        assert saved["vertices"] == expected["n"]
        assert normalize(expected["n"], saved["edges"]) == normalize(expected["n"], expected["edges"])
        assert saved["family"] == expected.get("family", "named_control")
        recomputed = exact_profile(saved["vertices"], saved["edges"])
        assert saved["profile"] == recomputed
        assert saved["profile"]["maximum_degree"] == 3
        expected_count = sum(comb(saved["vertices"], size)
                             for size in range(1, saved["vertices"] // 2 + 1))
        assert saved["profile"]["subsets_checked"] == expected_count
    for name, digest in artifact["source_sha256"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest
    output = {"status": "PASS", "case_count": len(controls),
              "profiles_match": True, "source_hashes_match": True}
    (HERE / "EXPANSION_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output))


if __name__ == "__main__":
    main()
