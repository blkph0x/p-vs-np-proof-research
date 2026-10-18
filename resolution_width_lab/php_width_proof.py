"""Construct the uniform width-n resolution proof for PHP(n+1,n).

The construction follows Proposition 4.1 of Stefan Dantchev's
*On Resolution Complexity of Matching Principles*.  Pigeons and holes are
numbered from one.  A resolution event stores references to earlier events,
so the resulting object is both a proof and a replayable certificate.
"""
from __future__ import annotations

import json
import math
from hashlib import sha256
from itertools import permutations
from pathlib import Path


HERE = Path(__file__).resolve().parent


def normalize_clause(clause):
    values = {int(lit) for lit in clause}
    if 0 in values or any(-lit in values for lit in values):
        raise ValueError("clauses must be non-tautological and contain no zero")
    return tuple(sorted(values, key=lambda lit: (abs(lit), lit < 0)))


def variable(pigeon: int, hole: int, holes: int) -> int:
    if not 1 <= pigeon <= holes + 1 or not 1 <= hole <= holes:
        raise ValueError("pigeon or hole outside PHP(n+1,n)")
    return (pigeon - 1) * holes + hole


def php_formula(holes: int):
    """Return the standard injective PHP(n+1,n) CNF and variable count."""
    if type(holes) is not int or holes < 1:
        raise ValueError("holes must be a positive integer")
    clauses = []
    pigeons = holes + 1
    for pigeon in range(1, pigeons + 1):
        clauses.append(tuple(variable(pigeon, hole, holes)
                             for hole in range(1, holes + 1)))
    for pigeon in range(1, pigeons + 1):
        for left in range(1, holes + 1):
            for right in range(left + 1, holes + 1):
                clauses.append((-variable(pigeon, left, holes),
                                -variable(pigeon, right, holes)))
    for hole in range(1, holes + 1):
        for left in range(1, pigeons + 1):
            for right in range(left + 1, pigeons + 1):
                clauses.append((-variable(left, hole, holes),
                                -variable(right, hole, holes)))
    return holes * pigeons, tuple(normalize_clause(clause) for clause in clauses)


def expected_stage_count(holes: int, stage: int) -> int:
    """Number of injections from the first ``stage`` pigeons into the holes."""
    return math.factorial(holes) // math.factorial(holes - stage)


def expected_resolution_steps(holes: int) -> int:
    return holes * sum(expected_stage_count(holes, stage)
                       for stage in range(holes + 1))


class PHPWidthProof:
    """Build Dantchev's explicit width-n proof as a resolution DAG."""

    def __init__(self, holes: int):
        if type(holes) is not int or holes < 1:
            raise ValueError("holes must be a positive integer")
        self.holes = holes
        self.pigeons = holes + 1
        self.nvars, self.formula = php_formula(holes)
        self.formula_set = set(self.formula)
        self.events = []
        self._axiom_ids = {}
        self._max_width = 0
        self._resolution_steps = 0
        self.stages = {}

    def _record_axiom(self, clause, tag):
        clause = normalize_clause(clause)
        if clause not in self.formula_set:
            raise AssertionError("proof requested a clause outside the PHP axioms")
        if clause in self._axiom_ids:
            return self._axiom_ids[clause]
        event_id = len(self.events)
        self.events.append({"kind": "axiom", "clause": list(clause), "tag": tag})
        self._axiom_ids[clause] = event_id
        self._max_width = max(self._max_width, len(clause))
        return event_id

    def _record_resolution(self, left_id, right_id, pivot, *, stage, role):
        left = tuple(self.events[left_id]["clause"])
        right = tuple(self.events[right_id]["clause"])
        positive, negative = pivot, -pivot
        if positive in left and negative in right:
            result = normalize_clause((set(left) - {positive}) |
                                       (set(right) - {negative}))
        elif negative in left and positive in right:
            result = normalize_clause((set(left) - {negative}) |
                                       (set(right) - {positive}))
        else:
            raise AssertionError("resolution pivot is not present with opposite signs")
        if len(result) > self.holes:
            raise AssertionError("constructed proof exceeded width n")
        event_id = len(self.events)
        self.events.append({
            "kind": "resolve",
            "left": left_id,
            "right": right_id,
            "pivot": pivot,
            "clause": list(result),
            "stage": stage,
            "role": role,
        })
        self._resolution_steps += 1
        self._max_width = max(self._max_width, len(result))
        return event_id

    def _positive_axiom(self, pigeon):
        return self._record_axiom(
            tuple(variable(pigeon, hole, self.holes)
                  for hole in range(1, self.holes + 1)),
            {"type": "at_least_one", "pigeon": pigeon},
        )

    def _hole_axiom(self, left_pigeon, right_pigeon, hole):
        if left_pigeon > right_pigeon:
            left_pigeon, right_pigeon = right_pigeon, left_pigeon
        return self._record_axiom(
            (-variable(left_pigeon, hole, self.holes),
             -variable(right_pigeon, hole, self.holes)),
            {"type": "hole_exclusivity", "hole": hole,
             "pigeons": [left_pigeon, right_pigeon]},
        )

    def _stage_n_clause(self, injection):
        current = self._positive_axiom(self.pigeons)
        for pigeon, hole in enumerate(injection, start=1):
            current = self._record_resolution(
                current,
                self._hole_axiom(self.pigeons, pigeon, hole),
                variable(self.pigeons, hole, self.holes),
                stage=self.holes,
                role="stage_n",
            )
        return current

    def _transition_clause(self, stage, injection):
        next_pigeon = stage + 1
        current = self._positive_axiom(next_pigeon)
        used = set(injection)
        for pigeon, hole in enumerate(injection, start=1):
            current = self._record_resolution(
                current,
                self._hole_axiom(next_pigeon, pigeon, hole),
                variable(next_pigeon, hole, self.holes),
                stage=stage,
                role="stage_transition_positive",
            )
        for hole in range(1, self.holes + 1):
            if hole in used:
                continue
            extension = self.stages[stage + 1][injection + (hole,)]
            current = self._record_resolution(
                current,
                extension,
                variable(next_pigeon, hole, self.holes),
                stage=stage,
                role="stage_transition_kill",
            )
        return current

    def build(self):
        self.stages[self.holes] = {}
        for injection in permutations(range(1, self.holes + 1), self.holes):
            self.stages[self.holes][injection] = self._stage_n_clause(injection)
        for stage in range(self.holes - 1, -1, -1):
            self.stages[stage] = {}
            for injection in permutations(range(1, self.holes + 1), stage):
                self.stages[stage][injection] = self._transition_clause(stage, injection)
        final_id = self.stages[0][()]
        final_clause = tuple(self.events[final_id]["clause"])
        if final_clause != ():
            raise AssertionError("stage zero did not derive the empty clause")
        stage_counts = [len(self.stages[stage]) for stage in range(self.holes + 1)]
        expected_counts = [expected_stage_count(self.holes, stage)
                           for stage in range(self.holes + 1)]
        if stage_counts != expected_counts:
            raise AssertionError((stage_counts, expected_counts))
        return {
            "schema": "php_width_resolution_v1",
            "holes": self.holes,
            "pigeons": self.pigeons,
            "nvars": self.nvars,
            "formula": [list(clause) for clause in self.formula],
            "events": self.events,
            "final_event": final_id,
            "stage_counts": stage_counts,
            "resolution_steps": self._resolution_steps,
            "expected_resolution_steps": expected_resolution_steps(self.holes),
            # For n >= 2 this is exactly n.  PHP(2,1) is a degenerate
            # base case whose hole-exclusivity axiom already has width 2.
            "max_width": self._max_width,
            "status": "PASS",
        }


def build_php_width_proof(holes: int):
    return PHPWidthProof(holes).build()


def source_hashes(names=None):
    names = names or ("php_width_proof.py", "review_php_width_proof.py",
                      "run_php_width.py", "test_resolution.py",
                      "THEOREM.md", "PHP_WIDTH_REPORT.md")
    return {name: sha256((HERE / name).read_bytes()).hexdigest()
            for name in names if (HERE / name).is_file()}


def certificate_digest(certificate) -> str:
    payload = json.dumps(certificate, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()
