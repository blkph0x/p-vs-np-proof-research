"""Independent replay of the residual-equivalence reduction artifact."""

from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).parent


def sat(clauses, assignment):
    return all(any((assignment[abs(l) - 1] if l > 0 else not assignment[abs(l) - 1])
                   for l in c) for c in clauses)


def models(clauses, nvars):
    return [bits for bits in product((False, True), repeat=nvars) if sat(clauses, bits)]


def table(clauses, nvars, z):
    # z=0 leaves G(y); z=1 falsifies the added literal not z.
    values = models(clauses, nvars) if not z else []
    mask = 0
    for bits in values:
        idx = 0
        for bit in bits:
            idx = (idx << 1) | int(bit)
        mask |= 1 << idx
    return mask


def check_row(row):
    clauses = tuple(tuple(c) for c in row["g_clauses"])
    n = int(row["nvars"])
    ms = models(clauses, n)
    r0 = table(clauses, n, False)
    r1 = table(clauses, n, True)
    return (
        len(ms) == int(row["g_model_count"])
        and bool(ms) == bool(row["g_satisfiable"])
        and r0 == int(row["residual_z0"])
        and r1 == int(row["residual_z1"])
        and (r0 == r1) == bool(row["future_equivalent"])
        and bool(row["future_equivalent"]) == (not bool(ms))
        and int(row["boundary_width"]) == 1
    )


def main():
    artifact = json.loads((ROOT / "RESIDUAL_EQUIVALENCE_BARRIER.json").read_text(encoding="utf-8"))
    assert artifact["all_checks_passed"]
    records = artifact["records"]
    assert len(records) == 256
    assert all(check_row(row) for row in records)
    assert artifact["small_formula_count"] == len(records)
    assert artifact["small_satisfiable_count"] == sum(bool(r["g_satisfiable"]) for r in records)
    assert artifact["small_equivalent_count"] == sum(bool(r["future_equivalent"]) for r in records)
    assert all(check_row(row) for row in artifact["controls"])
    assert artifact["boundary_width"] == 1
    print(json.dumps({
        "independent_checks_passed": True,
        "records": len(records),
        "satisfiable": artifact["small_satisfiable_count"],
        "future_equivalent": artifact["small_equivalent_count"],
        "boundary_width": artifact["boundary_width"],
    }))


if __name__ == "__main__":
    main()

