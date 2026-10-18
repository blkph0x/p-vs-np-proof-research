"""Check direct decision evidence for the four retained exact-counting failures.

This is a bounded witness search and original-clause unit contradiction probe,
not a new complete polynomial SAT algorithm. UNKNOWN is preserved on failure.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ['counting_vs_decision_audit.py', 'AFFINE_COMPRESSION_CROSSCHECK.json']


class Exhausted(Exception):
    pass


def original(n, clauses):
    if type(n) is not int or not 0 <= n <= 4096 or type(clauses) is not list:
        raise ValueError('invalid original formula')
    if len(clauses) > 10000:
        raise ValueError('original clause bound')
    if any(type(c) is not list or any(type(x) is not int or not 0 < abs(x) <= n
                                     for x in c) for c in clauses):
        raise ValueError('invalid original clauses')


def verify_witness(n, clauses, assignment):
    """Read every original clause; do not use any counting/search proof."""
    try:
        original(n, clauses)
        return (type(assignment) is list and len(assignment) == n
                and all(type(x) is int and x in (0, 1) for x in assignment)
                and all(any(assignment[abs(lit)-1] == int(lit > 0) for lit in c)
                        for c in clauses))
    except (ValueError, TypeError, IndexError):
        return False


def verify_unit_contradiction(n, clauses, proof):
    """Independently replay original-clause implications, with no branching."""
    try:
        original(n, clauses)
        if type(proof) is not dict or set(proof) != {'steps', 'conflict_clause'}:
            return False
        values = {}
        steps = proof['steps']
        if type(steps) is not list or len(steps) > n:
            return False
        for step in steps:
            if type(step) is not dict or set(step) != {'clause', 'literal'}:
                return False
            index, forced = step['clause'], step['literal']
            if type(index) is not int or not 0 <= index < len(clauses):
                return False
            if type(forced) is not int or not 0 < abs(forced) <= n:
                return False
            if abs(forced) in values:
                return False
            residual = set()
            for lit in clauses[index]:
                if abs(lit) not in values:
                    residual.add(lit)
                elif values[abs(lit)] == (lit > 0):
                    return False
            if residual != {forced}:
                return False
            values[abs(forced)] = forced > 0
        conflict = proof['conflict_clause']
        if type(conflict) is not int or not 0 <= conflict < len(clauses):
            return False
        return all(abs(lit) in values and values[abs(lit)] != (lit > 0)
                   for lit in clauses[conflict])
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def probe(n, clauses, max_nodes=10000, max_literal_visits=3000000):
    original(n, clauses)
    if any(type(x) is not int or x < 0 for x in (max_nodes, max_literal_visits)):
        raise ValueError('nonnegative exact caps required')
    stats = dict(nodes=0, literal_visits=0, branches=0)

    def scan(values, keep_trace=False):
        trace = []
        while True:
            unresolved = []
            pending = None
            for index, clause in enumerate(clauses):
                residual = set()
                satisfied = False
                for lit in clause:
                    stats['literal_visits'] += 1
                    if stats['literal_visits'] > max_literal_visits:
                        raise Exhausted('literal visit cap')
                    value = values[abs(lit)-1]
                    if value is None:
                        residual.add(lit)
                    elif value == int(lit > 0):
                        satisfied = True
                if satisfied or any(-lit in residual for lit in residual):
                    continue
                if not residual:
                    return False, [], trace, index
                unresolved.append(tuple(sorted(residual)))
                if len(residual) == 1 and pending is None:
                    pending = (index, next(iter(residual)))
            if pending is None:
                return True, unresolved, trace, None
            index, lit = pending
            values[abs(lit)-1] = int(lit > 0)
            if keep_trace:
                trace.append(dict(clause=index, literal=lit))

    def visit(values):
        stats['nodes'] += 1
        if stats['nodes'] > max_nodes:
            raise Exhausted('search node cap')
        ok, residual, _, _ = scan(values)
        if not ok:
            return None
        if not residual:
            return [0 if x is None else x for x in values]
        frequencies = {}
        for clause in residual:
            for lit in clause:
                frequencies[abs(lit)-1] = frequencies.get(abs(lit)-1, 0)+1
        var = max(frequencies, key=lambda x: (frequencies[x], -x))
        positive = sum(var+1 in clause for clause in residual)
        negative = sum(-(var+1) in clause for clause in residual)
        preferred = int(positive >= negative)
        stats['branches'] += 1
        for bit in (preferred, 1-preferred):
            child = values.copy()
            child[var] = bit
            answer = visit(child)
            if answer is not None:
                return answer
        return None

    try:
        values = [None]*n
        ok, _, trace, conflict = scan(values, True)
        if not ok:
            proof = dict(steps=trace, conflict_clause=conflict)
            assert verify_unit_contradiction(n, clauses, proof)
            return dict(status='UNSAT', proof=proof, assignment=None, stats=stats)
        witness = visit(values)
        if witness is not None:
            assert verify_witness(n, clauses, witness)
            return dict(status='SAT', assignment=witness, proof=None, stats=stats)
        return dict(status='UNKNOWN', assignment=None, proof=None, stats=stats,
                    reason='no witness; this probe exports no branching refutation')
    except (Exhausted, RecursionError) as error:
        return dict(status='UNKNOWN', assignment=None, proof=None, stats=stats,
                    reason=str(error) or 'Python recursion bound')


def checks():
    """Small exhaustive semantic and adversarial checks for exported claims."""
    from itertools import combinations, product
    atoms = [[], [1], [-1], [2], [-2], [1, 2], [1, -2], [-1, 2], [-1, -2]]
    checked = 0
    for mask in range(1 << len(atoms)):
        clauses = [c for i, c in enumerate(atoms) if mask >> i & 1]
        truth = any(verify_witness(2, clauses, list(a)) for a in product((0, 1), repeat=2))
        answer = probe(2, clauses)
        assert answer['status'] == 'UNKNOWN' or (answer['status'] == 'SAT') == truth
        if answer['status'] == 'SAT':
            assert verify_witness(2, clauses, answer['assignment'])
        if answer['status'] == 'UNSAT':
            assert verify_unit_contradiction(2, clauses, answer['proof'])
        checked += 1
    units = [[1], [-1, 2], [-2]]
    proof = probe(2, units)['proof']
    assert verify_unit_contradiction(2, units, proof)
    assert not verify_unit_contradiction(2, units[:-1], proof)
    assert not verify_unit_contradiction(2, units, {'steps': [], 'conflict_clause': 2})
    assert not verify_witness(2, units, [1, 1])
    assert not verify_witness(2, [], [True, 0])
    assert probe(1, [[1]], max_literal_visits=0)['status'] == 'UNKNOWN'
    assert probe(2, [[1, 2]], max_nodes=0)['status'] == 'UNKNOWN'
    assert probe(1, [[1, 1], [-1]])['status'] == 'UNSAT'
    assert probe(1, [[1, -1]])['status'] == 'SAT'
    return dict(exhaustive_two_variable_formulas=checked, additional_checks=9)


def hashes():
    return {p: hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in SOURCES}


def main():
    before = hashes()
    control_checks = checks()
    source = json.loads((HERE/'AFFINE_COMPRESSION_CROSSCHECK.json').read_text(encoding='utf-8'))
    rows = []
    for row in source['cases']:
        if row['result']['status'] != 'UNKNOWN':
            continue
        n, clauses = row['n'], row['clauses']
        result = probe(n, clauses)
        valid = (verify_witness(n, clauses, result['assignment']) if result['status'] == 'SAT'
                 else verify_unit_contradiction(n, clauses, result['proof'])
                 if result['status'] == 'UNSAT' else None)
        if valid:
            assert (result['status'] == 'SAT') == (row['expected_count'] > 0)
        rows.append(dict(name=row['name'], n=n, clauses=clauses,
                         counting_status='UNKNOWN', expected_count=row['expected_count'],
                         decision_result=result, independently_verified=valid))
    assert before == hashes()
    out = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=before,
               source_unchanged=True, control_checks=control_checks,
               caps=dict(max_nodes=10000, max_literal_visits=3000000), cases=rows,
               conclusion='Direct decision evidence is separate from exact counting. The witness search can take exponential time and returns UNKNOWN on limits; unit contradictions cover only a restricted class. No P versus NP conclusion.')
    (HERE/'COUNTING_VS_DECISION_AUDIT.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(control_checks))
    for row in rows:
        print(row['name'], row['decision_result']['status'], row['decision_result']['stats'])


if __name__ == '__main__':
    main()
