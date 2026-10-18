"""Independent replay of the full-transform cost artifact."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent


def independent_fwht(values):
    out = list(values)
    length = len(out)
    width = 1
    additions = subtractions = 0
    while width < length:
        for start in range(0, length, 2 * width):
            for offset in range(width):
                left = out[start + offset]
                right = out[start + offset + width]
                out[start + offset] = left + right
                out[start + offset + width] = left - right
                additions += 1
                subtractions += 1
        width *= 2
    return out, additions, subtractions


def independent_zeta(values):
    out = list(values)
    dimension = (len(out)).bit_length() - 1
    additions = 0
    for bit in range(dimension):
        for subset in range(len(out)):
            if subset & (1 << bit):
                out[subset] = out[subset] + out[subset ^ (1 << bit)]
                additions += 1
    return out, additions


def expected(dimension):
    length = 1 << dimension
    butterflies = dimension * length // 2
    return {
        "dimension": dimension,
        "state_count": length,
        "fwht_butterflies": butterflies,
        "fwht_additions": butterflies,
        "fwht_subtractions": butterflies,
        "fwht_arithmetic_operations": 2 * butterflies,
        "zeta_additions": butterflies,
        "combined_add_sub_operations": 3 * butterflies,
    }


def review():
    artifact_path = HERE / "FWHT_COST_RESULTS.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    rows = artifact["rows"]
    assert rows == [expected(dimension) for dimension in range(0, 21)]
    for dimension in range(0, 9):
        values = [((index * 7 + 3) % 19) - 9 for index in range(1 << dimension)]
        transformed, additions, subtractions = independent_fwht(values)
        assert additions == subtractions == expected(dimension)["fwht_butterflies"]
        assert len(transformed) == 1 << dimension
        zeta_input = list(range(1 << dimension))
        zeta, zeta_ops = independent_zeta(zeta_input)
        assert zeta_ops == expected(dimension)["zeta_additions"]
        direct_zeta = [sum(zeta_input[sub] for sub in range(1 << dimension)
                            if sub & ~subset == 0)
                       for subset in range(1 << dimension)]
        assert zeta == direct_zeta
    expected_sources = {"fwht_cost.py", "review_fwht_cost.py",
                        "run_fwht_cost.py", "FWHT_COST_REPORT.md",
                        "../test_fwht_cost_audit.py"}
    assert set(artifact["source_hashes"]) == expected_sources
    for name, digest in artifact["source_hashes"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    return {"status": "PASS", "rows": len(rows),
            "source_hashes_match": True, "sample_transforms_replayed": 9}


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, sort_keys=True))
