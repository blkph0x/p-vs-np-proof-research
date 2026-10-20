"""Independent replay of the saved Reed--Muller local-marginal controls.

This file intentionally reconstructs the generator rows, dual space, witness,
and small support replay without importing reed_muller.py.
"""

import json
from itertools import combinations
from fractions import Fraction
from math import comb
from pathlib import Path


def masks(m, degree):
    result = []
    for size in range(degree + 1):
        result.extend(sum(1 << index for index in support)
                      for support in combinations(range(m), size))
    return tuple(result)


def row(m, mask):
    return sum(1 << point for point in range(1 << m)
               if point & mask == mask)


def rank(rows):
    pivots = {}
    for value in rows:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


def dual_basis(rows, n):
    reduced = list(rows)
    pivots = []
    pivot_row = 0
    for bit in range(n):
        index = next((i for i in range(pivot_row, len(reduced))
                      if reduced[i] >> bit & 1), None)
        if index is None:
            continue
        reduced[pivot_row], reduced[index] = reduced[index], reduced[pivot_row]
        for i in range(len(reduced)):
            if i != pivot_row and reduced[i] >> bit & 1:
                reduced[i] ^= reduced[pivot_row]
        pivots.append(bit)
        pivot_row += 1
    result = []
    for free in range(n):
        if free in pivots:
            continue
        value = 1 << free
        for index, pivot in enumerate(pivots):
            if reduced[index] >> free & 1:
                value |= 1 << pivot
        result.append(value)
    return tuple(result)


def span(rows, limit=1 << 20):
    if len(rows) >= 21:
        return None
    words = [0]
    for value in rows:
        words += [word ^ value for word in tuple(words)]
    return tuple(sorted(words)) if len(words) <= limit else None


def witness_masks(m, degree, pin):
    required = pin & ((1 << degree) - 1)
    return tuple(mask for mask in range(1 << degree)
                 if mask & required == required)


def affine_minimum_support(m, codimension, pin):
    fixed = (1 << codimension) - 1
    return sum(1 << point for point in range(1 << m)
               if (point & fixed) == (pin & fixed))


def gaussian_binomial_2(n, k):
    row = [0] * (k + 1)
    row[0] = 1
    for size in range(1, n + 1):
        next_row = row[:]
        for width in range(1, min(size, k) + 1):
            previous = row[width] if width < size else 0
            next_row[width] = row[width - 1] + (1 << width) * previous
        row = next_row
    return row[k]


def verify_boundary_lower_bounds():
    cases = []
    for s in range(1, 9):
        m, r = 2 * s + 1, s
        total = gaussian_binomial_2(m, r + 1)
        through_other = gaussian_binomial_2(m - 1, r)
        ratio = Fraction(total, through_other)
        expected_ratio = Fraction((1 << m) - 1, (1 << (r + 1)) - 1)
        assert ratio == expected_ratio
        bound = Fraction(1) + ratio
        cases.append({"s": s, "n": 1 << m, "distance": 1 << (r + 1),
                      "level": (1 << (r + 1)) - 1,
                      "minimum_check_count": total,
                      "checks_through_nonpin": through_other,
                      "boundary_local_optimum": str(bound),
                      "zero_mass_at_boundary": "0"})
    return cases


def verify_boundary_and_scaling():
    boundary_cases = 0
    scaling_cases = []
    for s in range(1, 7):
        m, r, n = 2 * s + 1, s, 1 << (2 * s + 1)
        distance = 1 << (s + 1)
        rows = tuple(row(m, mask) for mask in masks(m, r))
        row_by_mask = dict(zip(masks(m, r), rows))
        for pin in (0, 1, n - 1):
            support = affine_minimum_support(m, r, pin)
            witness = 0
            for mask in witness_masks(m, r, pin):
                witness ^= row_by_mask[mask]
            assert support == witness
            assert support.bit_count() == distance
            assert support >> pin & 1
            assert all((support & value).bit_count() % 2 == 0 for value in rows)
            assert (support ^ (1 << pin)).bit_count() == distance - 1
            boundary_cases += 1
        level = distance - 2
        top_scope = comb(n, level)
        scopes = sum(comb(n, size) for size in range(level + 1))
        atoms = sum(comb(n, size) * (1 << size)
                    for size in range(level + 1))
        top_atoms = (1 << level) * top_scope
        supported_atoms = sum(
            comb(n - 1, size) * (1 << size)
            + (comb(n - 1, size - 1) * (1 << (size - 1)) if size else 0)
            for size in range(level + 1)
        )
        top_supported = (1 << level) * comb(n - 1, level)
        assert top_scope <= scopes <= (level + 1) * top_scope
        assert top_atoms <= atoms <= (level + 1) * top_atoms
        assert top_supported <= supported_atoms
        assert supported_atoms <= (level + 1) * (1 << (level + 1)) * comb(n - 1, level)
        scaling_cases.append({"s": s, "n": n, "level": level,
                              "scope_count": scopes,
                              "atom_slot_envelope": atoms,
                              "supported_atom_count": supported_atoms})
    return boundary_cases, scaling_cases


def verify_case(saved):
    cert = saved["certificate"]
    s = cert["s"]
    assert cert["family"] == "RM(s,2s+1)"
    m, r, n = 2 * s + 1, s, 1 << (2 * s + 1)
    dimension = sum(comb(m, degree) for degree in range(r + 1))
    distance = 1 << (s + 1)
    assert (cert["m"], cert["r"], cert["n"]) == (m, r, n)
    assert cert["dimension"] == dimension
    assert cert["distance"] == distance
    assert cert["dual_order"] == r
    assert cert["dual_distance"] == distance
    generator_masks = masks(m, r)
    rows = tuple(row(m, mask) for mask in generator_masks)
    assert tuple(cert["generator_masks"]) == generator_masks
    assert tuple(cert["generator_rows"]) == rows
    assert rank(rows) == dimension == n // 2
    assert all((left & right).bit_count() % 2 == 0
               for left in rows for right in rows)
    assert tuple(cert["dual_basis"]) == dual_basis(rows, n)
    assert len(cert["dual_basis"]) == n // 2
    assert cert["self_dual"] is True

    pin = cert["pin"]
    level = cert["level"]
    assert 0 <= pin < n
    assert level == distance - 2 == cert["theorem_level_bound"]
    assert cert["pinned_integer_optimum"] == distance
    assert cert["relaxation_point_weight"] == 1
    assert cert["integrality_gap"] == distance
    expected_masks = witness_masks(m, r, pin)
    assert tuple(cert["witness_monomial_masks"]) == expected_masks
    witness = 0
    row_by_mask = dict(zip(generator_masks, rows))
    for mask in expected_masks:
        witness ^= row_by_mask[mask]
    assert cert["minimum_weight_witness"] == witness
    assert witness.bit_count() == distance
    assert witness >> pin & 1
    assert cert["witness_weight"] == distance
    assert cert["scope_count"] == sum(comb(n, size) for size in range(level + 1))
    assert cert["atom_slot_count"] == sum(
        comb(n, size) * (1 << size) for size in range(level + 1))

    words = span(rows)
    summary = cert["word_enumeration"]
    if summary["status"] == "EXACT":
        assert words is not None
        pinned = [word for word in words if word >> pin & 1]
        nonzero = [word for word in words if word]
        assert summary == {
            "status": "EXACT",
            "word_count": len(words),
            "minimum_distance": min(word.bit_count() for word in nonzero),
            "pinned_minimum": min(word.bit_count() for word in pinned),
        }
    else:
        assert summary == {"status": "THEOREM_ONLY", "word_count": None,
                           "minimum_distance": None, "pinned_minimum": None}

    if cert["enumerated_support"] is not None:
        assert words is not None
        observed = True
        checked = 0
        target = 1 << pin
        for mask in range(1 << n):
            if mask.bit_count() > level:
                continue
            scope = tuple(index for index in range(n) if mask >> index & 1)
            wanted = tuple((target >> index) & 1 for index in scope)
            if not any(tuple((word >> index) & 1 for index in scope) == wanted
                       and word >> pin & 1 for word in words):
                observed = False
                break
            checked += 1
        assert cert["enumerated_support"] is observed
        assert cert["checked_scopes"] == checked
        assert saved["verification"]["support_replay"] is observed
    else:
        assert cert["checked_scopes"] is None
        assert cert["support_counterexample"] is None
    assert saved["verification"]["valid"] is True
    return {
        "name": saved["name"],
        "s": s,
        "n": n,
        "dimension": dimension,
        "distance": distance,
        "dual_distance": distance,
        "level": level,
        "theorem_level_valid": level <= distance - 2,
        "pinned_integer_optimum": distance,
        "integrality_gap": distance,
        "support_replay": cert["enumerated_support"],
    }


def main():
    saved = json.loads(Path("REED_MULLER_RESULTS.json").read_text(encoding="utf-8"))
    rows = [verify_case(case) for case in saved["cases"]]
    boundary_cases, scaling_cases = verify_boundary_and_scaling()
    boundary_lower_bound_cases = verify_boundary_lower_bounds()
    assert saved["all_valid"] is True
    assert rows == [
        {"name": "RM(1,3)_level_2", "s": 1, "n": 8, "dimension": 4,
         "distance": 4, "dual_distance": 4, "level": 2,
         "theorem_level_valid": True, "pinned_integer_optimum": 4,
         "integrality_gap": 4, "support_replay": True},
        {"name": "RM(2,5)_level_6", "s": 2, "n": 32, "dimension": 16,
         "distance": 8, "dual_distance": 8, "level": 6,
         "theorem_level_valid": True, "pinned_integer_optimum": 8,
         "integrality_gap": 8, "support_replay": None},
        {"name": "RM(3,7)_level_14", "s": 3, "n": 128, "dimension": 64,
         "distance": 16, "dual_distance": 16, "level": 14,
         "theorem_level_valid": True, "pinned_integer_optimum": 16,
         "integrality_gap": 16, "support_replay": None},
    ]
    output = {
        "status": "VERIFIED_INDEPENDENT_REED_MULLER_LOCAL_MARGINAL",
        "case_count": len(rows),
        "rows": rows,
        "self_dual_family": True,
        "scope_replay_cases": [row["name"] for row in rows if row["support_replay"]],
        "theorem_only_larger_case": "RM(3,7)",
        "boundary_obstruction_cases": boundary_cases,
        "boundary_lower_bound_cases": boundary_lower_bound_cases,
        "scaling_bound_cases": scaling_cases,
    }
    Path("REED_MULLER_INDEPENDENT_REVIEW.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    Path("REED_MULLER_INDEPENDENT_REVIEW.md").write_text(
        "# Independent Reed--Muller review\n\n"
        "Reconstructed the RM(s,2s+1) evaluation rows, rank, self-orthogonality, "
        "dual basis, affine minimum-weight witness, exact small word spans, and "
        "the level-two local support replay for RM(1,3). RM(2,5) is exactly "
        "enumerated over its 65,536 codewords; RM(3,7) uses the stated distance "
        "theorem because its 64-dimensional span is intentionally not expanded. "
        "The replay also reconstructs minimum dual supports through three pins "
        "for s=1..5, checks the exact boundary incidence values through s=8, "
        "and checks the exact all-scope size inequalities through s=6.\n"
    , encoding="utf-8")
    print(json.dumps({"status": output["status"], "case_count": len(rows),
                      "levels": [row["level"] for row in rows],
                      "boundary_obstruction_cases": boundary_cases,
                      "boundary_lower_bound_cases": len(boundary_lower_bound_cases),
                      "scaling_bound_cases": len(scaling_cases)}))


if __name__ == "__main__":
    main()
