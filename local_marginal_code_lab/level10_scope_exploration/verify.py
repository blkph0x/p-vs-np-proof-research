"""Independent complete replay of the D6 ten-point certificate.

Imports neither explore nor any previous moment producer. Coverage uses
stars-and-bars enumeration and independently generated invertible row maps;
moments are reconstructed by elimination of actual point coordinates.
"""
from collections import Counter
import gzip
from itertools import combinations, product
import json
from math import comb, factorial, prod
from pathlib import Path


G = (651, 155, 35, 7, 1)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def span(vectors):
    values = {0}
    for vector in vectors:
        values |= {value ^ vector for value in values}
    return frozenset(values)


def dimension(vectors):
    # Low-pivot elimination, distinct from the producer's high-pivot routine.
    basis = {}
    for vector in vectors:
        while vector:
            pivot = (vector & -vector).bit_length() - 1
            if pivot not in basis:
                basis[pivot] = vector
                break
            vector ^= basis[pivot]
    return len(basis)


def histograms(width, slots):
    for bars in combinations(range(width + slots - 1), slots - 1):
        cuts = (-1, *bars, width + slots - 1)
        yield tuple(cuts[i + 1] - cuts[i] - 1 for i in range(slots))


def admissible(histogram, d):
    # Every nonzero row combination must have weight at least three.
    # This also excludes a deficient generator rank.
    return all(sum(count for label, count in enumerate(histogram)
                   if (label & functional).bit_count() & 1) >= 3
               for functional in range(1, 1 << d))


def invertible_actions(d):
    result = []
    for rows in product(range(1 << d), repeat=d):
        if len(span(rows)) != 1 << d:
            continue
        action = tuple(sum(((row & label).bit_count() & 1) << i
                           for i, row in enumerate(rows))
                       for label in range(1 << d))
        require(len(set(action)) == 1 << d, "noninvertible action")
        result.append(action)
    return tuple(result)


def orbit(histogram, actions):
    images = set()
    for action in actions:
        new = [0] * len(histogram)
        for label, count in enumerate(histogram):
            new[action[label]] = count
        images.add(tuple(new))
    return images


def moments_by_point_elimination(points, numerators=G):
    values = []
    for word in range(1 << len(points)):
        rank = dimension(point for i, point in enumerate(points) if word >> i & 1)
        values.append(numerators[rank] if rank < len(numerators) else 0)
    return values


def direct_masses(points, numerators=G):
    masses = moments_by_point_elimination(points, numerators)
    # In-place adjacent blocks rather than the producer's mask-filter loop.
    stride = 1
    while stride < len(masses):
        for start in range(0, len(masses), 2 * stride):
            for offset in range(stride):
                masses[start + offset] -= masses[start + offset + stride]
        stride *= 2
    return masses


def projection_rank(points):
    width = max(points, default=0).bit_length()
    linear = [sum(((point >> i) & 1) << column
                  for column, point in enumerate(points)) for i in range(width)]
    # The pinned coordinate is0, with value1: constant1 translates these evaluations.
    return dimension(linear + [a & b for a, b in combinations(linear, 2)])


def empty_formula(relation_basis):
    relations = span(relation_basis)
    nonzero = relations - {0}
    a3 = sum(word.bit_count() == 3 for word in nonzero)
    a5 = sum(word.bit_count() == 5 for word in nonzero)
    two_subspaces = {frozenset((0, a, b, a ^ b)) for a, b in combinations(nonzero, 2)}
    union_sizes = []
    for subspace in two_subspaces:
        support = 0
        for word in subspace:
            support |= word
        union_sizes.append(support.bit_count())
    b5 = union_sizes.count(5)
    b6 = union_sizes.count(6)
    support = 0
    for word in relations:
        support |= word
    c6 = int(len(relations) == 8 and support.bit_count() == 6)
    c7 = int(len(relations) == 8 and support.bit_count() == 7)
    return (46 - 7 * a3 - a5 + b5 + b6 - 4 * c6 - c7,
            {"A3": a3, "A5": a5, "B5": b5, "B6": b6, "C6": c6, "C7": c7})


def coefficient_controls():
    # Subspace-lattice inversion for dimensions0..3, independently evaluated.
    gaussian = ((1,), (1, 1), (1, 3, 1), (1, 7, 7, 1))
    mobius = (1, -1, 2, -8)
    answer = {}
    for d, minimum_support in enumerate((0, 3, 5, 6)):
        values = {}
        for support in range(minimum_support, 11):
            value = 0
            for size in range(support, 11):
                h = sum(gaussian[d][i] * mobius[d - i] *
                        (G[size - i] if 0 <= size - i < len(G) else 0)
                        for i in range(d + 1))
                value += (-1) ** size * comb(10 - support, size - support) * h
            if value:
                values[str(support)] = value
        answer[str(d)] = values
    expected = {"1": {"3": -7, "5": -1},
                "2": {"5": 1, "6": 1},
                "3": {"6": -4, "7": -1}}
    # The zero subspace has support exactly0; other values are irrelevant.
    require(answer["0"].get("0") == 46, "zero-subspace coefficient")
    for d in ("1", "2", "3"):
        require(answer[d] == expected[d], "relation-support coefficient")
    answer["0"] = {"0": 46}
    return answer


def negative_controls():
    d5_points = (1, 2, 4, 8, 12, 16, 20, 24, 28, 32)
    d5 = direct_masses(d5_points, (155, 35, 7, 1))
    d6_points = (1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64)
    d6 = direct_masses(d6_points)
    require(d5[3] == -1, "D5 ten-point negative control")
    require(d6[7] == -1, "D6 eleven-point negative control")
    return {
        "D5_ten_points": {"points": list(d5_points), "atom": [1, 2],
                          "numerator": d5[3], "denominator": 155},
        "D6_eleven_points": {"points": list(d6_points), "atom": [1, 2, 4],
                             "numerator": d6[7], "denominator": 651},
    }


def verify_certificate(certificate):
    try:
        require(type(certificate) is dict and set(certificate) ==
                {"schema", "width", "denominator", "rank_numerators", "coverage", "cases"},
                "certificate fields")
        require(certificate["schema"] == "d6-ten-point-complete-histogram-certificate-v1",
                "certificate schema")
        require(type(certificate["width"]) is int and certificate["width"] == 10, "width")
        require(type(certificate["denominator"]) is int and certificate["denominator"] == 651,
                "denominator")
        require(certificate["rank_numerators"] == list(G) and
                all(type(value) is int for value in certificate["rank_numerators"]), "moments")
        require(type(certificate["cases"]) is list, "case list")
        expected = {}
        actions = {}
        raw_counts = {}
        for d in range(4):
            all_histograms = list(histograms(10, 1 << d))
            raw_counts[d] = len(all_histograms)
            expected[d] = {h for h in all_histograms if admissible(h, d)}
            actions[d] = invertible_actions(d)
        covered = {d: set() for d in range(4)}
        orbit_counts = Counter()
        atoms = positives = formula_checks = 0
        empty_histogram = Counter()
        for case in certificate["cases"]:
            require(type(case) is dict and set(case) ==
                    {"corank", "histogram", "histogram_orbit_size", "relation_basis", "points",
                     "masses", "minimum_mass", "empty_mass", "mass_histogram"}, "case fields")
            d = case["corank"]
            require(type(d) is int and 0 <= d <= 3, "corank")
            h = case["histogram"]
            require(type(h) is list and len(h) == 1 << d and
                    all(type(v) is int and v >= 0 for v in h) and sum(h) == 10, "histogram")
            require(tuple(h) in expected[d], "inadmissible histogram")
            images = orbit(h, actions[d])
            require(tuple(h) == min(images), "noncanonical histogram")
            require(not (images & covered[d]), "duplicated orbit")
            require(type(case["histogram_orbit_size"]) is int and
                    case["histogram_orbit_size"] == len(images), "orbit cardinality")
            covered[d] |= images
            orbit_counts[d] += 1
            labels = [label for label, number in enumerate(h) for _ in range(number)]
            rows = [sum((1 << column) for column, label in enumerate(labels) if label >> i & 1)
                    for i in range(d)]
            require(case["relation_basis"] == rows and
                    all(type(v) is int for v in case["relation_basis"]), "relation rows")
            points = case["points"]
            require(type(points) is list and len(points) == 10 and
                    all(type(v) is int and 0 < v < (1 << (10 - d)) for v in points) and
                    len(set(points)) == 10, "point coordinates")
            require(dimension(points) == 10 - d, "point rank")
            for relation in rows:
                total = 0
                for column, point in enumerate(points):
                    if relation >> column & 1:
                        total ^= point
                require(total == 0, "wrong relation/kernel binding")
            masses = case["masses"]
            require(type(masses) is list and len(masses) == 1024 and
                    all(type(v) is int and v >= 0 for v in masses), "negative/malformed table")
            require(sum(masses) == 651, "normalization")
            reconstructed = list(masses)
            stride = 1
            while stride < 1024:
                for start in range(0, 1024, 2 * stride):
                    for offset in range(stride):
                        reconstructed[start + offset] += reconstructed[start + offset + stride]
                stride *= 2
            require(reconstructed == moments_by_point_elimination(points), "all rank moments")
            require(projection_rank(points) == 10, "pinned projection not full")
            require(case["minimum_mass"] == min(masses) and
                    type(case["minimum_mass"]) is int, "minimum")
            require(case["empty_mass"] == masses[0] and type(case["empty_mass"]) is int, "empty")
            require(case["mass_histogram"] ==
                    {str(k): v for k, v in sorted(Counter(masses).items())}, "mass histogram")
            formula, counts = empty_formula(rows)
            require(formula == masses[0], "analytic empty formula")
            require(counts["A3"] + counts["A5"] <= 4 and formula >= 14, "analytic coarse bound")
            formula_checks += 1
            empty_histogram[masses[0]] += 1
            atoms += len(masses)
            positives += sum(value > 0 for value in masses)
        require(covered == expected, "incomplete histogram coverage")
        coverage = [{"corank": d, "raw_histograms": raw_counts[d],
                     "admissible_histograms": len(expected[d]), "gl_order": len(actions[d]),
                     "orbits": orbit_counts[d]} for d in range(4)]
        require(certificate["coverage"] == coverage, "coverage counters")
        return {"valid": True, "status": "PASS", "coverage": coverage,
                "labelled_simple_relation_subspaces": {
                    str(d): sum(factorial(10) // prod(factorial(v) for v in h)
                                for h in expected[d]) // len(actions[d])
                    for d in range(4)},
                "tables": len(certificate["cases"]), "atom_moment_comparisons": atoms,
                "positive_atoms": positives, "projection_full_rank_controls": len(certificate["cases"]),
                "analytic_formula_checks": formula_checks,
                "empty_numerator_histogram": dict(sorted(empty_histogram.items())),
                "relation_lattice_coefficients": coefficient_controls(),
                "negative_controls": negative_controls()}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def main():
    path = Path(__file__).resolve().parent / "CERTIFICATE.json.gz"
    certificate = json.loads(gzip.decompress(path.read_bytes()))
    checked = verify_certificate(certificate)
    print(json.dumps(checked, indent=2))
    if not checked["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
