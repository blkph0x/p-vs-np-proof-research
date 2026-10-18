"""Build and exhaustively audit small non-graphic internally-4-connected codes."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent


def rank_values(values):
    basis = {}
    for value in values:
        x = int(value)
        while x:
            top = x.bit_length() - 1
            if top in basis:
                x ^= basis[top]
            else:
                basis[top] = x
                break
    return len(basis)


def generate_columns(n, k, seed):
    if n < 8 or k < 3 or k >= n:
        raise ValueError("invalid dimensions")
    rng = random.Random(seed)
    columns = list(range(1, 8))  # Fano restriction in the first three rows.
    while len(columns) < n:
        value = rng.randrange(1, 1 << k)
        if value not in columns:
            columns.append(value)
    if rank_values(columns) != k:
        return None
    return tuple(columns)


def fano_restriction(columns):
    first = tuple(columns[:7])
    return (len(set(first)) == 7 and all(first) and rank_values(first) == 3
            and set(first) == set(range(1, 8)))


def distance(columns, k):
    best = len(columns) + 1
    for message in range(1, 1 << k):
        weight = sum((message & column).bit_count() & 1 for column in columns)
        best = min(best, weight)
    return best


def audit(binary, columns, k):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", dir=HERE,
                                    delete=False, encoding="ascii") as handle:
        path = Path(handle.name)
        handle.write(f"{len(columns)} {k}\n")
        handle.write(" ".join(map(str, columns)) + "\n")
    try:
        output = subprocess.check_output([str(binary), str(path)], text=True)
    finally:
        path.unlink(missing_ok=True)
    return json.loads(output)


def find_control(binary, n, k, seed_start):
    for seed in range(seed_start, seed_start + 2000):
        columns = generate_columns(n, k, seed)
        if columns is None:
            continue
        result = audit(binary, columns, k)
        if result["three_conn_violations"] == 0 and result["internal4_violations"] == 0:
            return seed, columns, result
    raise RuntimeError(f"no internally-4-connected control found for n={n}")


def main():
    binary = HERE / "matroid_audit.exe"
    subprocess.run(["g++", "-O3", "-std=c++17", str(HERE / "matroid_audit.cpp"),
                    "-o", str(binary)], check=True)
    records = []
    for n, k, seed_start in ((18, 9, 20261018), (20, 10, 20262018),
                             (22, 11, 20263018), (24, 12, 20264018),
                             (26, 13, 20265018)):
        seed, columns, result = find_control(binary, n, k, seed_start)
        if not fano_restriction(columns):
            raise AssertionError("Fano restriction construction failed")
        d = distance(columns, k)
        records.append({
            "n": n,
            "rank": k,
            "seed": seed,
            "columns": list(columns),
            "fano_restriction": True,
            "minimum_code_distance": d,
            "non_graphic_certificate": "F7 restriction",
            "audit": result,
            "trellis_state_lower_bound": 1 << result["central_min_lambda"],
        })
        print(json.dumps({"n": n, "seed": seed,
                          "central_min_lambda": result["central_min_lambda"],
                          "distance": d}, sort_keys=True), flush=True)
    sources = {}
    for path in (HERE / "matroid_audit.cpp", HERE / "run_experiments.py",
                 HERE / "test_non_graphic_core.py", HERE / "THEOREM.md",
                 HERE / "INDEPENDENT_REVIEW.py", HERE / "REPORT.md"):
        sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    output = {
        "format": "non-graphic-internal4-core-v1",
        "controls": records,
        "source_sha256": sources,
        "scope": "Finite exhaustive connectivity audits with an explicit F7 restriction; no general minimum-distance hardness claim.",
    }
    (HERE / "RESULTS.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"format": output["format"], "controls": len(records)}))


if __name__ == "__main__":
    main()
