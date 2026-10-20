"""Small nonlinear projection control for the affine baseline."""

from __future__ import annotations


def nonlinear_clauses() -> tuple[tuple[int, ...], ...]:
    """CNF for ``x0 OR (x1 AND x2)``."""
    return ((1, 2), (1, 3))


def projected_relation() -> tuple[int, ...]:
    bits = []
    for mask in range(8):
        x0, x1, x2 = ((mask >> index) & 1 for index in range(3))
        bits.append(int(bool(x0 or (x1 and x2))))
    return tuple(bits)


def is_affine_relation(bits: tuple[int, ...], width: int) -> bool:
    points = {mask for mask, bit in enumerate(bits) if bit}
    if not points:
        return True
    base = next(iter(points))
    translated = {point ^ base for point in points}
    return all(a ^ b in translated for a in translated for b in translated)


def classify() -> dict:
    bits = projected_relation()
    return {
        "status": "NOT_AFFINE" if not is_affine_relation(bits, 3) else "AFFINE",
        "clauses": [list(clause) for clause in nonlinear_clauses()],
        "projected_bits": list(bits),
    }

