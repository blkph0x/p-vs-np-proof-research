"""Replay the charged-work lower bound for coordinate conditioning."""
from hashlib import sha256
import json
from pathlib import Path

from deletion_solver import conditioned_width_profile


HERE = Path(__file__).resolve().parent


def baseline_width(generator, n, order):
    return conditioned_width_profile(generator, n, deleted=(), order=order)["width"]


def replay():
    artifact = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    records = []
    for sample in artifact["samples"]:
        n = sample["n"]
        generator = tuple(sample["generator_rows"])
        cases = {case["name"]: case for case in sample["cases"] if case.get("solve")}
        for name, case in cases.items():
            solve = case["solve"]
            order = tuple(solve["remaining_order"])
            if name.startswith("greedy_fix"):
                order = tuple(cases["greedy"]["solve"]["remaining_order"])
            original_width = baseline_width(generator, n, order)
            charged = solve["transitions"] + solve["branch_assignments_total"]
            bound = 1 << original_width
            if solve["status"] == "EXACT" and charged < bound:
                raise AssertionError((sample["n"], name, charged, bound))
            records.append({"n": n, "case": name, "original_width": original_width,
                            "charged_operations": charged,
                            "lower_bound": bound,
                            "bound_holds": charged >= bound,
                            "status": solve["status"]})
    return records


def main():
    records = replay()
    sources = {}
    for path in (HERE / "results.json", HERE / "deletion_solver.py",
                 HERE / "THEOREMS.md", HERE / "charged_work_review.py"):
        sources[path.name] = sha256(path.read_bytes()).hexdigest()
    output = {
        "format": "coordinate-conditioning-charged-work-v1",
        "records": records,
        "exact_records": sum(row["status"] == "EXACT" for row in records),
        "all_exact_bounds_hold": all(row["bound_holds"] for row in records if row["status"] == "EXACT"),
        "source_sha256": sources,
        "scope": "Fixed supplied order and coordinate conditioning only; branch enumeration and transitions are both charged.",
    }
    (HERE / "CHARGED_WORK_REVIEW.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": len(records),
                      "exact_records": output["exact_records"],
                      "all_exact_bounds_hold": output["all_exact_bounds_hold"]}))


if __name__ == "__main__":
    main()
