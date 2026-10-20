"""Orbit compression of the explicitly checked original ten-point table.

The seven inside points are K\\{0}, dim K=3; the three outside points are
independent modulo K. GL(K) x S3 acts by ambient linear maps. Its atom orbits
are five odd inside-subset types times four outside weights. Variables are
per-assignment masses, so multiplicities must be included in every moment.
"""
from collections import Counter
from fractions import Fraction
from math import comb
from pathlib import Path
import argparse
import hashlib
import time

import investigate_mixed_cut as mixed
import investigate_ten_scope as ten
import investigate_double_external as double

INSIDE = (4, 8, 12, 16, 20, 24, 28)
OUTSIDE = (1, 2, 32)


def atom_type(mask):
    size = mask.bit_count()
    if size == 1:
        return 0
    if size == 3:
        total = 0
        for i, point in enumerate(INSIDE):
            if mask >> i & 1:
                total ^= point
        return 1 if total == 0 else 2
    if size == 5:
        return 3
    if size == 7:
        return 4
    raise ValueError("inside projection requires odd weight")


def build():
    model, metadata = double.extend(*mixed.make_model(True))
    model["name"] = "rm2_level10_compact_combined"
    start = len(model["objective"])
    groups = [[mask for mask in range(128) if mask.bit_count() % 2
               and atom_type(mask) == i] for i in range(5)]
    if list(map(len, groups)) != [7, 7, 28, 21, 1]:
        raise ValueError("wrong inside atom classification")
    # Each t_(i,j) is the mass of ONE complete assignment of this orbit.
    model["objective"].extend(["0"] * 20)
    model["variable_ids"] = [f"x{i:06d}" for i in range(len(model["objective"]))]
    for i in range(5):
        row = {str(start + 4 * i + j): str(comb(3, j)) for j in range(4)}
        row[str(i)] = "-1"
        model["rows"].append(row)
        model["rhs"].append("0")
    moment_rows, seen = [], {}
    scope = INSIDE + OUTSIDE
    for mask in range(1, 1 << 10):
        points = tuple(point for i, point in enumerate(scope) if mask >> i & 1)
        if len(ten.affine_closure(points)) > 8:
            continue
        inside_mask = mask & 127
        k = (mask >> 7).bit_count()
        row = Counter()
        for i in range(5):
            incidence = sum(atom & inside_mask == inside_mask for atom in groups[i])
            for j in range(k, 4):
                row[start + 4 * i + j] = incidence * comb(3 - k, j - k)
        encoded, basis = ten.linear_image(points)
        moment = mixed.geometry.base_moment(encoded)
        for col, count in moment["coefficients"].items():
            row[col] -= count
        row = {str(col): str(value) for col, value in row.items() if value}
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen[key] = len(model["rows"])
            model["rows"].append(row)
            model["rhs"].append("0")
        moment_rows.append({"points": list(points), "encoded_points": list(encoded),
                            "linear_basis": basis, "row_index": seen[key],
                            "inside_mask": inside_mask, "outside_selected": k})
    model["row_ids"] = [f"r{i:06d}" for i in range(len(model["rows"]))]
    metadata["compact_original_scope"] = {
        "inside": list(INSIDE), "outside": list(OUTSIDE), "first_t_column": start,
        "type_multiplicities": list(map(len, groups)),
        "column_order": [[i, j] for i in range(5) for j in range(4)],
        "moment_rows": moment_rows, "distinct_moment_rows": len(seen),
    }
    mixed.model_digest(model)
    return model, metadata


def expand_to_raw(primal, metadata):
    """Exact projection to the previously saved 571-column raw combined model."""
    values = list(map(Fraction, primal))
    start = metadata["compact_original_scope"]["first_t_column"]
    atoms, _ = ten.projection_atoms(ten.SCOPE)
    raw = values[:41]
    for atom in atoms:
        selected = {point for i, point in enumerate(ten.SCOPE) if atom >> i & 1}
        inside_mask = sum(1 << i for i, point in enumerate(INSIDE) if point in selected)
        j = len(selected.intersection(OUTSIDE))
        raw.append(values[start + 4 * atom_type(inside_mask) + j])
    raw.extend(values[41:59])
    return raw


def source_hashes():
    result = double.source_hashes()
    result["level10_exploration/investigate_compact_combined.py"] = hashlib.sha256(
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
    model, metadata = build()
    result = mixed.solve(args.soplex, out / "compact_combined", model, metadata, args.timeout)
    # Check the chosen optimum against the full raw table's every equation.
    import json
    candidate = json.loads((out / "compact_combined/candidate.json").read_text())
    raw = expand_to_raw(candidate["primal"], metadata)
    raw_model, _ = double.extend(*ten.build())
    if len(raw) != len(raw_model["objective"]) or any(value < 0 for value in raw):
        raise ValueError("raw expansion shape/nonnegativity")
    residuals = [sum(Fraction(value) * raw[int(col)] for col, value in row.items()) - Fraction(rhs)
                 for row, rhs in zip(raw_model["rows"], raw_model["rhs"])]
    if any(residuals):
        raise ValueError("compact optimum does not expand to the full raw selected model")
    mixed.write_json(out / "raw-expansion.json", {
        "status": "EXACT_FEASIBLE_POINT", "model_sha256": mixed.model_digest(raw_model),
        "primal": list(map(str, raw)), "all_residuals_zero": True,
        "checked_rows": len(residuals), "singleton_probability": str(raw[27]),
    })
    after = source_hashes()
    report = {
        "schema": "rm2-level10-compact-combined-exploration-v1",
        "status": "EXACT_SELECTED_MODEL" if before == after else "UNKNOWN",
        "source_sha256_lf": before, "source_after_sha256_lf": after,
        "sources_unchanged": before == after, "selected_result": result,
        "elapsed_seconds": time.perf_counter() - started,
        "solver_sha256": hashlib.sha256(args.soplex.read_bytes()).hexdigest(),
        "raw_expansion_rows_checked": len(residuals),
        "full_L10_optimum": "NOT_DETERMINED_BY_SELECTED_MODEL_FEASIBILITY",
    }
    mixed.write_json(out / "RESULTS.json", report)
    print(report["status"], result["singleton_optimum"], result["variables"], result["rows"],
          "raw rows", len(residuals), flush=True)
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
