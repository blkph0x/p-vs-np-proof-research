"""Independent rational certificates for min c*x subject to A*x=b, x>=0.

The generic checker proves only the supplied mathematical LP. A digest binds
that LP to a certificate; it does not establish that the LP is a faithful
encoding of a named problem. ``replay_affine_overlap`` adds the independent
source reconstruction for the repository's fixed RM(2,5) affine-overlap LP.

No exporter, numerical solver, expected optimum, tolerance, or Python assert
participates in acceptance. Equality dual multipliers have unrestricted signs.
The reporting offset is added only after verifying the reduced objective.
"""
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import json
from math import gcd
import re


MODEL_FIELDS = frozenset(("schema", "name", "variable_ids", "row_ids", "rows",
                          "rhs", "objective", "objective_offset"))
CERTIFICATE_FIELDS = frozenset(("schema", "model_sha256", "primal", "dual",
                                "claimed_objective"))
_RATIONAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
_INDEX = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class VerificationError(ValueError):
    """Malformed input or a failed exact proof obligation."""


def _require(condition, message):
    if not condition:
        raise VerificationError(message)


def _decimal(text):
    """Parse nonnegative ASCII digits without a global int-string limit change."""
    value = 0
    for start in range(0, len(text), 9):
        chunk = text[start:start + 9]
        value = value * (10 ** len(chunk)) + int(chunk)
    return value


def _integer_text(value):
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    chunks = []
    while value:
        value, chunk = divmod(value, 10**9)
        chunks.append(chunk)
    return sign + str(chunks[-1]) + "".join(f"{c:09d}" for c in reversed(chunks[:-1]))


def _rational(text, location):
    _require(type(text) is str and _RATIONAL.fullmatch(text) is not None,
             location + ": canonical rational string required")
    negative = text.startswith("-")
    unsigned = text[1:] if negative else text
    parts = unsigned.split("/")
    numerator = _decimal(parts[0])
    denominator = _decimal(parts[1]) if len(parts) == 2 else 1
    _require(not (negative and numerator == 0), location + ": negative zero")
    if len(parts) == 2:
        _require(denominator > 1 and gcd(numerator, denominator) == 1,
                 location + ": fraction is not in canonical lowest terms")
    return Fraction(-numerator if negative else numerator, denominator)


def _rational_text(value):
    numerator = _integer_text(value.numerator)
    return numerator if value.denominator == 1 else numerator + "/" + _integer_text(value.denominator)


def _json(model):
    return json.dumps(model, sort_keys=True, separators=(",", ":"))


def _parse_model(model):
    _require(type(model) is dict and set(model) == MODEL_FIELDS, "model fields mismatch")
    _require(model["schema"] == "exact-equality-lp-v1", "model schema mismatch")
    _require(type(model["name"]) is str and _NAME.fullmatch(model["name"]) is not None,
             "invalid model name")
    for key in ("variable_ids", "row_ids", "rows", "rhs", "objective"):
        _require(type(model[key]) is list, key + " must be a list")
    n, m = len(model["variable_ids"]), len(model["row_ids"])
    _require(model["variable_ids"] == [f"x{i:06d}" for i in range(n)],
             "variable IDs must be consecutive and ordered")
    _require(model["row_ids"] == [f"r{i:06d}" for i in range(m)],
             "row IDs must be consecutive and ordered")
    _require(len(model["rows"]) == m and len(model["rhs"]) == m,
             "row/RHS dimensions mismatch")
    _require(len(model["objective"]) == n, "objective dimension mismatch")
    rows = []
    for i, raw in enumerate(model["rows"]):
        _require(type(raw) is dict, "sparse row must be a dictionary")
        row = {}
        for key, text in raw.items():
            _require(type(key) is str and _INDEX.fullmatch(key) is not None,
                     "column index must be a canonical decimal string")
            column = _decimal(key)
            _require(column < n, "sparse column index outside variable range")
            value = _rational(text, f"row {i}, column {key}")
            _require(value != 0, "explicit zero sparse coefficient")
            row[column] = value
        rows.append(row)
    rhs = [_rational(v, f"RHS {i}") for i, v in enumerate(model["rhs"])]
    objective = [_rational(v, f"objective {i}") for i, v in enumerate(model["objective"])]
    offset = _rational(model["objective_offset"], "objective offset")
    return rows, rhs, objective, offset


def model_digest(model):
    """Hash a strictly validated model; implemented independently of the exporter."""
    _parse_model(model)
    return sha256(_json(model).encode("utf-8")).hexdigest()


def _verify(model, certificate):
    rows, rhs, objective, offset = _parse_model(model)
    n, m = len(objective), len(rhs)
    _require(type(certificate) is dict and set(certificate) == CERTIFICATE_FIELDS,
             "solution fields mismatch")
    _require(certificate["schema"] == "exact-equality-lp-solution-v1",
             "solution schema mismatch")
    digest = certificate["model_sha256"]
    _require(type(digest) is str and _DIGEST.fullmatch(digest) is not None,
             "invalid model digest")
    _require(digest == sha256(_json(model).encode("utf-8")).hexdigest(),
             "solution is bound to a different model")
    _require(type(certificate["primal"]) is list and len(certificate["primal"]) == n,
             "primal dimension mismatch")
    _require(type(certificate["dual"]) is list and len(certificate["dual"]) == m,
             "dual dimension mismatch")
    primal = [_rational(v, f"primal {i}") for i, v in enumerate(certificate["primal"])]
    dual = [_rational(v, f"dual {i}") for i, v in enumerate(certificate["dual"])]
    claimed = _rational(certificate["claimed_objective"], "claimed objective")
    _require(all(value >= 0 for value in primal), "negative primal coordinate")
    reduced = list(objective)
    for i, row in enumerate(rows):
        activity = sum((coefficient * primal[j] for j, coefficient in row.items()), Fraction(0))
        _require(activity == rhs[i], f"primal equality failure at row {i}")
        for j, coefficient in row.items():
            reduced[j] -= coefficient * dual[i]
    _require(all(value >= 0 for value in reduced), "negative dual reduced cost")
    primal_value = sum((a * v for a, v in zip(objective, primal)), Fraction(0))
    dual_value = sum((b * y for b, y in zip(rhs, dual)), Fraction(0))
    _require(primal_value == dual_value, "nonzero primal-dual objective gap")
    _require(claimed == primal_value, "claimed reduced objective mismatch")
    return {
        "valid": True, "status": "EXACT_OPTIMUM", "errors": [],
        "model_sha256": digest,
        "reduced_objective": _rational_text(primal_value),
        "total_objective": _rational_text(primal_value + offset),
        "objective_offset": _rational_text(offset),
        "minimum_reduced_cost": _rational_text(min(reduced, default=Fraction(0))),
        "variables": n, "rows": m,
        "scope": "exact optimum of the supplied equality LP",
    }


def verify_solution(model, certificate):
    """Return INVALID for malformed/failed certificates; no infeasibility claim."""
    try:
        return _verify(model, certificate)
    except (VerificationError, TypeError, ValueError, KeyError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


verify_certificate = verify_solution


@lru_cache(maxsize=1)
def _affine_model_json():
    # Cache immutable data derived by the independent reviewer, never caller data.
    from REED_MULLER_LEVEL_D_AFFINE_OVERLAP_INDEPENDENT_REVIEW import _rebuild
    scopes, _, _, variables, _, row_orbits, matrix, rhs, objective, flat_rank = _rebuild()
    _require({size: len(values) for size, values in scopes.items()} ==
             {8: 620, 4: 1240, 2: 496, 1: 32}, "independent affine scope mismatch")
    _require(len(variables) == 28 and len(row_orbits) == 53 and flat_rank == 16,
             "independent affine orbit/rank mismatch")
    expected = {
        "schema": "exact-equality-lp-v1", "name": "rm25_affine_overlap",
        "variable_ids": [f"x{i:06d}" for i in range(len(variables))],
        "row_ids": [f"r{i:06d}" for i in range(len(row_orbits))],
        "rows": [{str(j): _rational_text(Fraction(value))
                  for j, value in row.items() if value != 0} for row in matrix],
        "rhs": [_rational_text(Fraction(value)) for value in rhs],
        "objective": [_rational_text(Fraction(value)) for value in objective],
        "objective_offset": "1",
    }
    _parse_model(expected)
    return _json(expected)


def replay_affine_overlap(model, certificate):
    """Bind a candidate LP to independently rebuilt fixed RM affine geometry."""
    try:
        _parse_model(model)
        _require(_json(model) == _affine_model_json(),
                 "model differs from independently rebuilt affine-overlap source")
        result = _verify(model, certificate)
        result["scope"] = "RM(2,5) affine-overlap quotient optimum"
        result["source_binding"] = "independent affine geometry and quotient reconstruction"
        return result
    except (VerificationError, TypeError, ValueError, KeyError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}
