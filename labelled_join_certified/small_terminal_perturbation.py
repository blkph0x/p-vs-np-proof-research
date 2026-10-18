"""Exact small-terminal solver for a supplied ``H = B + U V`` perturbation.

The columns of ``B`` are graph-incidence columns (a ground vertex absorbs odd
column support).  A selected edge has label ``V_e``.  For every label value
``z`` we solve

    boundary(x) = target + U z,   label(x) = z.

The labelled T-join engine is exact for a supplied terminal set; enumerating
the ``2**p`` label values is therefore an exact deterministic algorithm for
this restricted perturbation route.  It is intentionally parameterized and
does not claim a polynomial algorithm when ``p`` grows with the input.
"""
from __future__ import annotations

from labelled_tjoin import solve_tjoin, solve_nonempty, verify_tjoin, verify_nonempty


DEFAULT_LIMITS = {
    "max_branches": 4096,
    "max_dp_states": 65536,
    "max_dp_transitions": 1_000_000,
    "max_states": 4096,
    "max_total_states": 1_000_000,
    "max_relaxations": 1_000_000,
    "max_verification_arcs": 10_000_000,
}


class _Limit(Exception):
    pass


def _natural(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _validate(columns, u_columns, v_labels, target, weights, p, require_nonzero, row_count):
    if type(columns) not in (list, tuple) or type(u_columns) not in (list, tuple):
        raise ValueError("B columns and U columns must be sequences")
    if row_count is None:
        row_count = max([0, target.bit_length(), *(col.bit_length() for col in columns),
                         *(col.bit_length() for col in u_columns)])
    if type(row_count) is not int or row_count < 0:
        raise ValueError("row_count must be a nonnegative integer")
    r = row_count
    for column in columns:
        if type(column) is not int or column < 0 or column.bit_length() > r:
            raise ValueError("B columns must be nonnegative r-bit masks")
    if type(p) is not int or p < 0:
        raise ValueError("p must be a nonnegative integer")
    if len(u_columns) != p or any(type(col) is not int or col < 0 or col.bit_length() > r
                                   for col in u_columns):
        raise ValueError("U columns must be r-bit masks")
    if type(v_labels) not in (list, tuple):
        raise ValueError("V labels must be a sequence")
    m = len(v_labels)
    if len(v_labels) != len(columns) or len(weights) != m:
        raise ValueError("weights and V labels must have the same length")
    if any(type(label) is not int or label < 0 or label.bit_length() > p for label in v_labels):
        raise ValueError("V labels must be p-bit masks")
    if any(type(weight) is not int or weight < 0 for weight in weights):
        raise ValueError("weights must be nonnegative integers")
    if type(target) is not int or target < 0 or target.bit_length() > r:
        raise ValueError("target must be an r-bit mask")
    if type(require_nonzero) is not bool:
        raise ValueError("require_nonzero must be Boolean")
    for edge_mask in columns:
        if edge_mask.bit_count() > 2:
            raise ValueError("every B column must have graph incidence weight at most two")
    return r, m


def _limits(given):
    limits = dict(DEFAULT_LIMITS)
    if given is not None:
        if type(given) is not dict or set(given) - set(limits):
            raise ValueError("unknown perturbation limit")
        limits.update(given)
    for key, value in limits.items():
        _natural(value, key)
    return limits


def _graph_edges(columns, labels, weights, row_count):
    """Convert B columns to graph edges; vertex r is the ground vertex."""
    r = row_count
    edges = []
    for edge_id, mask in enumerate(columns):
        support = [i for i in range(r) if mask >> i & 1]
        if len(support) == 0:
            u = v = r
        elif len(support) == 1:
            u, v = support[0], r
        else:
            u, v = support
        edges.append((u, v, labels[edge_id], weights[edge_id]))
    return tuple(edges)


def _rhs_for_z(target, u_columns, z):
    rhs = target
    for j, column in enumerate(u_columns):
        if z >> j & 1:
            rhs ^= column
    return rhs


def _terminals(rhs, r):
    terminals = [i for i in range(r) if rhs >> i & 1]
    if len(terminals) & 1:
        terminals.append(r)
    return tuple(terminals)


def _direct_properties(columns, u_columns, labels, weights, target, word, row_count):
    r = row_count
    z = 0
    for j, label in enumerate(labels):
        if word >> j & 1:
            z ^= label
    rhs = 0
    for i in range(r):
        bit = sum((word >> j) & 1 for j, column in enumerate(columns) if column >> i & 1) & 1
        if bit:
            rhs |= 1 << i
    transformed = rhs
    for i, col in enumerate(u_columns):
        if z >> i & 1:
            transformed ^= col
    # Hx = Bx + U(Vx), so transformed must equal the caller's target.
    return transformed == target, z, sum(weight for j, weight in enumerate(weights) if word >> j & 1)


def _matrix_rows(columns, u_columns, labels, row_count):
    """Materialize B+UV row masks over the original coordinate columns."""
    rows = []
    for i in range(row_count):
        b_row = sum((1 << j) for j, column in enumerate(columns) if column >> i & 1)
        uv_row = 0
        for a, u_column in enumerate(u_columns):
            if u_column >> i & 1:
                uv_row ^= sum((1 << j) for j, label in enumerate(labels) if label >> a & 1)
        rows.append(b_row ^ uv_row)
    return tuple(rows)


def prepare_perturbation(original_rows, columns, u_columns, labels, target=0, *,
                         weights=None, p=None, row_count=None, require_nonzero=True):
    """Check an explicit original matrix against a supplied B+UV decomposition."""
    try:
        original_rows = tuple(original_rows)
        columns = tuple(columns)
        u_columns = tuple(u_columns)
        labels = tuple(labels)
    except TypeError as exc:
        raise ValueError("matrix inputs must be iterable") from exc
    if row_count is None:
        row_count = len(original_rows)
    if weights is None:
        weights = (1,) * len(labels)
    else:
        weights = tuple(weights)
    if p is None:
        p = max(len(u_columns), max((label.bit_length() for label in labels), default=0))
    r, m = _validate(columns, u_columns, labels, target, weights, p,
                     require_nonzero, row_count)
    if len(original_rows) != r:
        raise ValueError("original matrix row count does not match the representation")
    for row in original_rows:
        if type(row) is not int or row < 0 or row.bit_length() > m:
            raise ValueError("original matrix rows must be m-bit masks")
    computed = _matrix_rows(columns, u_columns, labels, r)
    if tuple(original_rows) != computed:
        raise ValueError("supplied B+UV decomposition does not equal the original matrix")
    return {"original_rows": original_rows, "columns": columns,
            "u_columns": u_columns, "labels": labels, "weights": weights,
            "p": p, "row_count": r, "coordinate_count": m, "target": target,
            "require_nonzero": require_nonzero}


def _branch_limits(limits):
    return {key: limits[key] for key in (
        "max_states", "max_total_states", "max_relaxations", "max_dp_states",
        "max_dp_transitions", "max_verification_arcs")}


def solve_perturbation(columns, u_columns, labels, target=0, *, weights=None, p=None,
                       row_count=None, require_nonzero=True, limits=None):
    """Solve a supplied graph perturbation, or return UNKNOWN without a claim."""
    labels = tuple(labels)
    weights = tuple((1,) * len(labels) if weights is None else weights)
    columns = tuple(columns)
    u_columns = tuple(u_columns)
    if p is None:
        p = max(len(u_columns), max((label.bit_length() for label in labels), default=0))
    r, m = _validate(columns, u_columns, labels, target, weights, p, require_nonzero, row_count)
    limits = _limits(limits)
    branches = 1 << p if p < 63 else None
    if branches is None or branches > limits["max_branches"]:
        return {"status": "UNKNOWN", "certificate": None, "weight": None, "word": None,
                "reason": "branch cap", "stats": {"branches": 0}}
    edges = _graph_edges(columns, labels, weights, r)
    branch_records, best = [], None
    stats = {"branches": 0, "completed_branches": 0, "branch_work": 0,
             "branch_transitions": 0}
    for z in range(branches):
        stats["branches"] += 1
        rhs = _rhs_for_z(target, tuple(u_columns), z)
        terminals = _terminals(rhs, r)
        branch_limits = _branch_limits(limits)
        if require_nonzero and z == 0 and rhs == 0:
            result = solve_nonempty(r + 1, edges, p, terminals=(), target=0,
                                    limits=branch_limits,
                                    max_pin_cases=limits["max_branches"])
            mode = "nonempty"
        else:
            result = solve_tjoin(r + 1, edges, p, terminals=terminals, target=z,
                                 limits=branch_limits)
            mode = "tjoin"
        branch_records.append({"z": z, "rhs": rhs, "terminals": list(terminals),
                               "mode": mode, "result": result})
        stats["branch_work"] += result.get("table_build_stats", {}).get("relaxations", 0)
        stats["branch_transitions"] += result.get("dp_transitions", 0)
        if result["status"] != "EXACT":
            return {"status": "UNKNOWN", "certificate": None, "weight": None, "word": None,
                    "reason": "branch solver exhausted", "stats": stats}
        stats["completed_branches"] += 1
        if result["weight"] is not None:
            candidate = (result["weight"], result["word"], z)
            if best is None or candidate[:2] < best[:2]:
                best = candidate
    certificate = {"format": "small-terminal-perturbation-v1", "columns": list(columns),
                   "u_columns": list(u_columns), "labels": list(labels),
                   "weights": list(weights), "p": p, "target": target,
                   "row_count": r, "require_nonzero": require_nonzero,
                   "branches": branch_records}
    if best is None:
        weight = word = None
    else:
        weight, word = best[:2]
    ok, z, actual_weight = _direct_properties(columns, u_columns, labels,
                                               weights, target, word or 0, r)
    if word is not None and (not ok or z != best[2] or actual_weight != weight):
        raise ArithmeticError("branch reconstruction failed original perturbation")
    return {"status": "EXACT", "certificate": certificate, "weight": weight,
            "word": word, "stats": stats, "reason": None}


def solve_original(original_rows, columns, u_columns, labels, target=0, *,
                   weights=None, p=None, row_count=None, require_nonzero=True,
                   limits=None):
    """Solve after independently binding the supplied decomposition to H."""
    prepared = prepare_perturbation(original_rows, columns, u_columns, labels, target,
                                    weights=weights, p=p, row_count=row_count,
                                    require_nonzero=require_nonzero)
    result = solve_perturbation(prepared["columns"], prepared["u_columns"], prepared["labels"],
                                prepared["target"], weights=prepared["weights"], p=prepared["p"],
                                row_count=prepared["row_count"], require_nonzero=prepared["require_nonzero"],
                                limits=limits)
    if result["status"] != "EXACT":
        return {"schema": "small-terminal-perturbation-original-v1",
                "status": "UNKNOWN", "certificate": None, "weight": None,
                "word": None, "reason": result.get("reason"), "stats": result.get("stats")}
    certificate = {"format": "small-terminal-perturbation-original-v1",
                   "original_rows": list(prepared["original_rows"]),
                   "columns": list(prepared["columns"]),
                   "u_columns": list(prepared["u_columns"]),
                   "labels": list(prepared["labels"]),
                   "weights": list(prepared["weights"]), "p": prepared["p"],
                   "row_count": prepared["row_count"],
                   "coordinate_count": prepared["coordinate_count"],
                   "target": prepared["target"],
                   "require_nonzero": prepared["require_nonzero"],
                   "perturbation": result["certificate"]}
    return {"schema": "small-terminal-perturbation-original-v1", "status": "EXACT",
            "certificate": certificate, "weight": result["weight"],
            "word": result["word"], "reason": None, "stats": result.get("stats")}


def verify_perturbation(columns, u_columns, labels, target, result, *, weights=None, p=None,
                        row_count=None, require_nonzero=True, verification_limits=None):
    """Replay every label branch and then check the selected word in Hx=target."""
    try:
        labels = tuple(labels)
        weights = tuple((1,) * len(labels) if weights is None else weights)
        columns = tuple(columns)
        u_columns = tuple(u_columns)
        if p is None:
            p = max(len(u_columns), max((label.bit_length() for label in labels), default=0))
        r, m = _validate(columns, u_columns, labels, target, weights, p, require_nonzero, row_count)
        if verification_limits is None:
            verification_limits = {}
        if type(verification_limits) is not dict or set(verification_limits) - {
                "verification_state_limit", "verification_arc_limit", "verification_dp_transitions"}:
            raise ValueError("unknown verification limit")
        if any(type(value) is not int or value < 0 for value in verification_limits.values()):
            raise ValueError("verification limits must be nonnegative integers")
        if not isinstance(result, dict):
            raise ValueError("result must be a mapping")
        if result.get("status") == "UNKNOWN":
            if result.get("certificate") is not None or result.get("weight") is not None or result.get("word") is not None:
                raise ValueError("UNKNOWN result contains an aggregate claim")
            return {"valid": True, "status": "UNKNOWN", "errors": []}
        if result.get("status") != "EXACT" or result.get("certificate", {}).get("format") != "small-terminal-perturbation-v1":
            raise ValueError("missing exact perturbation certificate")
        cert = result["certificate"]
        expected = {"columns": list(columns), "u_columns": list(u_columns), "labels": list(labels),
                    "weights": list(weights), "p": p, "target": target,
                    "row_count": r,
                    "require_nonzero": require_nonzero}
        for key, value in expected.items():
            if cert.get(key) != value:
                raise ValueError("perturbation certificate metadata mismatch")
        branches = cert.get("branches")
        count = 1 << p
        if not isinstance(branches, list) or len(branches) != count:
            raise ValueError("incomplete branch coverage")
        edges = _graph_edges(columns, labels, weights, r)
        best = None
        verify_limits = dict(verification_limits)
        for z, record in enumerate(branches):
            rhs = _rhs_for_z(target, tuple(u_columns), z)
            terminals = _terminals(rhs, r)
            if (record.get("z"), record.get("rhs"), record.get("terminals")) != (z, rhs, list(terminals)):
                raise ValueError("branch metadata mismatch")
            nested = record.get("result")
            if record.get("mode") == "nonempty":
                if not (require_nonzero and z == 0 and rhs == 0):
                    raise ValueError("nonempty mode used on the wrong branch")
                checked = verify_nonempty(r + 1, edges, p, nested, terminals=(), target=0, **verify_limits)
            elif record.get("mode") == "tjoin":
                checked = verify_tjoin(r + 1, edges, p, nested, terminals=terminals, target=z, **verify_limits)
            else:
                raise ValueError("unknown branch mode")
            if not checked["valid"]:
                return checked
            if nested.get("status") != "EXACT":
                return {"valid": False, "status": "UNKNOWN", "errors": ["branch verifier exhausted"]}
            if nested.get("weight") is not None:
                candidate = (nested["weight"], nested["word"], z)
                if best is None or candidate[:2] < best[:2]:
                    best = candidate
        expected_weight = None if best is None else best[0]
        expected_word = None if best is None else best[1]
        if result.get("weight") != expected_weight or result.get("word") != expected_word:
            raise ValueError("aggregate branch minimum mismatch")
        if expected_word is not None:
            ok, _, actual_weight = _direct_properties(columns, u_columns, labels,
                                                       weights, target, expected_word, r)
            if not ok or actual_weight != expected_weight:
                raise ValueError("returned word fails original perturbation")
        return {"valid": True, "status": "EXACT", "errors": [],
                "branches_verified": count}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}


def verify_original(original_rows, columns, u_columns, labels, target, result, *,
                    weights=None, p=None, row_count=None, require_nonzero=True,
                    verification_limits=None):
    """Verify the decomposition binding and replay its perturbation certificate."""
    try:
        prepared = prepare_perturbation(original_rows, columns, u_columns, labels, target,
                                        weights=weights, p=p, row_count=row_count,
                                        require_nonzero=require_nonzero)
        if not isinstance(result, dict):
            raise ValueError("result must be a mapping")
        if result.get("status") == "UNKNOWN":
            if result.get("certificate") is not None or result.get("weight") is not None or result.get("word") is not None:
                raise ValueError("UNKNOWN result contains an aggregate claim")
            return {"valid": True, "status": "UNKNOWN", "errors": []}
        if result.get("schema") != "small-terminal-perturbation-original-v1" or result.get("status") != "EXACT":
            raise ValueError("missing original-bound perturbation certificate")
        certificate = result.get("certificate")
        if not isinstance(certificate, dict) or certificate.get("format") != "small-terminal-perturbation-original-v1":
            raise ValueError("invalid original-bound certificate")
        expected = {"original_rows": list(prepared["original_rows"]),
                    "columns": list(prepared["columns"]),
                    "u_columns": list(prepared["u_columns"]),
                    "labels": list(prepared["labels"]),
                    "weights": list(prepared["weights"]), "p": prepared["p"],
                    "row_count": prepared["row_count"],
                    "coordinate_count": prepared["coordinate_count"],
                    "target": prepared["target"],
                    "require_nonzero": prepared["require_nonzero"]}
        for key, value in expected.items():
            if certificate.get(key) != value:
                raise ValueError("original-bound metadata mismatch")
        nested = {"status": "EXACT", "certificate": certificate.get("perturbation"),
                  "weight": result.get("weight"), "word": result.get("word")}
        checked = verify_perturbation(prepared["columns"], prepared["u_columns"],
                                      prepared["labels"], prepared["target"], nested,
                                      weights=prepared["weights"], p=prepared["p"],
                                      row_count=prepared["row_count"],
                                      require_nonzero=prepared["require_nonzero"],
                                      verification_limits=verification_limits)
        if not checked["valid"]:
            return checked
        return {"valid": True, "status": "EXACT", "errors": [],
                "branches_verified": checked.get("branches_verified", 0)}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"valid": False, "status": "INVALID", "errors": [str(exc)]}
