"""Independent replay of mixed-relation frontier certificates."""
from hashlib import sha256
import json
from itertools import combinations, product
from pathlib import Path


HERE = Path(__file__).resolve().parent
H = {(0, 0, 0), (1, 1, 0), (0, 0, 1)}
A = {(0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 1), (1, 1, 1, 1)}


def expected(clauses, n_original):
    n = n_original + 2 * len(clauses)
    constraints = []
    for i, (x, y, w) in enumerate(clauses):
        z0, z1 = n_original + 2 * i, n_original + 2 * i + 1
        constraints.extend([((x, z0, z1), H), ((y, w, z0, z1), A)])
    order = tuple(range(n))
    pos = {v: i for i, v in enumerate(order)}
    boundaries = [tuple(v for v in order[:cut]
                       if any(v in scope and any(pos[u] >= cut for u in scope)
                              for scope, _ in constraints))
                  for cut in range(n + 1)]
    states = [()]
    cuts = [{"boundary": list(boundaries[0]), "states": [[]], "transitions": []}]
    for cut, variable in enumerate(order):
        old, new = boundaries[cut], boundaries[cut + 1]
        candidates = []
        for si, state in enumerate(states):
            assignment = dict(zip(old, state))
            for bit in (0, 1):
                assignment[variable] = bit
                good = True
                for scope, relation in constraints:
                    if max((pos[v] for v in scope), default=-1) != cut:
                        continue
                    if tuple(assignment[v] for v in scope) not in relation:
                        good = False
                        break
                if good:
                    candidates.append((si, bit, tuple(assignment[v] for v in new)))
        unique = sorted({state for _, _, state in candidates})
        index = {state: i for i, state in enumerate(unique)}
        transitions = [{"from": si, "bit": bit, "to": index[state]}
                       for si, bit, state in candidates]
        states = unique
        cuts.append({"boundary": list(new), "states": [list(s) for s in states],
                     "transitions": transitions})
    constraint_rows = [{"scope": list(scope),
                        "relation": [list(row) for row in sorted(relation)]}
                       for scope, relation in constraints]
    return {"n": n, "order": list(order), "constraints": constraint_rows, "cuts": cuts,
            "sat": bool(states and states == [()]),
            "max_width": max(map(len, boundaries), default=0),
            "max_states": max((len(c["states"]) for c in cuts), default=0)}


def main():
    triples = tuple(combinations(range(4), 3))
    artifact = json.loads((HERE / "MIXED_RELATION_DP_RESULTS.json").read_text(encoding="utf-8"))
    certificates = json.loads((HERE / "MIXED_RELATION_DP_CERTIFICATES.json").read_text(encoding="utf-8"))
    rows = []
    for mask in range(1 << len(triples)):
        clauses = tuple(triples[i] for i in range(len(triples)) if mask >> i & 1)
        cert = expected(clauses, 4)
        assert cert == certificates[mask]
        rows.append({"mask": mask, "clause_count": len(clauses),
                     "sat": cert["sat"], "max_width": cert["max_width"],
                     "max_states": cert["max_states"]})
    assert artifact["rows"] == rows
    assert artifact["all_results_match_direct"]
    for name, digest in artifact["source_sha256"].items():
        assert sha256((HERE / name).read_bytes()).hexdigest() == digest
    result = {"status": "PASS", "formula_count": len(rows),
              "certificates_match": True, "source_hashes_match": True}
    (HERE / "MIXED_RELATION_DP_REVIEW.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
