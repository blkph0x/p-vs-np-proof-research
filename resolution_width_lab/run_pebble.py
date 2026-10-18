"""Generate the finite pebble-game width bridge artifact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pebble import BooleanPebbleGame


HERE = Path(__file__).resolve().parent


def all_assignment_clauses(nvars):
    from itertools import product
    return tuple(tuple((v + 1) if not bit else -(v + 1)
                       for v, bit in enumerate(bits))
                 for bits in product((0, 1), repeat=nvars))


def pigeonhole(pigeons, holes):
    variable = lambda pigeon, hole: pigeon * holes + hole + 1
    clauses = [tuple(variable(pigeon, hole) for hole in range(holes))
               for pigeon in range(pigeons)]
    clauses += [(-variable(pigeon, left), -variable(pigeon, right))
                for pigeon in range(pigeons)
                for left in range(holes) for right in range(left + 1, holes)]
    clauses += [(-variable(left, hole), -variable(right, hole))
                for hole in range(holes)
                for left in range(pigeons) for right in range(left + 1, pigeons)]
    return pigeons * holes, tuple(clauses)


def source_hashes():
    names = ("pebble.py", "run_pebble.py", "review_pebble.py", "resolution.py", "THEOREM.md")
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in names}


def main():
    controls = [
        {"name": "unit_contradiction_pebbles_2", "nvars": 1,
         "clauses": ((1,), (-1,)), "pebbles": 2,
         "expected": "SPOILER_WINS"},
        {"name": "all_assignments_n3_pebbles_4", "nvars": 3,
         "clauses": all_assignment_clauses(3), "pebbles": 4,
         "expected": "SPOILER_WINS"},
        {"name": "pigeonhole_4_3_pebbles_4", "nvars": 12,
         "clauses": pigeonhole(4, 3)[1], "pebbles": 4,
         "expected": "SPOILER_WINS"},
        {"name": "pigeonhole_5_4_pebbles_4", "nvars": 20,
         "clauses": pigeonhole(5, 4)[1], "pebbles": 4,
         "expected": "DUPLICATOR_WINS"},
        {"name": "pigeonhole_5_4_pebbles_5", "nvars": 20,
         "clauses": pigeonhole(5, 4)[1], "pebbles": 5,
         "expected": "SPOILER_WINS"},
    ]
    rows = []
    for case in controls:
        result = BooleanPebbleGame(case["nvars"], case["clauses"],
                                   case["pebbles"]).solve()
        if result["status"] != case["expected"]:
            raise AssertionError((case["name"], result["status"], case["expected"]))
        rows.append({"name": case["name"], "nvars": case["nvars"],
                     "pebbles": case["pebbles"], "clause_count": len(case["clauses"]),
                     "expected": case["expected"], "result": result})

    php = next(row for row in rows if row["name"] == "pigeonhole_5_4_pebbles_5")
    php_lower = next(row for row in rows if row["name"] == "pigeonhole_5_4_pebbles_4")
    output = {
        "format": "boolean-pebble-width-bridge-v1",
        "theorem": "Atserias-Dalmau Theorem 2: width w iff Spoiler wins (w+1) pebbles",
        "rows": rows,
        "php_5_4_width_conclusion": {
            "formula": "PHP(5,4) standard encoding",
            "lower_bound": {
                "width": 4,
                "evidence": "DUPLICATOR_WINS on 4 pebbles rules out width 3 only when combined with the complete width-3 closure; the saved bit-mask closure is the direct lower-bound certificate.",
                "pebble_row": php_lower["name"],
            },
            "upper_bound": {
                "width": 4,
                "evidence": "SPOILER_WINS on 5 pebbles, which is equivalent to a width-4 resolution refutation by the cited theorem.",
                "pebble_row": php["name"],
            },
            "minimum_refutation_width": 4,
        },
        "source_sha256": source_hashes(),
    }
    (HERE / "PEBBLE_RESULTS.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "case_count": len(rows),
                      "php_5_4_status": php["result"]["status"],
                      "php_5_4_rounds": php["result"]["round_count"]}))


if __name__ == "__main__":
    main()
