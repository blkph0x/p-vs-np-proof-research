"""Independent source-bound affine-hull and resolution replay.

No producer or SAT solver imports; no enumeration of original assignments.
UNKNOWN is validated as absence of a claim, never as proof of a hull.
"""
from __future__ import annotations
import json


class HullVerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise HullVerificationError(message)


def equal(actual, expected, label):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True),
            label + " mismatch")


def validate_source(m, q, clauses):
    require(type(m) is int and type(q) is int and min(m, q) >= 0, "invalid partition")
    require(isinstance(clauses, (list, tuple)), "invalid clause sequence")
    for clause in clauses:
        require(isinstance(clause, (list, tuple)), "invalid clause")
        require(all(type(lit) is int and 1 <= abs(lit) <= m + q for lit in clause),
                "invalid literal")
    return {"visible_width": m, "hidden_width": q, "clauses": [list(c) for c in clauses]}


def canonical_hull(m, points):
    require(bool(points), "nonempty hull required")
    # Separate boolean-matrix elimination, not producer integer-row operations.
    anchor = points[0]
    matrix = [[bool((point ^ anchor) & (1 << j)) for j in range(m)]
              for point in points[1:]]
    pivots, row = [], 0
    for col in range(m):
        selected = next((i for i in range(row, len(matrix)) if matrix[i][col]), None)
        if selected is None:
            continue
        matrix[row], matrix[selected] = matrix[selected], matrix[row]
        for i in range(len(matrix)):
            if i != row and matrix[i][col]:
                matrix[i] = [a != b for a, b in zip(matrix[i], matrix[row])]
        pivots.append(col)
        row += 1
    equations = []
    for free in range(m):
        if free in pivots:
            continue
        mask = 1 << free
        for i, pivot in enumerate(pivots):
            if matrix[i][free]:
                mask |= 1 << pivot
        rhs = sum(bool(mask & anchor & (1 << j)) for j in range(m)) % 2
        equations.append([mask, rhs])
    return equations, len(pivots)


def rebuild_query(m, q, clauses, points):
    if not points:
        return m + q, [list(c) for c in clauses]
    equations, dimension = canonical_hull(m, points)
    require(dimension < m, "query after full-dimensional hull")
    result, width, violations = [list(c) for c in clauses], m + q, []
    for mask, rhs in equations:
        variables = [i + 1 for i in range(m) if mask & (1 << i)]
        accumulator = variables[0]
        for variable in variables[1:]:
            width += 1
            # Exclude the four assignments with odd (a,b,z) parity.
            triple = (accumulator, variable, width)
            for forbidden in (1, 2, 4, 7):
                result.append([(-v if forbidden & (1 << bit) else v)
                               for bit, v in enumerate(triple)])
            accumulator = width
        violations.append(accumulator if rhs == 0 else -accumulator)
    result.append(violations)
    return width, result


def normal(clause, n):
    require(isinstance(clause, (list, tuple)), "malformed proof clause")
    require(all(type(lit) is int and 1 <= abs(lit) <= n for lit in clause),
            "proof literal outside query")
    literals = set(clause)
    if any(-lit in literals for lit in literals):
        return None
    return tuple(sorted(literals, key=lambda v: (abs(v), v < 0)))


def model_tuple(model, n):
    require(isinstance(model, dict), "missing SAT model")
    if all(type(k) is int for k in model):
        require(set(model) == set(range(n)), "SAT model variable coverage")
        values = tuple(model[i] for i in range(n))
    else:
        require(all(type(k) is str for k in model) and
                set(model) == {str(i) for i in range(n)}, "SAT model key encoding")
        values = tuple(model[str(i)] for i in range(n))
    require(all(type(v) is bool for v in values), "non-Boolean SAT model")
    return values


STATS = ("decisions", "boolean_props", "conflicts", "learned_clauses",
         "learned_literals", "resolution_steps", "backjumps")


def replay_solver(n, clauses, result):
    require(type(n) is int and n >= 0, "invalid query width")
    database = []
    for c in clauses:
        row = normal(c, n)
        if row is not None:
            database.append(row)
    known = set(database)
    proof = result.get("proof")
    require(isinstance(proof, list), "missing resolution proof")
    steps = learned = literals = terminals = 0
    for index, event in enumerate(proof):
        require(isinstance(event, dict) and event.get("kind") in ("learned", "terminal-empty"),
                "unknown proof event")
        current = normal(event["from_conflict"], n)
        require(current in known, "unavailable conflict clause")
        equal(event["from_conflict"], current, "noncanonical conflict")
        require(isinstance(event["derivation"], list), "invalid derivation")
        for step in event["derivation"]:
            equal(step["left"], current, "resolution left")
            right = normal(step["right"], n)
            require(right in known, "unavailable resolution parent")
            equal(step["right"], right, "noncanonical right")
            pivot = step["pivot"]
            require(type(pivot) is int and 0 <= pivot < n, "invalid pivot")
            positive = pivot + 1
            a, b = set(current), set(right)
            if positive in a and -positive in b:
                combined = (a - {positive}) | (b - {-positive})
            elif -positive in a and positive in b:
                combined = (a - {-positive}) | (b - {positive})
            else:
                raise HullVerificationError("pivot lacks opposite polarities")
            current = normal(list(combined), n)
            require(current is not None, "tautological resolvent")
            equal(step["result"], current, "resolution result")
            steps += 1
        if event["kind"] == "learned":
            equal(event["clause"], current, "learned clause")
            database.append(current)
            known.add(current)
            learned += 1
            literals += len(current)
        else:
            require(current == () and index == len(proof) - 1, "terminal is not final empty")
            terminals += 1
    equal(result["clauses"], database, "solver database")
    stats = result["stats"]
    require(isinstance(stats, dict) and set(stats) == set(STATS), "counter fields")
    require(all(type(v) is int and v >= 0 for v in stats.values()), "invalid counters")
    for name, expected in (("resolution_steps", steps), ("learned_clauses", learned),
                           ("learned_literals", literals), ("backjumps", learned),
                           ("conflicts", learned + terminals)):
        require(stats[name] == expected, "trace counter mismatch: " + name)
    status = result["status"]
    if status == "SAT":
        require(terminals == 0, "SAT with terminal contradiction")
        values = model_tuple(result["model"], n)
        require(all(any(values[abs(lit) - 1] == (lit > 0) for lit in clause)
                    for clause in clauses), "SAT model violates query")
        return status, values
    require(result["model"] is None, "non-SAT model claim")
    if status == "UNSAT":
        require(terminals == 1, "UNSAT lacks empty-clause proof")
    else:
        require(status == "UNKNOWN" and terminals == 0 and
                result.get("reason") == "DECISION_CAP", "invalid solver stopping status")
    return status, None


def _verify(m, q, clauses, certificate):
    """Verify a transcript against the externally supplied original CNF."""
    expected_source = validate_source(m, q, clauses)
    require(isinstance(certificate, dict), "invalid hull certificate")
    equal(certificate["source"], expected_source, "source")
    require(certificate["status"] in ("EXACT_HULL", "EMPTY", "UNKNOWN"), "invalid hull status")
    transcript = certificate["queries"]
    require(isinstance(transcript, list) and len(transcript) <= m + 1, "query count bound")
    # Bounds are verifier resource policy, not a mathematical input restriction.
    require(m + q <= 128 and sum(len(c) for c in clauses) <= 100000,
            "verifier input budget")
    points, terminal = [], None
    totals = {name: 0 for name in STATS}
    for index, query in enumerate(transcript):
        require(terminal is None, "query after terminal result")
        width, rebuilt = rebuild_query(m, q, clauses, points)
        equal(query["nvars"], width, "query variable count")
        equal(query["clauses"], rebuilt, "query CNF")
        status, model = replay_solver(width, rebuilt, query["result"])
        for name in STATS:
            totals[name] += query["result"]["stats"][name]
        if status == "SAT":
            point = sum(1 << i for i in range(m) if model[i])
            old_dimension = canonical_hull(m, points)[1] if points else -1
            points.append(point)
            dimension = canonical_hull(m, points)[1]
            require(dimension == old_dimension + 1, "non-increasing witness span")
            if dimension == m:
                terminal = "EXACT_HULL"
        elif status == "UNSAT":
            terminal = "EXACT_HULL" if points else "EMPTY"
        else:
            terminal = "UNKNOWN"
        if terminal is not None:
            require(index == len(transcript) - 1, "extra query after completion")
    equal(certificate["solver_totals"], totals, "aggregate counters")
    if certificate["status"] == "UNKNOWN":
        require(terminal in (None, "UNKNOWN"), "UNKNOWN hides completed evidence")
        require(certificate["equations"] is None and certificate["dimension"] is None,
                "UNKNOWN contains a hull claim")
        require(isinstance(certificate.get("reason"), str), "UNKNOWN lacks reason")
        return {"status": "UNKNOWN", "queries": len(transcript)}
    require(terminal == certificate["status"], "missing terminal evidence")
    if terminal == "EMPTY":
        equal(certificate["equations"], [[0, 1]], "empty equations")
        equal(certificate["dimension"], None, "empty dimension")
    else:
        equations, dimension = canonical_hull(m, points)
        equal(certificate["equations"], equations, "hull equations")
        equal(certificate["dimension"], dimension, "hull dimension")
    return {"status": "VERIFIED_" + terminal, "queries": len(transcript),
            "projection_affinity": "NOT_CHECKED"}


def verify(m, q, clauses, certificate):
    """Malformed certificates are rejected even when Python assertions are disabled."""
    try:
        return _verify(m, q, clauses, certificate)
    except (KeyError, TypeError, IndexError) as exc:
        raise HullVerificationError("malformed certificate") from exc

def verify_saved(artifact):
    from hashlib import sha256
    from pathlib import Path
    here = Path(__file__).resolve().parent
    names = ("affine_hull.py", "review_affine_hull.py", "run_affine_hull.py",
             "test_hull_engine.py", "test_hull_certificate.py", "AFFINE_HULL_METHOD.md")
    paths = [here / name for name in names] + [here.parent / "proof_producing_cdcl_lab" / "cdcl.py"]
    hashes = {p.relative_to(here.parent).as_posix(): sha256(
        p.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    ).hexdigest() for p in paths}
    equal(artifact["schema"], "certified-affine-hull-v1", "schema")
    equal(artifact["hash_scheme"], "sha256-utf8-lf-v1", "hash scheme")
    equal(artifact["source_sha256"], hashes, "source hashes")
    expected = [
        ("zero_width", 0, 0, [], {}),
        ("empty_zero_width", 0, 0, [[]], {}),
        ("nonaffine_hole", 2, 0, [[-1, -2]], {}),
        ("affine_guard_sat", 1, 1, [[-1, 2]], {}),
        ("affine_guard_unsat", 1, 1, [[-1, 2], [-1, -2]], {}),
        ("nonconstant_hidden_counts", 1, 1, [[1, 2]], {}),
        ("nonzero_offset", 3, 1, [[1], [-2, 3], [2, -3]], {}),
        ("decision_cap", 8, 0, [], {"max_decisions": 0}),
        ("call_cap", 4, 0, [], {"max_calls": 1}),
    ]
    for label, m, rhs in [("odd_parity", 3, 1)] + [
            ("even_parity_" + str(m), m, 0) for m in (3, 4, 6, 8)]:
        cnf, previous = [], 1
        for position in range(1, m):
            output = m + position
            ports = (previous, position + 1, output)
            for mask in range(8):
                if sum(bool(mask & (1 << i)) for i in range(3)) % 2:
                    cnf.append([-v if mask & (1 << i) else v for i, v in enumerate(ports)])
            previous = output
        cnf.append([previous if rhs else -previous])
        expected.append((label, m, m - 1, cnf, {}))
    equal(len(artifact["cases"]), len(expected), "case coverage")
    summary = []
    for row, (name, m, q, cnf, caps) in zip(artifact["cases"], expected):
        equal(row["name"], name, "case name")
        equal(row["source"], validate_source(m, q, cnf), "case original")
        equal(row["caps"], caps, "case caps")
        checked = verify(m, q, cnf, row["certificate"])
        wanted = ("UNKNOWN" if name in ("decision_cap", "call_cap") else
                  "VERIFIED_EMPTY" if name == "empty_zero_width" else "VERIFIED_EXACT_HULL")
        equal(checked["status"], wanted, "case outcome")
        require(len(row["certificate"]["queries"]) <= caps.get("max_calls", m+1), "saved call cap")
        require(row["certificate"]["solver_totals"]["decisions"] <= caps.get("max_decisions", 1000),
                "saved aggregate decision cap")
        summary.append({"name": name, **checked})
    return {"status": "VERIFIED", "cases": summary, "source_hashes_current": True}


if __name__ == "__main__":
    from pathlib import Path
    data = json.loads(Path(__file__).with_name("HULL_RESULTS.json").read_text(encoding="utf-8"))
    print(json.dumps(verify_saved(data), sort_keys=True))
