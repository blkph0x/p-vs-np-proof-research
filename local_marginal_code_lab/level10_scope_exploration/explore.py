"""Complete ten-column, corank-at-most-three classification for D=6 moments.

No optimizer or existing moment producer is imported. Histograms classify
relation-code generator columns up to coordinate permutation and GL(d,2).
The independent verifier reconstructs ranks directly from point coordinates.
"""
from collections import Counter
from itertools import combinations, permutations
import gzip
import hashlib
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
WIDTH = 10
NUMERATORS = (651, 155, 35, 7, 1)


def rank(rows):
    basis = {}
    for row in rows:
        while row:
            pivot = row.bit_length() - 1
            if pivot in basis:
                row ^= basis[pivot]
            else:
                basis[pivot] = row
                break
    return len(basis)


def compositions(total, slots):
    if slots == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for tail in compositions(total - first, slots - 1):
            yield (first, *tail)


def linear_permutations(d):
    if d == 0:
        return ((0,),)
    maps = []
    for images in permutations(range(1, 1 << d), d):
        if rank(images) != d:
            continue
        permutation = []
        for word in range(1 << d):
            image = 0
            for bit in range(d):
                if word >> bit & 1:
                    image ^= images[bit]
            permutation.append(image)
        maps.append(tuple(permutation))
    return tuple(maps)


def transform_histogram(histogram, permutation):
    transformed = [0] * len(histogram)
    for old, new in enumerate(permutation):
        transformed[new] = histogram[old]
    return tuple(transformed)


def relation_rows(histogram, d):
    labels = [label for label, count in enumerate(histogram) for _ in range(count)]
    return [sum(((label >> bit) & 1) << column for column, label in enumerate(labels))
            for bit in range(d)]


def relation_words(rows):
    words = [0]
    for row in rows:
        words += [word ^ row for word in words]
    return words


def simple_full_rank(histogram, d):
    if rank(label for label, count in enumerate(histogram) if count) != d:
        return False
    rows = relation_rows(histogram, d)
    return all(word.bit_count() >= 3 for word in relation_words(rows) if word)


def kernel_columns(rows, width):
    reduced = list(rows)
    pivots = []
    at = 0
    for column in range(width):
        chosen = next((i for i in range(at, len(reduced)) if reduced[i] >> column & 1), None)
        if chosen is None:
            continue
        reduced[at], reduced[chosen] = reduced[chosen], reduced[at]
        for i in range(len(reduced)):
            if i != at and reduced[i] >> column & 1:
                reduced[i] ^= reduced[at]
        pivots.append(column)
        at += 1
    basis = []
    for free in range(width):
        if free not in pivots:
            vector = 1 << free
            for pivot, row in zip(pivots, reduced):
                if row >> free & 1:
                    vector |= 1 << pivot
            basis.append(vector)
    return tuple(sum(((row >> column) & 1) << i for i, row in enumerate(basis))
                 for column in range(width))


def table_from_relations(rows, width, numerators=NUMERATORS):
    words = relation_words(rows)
    moments = []
    for subset in range(1 << width):
        supported = sum(word & ~subset == 0 for word in words)
        nullity = supported.bit_length() - 1
        if supported != 1 << nullity:
            raise ValueError("supported relations are not a vector space")
        dimension = subset.bit_count() - nullity
        moments.append(numerators[dimension] if dimension < len(numerators) else 0)
    masses = moments.copy()
    for bit in range(width):
        for mask in range(1 << width):
            if not mask >> bit & 1:
                masses[mask] -= masses[mask | (1 << bit)]
    return moments, masses


def enumerate_types():
    cases = []
    statistics = []
    for d in range(4):
        maps = linear_permutations(d)
        raw = admissible = 0
        orbit_histograms = {}
        for histogram in compositions(WIDTH, 1 << d):
            raw += 1
            if not simple_full_rank(histogram, d):
                continue
            admissible += 1
            canonical = min(transform_histogram(histogram, permutation) for permutation in maps)
            orbit_histograms[canonical] = orbit_histograms.get(canonical, 0) + 1
        for histogram, orbit_size in sorted(orbit_histograms.items()):
            rows = relation_rows(histogram, d)
            points = kernel_columns(rows, WIDTH)
            moments, masses = table_from_relations(rows, WIDTH)
            cases.append({
                "corank": d, "histogram": list(histogram),
                "histogram_orbit_size": orbit_size, "relation_basis": rows,
                "points": list(points), "masses": masses,
                "minimum_mass": min(masses), "empty_mass": masses[0],
                "mass_histogram": {str(key): value for key, value in sorted(Counter(masses).items())},
            })
        statistics.append({
            "corank": d, "raw_histograms": raw, "admissible_histograms": admissible,
            "gl_order": len(maps), "orbits": len(orbit_histograms),
        })
    return cases, statistics


def normalized_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    started = time.perf_counter()
    names = ("explore.py", "verify.py", "test_exploration.py", "THEOREM.md")
    before = {name: normalized_hash(HERE / name) for name in names}
    cases, statistics = enumerate_types()
    certificate = {
        "schema": "d6-ten-point-complete-histogram-certificate-v1",
        "width": WIDTH, "denominator": 651, "rank_numerators": list(NUMERATORS),
        "coverage": statistics, "cases": cases,
    }
    raw = json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (HERE / "CERTIFICATE.json.gz").write_bytes(gzip.compress(raw, mtime=0))
    from verify import verify_certificate
    checked = verify_certificate(certificate)
    after = {name: normalized_hash(HERE / name) for name in names}
    if after != before:
        raise RuntimeError("source changed during run")
    result = {
        "schema": "d6-ten-point-exhaustive-result-v1",
        "status": "PASS" if checked["valid"] else "FAIL",
        "source_sha256_lf": after, "source_unchanged": True,
        "certificate_sha256": hashlib.sha256((HERE / "CERTIFICATE.json.gz").read_bytes()).hexdigest(),
        "coverage": statistics, "independent_replay": checked,
        "elapsed_seconds": time.perf_counter() - started,
        "minimum_empty_numerator": min(case["empty_mass"] for case in cases),
        "minimum_atom_numerator": min(case["minimum_mass"] for case in cases),
    }
    (HERE / "RESULTS.json").write_text(json.dumps(result, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    if not checked["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
