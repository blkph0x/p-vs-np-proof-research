"""Selected ten-point H+u+v consequences, with independently counted incidences.

H={16,...,23}, u=24 and v=32. Their span has dimension six. Averaging
over GL(m,2) makes the two H+outside marginals equal to the existing b_i.
Let c_i be each H-atom's joint mass with both outside bits one. Then
c_i>=0, b_i-c_i>=0 and z_i-2b_i+c_i>=0. The three mixed moments of
u,v plus zero, one, or two H points equal q,r,v respectively.
All are necessary conditions of full L10 for every m>=6.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import argparse
import hashlib
import time

import investigate_mixed_cut as mixed
import investigate_ten_scope as ten


def extend(model, metadata):
    allowed, var_for, _, _, _ = mixed.geometry._base()
    flat = tuple(range(16, 24))
    groups = {}
    for atom in allowed[flat]:
        groups.setdefault(var_for[(flat, atom)], []).append(atom)
    start = len(model["objective"])
    model["objective"].extend(["0"] * 18)
    model["variable_ids"] = [f"x{i:06d}" for i in range(len(model["objective"]))]
    model["name"] += "_double_external"
    metadata["double_external"] = {
        "flat": list(flat), "outside": [24, 32], "first_c_column": start,
        "first_d_column": start + 6, "first_e_column": start + 12,
        "row_start": len(model["rows"]), "mixed_moments": [],
    }
    for i in range(6):
        # d_i=b_i-c_i and e_i=z_i-2b_i+c_i.
        model["rows"].append({str(start + i): "1", str(start + 6 + i): "1",
                              str(28 + i): "-1"})
        model["rhs"].append("0")
        model["rows"].append({str(5 + i): "1", str(28 + i): "-2",
                              str(start + i): "1", str(start + 12 + i): "-1"})
        model["rhs"].append("0")
    for subset in ((), (16,), (16, 17)):
        selected = sum(1 << flat.index(point) for point in subset)
        row = Counter()
        coefficients = []
        for i in range(6):
            count = sum(atom & selected == selected for atom in groups[5 + i])
            row[start + i] = count
            coefficients.append(count)
        original_points = (24, 32) + subset
        encoded, basis = ten.linear_image(original_points)
        moment = mixed.geometry.base_moment(encoded)
        for column, count in moment["coefficients"].items():
            row[column] -= count
        metadata["double_external"]["mixed_moments"].append({
            "original_points": list(original_points), "encoded_points": list(encoded),
            "linear_basis": basis, "coefficients": coefficients,
            "base_moment": moment, "row_index": len(model["rows"]),
        })
        model["rows"].append({str(column): str(value) for column, value in row.items() if value})
        model["rhs"].append("0")
    model["row_ids"] = [f"r{i:06d}" for i in range(len(model["rows"]))]
    mixed.model_digest(model)
    return model, metadata


def genuine_d6_extension(model, metadata, old_primal):
    kernels = set()
    for a, b in combinations(range(1, 64), 2):
        kernels.add(sum(1 << point for point in range(64)
                        if not (a & point).bit_count() % 2 and not (b & point).bit_count() % 2))
    allowed, var_for, _, _, _ = mixed.geometry._base()
    flat = tuple(range(16, 24))
    c = []
    for i in range(6):
        atom = next(atom for atom in allowed[flat] if var_for[(flat, atom)] == 5 + i)
        c.append(Fraction(sum(
            sum(((kernel >> point) & 1) << j for j, point in enumerate(flat)) == atom
            and ((kernel >> 24) & 1) and ((kernel >> 32) & 1)
            for kernel in kernels), len(kernels)))
    primal = list(map(Fraction, old_primal))
    primal += c
    primal += [primal[28 + i] - c[i] for i in range(6)]
    primal += [primal[5 + i] - 2 * primal[28 + i] + c[i] for i in range(6)]
    if len(primal) != len(model["objective"]) or any(x < 0 for x in primal):
        raise ValueError("D6 extension shape/nonnegativity")
    residuals = [sum(Fraction(value) * primal[int(col)] for col, value in row.items())
                 - Fraction(target) for row, target in zip(model["rows"], model["rhs"])]
    if any(residuals):
        raise ValueError("D6 actual distribution failed selected double-outside rows")
    return {"status": "EXACT_FEASIBLE_POINT", "primal": list(map(str, primal)),
            "kernel_count": len(kernels), "all_residuals_zero": True,
            "singleton_probability": str(primal[27]), "checked_rows": len(residuals)}


def source_hashes():
    result = ten.source_hashes()
    result["level10_exploration/investigate_double_external.py"] = hashlib.sha256(
        Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soplex", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    before, started = source_hashes(), time.perf_counter()
    # Derive one actual D6 distribution once, then take the relevant prefixes.
    original_model, original_metadata = ten.build()
    d6 = ten.genuine_d6_point(original_model, original_metadata)
    models = {"compact": mixed.make_model(True), "combined": (original_model, original_metadata)}
    results = {}
    for label, (model, metadata) in models.items():
        prefix = d6["primal"][:len(model["objective"])]
        model, metadata = extend(model, metadata)
        control = genuine_d6_extension(model, metadata, prefix)
        mixed.write_json(out / (label + "-d6-control.json"), control)
        results[label] = mixed.solve(args.soplex, out / label, model, metadata, args.timeout)
        print(label, results[label]["singleton_optimum"], flush=True)
    after = source_hashes()
    report = {
        "schema": "rm2-level10-double-external-exploration-v1",
        "status": "EXACT_SELECTED_MODELS" if before == after else "UNKNOWN",
        "source_sha256_lf": before, "source_after_sha256_lf": after,
        "sources_unchanged": before == after, "results": results,
        "elapsed_seconds": time.perf_counter() - started,
        "solver_sha256": hashlib.sha256(args.soplex.read_bytes()).hexdigest(),
        "scope": "Necessary L10 conditions; full-relaxation upper bounds need a separate construction.",
    }
    mixed.write_json(out / "RESULTS.json", report)
    print(report["status"], "unchanged", before == after, flush=True)
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
