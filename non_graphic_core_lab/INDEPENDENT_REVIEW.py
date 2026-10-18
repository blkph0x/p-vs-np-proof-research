"""Independent Python replay of the saved non-graphic controls."""
from hashlib import sha256
import itertools
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def rank_mask(mask, columns):
    basis = {}
    while mask:
        bit = mask & -mask
        index = bit.bit_length() - 1
        mask ^= bit
        value = columns[index]
        while value:
            top = value.bit_length() - 1
            if top in basis:
                value ^= basis[top]
            else:
                basis[top] = value
                break
    return len(basis)


def rank_values(values):
    basis = {}
    for value in values:
        value = int(value)
        while value:
            top = value.bit_length() - 1
            if top in basis:
                value ^= basis[top]
            else:
                basis[top] = value
                break
    return len(basis)


def fano_certificate(columns):
    first = tuple(columns[:7])
    return (len(first) == 7 and len(set(first)) == 7 and all(first)
            and rank_values(first) == 3 and set(first) == set(range(1, 8)))


def replay_connectivity(columns, expected, exhaustive):
    n = len(columns)
    rank = rank_values(columns)
    assert rank == expected["k"]
    full = (1 << n) - 1
    central_min = n
    checked = 0
    violations = 0
    if exhaustive:
        sizes = range(1, n // 2 + 1)
    else:
        sizes = (n // 2,)
    for size in sizes:
        subset = (1 << size) - 1
        while subset <= full:
            balanced = size == n // 2
            if not balanced or subset & 1:
                complement = full ^ subset
                lam = rank_mask(subset, columns) + rank_mask(complement, columns) - rank
                checked += 1
                if balanced:
                    central_min = min(central_min, lam)
                if exhaustive:
                    a, b = subset.bit_count(), n - subset.bit_count()
                    if a >= 2 and b >= 2 and lam <= 1:
                        violations += 1
                    if a >= 3 and b >= 3 and lam == 2:
                        if a == 3:
                            triangle = rank_mask(subset, columns) == 2
                            triad = 3 - rank + rank_mask(complement, columns) == 2
                            if not triangle and not triad:
                                violations += 1
                        else:
                            violations += 1
            lowest = subset & -subset
            next_subset = subset + lowest
            next_subset = (((next_subset ^ subset) >> 2) // lowest) | next_subset
            if next_subset <= subset or next_subset > full:
                break
            subset = next_subset
    assert checked == expected["checked_unordered_cuts"] if exhaustive else checked == expected["central_checked"]
    assert central_min == expected["central_min_lambda"]
    assert violations == 0


def main():
    artifact = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    assert artifact["format"] == "non-graphic-internal4-core-v1"
    controls = artifact["controls"]
    assert len(controls) == 5
    for index, control in enumerate(controls):
        columns = tuple(control["columns"])
        assert fano_certificate(columns)
        assert control["non_graphic_certificate"] == "F7 restriction"
        audit = control["audit"]
        assert audit["three_conn_violations"] == 0
        assert audit["internal4_violations"] == 0
        assert audit["checked_unordered_cuts"] == (1 << (len(columns) - 1)) - 1
        replay_connectivity(columns, audit, exhaustive=index < 2)
        expected_distance = min(
            sum((message & column).bit_count() & 1 for column in columns)
            for message in range(1, 1 << control["rank"])
        )
        assert expected_distance == control["minimum_code_distance"]
    for name, expected in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == expected
    output = {"status": "PASS", "controls": len(controls),
              "fano_certificates": len(controls), "source_hashes_match": True}
    (HERE / "INDEPENDENT_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
