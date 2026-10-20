"""Exact discovery for a conditioned, already proved level-nine identity.

The scalar inequality and the full identity are separate controls. No
expected optimum or basis is passed to the optimizer.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import sys
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OLD = LAB / "level10_exploration"
sys.path[:0] = [str(OLD), str(LAB)]
import investigate_mixed_cut as mixed
import investigate_double_external as double

CONDITIONAL_ROW = {
    24: 279, 27: -63, 8: -672, 43: -1904, 44: -8568,
    45: -4928, 46: -216, 50: -952, 52: -328,
}


def build(identity):
    model, metadata = double.extend(*mixed.make_model(True))
    model["name"] = ("rm2_level10_conditioned_identity" if identity
                     else "rm2_level10_conditioned_scalar")
    if identity:
        row = dict(CONDITIONAL_ROW)
        metadata["new_condition"] = "full conditioned level-nine identity"
    else:
        row = {24: 31, 27: -7, 59: -1}
        model["objective"].append("0")
        model["variable_ids"].append("x000059")
        metadata["new_condition"] = "31q-7p>=0"
    model["rows"].append({str(key): str(value) for key, value in row.items()})
    model["rhs"].append("0")
    model["row_ids"].append(f"r{len(model['rows'])-1:06d}")
    metadata["conditioned_identity_geometry"] = {
        "affine_three_flat": list(range(16, 24)),
        "conditioned_point": 24,
        "second_outside_point": 32,
        "common_affine_five_flat_equation": "bit4 XOR bit5 = 1",
        "scope_size": 10,
    }
    return model, metadata


def source_hashes():
    answer = double.source_hashes()
    for path in (Path(__file__).resolve(),
                 LAB / "REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md"):
        answer[path.relative_to(LAB).as_posix()] = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soplex", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=HERE / "exact_run")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    before, started = source_hashes(), time.perf_counter()
    results = {}
    for label, identity in (("scalar", False), ("identity", True)):
        model, metadata = build(identity)
        results[label] = mixed.solve(args.soplex, out / label, model, metadata, 120)
    after = source_hashes()
    report = {
        "schema": "rm2-level10-conditioning-discovery-v1",
        "status": "EXACT_SELECTED_MODELS" if before == after else "UNKNOWN",
        "source_sha256_lf": before, "source_after_sha256_lf": after,
        "sources_unchanged": before == after, "results": results,
        "solver_sha256": hashlib.sha256(args.soplex.read_bytes()).hexdigest(),
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "Selected necessary models; full upper requires a separate theorem.",
    }
    mixed.write_json(out / "RESULTS.json", report)
    for label, result in results.items():
        print(label, result["status"], result["singleton_optimum"],
              result["variables"], result["rows"], flush=True)
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
