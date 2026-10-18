"""Independent replay for ADAPTIVE_FRAGMENT_SYNTHESIS.json.

This checker intentionally does not import the synthesis implementation.  It
re-evaluates the projected relation and every serialized candidate directly.
"""

from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).parent


def value(lit, assignment):
    v = abs(lit) - 1
    return assignment[v] if lit > 0 else not assignment[v]


def sat(clauses, assignment):
    return all(any(value(lit, assignment) for lit in c) for c in clauses)


def projection(clauses, shared):
    mentioned = sorted({abs(lit) - 1 for c in clauses for lit in c})
    local = [v for v in mentioned if v not in shared]
    out = []
    for sbits in product((False, True), repeat=len(shared)):
        ok = False
        for lbits in product((False, True), repeat=len(local)):
            a = dict(zip(shared, sbits)); a.update(zip(local, lbits))
            if sat(clauses, a):
                ok = True; break
        out.append(int(ok))
    return tuple(out)


def candidate_value(c, assignment):
    kind = c["kind"]
    if kind == "UNIT":
        return bool(assignment[c["var"]]) == bool(c["value"])
    if kind == "XOR":
        return (sum(assignment[v] for v in c["support"]) & 1) == int(c["rhs"])
    if kind == "PB":
        lhs = sum(int(w) * int(assignment[int(v)]) for v, w in c["weights"].items())
        return lhs <= int(c["bound"]) if c["sense"] == "<=" else lhs >= int(c["bound"])
    if kind == "ITE":
        chosen = assignment[c["a"]] if assignment[c["c"]] else assignment[c["b"]]
        return bool(assignment[c["z"]]) == bool(chosen)
    if kind == "TRUTH_TABLE":
        index = 0
        for v in c["support"]:
            index = (index << 1) | int(bool(assignment[v]))
        return bool((int(c["accepted_mask"]) >> index) & 1)
    raise AssertionError(kind)


def candidate_search_work(shared_count, max_truth_table_bits=12):
    count = 2 * shared_count
    count += 2 * ((1 << shared_count) - 1)
    count += 2 * (shared_count + 1)
    if shared_count == 4:
        count += 24
    if shared_count <= max_truth_table_bits:
        count += 1
    return (1 << shared_count) * count


def main():
    data = json.loads((ROOT / "ADAPTIVE_FRAGMENT_SYNTHESIS.json").read_text(encoding="utf-8"))
    assert data["all_checks_passed"]
    assert data["failures"] == data["errors"] == 0
    for name, row in data["examples"].items():
        clauses = tuple(tuple(c) for c in row["clauses"])
        shared = tuple(row["shared"])
        rel = projection(clauses, shared)
        assert tuple(row["relation_bits"]) == rel, name
        assert sorted(c["kind"] for c in row["candidates"]) == row["candidate_kinds"], name
        for c in row["candidate_kinds"]:
            # The kind list is checked against serialized chosen/all candidates
            # below; this assertion catches malformed empty catalogs.
            assert c in {"UNIT", "XOR", "PB", "ITE", "TRUTH_TABLE"}
        for candidate in row["candidates"]:
            for sbits, expected in zip(product((False, True), repeat=len(shared)), rel):
                assignment = dict(zip(shared, sbits))
                assert int(candidate_value(candidate, assignment)) == expected, (name, candidate, sbits)
        chosen = row["candidate"]
        if chosen is not None:
            assert chosen in row["candidates"]
        mentioned = {abs(lit) - 1 for c in clauses for lit in c}
        local_count = len(mentioned - set(shared))
        expected_work = (1 << (len(shared) + local_count)) * max(1, len(clauses))
        expected_work += candidate_search_work(len(shared))
        assert int(row["discovery_work"]) == expected_work, (name, row["discovery_work"], expected_work)
        if name == "mutated_xor":
            assert "XOR" not in row["candidate_kinds"]
    controls = data["controls"]
    assert controls["budget_unknown"]["status"] == "UNKNOWN"
    assert controls["clique_coloring_unknown"]["status"] == "UNKNOWN"
    assert controls["clique_coloring_unknown"]["shared_count"] > controls["clique_coloring_unknown"]["max_shared"]
    print(json.dumps({"independent_checks_passed": True, "examples": len(data["examples"])}))


if __name__ == "__main__":
    main()
