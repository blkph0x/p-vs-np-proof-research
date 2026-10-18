"""A source-bound barrier for exact future-equivalence discovery.

For an arbitrary CNF G(y), form F(z,y) = G(y) AND (not z).  At the cut whose
boundary is z, the two residual functions are G and False.  They are equal iff
G is unsatisfiable.  Thus exact residual-equivalence testing is coNP-hard even
when the boundary has one Boolean variable.  The implementation below only
performs finite truth-table replay; it does not infer the complexity result from
those finite cases.
"""

from __future__ import annotations

from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def normalize_clause(clause):
    vals = tuple(sorted(set(int(x) for x in clause), key=lambda z: (abs(z), z < 0)))
    if any(-x in vals for x in vals):
        return None
    return vals


def cnf_sat(clauses, assignment):
    for clause in clauses:
        if not any((assignment[abs(lit) - 1] if lit > 0 else not assignment[abs(lit) - 1])
                   for lit in clause):
            return False
    return True


def satisfying_assignments(clauses, nvars):
    return [bits for bits in product((False, True), repeat=nvars)
            if cnf_sat(clauses, bits)]


def residual_truth_table(g_clauses, nvars, z_value):
    """Truth table over y for F(z,y)=G(y) AND not z."""
    rows = satisfying_assignments(g_clauses, nvars) if not z_value else []
    mask = 0
    for bits in rows:
        index = 0
        for bit in bits:
            index = (index << 1) | int(bit)
        mask |= 1 << index
    return mask


def exact_equivalence_record(g_clauses, nvars):
    rows = satisfying_assignments(g_clauses, nvars)
    r0 = residual_truth_table(g_clauses, nvars, False)
    r1 = residual_truth_table(g_clauses, nvars, True)
    return {
        "nvars": nvars,
        "g_clauses": [list(c) for c in g_clauses],
        "g_satisfiable": bool(rows),
        "g_model_count": len(rows),
        "residual_z0": r0,
        "residual_z1": r1,
        "future_equivalent": r0 == r1,
        "boundary_width": 1,
    }


def all_non_tautological_clauses(nvars):
    """Enumerate every nonempty clause over n variables without tautologies."""
    out = []
    for choices in product((-1, 0, 1), repeat=nvars):
        if all(c == 0 for c in choices):
            continue
        out.append(tuple((i + 1) * c for i, c in enumerate(choices) if c))
    return tuple(out)


def exhaustive_small_records(nvars=2):
    pool = all_non_tautological_clauses(nvars)
    records = []
    for selector in range(1 << len(pool)):
        clauses = tuple(pool[i] for i in range(len(pool)) if (selector >> i) & 1)
        records.append(exact_equivalence_record(clauses, nvars))
    return records


def verify_reduction_record(record):
    clauses = tuple(tuple(c) for c in record["g_clauses"])
    nvars = int(record["nvars"])
    rows = satisfying_assignments(clauses, nvars)
    r0 = residual_truth_table(clauses, nvars, False)
    r1 = residual_truth_table(clauses, nvars, True)
    return (
        bool(rows) == bool(record["g_satisfiable"])
        and len(rows) == int(record["g_model_count"])
        and r0 == int(record["residual_z0"])
        and r1 == int(record["residual_z1"])
        and (r0 == r1) == bool(record["future_equivalent"])
        and int(record["boundary_width"]) == 1
        and bool(record["future_equivalent"]) == (not bool(rows))
    )


def build_artifact():
    records = exhaustive_small_records(2)
    controls = [
        exact_equivalence_record((), 3),
        exact_equivalence_record(((1,), (-1,)), 1),
        exact_equivalence_record(((1, 2), (-1, 2), (1, -2), (-1, -2)), 2),
        exact_equivalence_record(((1, 2), (-1, 2), (1, -2)), 2),
    ]
    assert all(verify_reduction_record(row) for row in records + controls)
    return {
        "all_checks_passed": True,
        "theorem_construction": "F(z,y) = G(y) AND NOT z",
        "boundary_width": 1,
        "small_nvars": 2,
        "small_formula_count": len(records),
        "small_equivalent_count": sum(r["future_equivalent"] for r in records),
        "small_satisfiable_count": sum(r["g_satisfiable"] for r in records),
        "controls": controls,
        "records": records,
    }


def write_artifact():
    artifact = build_artifact()
    path = ROOT / "RESIDUAL_EQUIVALENCE_BARRIER.json"
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


if __name__ == "__main__":
    print(json.dumps(write_artifact(), indent=2))

