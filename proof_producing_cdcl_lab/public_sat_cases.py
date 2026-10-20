"""Deterministic original CNFs shared by both benchmark engines.

Standard PHP, parity gadgets, and planted/random clauses are controls, not
new hardness constructions. Shuffled copies test encoding sensitivity.
"""
from itertools import combinations, product
import random


def request(nvars, clauses):
    return {"schema": "original-cnf-v1", "nvars": nvars,
            "clauses": [list(clause) for clause in clauses]}


def php(holes):
    pigeons = holes + 1
    variable = lambda p, h: 1 + p * holes + h
    clauses = [[variable(p, h) for h in range(holes)] for p in range(pigeons)]
    clauses += [[-variable(p, a), -variable(p, b)]
                for p in range(pigeons) for a, b in combinations(range(holes), 2)]
    clauses += [[-variable(a, h), -variable(b, h)]
                for h in range(holes) for a, b in combinations(range(pigeons), 2)]
    return request(pigeons * holes, clauses)


def xor_chain(size, contradiction):
    # h_i is the XOR of the first i+2 inputs, with a final parity condition.
    clauses = []
    previous = 1
    for variable in range(2, size + 1):
        helper = size + variable - 1
        scope = (previous, variable, helper)
        for values in product((0, 1), repeat=3):
            if sum(values) % 2:
                clauses.append([v if not bit else -v for v, bit in zip(scope, values)])
        previous = helper
    clauses.append([-previous])
    # An odd fully fixed input contradicts the even-parity endpoint.
    if contradiction:
        clauses += [[1]] + [[-i] for i in range(2, size + 1)]
    return request(2 * size - 1, clauses)


def shuffled(original, seed):
    rng = random.Random(seed)
    mapping = list(range(1, original["nvars"] + 1))
    rng.shuffle(mapping)
    clauses = [[mapping[abs(lit) - 1] * (1 if lit > 0 else -1) for lit in clause]
               for clause in original["clauses"]]
    for clause in clauses:
        rng.shuffle(clause)
    rng.shuffle(clauses)
    return request(original["nvars"], clauses)


def cases():
    values = [
        ("empty_sat", request(0, [])),
        ("explicit_empty_unsat", request(0, [[]])),
        ("units_unsat", request(1, [[1], [-1]])),
        ("duplicates_tautologies_sat", request(3, [[1, 1], [2, -2], [1], [-1, 3]])),
        ("unused_variables_sat", request(7, [[1, 2], [-1, 2]])),
    ]
    for holes in (2, 3, 4, 5, 6):
        values.append((f"php_{holes+1}_{holes}", php(holes)))
    values.append(("php_6_5_shuffled", shuffled(php(5), 20261020)))
    for size in (16, 64):
        for contradiction in (False, True):
            values.append((f"xor_{size}_{'unsat' if contradiction else 'sat'}",
                           shuffled(xor_chain(size, contradiction), size)))
    rng = random.Random(20261020)
    for nvars, count in ((20, 86), (40, 172)):
        clauses = []
        for _ in range(count):
            variables = rng.sample(range(1, nvars + 1), 3)
            clauses.append([v if rng.randrange(2) else -v for v in variables])
        values.append((f"random3_{nvars}_{count}", request(nvars, clauses)))
        planted = [clause if any(lit > 0 for lit in clause)
                   else [-clause[0], *clause[1:]] for clause in clauses]
        values.append((f"planted3_{nvars}_{count}", request(nvars, planted)))
    return [{"name": name, "request": cnf} for name, cnf in values]
