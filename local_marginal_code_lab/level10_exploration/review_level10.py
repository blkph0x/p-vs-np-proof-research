"""Source-bound exact replay of the final compact selected L10 model.

Imports no exploration producer or solver/exporter. Uses the historical
independent base-geometry reconstruction, then independently counts actual
assignments in the new atom orbits. Projection support is obtained by visiting
all 2^21 pinned quadratic polynomials. Exact rational primal/dual verification
is delegated only after the supplied matrix equals this reconstruction.
"""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import argparse
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from review_rm2_nine_scope import _base
from exact_lp_verify import model_digest, verify_solution

INSIDE = (4, 8, 12, 16, 20, 24, 28)
OUTSIDE = (1, 2, 32)
SCOPE = INSIDE + OUTSIDE
POSITIVE_IDENTITY = {
    43: 125552, 44: 146048, 52: 5856, 56: 356160, 57: 753312,
    58: 59664, 66: 66528, 67: 40992, 68: 61488, 70: 245616,
    72: 110096, 74: 289072, 76: 15728, 78: 12784,
}


def closure(points):
    direction = {0}
    origin = points[0]
    for point in points[1:]:
        difference = point ^ origin
        direction.update(value ^ difference for value in tuple(direction))
    return tuple(sorted(origin ^ value for value in direction))


def exact_image(points):
    """Build an explicit linear bijection of the small span by translations."""
    image = {0: 0}
    dimension = 0
    for point in points:
        if point not in image:
            image.update({value ^ point: code ^ (1 << dimension)
                          for value, code in tuple(image.items())})
            dimension += 1
    return tuple(image[point] for point in points)


def moment(points, allowed, var_for):
    points = exact_image(points)
    flat = closure(points)
    if len(flat) > 8 or flat not in allowed:
        raise ValueError("unreadable source moment")
    selected = sum(1 << flat.index(point) for point in points)
    answer = Counter()
    for atom in allowed[flat]:
        if atom & selected == selected:
            answer[var_for[(flat, atom)]] += 1
    return answer


def all_polynomial_restrictions():
    evaluations = []
    for first in range(6):
        evaluations.append(sum(((point >> first) & 1) << i for i, point in enumerate(SCOPE)))
    for first in range(6):
        for second in range(first + 1, 6):
            evaluations.append(sum((((point >> first) & (point >> second)) & 1) << i
                                   for i, point in enumerate(SCOPE)))
    word, words = 1023, {1023}
    for coefficients in range(1, 1 << 21):
        word ^= evaluations[(coefficients & -coefficients).bit_length() - 1]
        words.add(word)
    return words


@lru_cache(maxsize=1)
def _reconstruction():
    allowed, var_for, original_rows, original_rhs, _ = _base()
    rows, targets = [dict(row) for row in original_rows], list(original_rhs)
    flat = tuple(range(16, 24))
    families = {i: [word for word in allowed[flat] if var_for[(flat, word)] == i]
                for i in range(5, 11)}

    def append(row, rhs=0):
        rows.append({int(col): Fraction(value) for col, value in row.items() if value})
        targets.append(Fraction(rhs))

    def moment_equation(points, left):
        row = Counter(left)
        for col, count in moment(points, allowed, var_for).items():
            row[col] -= count
        return {col: count for col, count in row.items() if count}

    for i in range(6):
        append({28+i: 1, 34+i: 1, 5+i: -1})
    for selected_points in ((), (16,), (16, 17), (16, 17, 18), (16, 17, 18, 19)):
        mask = sum(1 << flat.index(point) for point in selected_points)
        counts = {28+i: sum(word & mask == mask for word in families[5+i]) for i in range(6)}
        append(moment_equation((24,) + selected_points, counts))
    cut = Counter({40: -1})
    for points, coefficient in (((1, 2), 1), ((1, 2, 4), -8), ((1, 2, 4, 8), 28)):
        for col, count in moment(points, allowed, var_for).items():
            cut[col] += coefficient * count
    append(cut)
    for i in range(6):
        append({41+i: 1, 47+i: 1, 28+i: -1})
        append({5+i: 1, 28+i: -2, 41+i: 1, 53+i: -1})
    for selected_points in ((), (16,), (16, 17)):
        mask = sum(1 << flat.index(point) for point in selected_points)
        counts = {41+i: sum(word & mask == mask for word in families[5+i]) for i in range(6)}
        append(moment_equation((24, 32) + selected_points, counts))

    # Classify complete assignments through the ORIGINAL base orbit ownership.
    # No producer's parity/type classifier or binomial moment formula is used.
    words = all_polynomial_restrictions()
    groups = {59 + 4*i+j: [] for i in range(5) for j in range(4)}
    pinned_flat = (0,) + INSIDE
    for word in words:
        original_atom = 1 | ((word & 127) << 1)
        orbit = var_for[(pinned_flat, original_atom)]
        if not 0 <= orbit < 5:
            raise ValueError("unexpected source orbit on pinned flat")
        groups[59 + 4*orbit + (word >> 7).bit_count()].append(word)
    if len(words) != 512 or any(not group for group in groups.values()):
        raise ValueError("wrong exact polynomial projection/orbit coverage")
    for i in range(5):
        row = {i: -1}
        representative_inside = groups[59 + 4*i][0] & 127
        for j in range(4):
            row[59+4*i+j] = sum(word & 127 == representative_inside
                               for word in groups[59+4*i+j])
        append(row)
    seen = set()
    moment_count = 0
    for mask in range(1, 1024):
        points = tuple(point for i, point in enumerate(SCOPE) if mask >> i & 1)
        if len(closure(points)) > 8:
            continue
        counts = {col: sum(word & mask == mask for word in group) for col, group in groups.items()}
        row = moment_equation(points, counts)
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            append(row)
        moment_count += 1
    model = {
        "schema": "exact-equality-lp-v1", "name": "rm2_level10_compact_combined",
        "variable_ids": [f"x{i:06d}" for i in range(79)],
        "row_ids": [f"r{i:06d}" for i in range(len(rows))],
        "rows": [{str(col): str(value) for col, value in row.items()} for row in rows],
        "rhs": list(map(str, targets)),
        "objective": ["1" if i == 27 else "0" for i in range(79)],
        "objective_offset": "0",
    }
    model_digest(model)
    return json.dumps(model, sort_keys=True), {
        "polynomials_enumerated": 1 << 21, "projection_atoms": len(words),
        "atom_orbits": len(groups), "original_moment_subsets": moment_count,
        "distinct_new_moment_rows": len(seen),
    }


def rebuild_model():
    return json.loads(_reconstruction()[0])


def replay(model, certificate):
    try:
        model_digest(model)
        if model != rebuild_model():
            raise ValueError("supplied model differs from independently counted original scopes")
        result = verify_solution(model, certificate)
        if result["valid"]:
            result["scope"] = (
                "Exact optimum of the selected necessary model; all-m>=6 lower consequence, "
                "not a full-L10 upper certificate.")
            result["source_reconstruction"] = dict(_reconstruction()[1])
        return result
    except (TypeError, ValueError, KeyError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def verify_short_identity(model, identity):
    if model != rebuild_model():
        raise ValueError("identity model is not source-bound")
    # Divide the supplied integral row combination by54. Check its value on
    # EVERY original column and RHS against the written fourteen-term formula.
    combination = Counter()
    constant = Fraction()
    for index, multiplier in identity["equality_row_multipliers"].items():
        i, multiplier = int(index), Fraction(multiplier, 54)
        constant += multiplier * Fraction(model["rhs"][i])
        for col, value in model["rows"][i].items():
            combination[int(col)] += multiplier * Fraction(value)
    if constant != 3843:
        raise ValueError("wrong identity constant")
    for col in range(79):
        wanted = (16627 if col == 27 else 0) - POSITIVE_IDENTITY.get(col, 0)
        if combination[col] != wanted:
            raise ValueError("wrong identity coefficient at column " + str(col))
    return {"valid": True, "status": "EXACT_IDENTITY", "nonnegative_terms": 14,
            "singleton_lower_bound": "3843/16627"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path,
                        default=HERE / "compact_combined_run/compact_combined")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_paths = [
        Path(__file__).resolve(), HERE.parent / "review_rm2_nine_scope.py",
        HERE.parent / "REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW.py",
        HERE.parent / "reed_muller_affine_overlap.py", HERE.parent / "exact_lp_verify.py",
    ]
    source_hashes = lambda: {
        path.relative_to(HERE.parent).as_posix(): hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for path in source_paths}
    input_hashes = lambda: {
        name: hashlib.sha256((args.directory / name).read_bytes()).hexdigest()
        for name in ("model.json", "candidate.json", "integer-identity.json")}
    before, inputs_before = source_hashes(), input_hashes()
    load = lambda name: json.loads((args.directory / name).read_text())
    model, candidate = load("model.json"), load("candidate.json")
    checked = replay(model, candidate)
    if checked["valid"]:
        checked["short_identity"] = verify_short_identity(model, load("integer-identity.json"))
    after, inputs_after = source_hashes(), input_hashes()
    checked.update(source_sha256_lf=before, source_after_sha256_lf=after,
                   sources_unchanged=before == after, artifact_sha256=inputs_before,
                   artifacts_unchanged=inputs_before == inputs_after)
    if before != after or inputs_before != inputs_after:
        checked.update(valid=False, status="UNKNOWN",
                       errors=["source or input artifacts changed during replay"])
    text = json.dumps(checked, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0 if checked["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
