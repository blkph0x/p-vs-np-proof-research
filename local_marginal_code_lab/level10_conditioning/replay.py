"""Independent source-bound replay of the conditioned level-ten models.

No discovery producer, exporter, LP parser, or optimizer is imported. The
historical independent geometry reviewer rebuilds the old rows; the added
row is reconstructed from the stated conditional atom maps. The final
eight-term identity is also checked from elementary incidence equations,
without the historical quotient matrix.
"""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OLD = LAB / "level10_exploration"
sys.path[:0] = [str(OLD), str(LAB)]
import review_level10 as original
from exact_lp_verify import model_digest, verify_solution

MULTIPLIERS = [
    1305, 9135, -18270, 22620, -12180, 0, -126, 882, -13944,
    12180, 17584, 0, 1764, -12348, 8120, 16576, 0, 3672, -25704, 56,
]


def _add(*parts):
    out = Counter()
    for multiplier, expression in parts:
        for variable, coefficient in expression.items():
            out[variable] += multiplier * coefficient
    return {variable: value for variable, value in out.items() if value}


def elementary_equations():
    """Each expression is zero, in the exact order printed in THEOREM.md."""
    z = lambda i: f"z{i}"
    equations = [
        {z(0): 7, z(1): 7, z(2): 28, z(3): 21, z(4): 1, "one": -1},
        {"p": 1, z(0): -1, z(1): -3, z(2): -12, z(3): -15, z(4): -1},
        {"q": 1, z(1): -1, z(2): -4, z(3): -10, z(4): -1},
        {"r": 1, z(2): -1, z(3): -6, z(4): -1},
        {"h": 1, z(3): -3, z(4): -1},
        {z(5): 1, z(6): 28, z(7): 14, z(8): 56, z(9): 28, z(10): 1, "one": -1},
        {"p": 1, z(6): -7, z(7): -7, z(8): -28, z(9): -21, z(10): -1},
        {"q": 1, z(6): -1, z(7): -3, z(8): -12, z(9): -15, z(10): -1},
        {"r": 1, z(7): -1, z(8): -4, z(9): -10, z(10): -1},
        {"h": 1, z(7): -1, z(9): -6, z(10): -1},
        {"v": 1, z(8): -1, z(9): -6, z(10): -1},
        {"p": 1, "b0": -1, "b2": -28, "bP": -14, "bN": -56, "b6": -28, "b8": -1},
        {"q": 1, "b2": -7, "bP": -7, "bN": -28, "b6": -21, "b8": -1},
        {"r": 1, "b2": -1, "bP": -3, "bN": -12, "b6": -15, "b8": -1},
        {"v": 1, "bP": -1, "bN": -4, "b6": -10, "b8": -1},
        {z(9): 3, z(10): 1, "bP": -1, "b6": -6, "b8": -1},
        {"q": 1, "g0": -1, "g2": -28, "gP": -14, "gN": -56, "g6": -28, "g8": -1},
        {"r": 1, "g2": -7, "gP": -7, "gN": -28, "g6": -21, "g8": -1},
        {"v": 1, "g2": -1, "gP": -3, "gN": -12, "g6": -15, "g8": -1},
        # The old L9 identity, conditioned at a point of an affine5-flat.
        {"q": 279, "p": -63, "z8": -672, "gP": -1904,
         "gN": -7616, "g6": -4928, "g8": 112, "bN": -952, "b8": -328},
    ]
    return equations


def verify_elementary_identity(multipliers=None):
    if multipliers is None:
        multipliers = MULTIPLIERS
    if (type(multipliers) is not list or len(multipliers) != 20
            or any(type(value) is not int for value in multipliers)):
        raise ValueError("twenty exact integer incidence multipliers required")
    rhs = {
        "z2": 22620, "z3": 26100, "gP": 55216, "gN": 214368,
        "g8": 4176,
    }
    rhs = _add((1, rhs), (32480, {"b6": 1, "g6": -1}),
               (32480, {"b8": 1, "g8": -1}),
               (6496, {"z8": 1, "bN": -2, "gN": 1}))
    wanted = _add((1, {"p": 5481, "one": -1305}), (-1, rhs))
    actual = _add(*zip(multipliers, elementary_equations()))
    if actual != wanted:
        raise ValueError("elementary identity mismatch")
    return {"status": "EXACT_IDENTITY", "equations": 20, "terms": 8,
            "scale": 5481, "constant": 1305, "lower_bound": "5/21",
            "multipliers": list(multipliers)}


def check_atom_maps():
    """Finite geometry check of the subtle z2' -> z8 map and all H types."""
    a, u = 24, 32
    flat = tuple(range(16, 24))
    if any(((point >> 4) ^ (point >> 5)) & 1 != 1 for point in flat + (a, u)):
        raise ValueError("scope not contained in the stated affine5-flat")
    translated = tuple(point ^ a for point in flat)
    span = {0}
    for point in translated:
        span.update(point ^ item for item in tuple(span))
    if len(span) != 16 or u ^ a in span:
        raise ValueError("conditional outside point lies in the flat span")
    # A pinned linear3-flat relative to a translates to an original affine3-flat.
    independent_triples = 0
    for mask in range(128):
        points = [i + 1 for i in range(7) if mask >> i & 1]
        if len(points) != 3 or points[0] ^ points[1] ^ points[2] == 0:
            continue
        ones = [a] + [a ^ point for point in points]
        # Four points in characteristic two form an affine plane iff xor is0.
        total = 0
        for point in ones:
            total ^= point
        if total == 0 or len(set(ones)) != 4:
            raise ValueError("independent-three atom did not become a nonplane4-set")
        independent_triples += 1
    if independent_triples != 28:
        raise ValueError("wrong independent-three atom count")
    type_counts = Counter()
    for atom in range(256):
        if atom.bit_count() % 2:
            continue
        size = atom.bit_count()
        if size == 4:
            total = 0
            translated_total = 0
            for i, point in enumerate(flat):
                if atom >> i & 1:
                    total ^= point
                    translated_total ^= point ^ a
            if (total == 0) != (translated_total == 0):
                raise ValueError("translation changed the plane/nonplane type")
            kind = "P" if total == 0 else "N"
        else:
            kind = str(size)
        type_counts[kind] += 1
    if dict(type_counts) != {"0": 1, "2": 28, "P": 14, "N": 56, "6": 28, "8": 1}:
        raise ValueError("conditional H-type counts changed")
    return {"status": "EXACT_GEOMETRY", "independent_triples": independent_triples,
            "even_H_atoms": sum(type_counts.values()), "type_counts": dict(type_counts),
            "original_scope_size": 10, "conditional_scope_size": 9}


@lru_cache(maxsize=2)
def _rebuild(identity):
    # The independent historical reconstruction counts original assignments.
    full = original.rebuild_model()
    model = {
        "schema": full["schema"],
        "name": ("rm2_level10_conditioned_identity" if identity
                 else "rm2_level10_conditioned_scalar"),
        "variable_ids": full["variable_ids"][:59],
        "row_ids": full["row_ids"][:80],
        "rows": [dict(row) for row in full["rows"][:80]],
        "rhs": list(full["rhs"][:80]),
        "objective": list(full["objective"][:59]),
        "objective_offset": "0",
    }
    if any(int(col) >= 59 for row in model["rows"] for col in row):
        raise ValueError("historical base extraction crossed a scope boundary")
    allowed, var_for, _, _, _ = original._base()
    p = original.moment((1,), allowed, var_for)
    q = original.moment((1, 2), allowed, var_for)
    if identity:
        check_atom_maps()
        # Select an actual nonplane four-atom, rather than trust its column id.
        flat = tuple(range(16, 24))
        z_nonplane = var_for[(flat, 23)]
        if z_nonplane != 8:
            raise ValueError("historical nonplane atom convention changed")
        row = _add((279, q), (-63, p), (-672, {z_nonplane: 1}),
                   (-1904, {43: 1}), (-8568, {44: 1}), (-4928, {45: 1}),
                   (-216, {46: 1}), (-952, {50: 1}), (-328, {52: 1}))
    else:
        row = _add((31, q), (-7, p), (-1, {59: 1}))
        model["variable_ids"].append("x000059")
        model["objective"].append("0")
    model["rows"].append({str(col): str(value) for col, value in row.items()})
    model["row_ids"].append("r000080")
    model["rhs"].append("0")
    model_digest(model)
    return json.dumps(model, sort_keys=True)


def rebuild_model(identity=True):
    return json.loads(_rebuild(identity))


def replay(model, certificate, identity=True):
    try:
        if type(identity) is not bool:
            raise ValueError("identity selector must be an exact bool")
        model_digest(model)
        if model != rebuild_model(identity):
            raise ValueError("model differs from original geometry and conditional identity")
        checked = verify_solution(model, certificate)
        if checked["valid"]:
            checked["source_bound"] = True
        return checked
    except (KeyError, ValueError, TypeError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def source_hashes():
    paths = [Path(__file__).resolve(), HERE / "discover.py",
             OLD / "review_level10.py", LAB / "review_rm2_nine_scope.py",
             LAB / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py",
             LAB / "reed_muller_affine_overlap.py", LAB / "exact_lp_verify.py",
             LAB / "REED_MULLER_QUADRATIC_LEVEL9_THEOREM.md"]
    return {path.relative_to(LAB).as_posix(): hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for path in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=HERE / "exact_run")
    parser.add_argument("--output", type=Path, default=HERE / "REPLAY.json")
    args = parser.parse_args()
    before, start = source_hashes(), time.perf_counter()
    results = {}
    for label, identity in (("scalar", False), ("identity", True)):
        directory = args.directory / label
        model = json.loads((directory / "model.json").read_text())
        candidate = json.loads((directory / "candidate.json").read_text())
        checked = replay(model, candidate, identity)
        if not checked["valid"]:
            raise ValueError(label + ": " + repr(checked))
        results[label] = checked
    discovery = json.loads((args.directory / "RESULTS.json").read_text())
    for label, value in discovery["results"].items():
        for name, digest in value["artifact_sha256"].items():
            if hashlib.sha256((args.directory / label / name).read_bytes()).hexdigest() != digest:
                raise ValueError("discovery artifact changed: " + label + "/" + name)
    after = source_hashes()
    if before != after:
        raise ValueError("replay source changed during verification")
    report = {
        "schema": "rm2-level10-conditioning-replay-v1", "status": "PASS",
        "source_sha256_lf": before, "source_after_sha256_lf": after,
        "sources_unchanged": True, "results": results,
        "atom_maps": check_atom_maps(), "elementary_identity": verify_elementary_identity(),
        "elapsed_seconds": time.perf_counter() - start,
        "scope": "Source-bound selected optima and all-family lower identity; separate upper theorem.",
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8", newline="\n")
    print("PASS", {key: value["reduced_objective"] for key, value in results.items()})


if __name__ == "__main__":
    main()
