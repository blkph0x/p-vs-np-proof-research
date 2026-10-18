"""Count a certified SAT-packed coefficient by exact clause-factor elimination.

Bounded reference implementation. UNKNOWN carries no coefficient claim.
The checker replays all local sums against the external original request.
"""
from hashlib import sha256
from itertools import combinations, product
from math import comb


DEFAULT_LIMITS = {"max_variables": 4096, "max_clauses": 4096,
                  "max_bucket_states": 4096, "max_table_entries": 100000,
                  "max_arithmetic": 1000000, "max_structure_work": 1000000}


class BudgetExceeded(Exception):
    pass


def _limits(overrides):
    if set(overrides) - set(DEFAULT_LIMITS):
        raise ValueError("unknown budget name")
    limits = {**DEFAULT_LIMITS, **overrides}
    if any(type(v) is not int or v < 0 for v in limits.values()):
        raise ValueError("budgets must be nonnegative exact integers")
    return limits


def _formula(n, clauses, limits):
    if type(n) is not int or n < 0:
        raise ValueError("invalid variable count")
    if type(clauses) not in (list, tuple):
        raise ValueError("clauses must be a list or tuple")
    if n > limits["max_variables"] or len(clauses) > limits["max_clauses"]:
        raise BudgetExceeded("original formula dimensions exceed verification budget")
    checked = []
    for clause in clauses:
        if type(clause) not in (list, tuple) or not 1 <= len(clause) <= 3:
            raise ValueError("expected nonempty clauses of size at most three")
        if any(type(lit) is not int or lit == 0 or abs(lit) > n for lit in clause):
            raise ValueError("invalid literal")
        if len({abs(lit) for lit in clause}) != len(clause):
            raise ValueError("each clause must use distinct underlying variables")
        checked.append(tuple(clause))
    return tuple(checked)


def expected_packing(n, clauses, **limits):
    """Local encoder; tests also compare with the separately saved original encoder."""
    clauses = _formula(n, clauses, _limits(limits))
    pairs = [[0, 0] for _ in range(n)]
    target, power = 0, 1
    for clause in clauses:
        for lit in clause:
            pairs[abs(lit) - 1][int(lit < 0)] += power
        pairs.extend([[0, power] for _ in range(len(clause) - 1)])
        target += (len(clause) - 1) * power
        power *= 6
    return pairs, target


def _request(n, clauses, pairs, target, order, limits):
    clauses = _formula(n, clauses, limits)
    if type(order) not in (list, tuple) or len(order) != n:
        raise ValueError("external elimination order must contain every variable")
    if any(type(v) is not int for v in order) or set(order) != set(range(n)):
        raise ValueError("external order is not a permutation of original variables")
    if type(target) is not int or target < 0 or type(pairs) not in (list, tuple):
        raise ValueError("invalid packed coefficient request")
    q = n + sum(len(c) - 1 for c in clauses)
    if len(pairs) != q:
        raise ValueError("wrong number of original product factors")
    for pair in pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise ValueError("malformed product factor")
        if any(type(w) is not int or w < 0 for w in pair):
            raise ValueError("exponents must be nonnegative exact integers")
    # Verify every digit from the external original clauses, independently of the encoder.
    powers = [6 ** j for j in range(len(clauses))]
    for i in range(n):
        for bit in (0, 1):
            wanted = sum(power for c, power in zip(clauses, powers)
                         if (i + 1 if bit == 0 else -(i + 1)) in c)
            if pairs[i][bit] != wanted:
                raise ValueError("logical exponent does not match original clauses")
    cursor = n
    for clause, power in zip(clauses, powers):
        for _ in range(len(clause) - 1):
            if tuple(pairs[cursor]) != (0, power):
                raise ValueError("slack exponent does not match original clauses")
            cursor += 1
    if target != sum((len(c) - 1) * p for c, p in zip(clauses, powers)):
        raise ValueError("target does not match original packed clause bounds")
    digest = sha256(b"clause-factor-coefficient-v1\0")

    def integer(value):
        sign = int(value < 0)
        magnitude = abs(value)
        data = magnitude.to_bytes(max(1, (magnitude.bit_length() + 7) // 8), "little")
        digest.update(bytes([sign])); digest.update(len(data).to_bytes(8, "little")); digest.update(data)

    for value in (n, len(clauses), q, target):
        integer(value)
    for clause in clauses:
        integer(len(clause))
        for lit in clause:
            integer(lit)
    for pair in pairs:
        for value in pair:
            integer(value)
    for v in order:
        integer(v)
    return clauses, tuple(order), q, digest.hexdigest()


def _power2(exponent, cap, reason):
    if exponent >= cap.bit_length():
        raise BudgetExceeded(reason)
    return 1 << exponent


def _plan(n, clauses, order, limits):
    """Graph-fill width, independently checked against factor scopes on replay."""
    graph = [set() for _ in range(n)]
    work = 0
    for clause in clauses:
        for u, v in combinations((abs(lit) - 1 for lit in clause), 2):
            work += 1
            if work > limits["max_structure_work"]:
                raise BudgetExceeded("interaction-graph construction budget")
            graph[u].add(v); graph[v].add(u)
    entries = sum(1 << len(clause) for clause in clauses)
    if entries > limits["max_table_entries"]:
        raise BudgetExceeded("initial clause tables exceed total entry budget")
    peak = max((1 << len(c) for c in clauses), default=1)
    if peak > limits["max_bucket_states"]:
        raise BudgetExceeded("initial clause table exceeds bucket budget")
    steps, width = [], 0
    for variable in order:
        neighbors = sorted(graph[variable])
        width = max(width, len(neighbors))
        states = _power2(len(neighbors) + 1, limits["max_bucket_states"], "induced bucket width exceeds state budget")
        peak = max(peak, states)
        entries += states // 2
        if entries > limits["max_table_entries"]:
            raise BudgetExceeded("elimination certificate exceeds total entry budget")
        added_work = len(neighbors) * (len(neighbors) - 1) // 2 + len(neighbors)
        if work + added_work > limits["max_structure_work"]:
            raise BudgetExceeded("graph-fill work budget")
        work += added_work
        for u, v in combinations(neighbors, 2):
            graph[u].add(v); graph[v].add(u)
        for neighbor in neighbors:
            graph[neighbor].remove(variable)
        graph[variable].clear()
        steps.append(neighbors)
    return {"neighbors": steps, "width": width, "table_entries": entries,
            "peak_bucket_states": peak, "structure_work": work}


def _initial_factors(clauses):
    factors = {}
    for index, clause in enumerate(clauses):
        scope = tuple(sorted(abs(lit) - 1 for lit in clause))
        positions = {v: j for j, v in enumerate(scope)}
        table, bound = [], len(clause) - 1
        for assignment in range(1 << len(scope)):
            false_count = sum(bool((assignment >> positions[abs(lit) - 1]) & 1) != (lit > 0)
                              for lit in clause)
            slack = bound - false_count
            table.append(comb(bound, slack) if 0 <= slack <= bound else 0)
        factors[index] = (scope, table)
    return factors


def _stats(plan, arithmetic, bits):
    return {key: value for key, value in plan.items() if key != "neighbors"} | {
        "arithmetic": arithmetic, "peak_count_bits": bits}


def solve_structure(n, clauses, pairs, target, *, order, **budget_overrides):
    limits = _limits(budget_overrides)
    try:
        clauses, order, q, request_hash = _request(n, clauses, pairs, target, order, limits)
        plan = _plan(n, clauses, order, limits)
        active = _initial_factors(clauses)
        steps, arithmetic = [], 0
        bits = max((value.bit_length() for _, table in active.values() for value in table), default=1)
        for step, (variable, neighbors) in enumerate(zip(order, plan["neighbors"])):
            bucket = sorted(key for key, (scope, _) in active.items() if variable in scope)
            scope = tuple(sorted({variable}.union(*(set(active[key][0]) for key in bucket))))
            remaining = tuple(v for v in scope if v != variable)
            if list(remaining) != neighbors:
                raise ArithmeticError("factor scopes disagree with independently filled graph")
            row_count = 1 << len(remaining)
            work = row_count * (2 * len(bucket) + 1)
            if arithmetic + work > limits["max_arithmetic"]:
                raise BudgetExceeded("factor arithmetic budget")
            arithmetic += work
            table = []
            for row in range(row_count):
                assignment = {v: (row >> j) & 1 for j, v in enumerate(remaining)}
                value = 0
                for bit in (0, 1):
                    assignment[variable] = bit
                    term = 1
                    for key in bucket:
                        old_scope, old_table = active[key]
                        index = sum(assignment[v] << j for j, v in enumerate(old_scope))
                        term *= old_table[index]
                        bits = max(bits, term.bit_length())
                    value += term
                    bits = max(bits, value.bit_length())
                table.append(value)
            for key in bucket:
                del active[key]
            active[len(clauses) + step] = (remaining, table)
            steps.append({"variable": variable, "bucket": bucket, "scope": list(remaining), "table": table})
        coefficient = 1
        if arithmetic + len(active) > limits["max_arithmetic"]:
            raise BudgetExceeded("final component multiplication budget")
        arithmetic += len(active)
        for _, table in active.values():
            coefficient *= table[0]
            bits = max(bits, coefficient.bit_length())
        if bits > q + 1:
            raise ArithmeticError("count exceeded original binary-choice assignment bound")
        return {"format": "clause-factor-coefficient-v1", "status": "EXACT",
                "request_hash": request_hash, "order": list(order), "coefficient": coefficient,
                "positive": coefficient > 0, "steps": steps,
                "final_factors": sorted(active), "stats": _stats(plan, arithmetic, bits)}
    except BudgetExceeded as exc:
        return {"format": "clause-factor-coefficient-v1", "status": "UNKNOWN",
                "coefficient": None, "positive": None, "reason": str(exc)}


def _exact_int_list(value, expected):
    return (type(value) is list and all(type(v) is int for v in value)
            and value == list(expected))


def verify_structure(n, clauses, pairs, target, result, *, order, **budget_overrides):
    """Check local contractions by independently enumerating each full bucket.

    No coefficient oracle or producer call is used. The request and the order
    are external arguments; none are taken from the purported certificate.
    """
    try:
        limits = _limits(budget_overrides)
        clauses, order, q, request_hash = _request(n, clauses, pairs, target, order, limits)
        plan = _plan(n, clauses, order, limits)
        keys = {"format", "status", "request_hash", "order", "coefficient", "positive", "steps", "final_factors", "stats"}
        if type(result) is not dict or set(result) != keys:
            raise ValueError("missing or unexpected exact-certificate fields")
        if result["format"] != "clause-factor-coefficient-v1" or result["status"] != "EXACT":
            raise ValueError("not an exact certificate")
        if result["request_hash"] != request_hash or not _exact_int_list(result["order"], order):
            raise ValueError("certificate does not bind original product, formula, target and order")
        if type(result["steps"]) is not list or len(result["steps"]) != n:
            raise ValueError("wrong number of elimination steps")
        active = _initial_factors(clauses)
        arithmetic = 0
        bits = max((x.bit_length() for _, values in active.values() for x in values), default=1)
        for step, variable in enumerate(order):
            certificate = result["steps"][step]
            if type(certificate) is not dict or set(certificate) != {"variable", "bucket", "scope", "table"}:
                raise ValueError("malformed local certificate")
            bucket = sorted(key for key, (scope, _) in active.items() if variable in scope)
            joint = sorted({variable}.union(*(set(active[key][0]) for key in bucket)))
            output = [v for v in joint if v != variable]
            if output != plan["neighbors"][step]:
                raise ValueError("width certificate disagrees with factor interaction")
            if type(certificate["variable"]) is not int or certificate["variable"] != variable:
                raise ValueError("wrong eliminated variable")
            if not _exact_int_list(certificate["bucket"], bucket) or not _exact_int_list(certificate["scope"], output):
                raise ValueError("wrong factor ownership or remaining scope")
            claimed = certificate["table"]
            if type(claimed) is not list or len(claimed) != 1 << len(output):
                raise ValueError("wrong output table dimension")
            if any(type(v) is not int or v < 0 or v.bit_length() > q + 1 for v in claimed):
                raise ValueError("invalid output count")
            work = len(claimed) * (2 * len(bucket) + 1)
            if arithmetic + work > limits["max_arithmetic"]:
                raise BudgetExceeded("verification arithmetic budget")
            arithmetic += work
            totals = [0] * len(claimed)
            # Different traversal from the producer: enumerate full assignments,
            # project into input tables, then accumulate into the output row.
            for joint_values in product((0, 1), repeat=len(joint)):
                assignment = dict(zip(joint, joint_values))
                term = 1
                for key in bucket:
                    scope, values = active[key]
                    index = 0
                    for position, v in enumerate(scope):
                        index |= assignment[v] << position
                    term *= values[index]
                    bits = max(bits, term.bit_length())
                output_index = sum(assignment[v] << j for j, v in enumerate(output))
                totals[output_index] += term
                bits = max(bits, totals[output_index].bit_length())
            if totals != claimed:
                raise ValueError("incorrect local multiply-and-sum recurrence")
            for key in bucket:
                del active[key]
            active[len(clauses) + step] = (tuple(output), claimed)
        if not _exact_int_list(result["final_factors"], sorted(active)):
            raise ValueError("missing or repeated final component")
        if arithmetic + len(active) > limits["max_arithmetic"]:
            raise BudgetExceeded("verification final product budget")
        arithmetic += len(active)
        expected = 1
        for scope, values in active.values():
            if scope or len(values) != 1:
                raise ValueError("uneliminated final factor")
            expected *= values[0]
            bits = max(bits, expected.bit_length())
        if type(result["coefficient"]) is not int or result["coefficient"] != expected:
            raise ValueError("incorrect original coefficient")
        if type(result["positive"]) is not bool or result["positive"] != (expected > 0):
            raise ValueError("incorrect positivity claim")
        expected_stats = _stats(plan, arithmetic, bits)
        if type(result["stats"]) is not dict or set(result["stats"]) != set(expected_stats):
            raise ValueError("malformed work/width statistics")
        if any(type(result["stats"][key]) is not int or result["stats"][key] != value for key, value in expected_stats.items()):
            raise ValueError("false width, work or bit-length claim")
        if bits > q + 1:
            raise ValueError("count exceeds original assignment bound")
        return {"valid": True, "status": "EXACT", "coefficient": expected, "stats": expected_stats}
    except BudgetExceeded as exc:
        return {"valid": False, "status": "UNKNOWN", "reason": str(exc)}
    except (ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        return {"valid": False, "status": "INVALID", "reason": str(exc)}
