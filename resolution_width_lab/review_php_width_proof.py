"""Independent replay of the uniform PHP width certificate.

This module intentionally reconstructs the formula, literal numbering, and
resolution rule instead of importing ``php_width_proof``.
"""
from __future__ import annotations

import json
import math
from hashlib import sha256
from itertools import permutations
from pathlib import Path


HERE = Path(__file__).resolve().parent


def canonical(clause):
    values = {int(lit) for lit in clause}
    if 0 in values or any(-lit in values for lit in values):
        raise AssertionError("tautological or zero literal")
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def variable(pigeon, hole, holes):
    assert 1 <= pigeon <= holes + 1 and 1 <= hole <= holes
    return (pigeon - 1) * holes + hole


def reconstruct_formula(holes):
    clauses = []
    for pigeon in range(1, holes + 2):
        clauses.append(tuple(variable(pigeon, hole, holes)
                             for hole in range(1, holes + 1)))
    for pigeon in range(1, holes + 2):
        for left in range(1, holes + 1):
            for right in range(left + 1, holes + 1):
                clauses.append((-variable(pigeon, left, holes),
                                -variable(pigeon, right, holes)))
    for hole in range(1, holes + 1):
        for left in range(1, holes + 2):
            for right in range(left + 1, holes + 2):
                clauses.append((-variable(left, hole, holes),
                                -variable(right, hole, holes)))
    return {canonical(clause) for clause in clauses}


def expected_stage_count(holes, stage):
    return math.factorial(holes) // math.factorial(holes - stage)


def expected_steps(holes):
    return holes * sum(expected_stage_count(holes, stage)
                       for stage in range(holes + 1))


def replay(certificate):
    holes = certificate["holes"]
    assert certificate["pigeons"] == holes + 1
    assert certificate["nvars"] == holes * (holes + 1)
    formula = reconstruct_formula(holes)
    assert {canonical(clause) for clause in certificate["formula"]} == formula
    events = certificate["events"]
    clauses = []
    resolutions_by_stage = {stage: 0 for stage in range(holes + 1)}
    max_width = 0
    for index, event in enumerate(events):
        clause = canonical(event["clause"])
        if len(clause) > max(2, holes):
            raise AssertionError(("width", index, len(clause), max(2, holes)))
        max_width = max(max_width, len(clause))
        if event["kind"] == "axiom":
            if clause not in formula:
                raise AssertionError(("axiom", index, clause))
        elif event["kind"] == "resolve":
            left_id = event["left"]
            right_id = event["right"]
            pivot = int(event["pivot"])
            if not (0 <= left_id < index and 0 <= right_id < index):
                raise AssertionError(("parent", index, left_id, right_id))
            left, right = clauses[left_id], clauses[right_id]
            if pivot in left and -pivot in right:
                actual = canonical((set(left) - {pivot}) |
                                   (set(right) - {-pivot}))
            elif -pivot in left and pivot in right:
                actual = canonical((set(left) - {-pivot}) |
                                   (set(right) - {pivot}))
            else:
                raise AssertionError(("pivot", index, pivot, left, right))
            if actual != clause:
                raise AssertionError(("conclusion", index, actual, clause))
            stage = int(event["stage"])
            if stage not in resolutions_by_stage:
                raise AssertionError(("stage", index, stage))
            resolutions_by_stage[stage] += 1
        else:
            raise AssertionError(("kind", index, event["kind"]))
        clauses.append(clause)
    final_id = certificate["final_event"]
    assert 0 <= final_id < len(clauses)
    assert clauses[final_id] == ()
    assert certificate["stage_counts"] == [expected_stage_count(holes, stage)
                                             for stage in range(holes + 1)]
    assert certificate["resolution_steps"] == expected_steps(holes)
    assert sum(resolutions_by_stage.values()) == expected_steps(holes)
    assert all(count == holes * expected_stage_count(holes, stage)
               for stage, count in resolutions_by_stage.items())
    assert certificate["max_width"] == max_width == max(2, holes)
    return {
        "holes": holes,
        "status": "PASS",
        "event_count": len(events),
        "resolution_steps": len([event for event in events
                                  if event["kind"] == "resolve"]),
        "max_width": max_width,
        "final_clause": [],
        "stage_resolution_counts": resolutions_by_stage,
    }


def review_certificate(path=HERE / "PHP_WIDTH_CERTIFICATE_N6.json"):
    certificate = json.loads(Path(path).read_text(encoding="utf-8"))
    result = replay(certificate)
    result["certificate_sha256"] = sha256(Path(path).read_bytes()).hexdigest()
    return result


def review_saved_results():
    """Replay the saved certificate and verify every recorded source digest."""
    results_path = HERE / "PHP_WIDTH_RESULTS.json"
    saved = json.loads(results_path.read_text(encoding="utf-8"))
    result = review_certificate(HERE / saved["certificate"])
    for name, digest in saved["source_hashes"].items():
        actual = sha256((HERE / name).read_bytes()).hexdigest()
        assert actual == digest, (name, actual, digest)
    return {"status": "PASS", "certificate": result,
            "source_hashes_match": True}


if __name__ == "__main__":
    print(json.dumps(review_saved_results(), indent=2, sort_keys=True))
