"""Original-CNF binding and acceptance for untrusted public SAT backends.

No solver or benchmark generator is imported. UNSAT acceptance uses the
separate restricted RUP checker, not a solver status or a matching hash alone.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sibling(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    key = "_public_sat_certificate_" + name
    if key in sys.modules:
        module = sys.modules[key]
        require(Path(module.__file__).resolve() == path, "checker module path collision")
        return module
    spec = importlib.util.spec_from_file_location(key, path)
    require(spec is not None and spec.loader is not None, "checker is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[key]
        raise
    return module


def validate_request(request):
    require(type(request) is dict and set(request) == {"schema", "nvars", "clauses"},
            "request fields")
    require(request["schema"] == "original-cnf-v1", "request schema")
    nvars = request["nvars"]
    require(type(nvars) is int and nvars >= 0, "variable count")
    require(type(request["clauses"]) is list, "clauses must be an explicit list")
    for clause in request["clauses"]:
        require(type(clause) is list, "clause must be a list")
        require(all(type(lit) is int and 0 < abs(lit) <= nvars for lit in clause),
                "literal must be a nonzero exact integer in the original range")
    return request


def request_digest(request):
    validate_request(request)
    data = json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def dimacs(request):
    validate_request(request)
    lines = [f'p cnf {request["nvars"]} {len(request["clauses"])}']
    lines.extend(" ".join(map(str, clause + [0])) for clause in request["clauses"])
    return "\n".join(lines) + "\n"


def proof_digest(proof):
    require(type(proof) in (str, bytes), "proof must be text or bytes")
    data = proof.encode("utf-8") if isinstance(proof, str) else proof
    return hashlib.sha256(data).hexdigest()


def verify_candidate(request, candidate, proof=None, **limits):
    """Return VERIFIED_SAT/VERIFIED_UNSAT, UNKNOWN, or INVALID.

    Resource exhaustion and a solver's explicit UNKNOWN are never decisions.
    The original request is an explicit input, not read from the candidate.
    """
    try:
        digest = request_digest(request)
        require(type(candidate) is dict, "candidate must be a dictionary")
        require(candidate.get("schema") == "public-sat-candidate-v1", "candidate schema")
        require(candidate.get("request_sha256") == digest, "original request binding")
        status = candidate.get("status")
        base = {"schema", "request_sha256", "status"}
        if status == "UNKNOWN":
            require(set(candidate) == base | {"reason"}, "UNKNOWN fields")
            require(type(candidate["reason"]) is str and candidate["reason"], "UNKNOWN reason")
            return {"valid": False, "status": "UNKNOWN", "errors": [],
                    "reason": candidate["reason"], "request_sha256": digest}
        if status == "SAT":
            require(set(candidate) == base | {"model"}, "SAT fields")
            model = candidate["model"]
            require(type(model) is list and len(model) == request["nvars"], "model shape")
            require(all(type(value) is bool for value in model), "model values must be Boolean")
            for index, clause in enumerate(request["clauses"]):
                require(any(model[abs(lit) - 1] == (lit > 0) for lit in clause),
                        "model falsifies original clause " + str(index))
            return {"valid": True, "status": "VERIFIED_SAT", "errors": [],
                    "request_sha256": digest, "original_clauses_checked": len(request["clauses"])}
        require(status == "UNSAT", "unrecognized candidate status")
        require(set(candidate) == base | {"proof_sha256"}, "UNSAT fields")
        require(candidate["proof_sha256"] == proof_digest(proof), "proof binding")
        result = sibling("rup_verify").verify_rup(
            request["nvars"], request["clauses"], proof, **limits)
        return {**result, "status": "VERIFIED_UNSAT" if result["valid"] else result["status"],
                "request_sha256": digest}
    except (TypeError, ValueError, KeyError, UnicodeError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def verify_native_candidate(request, envelope):
    """Replay the retained native solver's different, explicit resolution format."""
    try:
        digest = request_digest(request)
        require(type(envelope) is dict and
                set(envelope) == {"schema", "request_sha256", "result"}, "native envelope fields")
        require(envelope["schema"] == "native-cdcl-candidate-v1", "native envelope schema")
        require(envelope["request_sha256"] == digest, "original request binding")
        sibling("review").replay(request["nvars"], request["clauses"], envelope["result"])
        status = envelope["result"]["status"]
        return {"valid": status != "UNKNOWN",
                "status": "UNKNOWN" if status == "UNKNOWN" else "VERIFIED_" + status,
                "errors": [], "request_sha256": digest}
    except (TypeError, ValueError, KeyError, UnicodeError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}
