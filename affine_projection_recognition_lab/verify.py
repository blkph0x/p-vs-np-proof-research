"""Independent replay for the affine-projection recognition reduction."""

from __future__ import annotations

from itertools import product

SHARED = (0, 1, 2)
SELECTOR = 3
Y_OFFSET = 4


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

