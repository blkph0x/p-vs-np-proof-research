"""Independent finite replay of the fixed mixed Horn/affine reduction."""
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
H = {(0, 0, 0), (1, 1, 0), (0, 0, 1)}
A = {(0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 1), (1, 1, 1, 1)}


def valid(clauses, n):
    return any(all(sum(bits[v] for v in c) == 1 for c in clauses)
               for bits in product((0, 1), repeat=n))


def transformed(clauses, n):
    for bits in product((0, 1), repeat=n + 2 * len(clauses)):
        if all((bits[x], bits[n + 2 * i], bits[n + 2 * i + 1]) in H and
               (bits[y], bits[w], bits[n + 2 * i], bits[n + 2 * i + 1]) in A
               for i, (x, y, w) in enumerate(clauses)):
            return True
    return False


def main():
    clauses = tuple(combinations(range(4), 3))
    rows = []
    for mask in range(1 << len(clauses)):
        formula = tuple(clauses[i] for i in range(len(clauses)) if mask >> i & 1)
        before, after = valid(formula, 4), transformed(formula, 4)
        assert before == after
        rows.append({"mask": mask, "original_sat": before, "transformed_sat": after})
    source_names = ["two_bridge_factorization.py", "mixed_horn_affine_reduction.py",
                    "MIXED_REDUCTION_REVIEW.py", "test_mixed_horn_affine_reduction.py"]
    result = {"status": "PASS", "formula_count": len(rows),
              "all_answers_match": True,
              "source_sha256": {name: sha256((HERE / name).read_bytes()).hexdigest()
                                for name in source_names}}
    (HERE / "MIXED_REDUCTION_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
