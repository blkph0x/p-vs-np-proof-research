"""Source-bound independent replay. Does not import the producer.

The expected case list is reconstructed here. A certificate cannot replace its
input by an easier formula. Projection is enumerated using Boolean tuples;
affinity is checked by ternary closure, independently of the producer's rank
test. This is conventional Python verification, not formal verification.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path


class VerificationError(ValueError):
    pass


def require_equal(actual, expected, field):
    # Canonical JSON comparison preserves bool-versus-int distinctions.
    if json.dumps(actual, sort_keys=True, separators=(",", ":")) != json.dumps(
            expected, sort_keys=True, separators=(",", ":")):
        raise VerificationError(field + " mismatch")


def truth(clauses, values):
    for clause in clauses:
        if not any(values[abs(lit) - 1] == (lit > 0) for lit in clause):
            return False
    return True


def binary_tuple(mask, width):
    return tuple(bool(mask & (2 ** i)) for i in range(width))


def expected_record(spec):
    p, q, clauses = spec["universal_width"], spec["existential_width"], spec["clauses"]
    if type(p) is not int or type(q) is not int or p < 0 or q < 0 or p + q > 12:
        raise VerificationError("review partition outside bounded domain")
    if not isinstance(clauses, list) or any(not isinstance(c, list) for c in clauses):
        raise VerificationError("malformed source")
    if any(type(lit) is not int or not 1 <= abs(lit) <= p + q
           for clause in clauses for lit in clause):
        raise VerificationError("invalid source literal")
    guarded = []
    for clause in clauses:
        shifted = [(1 if lit > 0 else -1) * (abs(lit) + 2) for lit in clause]
        guarded.append([-1, -2] + shifted)
    local = list(itertools.product((False, True), repeat=q))
    rows, evaluations = [], 0
    for u in range(2 ** p):
        hits = 0
        for v in local:
            hits += truth(clauses, binary_tuple(u, p) + v)
            evaluations += 1
        rows.append(hits)
    bits = []
    for x in range(2 ** (p + 2)):
        hits = 0
        for v in local:
            hits += truth(guarded, binary_tuple(x, p + 2) + v)
            evaluations += 1
        bits.append(int(hits != 0))
    points = [x for x, bit in enumerate(bits) if bit]
    # Independent algorithm: translate by one present point, then check pairs.
    # The tests also exhaustively compare with direct ternary closure.
    affine = bool(points) and all(bits[a ^ b ^ points[0]] for a in points for b in points)
    qbf = all(count > 0 for count in rows)
    if affine != qbf or not bits[0]:
        raise VerificationError("mathematical reduction does not hold on this input")
    violation = None
    if not qbf:
        u = next(i for i, count in enumerate(rows) if not count)
        parents = [4 * u, 4 * u + 1, 4 * u + 2]
        violation = {"universal_mask": u, "parents": parents, "missing": 4 * u + 3}
        if any(not bits[a] for a in parents) or bits[violation["missing"]]:
            raise VerificationError("closure witness is invalid")
    return {"status": "EXACT", "source": spec, "lifted_clauses": guarded,
            "source_witness_counts": rows, "qbf_true": qbf, "projection_bits": bits,
            "projection_affine": bool(affine), "ternary_violation": violation,
            "formula_evaluations": evaluations}


def verify_record(record, expected_source):
    """Reject missing/extra fields and all deviations from independently rebuilt input."""
    expected = expected_record(expected_source)
    if not isinstance(record, dict) or record.keys() != expected.keys():
        raise VerificationError("record fields mismatch")
    for field, value in expected.items():
        require_equal(record[field], value, field)
    return True


def spec(p, q, clauses):
    return {"universal_width": p, "existential_width": q, "clauses": clauses}


def expected_examples():
    return [spec(0, 0, []), spec(0, 0, [[]]),
            spec(1, 1, [[-1, 2], [1, -2]]), spec(1, 1, [[1]]),
            spec(1, 1, [[2], [-2]]), spec(2, 0, [[1, -1]]),
            spec(2, 0, [[1], [1]]), spec(0, 2, [[1, 2], [-1, -2]])]


def verify_artifact(artifact):
    totals = {"cases": 0, "true": 0, "false": 0, "formula_evaluations": 0}
    digest = hashlib.sha256()
    pool = [[-1, -2], [-1], [-1, 2], [-2], [], [2], [1, -2], [1], [1, 2]]
    for p in (0, 1, 2):
        for selection in range(512):
            clauses = [row[:] for i, row in enumerate(pool) if (selection >> i) & 1]
            result = expected_record(spec(p, 2 - p, clauses))
            encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
            digest.update((encoded + "\n").encode("ascii"))
            totals["cases"] += 1
            totals["true" if result["qbf_true"] else "false"] += 1
            totals["formula_evaluations"] += result["formula_evaluations"]
    expected = {"schema": "quantified-affine-boundary-v1",
                "status": "EXACT_FINITE_REDUCTION_CHECKS",
                "campaign": {**totals, "records_sha256": digest.hexdigest()},
                "examples": [expected_record(s) for s in expected_examples()],
                "scope": "Finite regression evidence; the all-input proof is in COMPLEXITY_THEOREM.md."}
    require_equal(artifact, expected, "complete artifact")
    return True


def adversarial_controls(artifact):
    """Every control invokes the complete replay, not an inequality comparison."""
    import copy
    verify_artifact(artifact)
    mutations = [
        ("guard sign", lambda a: a["examples"][2]["lifted_clauses"][0].__setitem__(0, 1)),
        ("omitted clause", lambda a: a["examples"][2]["lifted_clauses"].pop()),
        ("projection bit", lambda a: a["examples"][3]["projection_bits"].__setitem__(3, 1)),
        ("quantifier result", lambda a: a["examples"][2].__setitem__("qbf_true", False)),
        ("source substitution", lambda a: a["examples"][3]["source"].__setitem__("clauses", [])),
        ("counterexample", lambda a: a["examples"][3]["ternary_violation"].__setitem__("missing", 0)),
        ("campaign digest", lambda a: a["campaign"].__setitem__("records_sha256", "0" * 64)),
        ("work count", lambda a: a["examples"][0].__setitem__("formula_evaluations", 0)),
    ]
    rejected = []
    for label, mutate in mutations:
        corrupt = copy.deepcopy(artifact)
        mutate(corrupt)
        try:
            verify_artifact(corrupt)
        except VerificationError as exc:
            rejected.append({"control": label, "failure": str(exc)})
        else:
            raise VerificationError("mutation accepted: " + label)
    return rejected


if __name__ == "__main__":
    data = json.loads(Path(__file__).with_name("QUANTIFIED_RESULTS.json").read_text(encoding="utf-8"))
    verify_artifact(data)
    controls = adversarial_controls(data)
    print(json.dumps({"status": "VERIFIED", "campaign": data["campaign"],
                      "examples": len(data["examples"]), "rejected_controls": controls},
                     sort_keys=True))
