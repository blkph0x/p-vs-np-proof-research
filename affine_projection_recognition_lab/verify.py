"""Independent replay for the affine-projection recognition reduction."""

from __future__ import annotations

from itertools import product

SHARED = (0, 1, 2)
SELECTOR = 3
Y_OFFSET = 4
TWO_SOURCE_SHARED = (0, 1, 2, 3)


def nonlinear_clauses():
    return ((1, 2), (1, 3))


def sat(clauses, assignment):
    return all(any((assignment[abs(literal) - 1] if literal > 0 else
                    not assignment[abs(literal) - 1]) for literal in clause)
               for clause in clauses)


def lift(source, nvars):
    clauses = []
    for clause in source:
        shifted = tuple(literal + Y_OFFSET if literal > 0 else literal - Y_OFFSET
                        for literal in clause)
        clauses.append((-SELECTOR - 1,) + shifted)
    clauses.extend((SELECTOR + 1,) + clause for clause in nonlinear_clauses())
    return tuple(clauses)


def projection(source, nvars):
    clauses = lift(source, nvars)
    bits = []
    for xmask in range(8):
        found = False
        for local_mask in range(1 << (nvars + 1)):
            assignment = {index: bool(xmask & (1 << index)) for index in range(3)}
            assignment[SELECTOR] = bool(local_mask & 1)
            for index in range(nvars):
                assignment[Y_OFFSET + index] = bool(local_mask & (1 << (index + 1)))
            if sat(clauses, assignment):
                found = True
                break
        bits.append(int(found))
    return tuple(bits)


def affine(bits):
    points = {mask for mask, bit in enumerate(bits) if bit}
    if not points:
        return False
    base = next(iter(points))
    translated = {point ^ base for point in points}
    return all(left ^ right in translated for left in translated for right in translated)


def point_clauses(selector, point):
    return tuple((-selector - 1, (index + 1) if point & (1 << index)
                  else -(index + 1)) for index in range(4))


def shift(clause, offset):
    return tuple(literal + offset if literal > 0 else literal - offset
                 for literal in clause)


def two_source_lift(a_source, a_nvars, b_source, b_nvars):
    selectors = tuple(range(4, 9))
    a_offset = 9
    b_offset = a_offset + a_nvars
    clauses = [tuple(index + 1 for index in selectors)]
    clauses.extend((-(selectors[left] + 1), -(selectors[right] + 1))
                   for left in range(5) for right in range(left + 1, 5))
    clauses.extend((-(selectors[0] + 1),) + clause
                    for clause in ((1, 2), (1, 3), (-4,)))
    for branch, point in zip((1, 2, 3), (0, 2, 4)):
        clauses.extend(point_clauses(selectors[branch], point))
        clauses.extend((-(selectors[branch] + 1),) + shift(clause, a_offset)
                        for clause in a_source)
    clauses.extend(point_clauses(selectors[4], 8))
    clauses.extend((-(selectors[4] + 1),) + shift(clause, b_offset)
                    for clause in b_source)
    return tuple(clauses)


def verify_two_source(record):
    try:
        a_nvars = int(record["a_nvars"])
        b_nvars = int(record["b_nvars"])
        a_source = tuple(tuple(int(literal) for literal in clause)
                         for clause in record["a_clauses"])
        b_source = tuple(tuple(int(literal) for literal in clause)
                         for clause in record["b_clauses"])
        a_models = sum(sat(a_source, {index: bool(mask & (1 << index))
                                      for index in range(a_nvars)})
                       for mask in range(1 << a_nvars))
        b_models = sum(sat(b_source, {index: bool(mask & (1 << index))
                                      for index in range(b_nvars)})
                       for mask in range(1 << b_nvars))
        clauses = two_source_lift(a_source, a_nvars, b_source, b_nvars)
        bits = []
        local_width = 5 + a_nvars + b_nvars
        for xmask in range(16):
            found = False
            for local_mask in range(1 << local_width):
                assignment = {index: bool(xmask & (1 << index)) for index in range(4)}
                for index in range(5):
                    assignment[4 + index] = bool(local_mask & (1 << index))
                for index in range(a_nvars):
                    assignment[9 + index] = bool(local_mask & (1 << (5 + index)))
                for index in range(b_nvars):
                    assignment[9 + a_nvars + index] = bool(local_mask & (1 << (5 + a_nvars + index)))
                if sat(clauses, assignment):
                    found = True
                    break
            bits.append(int(found))
        expected_class = "AFFINE" if affine(tuple(bits)) else "NON_AFFINE_OR_EMPTY"
        return (record["shared_width"] == 4 and
                record["a_model_count"] == a_models and
                record["b_model_count"] == b_models and
                record["a_satisfiable"] == bool(a_models) and
                record["b_satisfiable"] == bool(b_models) and
                record["projection_bits"] == bits and
                record["projection_class"] == expected_class and
                record["lifted_clauses"] == [list(clause) for clause in clauses])
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def verify(record):
    try:
        nvars = int(record["source_nvars"])
        source = tuple(tuple(int(literal) for literal in clause)
                       for clause in record["source_clauses"])
        bits = projection(source, nvars)
        expected_models = sum(sat(source, {index: bool(mask & (1 << index))
                                            for index in range(nvars)})
                              for mask in range(1 << nvars))
        return (record["shared_width"] == 3 and
                record["projection_bits"] == list(bits) and
                record["source_model_count"] == expected_models and
                record["source_satisfiable"] == bool(expected_models) and
                record["projection_class"] == ("AFFINE" if affine(bits) else "NON_AFFINE_OR_EMPTY") and
                record["lifted_clauses"] == [list(clause) for clause in lift(source, nvars)])
    except (KeyError, TypeError, ValueError, IndexError):
        return False
