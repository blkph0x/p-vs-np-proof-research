from itertools import combinations
import json
from hashlib import sha256
from pathlib import Path

from mixed_bridge_width import all_three_subsets, width_pair


HERE = Path(__file__).resolve().parent


def main():
    clauses = all_three_subsets(4)
    rows = []
    for mask in range(1 << len(clauses)):
        formula = tuple(clauses[i] for i in range(len(clauses)) if mask >> i & 1)
        original, transformed = width_pair(formula, 4)
        assert original <= transformed <= original + 2
        rows.append({"mask": mask, "clause_count": len(formula),
                     "original_pathwidth": original,
                     "transformed_pathwidth": transformed})
    names = ["mixed_bridge_width.py", "run_mixed_bridge_width.py",
             "MIXED_BRIDGE_WIDTH_THEOREM.md", "MIXED_BRIDGE_WIDTH_REVIEW.py",
             "test_mixed_bridge_width.py"]
    output = {"format": "two-bridge-primal-width-v1", "variables": 4,
              "formula_count": len(rows), "rows": rows,
              "all_bounds_hold": True,
              "source_sha256": {name: sha256((HERE / name).read_bytes()).hexdigest()
                                for name in names}}
    (HERE / "MIXED_BRIDGE_WIDTH_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "formula_count": len(rows),
                      "all_bounds_hold": True}))


if __name__ == "__main__":
    main()
