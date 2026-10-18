"""Compact exact marginalization for affine-support quadratic phases.

The variable order is ``boundary`` followed by ``internal``.  A summary is

    scalar * 1[equations] * (-1)**phase,

where every equation is binary affine and every phase monomial has degree at
most two.  Internal variables are eliminated one at a time.  A pivot equation
substitutes one bit without changing the scalar; a free bit contributes a
factor two and adds the affine equation that its phase coefficient must be
zero.  The producer emits the elimination trace and the verifier replays it
from the externally supplied request.

This is an exact symbolic primitive, not a SAT algorithm.  It never expands a
boundary truth table, and a later sum of many such summaries can still have
exponentially many terms.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json


LIMITS = {
    "max_variables": 20000,
    "max_equations": 40000,
    "max_phase_terms": 40000,
    "max_work": 2_000_000,
    "max_integer_bits": 100000,
}


class Exhausted(Exception):
    """A declared resource cap stopped an exact computation."""


class Invalid(Exception):
    """Malformed symbolic input or certificate."""


class Budget:
    def __init__(self, overrides=None):
        overrides = {} if overrides is None else dict(overrides)
        if set(overrides) - set(LIMITS):
            raise ValueError("unknown budget")
        self.limits = {**LIMITS, **overrides}
        if any(type(value) is not int or value < 0 for value in self.limits.values()):
            raise ValueError("caps must be nonnegative integers")
        self.work = 0
        self.bits = 0

    def tick(self, amount=1):
        if type(amount) is not int or amount < 0:
            raise ValueError("work amount must be a nonnegative integer")
        self.work += amount
        if self.work > self.limits["max_work"]:
            raise Exhausted("work budget")

    def rational(self, value):
        value = _ratio(value)
        self.bits = max(self.bits, value.numerator.bit_length(), value.denominator.bit_length())
        if self.bits > self.limits["max_integer_bits"]:
            raise Exhausted("integer bit budget")
        return value

    def stats(self):
        return {"work": self.work, "max_integer_bits": self.bits}


def _ratio(value):
    if type(value) is int:
        return Fraction(value)
    if type(value) is Fraction:
        return value
    if (type(value) in (list, tuple) and len(value) == 2
            and all(type(x) is int for x in value) and value[1] > 0):
        return Fraction(value[0], value[1])
    raise Invalid("expected an exact rational")


def _pack(value):
    return [value.numerator, value.denominator]


def _toggle(target, value):
    if value in target:
        target.remove(value)
    else:
        target.add(value)


def _canonical_equations(equations, budget):
    out = set()
    for row in equations:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise Invalid("equations must contain [mask, rhs] rows")
        mask, rhs = row
        if type(mask) is not int or mask < 0 or type(rhs) is not int or rhs not in (0, 1):
            raise Invalid("invalid binary equation")
        if mask == 0 and rhs == 0:
            continue
        out.add((mask, rhs))
        budget.tick()
    if len(out) > budget.limits["max_equations"]:
        raise Exhausted("equation budget")
    return sorted(out)


def _canonical_phase(phase, n, budget):
    if type(phase) not in (list, tuple):
        raise Invalid("phase must be a list of monomial masks")
    out = set()
    for term in phase:
        if type(term) is not int or term < 0 or term >= 1 << n or term.bit_count() > 2:
            raise Invalid("phase monomials must have degree at most two")
        _toggle(out, term)
        budget.tick()
    if len(out) > budget.limits["max_phase_terms"]:
        raise Exhausted("phase budget")
    return sorted(out)


def _request(request, budget):
    if type(request) is not dict or set(request) != {
            "schema", "boundary", "internal", "equations", "phase", "scalar"}:
        raise Invalid("wrong request schema")
    if request["schema"] != "weighted_affine_marginal_v1":
        raise Invalid("wrong request schema")
    boundary, internal = request["boundary"], request["internal"]
    if type(boundary) not in (list, tuple) or type(internal) not in (list, tuple):
        raise Invalid("variable IDs must be lists")
    if any(type(x) is not str or not x for x in list(boundary) + list(internal)):
        raise Invalid("variable IDs must be nonempty strings")
    if len(set(boundary)) != len(boundary) or len(set(internal)) != len(internal):
        raise Invalid("variable IDs must be distinct within each side")
    if set(boundary) & set(internal):
        raise Invalid("boundary and internal IDs must be disjoint")
    n = len(boundary) + len(internal)
    if n > budget.limits["max_variables"]:
        raise Exhausted("variable budget")
    equations = _canonical_equations(request["equations"], budget)
    if any(mask.bit_length() > n for mask, _ in equations):
        raise Invalid("equation mask exceeds variable count")
    phase = _canonical_phase(request["phase"], n, budget)
    scalar = budget.rational(_ratio(request["scalar"]))
    return {
        "schema": request["schema"], "boundary": list(boundary),
        "internal": list(internal), "equations": equations,
        "phase": phase, "scalar": scalar,
    }


def _hash_request(request):
    encoded = json.dumps(request, separators=(",", ":"), sort_keys=True).encode()
    return sha256(b"weighted-affine-marginal-request-v1\0" + encoded).hexdigest()


def _substitute(phase, variable, affine_mask, affine_rhs, budget):
    """Substitute variable = affine_rhs + affine_mask*x in a degree-two phase."""
    bit = 1 << variable
    out = set()
    for term in phase:
        if not term & bit:
            _toggle(out, term)
            continue
        remainder = term ^ bit
        if affine_rhs:
            _toggle(out, remainder)
        for j in range(affine_mask.bit_length()):
            if affine_mask >> j & 1:
                _toggle(out, remainder | (1 << j))
        budget.tick(1 + affine_mask.bit_count())
    if len(out) > budget.limits["max_phase_terms"]:
        raise Exhausted("phase budget")
    return sorted(out)


def _pivot(equations, phase, variable, pivot, budget):
    mask, rhs = pivot
    bit = 1 << variable
    if not mask & bit:
        raise Invalid("pivot row does not contain the eliminated variable")
    affine_mask = mask ^ bit
    reduced = []
    used = False
    for row_mask, row_rhs in equations:
        if (row_mask, row_rhs) == pivot and not used:
            used = True
            continue
        if row_mask & bit:
            row_mask ^= mask
            row_rhs ^= rhs
        reduced.append((row_mask, row_rhs))
        budget.tick()
    if not used:
        raise Invalid("pivot row is not present")
    return _canonical_equations(reduced, budget), _substitute(
        phase, variable, affine_mask, rhs, budget)


def _free(equations, phase, variable, budget):
    bit = 1 << variable
    if any(mask & bit for mask, _ in equations):
        raise Invalid("free step used while a support equation contains the variable")
    coefficient = set()
    remaining = set()
    for term in phase:
        if term & bit:
            _toggle(coefficient, term ^ bit)
        else:
            _toggle(remaining, term)
        budget.tick()
    mask = 0
    rhs = 0
    for term in coefficient:
        if term == 0:
            rhs ^= 1
        elif term.bit_count() == 1:
            mask ^= term
        else:
            raise Invalid("phase coefficient is not affine")
    if mask or rhs:
        equations = list(equations) + [(mask, rhs)]
    return _canonical_equations(equations, budget), sorted(remaining)


def _state_summary(boundary, equations, phase, scalar):
    return {
        "schema": "weighted_affine_summary_v1",
        "boundary": list(boundary),
        "equations": [[mask, rhs] for mask, rhs in equations],
        "phase": list(phase),
        "scalar": _pack(scalar),
    }


def marginalize(request, **caps):
    """Produce an exact compact boundary summary or UNKNOWN on a cap."""
    budget = Budget(caps)
    try:
        net = _request(request, budget)
        equations, phase, scalar = net["equations"], net["phase"], net["scalar"]
        steps = []
        base = len(net["boundary"])
        for offset, name in enumerate(net["internal"]):
            variable = base + offset
            pivot = next((row for row in equations if row[0] >> variable & 1), None)
            if pivot is None:
                equations, phase = _free(equations, phase, variable, budget)
                scalar = budget.rational(scalar * 2)
                steps.append({"kind": "free", "variable": variable, "id": name})
            else:
                equations, phase = _pivot(equations, phase, variable, pivot, budget)
                steps.append({"kind": "pivot", "variable": variable, "id": name,
                              "pivot": [pivot[0], pivot[1]]})
        summary = _state_summary(net["boundary"], equations, phase, scalar)
        certificate = {
            "schema": "weighted_affine_marginal_certificate_v1",
            "input_sha256": _hash_request(request), "steps": steps,
            "summary": summary,
        }
        return {"schema": "weighted_affine_marginal_result_v1", "status": "EXACT",
                "summary": summary, "certificate": certificate, "stats": budget.stats()}
    except Exhausted as exc:
        return {"schema": "weighted_affine_marginal_result_v1", "status": "UNKNOWN",
                "summary": None, "certificate": None, "reason": str(exc),
                "stats": budget.stats()}
    except Invalid as exc:
        raise ValueError(str(exc)) from exc


def _verify_request(request, budget):
    return _request(request, budget)


def verify_marginal(request, result, **caps):
    """Independently replay and verify a producer result."""
    budget = Budget(caps)
    try:
        net = _verify_request(request, budget)
        if type(result) is not dict or result.get("schema") != "weighted_affine_marginal_result_v1":
            raise Invalid("wrong result schema")
        if result.get("status") != "EXACT" or type(result.get("certificate")) is not dict:
            raise Invalid("expected an exact certificate")
        cert = result["certificate"]
        if set(cert) != {"schema", "input_sha256", "steps", "summary"}:
            raise Invalid("malformed certificate")
        if cert["schema"] != "weighted_affine_marginal_certificate_v1" or cert["input_sha256"] != _hash_request(request):
            raise Invalid("request binding mismatch")
        steps = cert["steps"]
        if type(steps) is not list or len(steps) != len(net["internal"]):
            raise Invalid("one step is required for every internal variable")
        equations, phase, scalar = net["equations"], net["phase"], net["scalar"]
        base = len(net["boundary"])
        seen = set()
        for offset, name in enumerate(net["internal"]):
            variable = base + offset
            step = steps[offset]
            if type(step) is not dict or step.get("id") != name or step.get("variable") != variable:
                raise Invalid("internal variable order or identity mismatch")
            if variable in seen:
                raise Invalid("internal variable eliminated twice")
            seen.add(variable)
            kind = step.get("kind")
            if kind == "pivot":
                if set(step) != {"kind", "variable", "id", "pivot"}:
                    raise Invalid("malformed pivot step")
                pivot = step["pivot"]
                if type(pivot) is not list or len(pivot) != 2:
                    raise Invalid("malformed pivot row")
                equations, phase = _pivot(equations, phase, variable, tuple(pivot), budget)
            elif kind == "free":
                if set(step) != {"kind", "variable", "id"}:
                    raise Invalid("malformed free step")
                equations, phase = _free(equations, phase, variable, budget)
                scalar = budget.rational(scalar * 2)
            else:
                raise Invalid("unknown elimination step")
        expected = _state_summary(net["boundary"], equations, phase, scalar)
        if result.get("summary") != expected or cert.get("summary") != expected:
            raise Invalid("summary does not match replay")
        return {"valid": True, "status": "VERIFIED", "errors": [], "stats": budget.stats()}
    except Exhausted as exc:
        return {"valid": False, "status": "UNKNOWN", "errors": [str(exc)], "stats": budget.stats()}
    except (Invalid, TypeError, KeyError, ValueError, IndexError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)], "stats": budget.stats()}


def evaluate_summary(summary, assignment):
    """Evaluate a boundary summary at a Boolean assignment for test oracles."""
    if type(summary) is not dict or summary.get("schema") != "weighted_affine_summary_v1":
        raise ValueError("wrong summary")
    boundary = summary["boundary"]
    if type(assignment) not in (list, tuple) or len(assignment) != len(boundary) or any(x not in (0, 1) for x in assignment):
        raise ValueError("wrong boundary assignment")
    values = sum(x << i for i, x in enumerate(assignment))
    for mask, rhs in summary["equations"]:
        if ((mask & values).bit_count() & 1) != rhs:
            return Fraction(0)
    phase = sum(((values & term).bit_count() == term.bit_count()) for term in summary["phase"]) & 1
    return _ratio(summary["scalar"]) * (-1 if phase else 1)


def direct_marginal(request, assignment):
    """Independent finite oracle for small requests, used only in tests."""
    net = _request(request, Budget({"max_variables": 30, "max_equations": 1000,
                                    "max_phase_terms": 1000, "max_work": 10_000_000,
                                    "max_integer_bits": 10000}))
    k = len(net["boundary"])
    m = len(net["internal"])
    boundary_value = sum(x << i for i, x in enumerate(assignment))
    total = Fraction(0)
    for internal_value in range(1 << m):
        values = boundary_value | (internal_value << k)
        if any(((mask & values).bit_count() & 1) != rhs for mask, rhs in net["equations"]):
            continue
        exponent = sum((values & term).bit_count() == term.bit_count() for term in net["phase"]) & 1
        total += net["scalar"] * (-1 if exponent else 1)
    return total
