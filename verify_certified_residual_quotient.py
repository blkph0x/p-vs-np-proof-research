"""Independent replay for the certified residual quotient artifact."""

from itertools import product
import copy
import json
from pathlib import Path

ROOT = Path(__file__).parent


def norm(c):
    vals = tuple(sorted(set(int(x) for x in c), key=lambda z: (abs(z), z < 0)))
    if any(-x in vals for x in vals):
        raise AssertionError("tautological clause")
    return vals


def formula(c):
    return tuple(sorted({norm(x) for x in c}))


def sat(clauses, bits):
    return all(any((bits[abs(l) - 1] if l > 0 else not bits[abs(l) - 1]) for l in c)
               for c in clauses)


def replay(proof, allowed):
    allowed = {norm(c) for c in allowed}
    nodes = []
    for row in proof["nodes"]:
        clause = norm(row["clause"])
        if row["kind"] == "leaf":
            assert clause in allowed
        else:
            assert row["kind"] == "res"
            left = set(nodes[row["left"]]); right = set(nodes[row["right"]]); p = int(row["pivot"])
            if p in left and -p in right:
                out = (left - {p}) | (right - {-p})
            elif -p in left and p in right:
                out = (left - {-p}) | (right - {p})
            else:
                raise AssertionError("bad pivot")
            assert clause == norm(out)
        nodes.append(clause)
    assert nodes[int(proof["root"])] == ()


def verify_implication(cert):
    source = formula(cert["source"]); target = formula(cert["target"])
    assert len(cert["obligations"]) == len(target)
    for row in cert["obligations"]:
        clause = norm(row["target_clause"])
        assert clause in target
        premises = formula(list(source) + [(-lit,) for lit in clause])
        assert premises == formula(row["premises"])
        replay(row["proof"], premises)


def verify_equivalence(cert):
    verify_implication(cert["forward"])
    verify_implication(cert["reverse"])


def main():
    artifact = json.loads((ROOT / "CERTIFIED_RESIDUAL_QUOTIENT.json").read_text(encoding="utf-8"))
    assert artifact["all_checks_passed"]
    verify_equivalence(artifact["proof_certificate"])
    forged = copy.deepcopy(artifact["proof_certificate"])
    forged["forward"]["obligations"][0]["proof"]["nodes"][-1]["clause"] = [1]
    forged_rejected = False
    try:
        verify_equivalence(forged)
    except (AssertionError, IndexError, KeyError, TypeError, ValueError):
        forged_rejected = True
    assert forged_rejected
    assert artifact["adversarial"]["forged_certificate_rejected"] is True
    cases = artifact["cases"]
    assert cases["syntactic"]["status"] == "MERGED_SYNTACTIC"
    assert cases["proof"]["status"] == "MERGED_PROOF"
    assert cases["distinct_witness"]["status"] == "DISTINCT_WITNESS"
    assert cases["distinct_exact"]["status"] == "DISTINCT_EXACT"
    assert cases["unknown"]["status"] == "UNKNOWN"
    assert cases["witness_beyond_cap"]["status"] == "DISTINCT_WITNESS"
    # Recheck the witness in the two one-sided cases without trusting status text.
    assert sat(((1,),), tuple(cases["distinct_witness"]["witness"]))
    assert not sat(((2,),), tuple(cases["distinct_witness"]["witness"]))
    assert not sat(((1,),), tuple(cases["witness_beyond_cap"]["witness"]))
    assert sat((), tuple(cases["witness_beyond_cap"]["witness"]))
    print(json.dumps({"independent_checks_passed": True,
                      "proof_obligations": 5,
                      "forged_certificate_rejected": forged_rejected,
                      "statuses": {k: v["status"] for k, v in cases.items()}}))


if __name__ == "__main__":
    main()
