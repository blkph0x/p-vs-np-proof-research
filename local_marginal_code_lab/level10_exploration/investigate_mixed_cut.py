"""Exploratory exact selected-model optimization; not a full-L10 upper proof.

Every original base row is rebuilt by the frozen independent reviewer. Mixed
rows are counted from the original eight-point atom families. The new cut is
the previously proved pointwise ten-coordinate inequality q-8r+28v>=0.
No saved optimum, basis, or approximate solution is supplied to SoPlex.
"""
from collections import Counter
from fractions import Fraction
from functools import reduce
from math import gcd, lcm
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
import review_rm2_nine_scope as geometry
from exact_lp_model import to_lp
from exact_lp_soplex import candidate_from_output
from exact_lp_verify import verify_solution, model_digest

SOURCES = (
    Path(__file__).resolve(),
    LAB / "review_rm2_nine_scope.py",
    LAB / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py",
    LAB / "reed_muller_affine_overlap.py",
    LAB / "exact_lp_model.py",
    LAB / "exact_lp_soplex.py",
    LAB / "exact_lp_verify.py",
    LAB / "RM2_LEVEL10_CONTROL.md",
    LAB / "REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md",
)


def hashes():
    return {path.relative_to(LAB).as_posix():
            hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for path in SOURCES}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def make_model(cut=True):
    allowed, var_for, base_rows, base_rhs, _ = geometry._base()
    flat, outside = tuple(range(16, 24)), 24
    groups = {}
    for atom in allowed[flat]:
        groups.setdefault(var_for[(flat, atom)], []).append(atom)
    orbits = sorted(groups)
    if orbits != list(range(5, 11)):
        raise ValueError("changed source orbit order")
    rows, rhs = [dict(row) for row in base_rows], list(base_rhs)
    metadata = []
    for i, orbit in enumerate(orbits):
        rows.append({28 + i: 1, 34 + i: 1, orbit: -1})
        rhs.append(0)
    for subset in ((), (16,), (16, 17), (16, 17, 18), (16, 17, 18, 19)):
        selected = sum(1 << flat.index(point) for point in subset)
        row = Counter()
        incidence = []
        for i, orbit in enumerate(orbits):
            count = sum(atom & selected == selected for atom in groups[orbit])
            incidence.append(count)
            row[28 + i] = count
        moment = geometry.base_moment((outside,) + subset)
        for column, count in moment["coefficients"].items():
            row[column] -= count
        metadata.append({"subset": list(subset), "outside": outside,
                         "incidences": incidence, "base_moment": moment,
                         "row_index": len(rows)})
        rows.append({column: count for column, count in row.items() if count})
        rhs.append(0)
    if cut:
        row = Counter({40: -1})
        for points, multiplier in (((1, 2), 1), ((1, 2, 4), -8), ((1, 2, 4, 8), 28)):
            for column, count in geometry.base_moment(points)["coefficients"].items():
                row[column] += multiplier * count
        rows.append({column: count for column, count in row.items() if count})
        rhs.append(0)
    size = 41 if cut else 40
    model = {
        "schema": "exact-equality-lp-v1",
        "name": "rm2_mixed_nine_with_ten_cut" if cut else "rm2_mixed_nine_control",
        "variable_ids": [f"x{i:06d}" for i in range(size)],
        "row_ids": [f"r{i:06d}" for i in range(len(rows))],
        "rows": [{str(key): str(value) for key, value in row.items()} for row in rows],
        "rhs": [str(value) for value in rhs],
        "objective": ["1" if i == 27 else "0" for i in range(size)],
        "objective_offset": "0",
    }
    model_digest(model)
    return model, {"mixed_rows": metadata, "objective": "singleton probability p",
                   "cut": "q-8r+28v>=0" if cut else None,
                   "base_variables": 28, "base_rows": len(base_rows)}


def integer_identity(model, candidate):
    y = list(map(Fraction, candidate["dual"]))
    costs = list(map(Fraction, model["objective"]))
    reduced = costs[:]
    for row, multiplier in zip(model["rows"], y):
        for col, coefficient in row.items():
            reduced[int(col)] -= Fraction(coefficient) * multiplier
    objective = Fraction(candidate["claimed_objective"])
    denominator = lcm(*(value.denominator for value in y + reduced + [objective]))
    divisor = reduce(gcd, [denominator] + [int(value * denominator)
                                         for value in y + reduced + [objective]])
    denominator //= divisor
    return {
        "identity": "scale*p - constant = sum(nonnegative_coefficient_i*x_i)",
        "scale": denominator,
        "constant": int(denominator * objective),
        "nonnegative_coefficients": {
            str(i): int(value * denominator) for i, value in enumerate(reduced) if value},
        "equality_row_multipliers": {
            str(i): int(value * denominator) for i, value in enumerate(y) if value},
    }


def solve(executable, out, model, metadata, timeout):
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "model.json", model)
    write_json(out / "model-details.json", metadata)
    (out / "model.lp").write_text(to_lp(model), encoding="ascii", newline="\n")
    command = [str(executable.resolve()), "--readmode=1", "--solvemode=2",
               "--int:syncmode=1", "--real:feastol=0", "--real:opttol=0",
               "--int:checkmode=2", "-X=primal.sol", "-Y=dual.sol", "-q", "-c",
               f"-t{timeout}", "model.lp"]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=out, capture_output=True,
                               text=True, timeout=timeout + 5)
    elapsed = time.perf_counter() - started
    (out / "solver.stdout.txt").write_text(completed.stdout, encoding="utf-8", newline="\n")
    (out / "solver.stderr.txt").write_text(completed.stderr, encoding="utf-8", newline="\n")
    candidate = candidate_from_output(
        model, (out / "primal.sol").read_text(), (out / "dual.sol").read_text(),
        completed.stdout, completed.returncode)
    write_json(out / "candidate.json", candidate)
    checked = verify_solution(model, candidate)
    write_json(out / "replay.json", checked)
    if not checked["valid"]:
        raise ValueError("exact primal-dual verification failed: " + repr(checked))
    identity = integer_identity(model, candidate)
    write_json(out / "integer-identity.json", identity)
    return {"status": checked["status"], "singleton_optimum": candidate["claimed_objective"],
            "rows": len(model["rows"]), "variables": len(model["objective"]),
            "nonzeros": sum(map(len, model["rows"])),
            "command": command, "solver_seconds": elapsed,
            "model_sha256": model_digest(model), "integer_identity": identity,
            "artifact_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted(out.iterdir()) if path.is_file()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soplex", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("positive timeout required")
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    before = hashes()
    started = time.perf_counter()
    results = {}
    for label, cut in (("nine_control", False), ("ten_cut", True)):
        model, metadata = make_model(cut)
        results[label] = solve(args.soplex, out / label, model, metadata, args.timeout)
    after = hashes()
    result = {
        "schema": "rm2-level10-selected-cut-exploration-v1",
        "status": "EXACT_SELECTED_MODELS" if before == after else "UNKNOWN",
        "source_sha256_lf": before, "source_after_sha256_lf": after,
        "sources_unchanged": before == after,
        "solver_sha256": hashlib.sha256(args.soplex.read_bytes()).hexdigest(),
        "elapsed_seconds": time.perf_counter() - started, "results": results,
        "scope": "Selected necessary consequence models; no full-L10 upper bound.",
    }
    write_json(out / "RESULTS.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
