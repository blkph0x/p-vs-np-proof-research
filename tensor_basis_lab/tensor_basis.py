"""Exact rational bipartite basis changes, with bounded contraction proofs.

Local indices are little endian. Variables are row equality tensors and
clauses are columns: G -> G*T**tensor(d), R -> inverse(T)**tensor(k)*R.
Transformation is exposed separately so it does not require global 2**E work.
"""
from fractions import Fraction
from hashlib import sha256
from math import comb, gcd


DEFAULT_LIMITS = {"max_variables": 4096, "max_clauses": 4096,
                  "max_occurrences": 4096, "max_local_states": 4096,
                  "max_tensor_entries": 65536, "max_edge_assignments": 4096,
                  "max_arithmetic": 1000000, "max_rational_bits": 65536}


class BudgetExceeded(Exception):
    pass


def _limits(overrides):
    if set(overrides) - set(DEFAULT_LIMITS):
        raise ValueError("unknown budget name")
    limits = {**DEFAULT_LIMITS, **overrides}
    if any(type(value) is not int or value < 0 for value in limits.values()):
        raise ValueError("budgets must be nonnegative exact integers")
    return limits


def _fraction(value):
    if type(value) in (int, Fraction):
        return Fraction(value)
    if type(value) in (list, tuple) and len(value) == 2:
        a, b = value
        if type(a) is int and type(b) is int and b > 0:
            return Fraction(a, b)
    raise ValueError("rational inputs must be integers, Fractions or exact numerator/positive-denominator pairs")


def encode_rational(value):
    value = _fraction(value)
    return [value.numerator, value.denominator]


def decode_rational(value):
    if type(value) is not list or len(value) != 2:
        raise ValueError("certificate rationals must be canonical pairs")
    a, b = value
    if type(a) is not int or type(b) is not int or b <= 0 or gcd(abs(a), b) != 1:
        raise ValueError("invalid or noncanonical certificate rational")
    return Fraction(a, b)


def _power2(exponent, cap, reason):
    if exponent >= cap.bit_length():
        raise BudgetExceeded(reason)
    return 1 << exponent


class Meter:
    def __init__(self, limits):
        self.limits = limits
        self.stats = {"arithmetic": 0, "inverse_ops": 0, "transform_ops": 0,
                      "contraction_ops": 0, "tensor_entries": 0,
                      "edge_assignments": 0, "peak_numerator_bits": 0,
                      "peak_denominator_bits": 0, "input_hash_bytes": 0}

    def checked(self, value):
        numerator_bits, denominator_bits = abs(value.numerator).bit_length(), value.denominator.bit_length()
        self.stats["peak_numerator_bits"] = max(self.stats["peak_numerator_bits"], numerator_bits)
        self.stats["peak_denominator_bits"] = max(self.stats["peak_denominator_bits"], denominator_bits)
        if max(numerator_bits, denominator_bits) > self.limits["max_rational_bits"]:
            raise BudgetExceeded("rational numerator/denominator bit limit exceeded")
        return value

    def op(self, kind, operation, a, b):
        if self.stats["arithmetic"] >= self.limits["max_arithmetic"]:
            raise BudgetExceeded("rational arithmetic limit reached")
        self.stats["arithmetic"] += 1
        self.stats[kind] += 1
        if operation == "add":
            value = a + b
        elif operation == "sub":
            value = a - b
        elif operation == "mul":
            value = a * b
        else:
            value = a / b
        return self.checked(value)

    def store(self, values):
        if self.stats["tensor_entries"] + len(values) > self.limits["max_tensor_entries"]:
            raise BudgetExceeded("stored tensor-entry limit reached")
        self.stats["tensor_entries"] += len(values)
        return [encode_rational(self.checked(value)) for value in values]


def _request(n, clauses, basis, mode, limits, meter):
    if type(n) is not int or n < 0:
        raise ValueError("variable count must be a nonnegative exact integer")
    if type(clauses) not in (list, tuple):
        raise ValueError("clauses must be a list or tuple")
    if n > limits["max_variables"] or len(clauses) > limits["max_clauses"]:
        raise BudgetExceeded("original formula dimension limit exceeded")
    if type(mode) is not str or mode not in ("sat", "slack"):
        raise ValueError("mode must be sat or slack")
    normalized, occurrences = [], 0
    for clause in clauses:
        if type(clause) not in (list, tuple):
            raise ValueError("each clause must be a list or tuple")
        if any(type(lit) is not int or lit == 0 or abs(lit) > n for lit in clause):
            raise ValueError("literal must be a signed original variable index")
        occurrences += len(clause)
        if occurrences > limits["max_occurrences"]:
            raise BudgetExceeded("literal-occurrence limit exceeded")
        normalized.append(tuple(clause))
    if type(basis) not in (list, tuple) or len(basis) != 2 or any(type(row) not in (list, tuple) or len(row) != 2 for row in basis):
        raise ValueError("basis must be a two-by-two matrix")
    matrix = tuple(tuple(meter.checked(_fraction(value)) for value in row) for row in basis)
    digest = sha256()
    length = 0

    def write(raw):
        nonlocal length
        digest.update(raw)
        length += len(raw)

    def integer(value):
        write(b"\x01" if value < 0 else b"\x00")
        magnitude = abs(value)
        raw = magnitude.to_bytes((magnitude.bit_length() + 7) // 8, "big")
        write(len(raw).to_bytes(8, "big")); write(raw)

    write(b"rational-bipartite-tensor-basis-v1\0")
    integer(n); integer(len(normalized))
    for clause in normalized:
        integer(len(clause))
        for lit in clause:
            integer(lit)
    write(b"\x00" if mode == "sat" else b"\x01")
    for row in matrix:
        for value in row:
            integer(value.numerator); integer(value.denominator)
    meter.stats["input_hash_bytes"] = length
    return tuple(normalized), matrix, digest.hexdigest()


def _layout(n, clauses, limits):
    variable_ports, clause_ports, edges = [[] for _ in range(n)], [], []
    for j, clause in enumerate(clauses):
        ports = []
        for position, literal in enumerate(clause):
            edge = len(edges)
            variable = abs(literal) - 1
            edges.append([variable, j, position])
            variable_ports[variable].append(edge)
            ports.append(edge)
        clause_ports.append(ports)
    planned_entries = 0
    for ports in variable_ports + clause_ports:
        size = _power2(len(ports), limits["max_local_states"], "local tensor-state limit exceeded")
        planned_entries += (len(ports) + 1) * size
        if planned_entries > limits["max_tensor_entries"]:
            raise BudgetExceeded("complete local tensor trace exceeds entry limit")
    return {"edges": edges, "variable_ports": variable_ports, "clause_ports": clause_ports}


def _original_tables(n, clauses, layout, mode):
    rows = []
    for ports in layout["variable_ports"]:
        degree = len(ports)
        if degree == 0:
            rows.append([Fraction(2)])
        else:
            table = [Fraction(0)] * (1 << degree)
            table[0] = table[-1] = Fraction(1)
            rows.append(table)
    columns = []
    for clause in clauses:
        table = []
        for assignment in range(1 << len(clause)):
            true_literals = sum(bool((assignment >> j) & 1) == (lit > 0) for j, lit in enumerate(clause))
            if mode == "sat":
                value = int(true_literals > 0)
            else:
                value = comb(len(clause) - 1, true_literals - 1) if true_literals else 0
            table.append(Fraction(value))
        columns.append(table)
    return rows, columns


def _inverse(matrix, meter):
    (a, b), (c, d) = matrix
    determinant = meter.op("inverse_ops", "sub",
                           meter.op("inverse_ops", "mul", a, d),
                           meter.op("inverse_ops", "mul", b, c))
    if determinant == 0:
        raise ValueError("basis is singular")
    return [[meter.op("inverse_ops", "div", value, determinant) for value in row]
            for row in ((d, -b), (-c, a))]


def _transform_stages(values, matrix, side, meter):
    stages = [meter.store(values)]
    degree = len(values).bit_length() - 1
    for axis in range(degree):
        following = [Fraction(0)] * len(values)
        for low in range(len(values)):
            if (low >> axis) & 1:
                continue
            high = low | (1 << axis)
            for out_bit, index in ((0, low), (1, high)):
                m0 = matrix[0][out_bit] if side == "row" else matrix[out_bit][0]
                m1 = matrix[1][out_bit] if side == "row" else matrix[out_bit][1]
                following[index] = meter.op("transform_ops", "add",
                    meter.op("transform_ops", "mul", values[low], m0),
                    meter.op("transform_ops", "mul", values[high], m1))
        values = following
        stages.append(meter.store(values))
    return stages


def _produce_transformation(n, clauses, basis, mode, limits, meter):
    clauses, matrix, binding = _request(n, clauses, basis, mode, limits, meter)
    layout = _layout(n, clauses, limits)
    inverse = _inverse(matrix, meter)
    originals = _original_tables(n, clauses, layout, mode)
    rows = [{"ports": ports, "stages": _transform_stages(values, matrix, "row", meter)}
            for ports, values in zip(layout["variable_ports"], originals[0])]
    columns = [{"ports": ports, "stages": _transform_stages(values, inverse, "column", meter)}
               for ports, values in zip(layout["clause_ports"], originals[1])]
    return {"kind": "rational_tensor_basis_v1", "input_sha256": binding,
            "layout": layout, "inverse": [[encode_rational(v) for v in row] for row in inverse],
            "rows": rows, "columns": columns}


def _unknown(reason, meter):
    return {"status": "UNKNOWN", "reason": str(reason), "count": None,
            "certificate": None, "stats": dict(meter.stats)}


def transform_network(n, clauses, basis, *, mode="sat", **budget_overrides):
    """Produce local transform traces, with no global edge-assignment expansion."""
    limits = _limits(budget_overrides)
    meter = Meter(limits)
    try:
        certificate = _produce_transformation(n, clauses, basis, mode, limits, meter)
        return {"status": "EXACT", "certificate": certificate, "stats": dict(meter.stats)}
    except BudgetExceeded as exc:
        return _unknown(exc, meter)


def _contract(certificate, stage, meter):
    nodes = certificate["rows"] + certificate["columns"]
    tables = [(node["ports"], [decode_rational(value) for value in node["stages"][stage]]) for node in nodes]
    count = _power2(len(certificate["layout"]["edges"]), meter.limits["max_edge_assignments"],
                    "global edge-assignment limit exceeded")
    terms, total = [], Fraction(0)
    for assignment in range(count):
        term = Fraction(1)
        for ports, values in tables:
            index = sum(((assignment >> edge) & 1) << j for j, edge in enumerate(ports))
            term = meter.op("contraction_ops", "mul", term, values[index])
        total = meter.op("contraction_ops", "add", total, term)
        terms.append(encode_rational(term))
        meter.stats["edge_assignments"] += 1
    return terms, total


def solve_basis(n, clauses, basis, *, mode="sat", **budget_overrides):
    """Transform then fully contract both networks under explicit finite caps."""
    limits = _limits(budget_overrides)
    meter = Meter(limits)
    try:
        transformed = _produce_transformation(n, clauses, basis, mode, limits, meter)
        original_terms, original_count = _contract(transformed, 0, meter)
        transformed_terms, count = _contract(transformed, -1, meter)
        if count != original_count or original_count.denominator != 1 or original_count < 0:
            raise ArithmeticError("basis contraction failed original nonnegative-count invariance")
        certificate = {"kind": "rational_basis_contraction_v1", "transformation": transformed,
                       "original_terms": original_terms, "transformed_terms": transformed_terms,
                       "original_count": encode_rational(original_count), "count": encode_rational(count)}
        return {"status": "EXACT", "count": encode_rational(count),
                "certificate": certificate, "stats": dict(meter.stats)}
    except BudgetExceeded as exc:
        return _unknown(exc, meter)


def _equal_exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(_equal_exact(x, y) for x, y in zip(a, b))
    if type(a) is dict:
        return set(a) == set(b) and all(_equal_exact(a[key], b[key]) for key in a)
    return a == b


def _verify_transformation(n, clauses, basis, mode, certificate, limits, meter):
    clauses, matrix, binding = _request(n, clauses, basis, mode, limits, meter)
    layout = _layout(n, clauses, limits)
    fields = {"kind", "input_sha256", "layout", "inverse", "rows", "columns"}
    if type(certificate) is not dict or set(certificate) != fields or certificate["kind"] != "rational_tensor_basis_v1":
        raise ValueError("malformed transformation certificate")
    if certificate["input_sha256"] != binding or not _equal_exact(certificate["layout"], layout):
        raise ValueError("transformation does not bind the original formula, basis and ordered ports")
    raw_inverse = certificate["inverse"]
    if type(raw_inverse) is not list or len(raw_inverse) != 2 or any(type(row) is not list or len(row) != 2 for row in raw_inverse):
        raise ValueError("malformed inverse matrix")
    inverse = [[meter.checked(decode_rational(value)) for value in row] for row in raw_inverse]
    # Check the supplied inverse by both matrix products, not the producer's
    # adjugate/division routine. These identities also exclude singular bases.
    for left, right in ((matrix, inverse), (inverse, matrix)):
        for i in range(2):
            for j in range(2):
                value = meter.op("inverse_ops", "add",
                    meter.op("inverse_ops", "mul", left[i][0], right[0][j]),
                    meter.op("inverse_ops", "mul", left[i][1], right[1][j]))
                if value != int(i == j):
                    raise ValueError("claimed inverse fails an original-basis matrix identity")
    originals = _original_tables(n, clauses, layout, mode)
    for label, port_lists, expected_tables, action, side in (
            ("rows", layout["variable_ports"], originals[0], matrix, "row"),
            ("columns", layout["clause_ports"], originals[1], inverse, "column")):
        nodes = certificate[label]
        if type(nodes) is not list or len(nodes) != len(port_lists):
            raise ValueError("wrong number of original tensor nodes")
        for node, ports, expected in zip(nodes, port_lists, expected_tables):
            if type(node) is not dict or set(node) != {"ports", "stages"} or not _equal_exact(node["ports"], ports):
                raise ValueError("node ports differ from original ordered occurrences")
            stages = node["stages"]
            if type(stages) is not list or len(stages) != len(ports) + 1:
                raise ValueError("wrong number of one-axis tensor stages")
            parsed = []
            for stage in stages:
                if type(stage) is not list or len(stage) != len(expected):
                    raise ValueError("wrong tensor-table dimension")
                values = [meter.checked(decode_rational(value)) for value in stage]
                meter.store(values)
                parsed.append(values)
            if parsed[0] != expected:
                raise ValueError("initial tensor does not equal the original clause/copy signature")
            for axis in range(len(ports)):
                before, after = parsed[axis], parsed[axis + 1]
                # Independent traversal: check every output index separately.
                for output_index, claimed in enumerate(after):
                    bit = (output_index >> axis) & 1
                    low = output_index & ~(1 << axis)
                    high = low | (1 << axis)
                    coefficients = (action[0][bit], action[1][bit]) if side == "row" else (action[bit][0], action[bit][1])
                    value = meter.op("transform_ops", "add",
                        meter.op("transform_ops", "mul", coefficients[0], before[low]),
                        meter.op("transform_ops", "mul", coefficients[1], before[high]))
                    if value != claimed:
                        raise ValueError("local tensor stage fails its original-basis action")
    return certificate


def verify_transformation(n, clauses, basis, certificate, *, mode="sat", **budget_overrides):
    """Check only local basis invariance; no claim of efficient global counting."""
    meter = None
    try:
        limits = _limits(budget_overrides)
        meter = Meter(limits)
        _verify_transformation(n, clauses, basis, mode, certificate, limits, meter)
        return {"valid": True, "status": "EXACT", "stats": dict(meter.stats)}
    except BudgetExceeded as exc:
        return {"valid": False, "status": "UNKNOWN", "reason": str(exc), "stats": {} if meter is None else dict(meter.stats)}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, ZeroDivisionError) as exc:
        return {"valid": False, "status": "INVALID", "reason": str(exc)}


def verify_basis(n, clauses, basis, certificate, *, mode="sat", **budget_overrides):
    """Replay the local actions and every original/transformed contraction term."""
    meter = None
    try:
        limits = _limits(budget_overrides)
        meter = Meter(limits)
        fields = {"kind", "transformation", "original_terms", "transformed_terms", "original_count", "count"}
        if type(certificate) is not dict or set(certificate) != fields or certificate["kind"] != "rational_basis_contraction_v1":
            raise ValueError("malformed complete contraction certificate")
        transformed = _verify_transformation(n, clauses, basis, mode, certificate["transformation"], limits, meter)
        assignments = _power2(len(transformed["layout"]["edges"]), limits["max_edge_assignments"],
                              "verification edge-assignment limit exceeded")
        totals = []
        for field, stage in (("original_terms", 0), ("transformed_terms", -1)):
            raw_terms = certificate[field]
            if type(raw_terms) is not list or len(raw_terms) != assignments:
                raise ValueError("contraction trace omits or duplicates edge assignments")
            total = Fraction(0)
            nodes = transformed["rows"] + transformed["columns"]
            for edge_assignment, raw_term in enumerate(raw_terms):
                claimed = meter.checked(decode_rational(raw_term))
                value = Fraction(1)
                for node in reversed(nodes):
                    local = 0
                    for position, edge in enumerate(node["ports"]):
                        if edge_assignment & (1 << edge):
                            local |= 1 << position
                    entry = decode_rational(node["stages"][stage][local])
                    value = meter.op("contraction_ops", "mul", value, entry)
                if value != claimed:
                    raise ValueError("contraction term disagrees with original ports and checked tensor entries")
                total = meter.op("contraction_ops", "add", total, value)
                meter.stats["edge_assignments"] += 1
            totals.append(total)
        original = decode_rational(certificate["original_count"])
        changed = decode_rational(certificate["count"])
        if totals != [original, changed] or original != changed or original.denominator != 1 or original < 0:
            raise ValueError("claimed original/transformed count or invariance is false")
        return {"valid": True, "status": "EXACT", "count": encode_rational(original), "stats": dict(meter.stats)}
    except BudgetExceeded as exc:
        return {"valid": False, "status": "UNKNOWN", "reason": str(exc), "stats": {} if meter is None else dict(meter.stats)}
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, ZeroDivisionError) as exc:
        return {"valid": False, "status": "INVALID", "reason": str(exc)}


def wrong_same_basis_control(n, clauses, basis, *, mode="sat", **budget_overrides):
    """Deliberately wrong column action, for a labelled finite countercontrol."""
    limits = _limits(budget_overrides)
    meter = Meter(limits)
    try:
        clauses, matrix, binding = _request(n, clauses, basis, mode, limits, meter)
        layout = _layout(n, clauses, limits)
        _inverse(matrix, meter)  # Still require a legitimate invertible basis.
        originals = _original_tables(n, clauses, layout, mode)
        network = {"layout": layout,
                   "rows": [{"ports": ports, "stages": _transform_stages(values, matrix, "row", meter)}
                            for ports, values in zip(layout["variable_ports"], originals[0])],
                   "columns": [{"ports": ports, "stages": _transform_stages(values, matrix, "column", meter)}
                               for ports, values in zip(layout["clause_ports"], originals[1])]}
        original_terms, original_count = _contract(network, 0, meter)
        wrong_terms, wrong_count = _contract(network, -1, meter)
        return {"status": "CONTROL", "warning": "Columns deliberately use T rather than inverse(T); not an invariance certificate.",
                "input_sha256": binding, "network": network, "original_terms": original_terms,
                "wrong_terms": wrong_terms, "original_count": encode_rational(original_count),
                "wrong_count": encode_rational(wrong_count), "changes_count": original_count != wrong_count,
                "stats": dict(meter.stats)}
    except BudgetExceeded as exc:
        return _unknown(exc, meter)
