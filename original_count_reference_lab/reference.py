"""Bounded #SAT reference using the project's old branch/component utilities.

This is an exponential reference algorithm, not a claimed new fast SAT solver.
The checker reconstructs restrictions/components independently from the original
formula. Disappearing variables are counted explicitly at every edge.
"""
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

OLD = Path(__file__).resolve().parents[2]/'automatic_parameter_discovery_lab'
sys.path.insert(0, str(OLD))
spec = importlib.util.spec_from_file_location('count_reference_legacy', OLD/'engine.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

LIMITS = dict(max_variables=4096, max_clauses=10000, max_states=100000,
              max_work=10000000, max_depth=400, max_count_bits=100000)


class Exhausted(Exception):
    pass


class Meter:
    def __init__(self, caps):
        if set(caps)-set(LIMITS):
            raise ValueError('unknown cap')
        self.limits = {**LIMITS, **caps}
        if any(type(x) is not int or x < 0 for x in self.limits.values()):
            raise ValueError('nonnegative exact caps required')
        self.work = self.states = self.hits = self.peak_bits = 0

    def tick(self, work=1):
        self.work += work
        if self.work > self.limits['max_work']:
            raise Exhausted('work cap')

    def value(self, x):
        self.peak_bits = max(self.peak_bits, x.bit_length())
        if self.peak_bits > self.limits['max_count_bits']:
            raise Exhausted('count bit cap')
        return x

    def stats(self):
        return dict(work=self.work, states=self.states, cache_hits=self.hits, peak_count_bits=self.peak_bits)


def request(n, clauses, meter):
    if type(n) is not int or n < 0 or type(clauses) not in (list, tuple):
        raise ValueError('invalid original formula')
    if n > meter.limits['max_variables'] or len(clauses) > meter.limits['max_clauses']:
        raise Exhausted('original dimension cap')
    result = []
    for clause in clauses:
        if type(clause) not in (list, tuple) or any(type(v) is not int or v == 0 or abs(v) > n for v in clause):
            raise ValueError('invalid original literal')
        meter.tick(len(clause)+1)
        result.append(tuple(clause))
    return tuple(result)


def request_hash(n, clauses):
    h = sha256(b'original-count-reference-v1\0')
    for x in [n, len(clauses), *(v for c in clauses for v in (len(c), *c))]:
        raw = abs(x).to_bytes(max(1, (abs(x).bit_length()+7)//8), 'big')
        h.update(bytes([int(x < 0)])); h.update(len(raw).to_bytes(8, 'big')); h.update(raw)
    return h.hexdigest()


def solve(n, clauses, **caps):
    meter = Meter(caps)
    try:
        original = request(n, clauses, meter)
        root_formula = legacy.canon_formula(original)
        nodes, memo = [], {}

        def visit(formula, depth):
            meter.tick(1+sum(len(c)+1 for c in formula))
            if formula in memo:
                meter.hits += 1
                return memo[formula]
            if depth > meter.limits['max_depth'] or meter.states >= meter.limits['max_states']:
                raise Exhausted('state or depth cap')
            meter.states += 1
            variables = legacy.vars_of(formula)
            node = {'formula': [list(c) for c in formula]}
            if () in formula:
                node.update(kind='false', count=0)
            elif not formula:
                node.update(kind='true', count=1)
            else:
                unit = next((c[0] for c in formula if len(c) == 1), None)
                if unit is not None:
                    v, bit = abs(unit)-1, int(unit > 0)
                    child_formula = legacy.simplify(formula, v, bit)
                    child = visit(child_formula, depth+1)
                    free = len(variables)-1-len(legacy.vars_of(child_formula))
                    count = meter.value(nodes[child]['count'] << free)
                    node.update(kind='unit', literal=unit, child=child, free=free, count=count)
                else:
                    # The legacy component builder materializes pairs of clauses
                    # sharing each variable. Charge that discovery before calling it.
                    degrees = {v: 0 for v in variables}
                    for c in formula:
                        for lit in c:
                            degrees[abs(lit)-1] += 1
                    meter.tick(sum(d*d for d in degrees.values()))
                    components = legacy.incidence_components(formula)
                    if len(components) > 1:
                        children = [visit(part, depth+1) for part in components]
                        count = 1
                        for child in children:
                            count = meter.value(count*nodes[child]['count'])
                        node.update(kind='components', children=children, count=count)
                    else:
                        # An inexpensive existing-style branch choice; discovery work is charged.
                        occurrences = {v: 0 for v in variables}
                        for c in formula:
                            for lit in c:
                                occurrences[abs(lit)-1] += 1
                        v = max(variables, key=lambda x: (occurrences[x], -x))
                        children, free, count = [], [], 0
                        for bit in (0, 1):
                            child_formula = legacy.simplify(formula, v, bit)
                            child = visit(child_formula, depth+1)
                            unused = len(variables)-1-len(legacy.vars_of(child_formula))
                            children.append(child); free.append(unused)
                            count = meter.value(count+(nodes[child]['count'] << unused))
                        node.update(kind='branch', variable=v, children=children, free=free, count=count)
            meter.value(node['count'])
            index = len(nodes)
            nodes.append(node); memo[formula] = index
            return index

        root = visit(root_formula, 0)
        free = n-len(legacy.vars_of(root_formula))
        count = meter.value(nodes[root]['count'] << free)
        return {'status': 'EXACT', 'count': count, 'certificate': {
            'format': 'original-count-dag-v1', 'input_sha256': request_hash(n, original),
            'root': root, 'free': free, 'nodes': nodes}, 'stats': meter.stats()}
    except Exhausted as e:
        return {'status': 'UNKNOWN', 'count': None, 'certificate': None, 'reason': str(e), 'stats': meter.stats()}


def _normalize(clauses):
    """Checker canonicalization independent of the imported producer helpers."""
    rows = set()
    for clause in clauses:
        row = frozenset(clause)
        if any(-lit in row for lit in row):
            continue
        rows.add(tuple(sorted(row, key=lambda x: (abs(x), x < 0))))
    return tuple(sorted(rows, key=lambda c: (len(c), c)))


def _vars(formula):
    return {abs(lit)-1 for clause in formula for lit in clause}


def _restrict(formula, v, bit):
    true_literal = v+1 if bit else -(v+1)
    return _normalize([[lit for lit in clause if abs(lit)-1 != v]
                       for clause in formula if true_literal not in clause])


def verify(n, clauses, result, **caps):
    meter = Meter(caps)
    try:
        original = request(n, clauses, meter)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return {'status': 'UNKNOWN', 'valid': False, 'reason': 'no exact proof'}
        cert = result['certificate']
        if set(cert) != {'format', 'input_sha256', 'root', 'free', 'nodes'} or cert['format'] != 'original-count-dag-v1':
            raise ValueError('invalid proof format')
        if cert['input_sha256'] != request_hash(n, original):
            raise ValueError('wrong external original formula')
        nodes, root = cert['nodes'], cert['root']
        if type(nodes) is not list or not nodes or len(nodes) > meter.limits['max_states']:
            raise Exhausted('verification state cap or empty evidence')
        if type(root) is not int or root != len(nodes)-1:
            raise ValueError('root must be final topological node')
        formulas, counts, used = [], [], {root}
        for i, node in enumerate(nodes):
            meter.tick()
            if type(node) is not dict or type(node.get('formula')) is not list:
                raise ValueError('invalid node')
            formula = request(n, node['formula'], meter)
            if formula != _normalize(formula):
                raise ValueError('noncanonical stored formula')
            variables = _vars(formula)
            kind = node['kind']
            children = []
            def child(index):
                if type(index) is not int or not 0 <= index < i:
                    raise ValueError('invalid forward or cyclic reference')
                children.append(index)
                return formulas[index], counts[index]
            if kind == 'false':
                if set(node) != {'formula', 'kind', 'count'} or () not in formula:
                    raise ValueError('unjustified false terminal')
                count = 0
            elif kind == 'true':
                if set(node) != {'formula', 'kind', 'count'} or formula:
                    raise ValueError('unjustified true terminal')
                count = 1
            elif kind == 'unit':
                if set(node) != {'formula', 'kind', 'literal', 'child', 'free', 'count'}:
                    raise ValueError('unit fields')
                lit = node['literal']
                if type(lit) is not int or (lit,) not in formula:
                    raise ValueError('unjustified unit restriction')
                wanted = _restrict(formula, abs(lit)-1, int(lit > 0))
                sub, value = child(node['child'])
                free = len(variables)-1-len(_vars(wanted))
                if sub != wanted or type(node['free']) is not int or node['free'] != free:
                    raise ValueError('unit restriction or free-variable factor')
                count = value << free
            elif kind == 'branch':
                if set(node) != {'formula', 'kind', 'variable', 'children', 'free', 'count'}:
                    raise ValueError('branch fields')
                v = node['variable']
                if type(v) is not int or v not in variables or type(node['children']) is not list or len(node['children']) != 2:
                    raise ValueError('invalid branch variable or references')
                if type(node['free']) is not list or len(node['free']) != 2 or any(type(x) is not int for x in node['free']):
                    raise ValueError('invalid branch free factors')
                count = 0
                for bit, index in enumerate(node['children']):
                    sub, value = child(index)
                    wanted = _restrict(formula, v, bit)
                    free = len(variables)-1-len(_vars(wanted))
                    if sub != wanted or node['free'][bit] != free:
                        raise ValueError('branch restriction or free-variable factor')
                    count += value << free
            elif kind == 'components':
                if set(node) != {'formula', 'kind', 'children', 'count'} or type(node['children']) is not list or len(node['children']) < 2:
                    raise ValueError('component fields')
                union, var_union, count = [], set(), 1
                for index in node['children']:
                    sub, value = child(index)
                    scope = _vars(sub)
                    if not sub or not scope or scope & var_union:
                        raise ValueError('component variables not disjoint')
                    var_union |= scope; union.extend(sub)
                    count *= value
                if len(union) != len(formula) or _normalize(union) != formula or var_union != variables:
                    raise ValueError('components do not cover parent exactly')
            else:
                raise ValueError('unknown node kind')
            if type(node.get('count')) is not int or node['count'] != count:
                raise ValueError('incorrect recurrence count')
            meter.value(count)
            formulas.append(formula); counts.append(count)
        # All nodes must be reachable; references have already been checked topologically.
        for i in range(root, -1, -1):
            if i not in used:
                continue
            node = nodes[i]
            if node['kind'] == 'unit':
                used.add(node['child'])
            elif node['kind'] in ('branch', 'components'):
                used.update(node['children'])
        if len(used) != len(nodes) or formulas[root] != _normalize(original):
            raise ValueError('unused nodes or incomplete original root')
        free = n-len(_vars(formulas[root]))
        if type(cert['free']) is not int or cert['free'] != free:
            raise ValueError('wrong original free variables')
        count = meter.value(counts[root] << free)
        if type(result.get('count')) is not int or result['count'] != count:
            raise ValueError('wrong final original count')
        return {'status': 'VERIFIED', 'valid': True, 'count': count, 'stats': meter.stats()}
    except Exhausted as e:
        return {'status': 'UNKNOWN', 'valid': False, 'reason': str(e), 'stats': meter.stats()}
    except (ValueError, KeyError, IndexError, TypeError, AttributeError, OverflowError) as e:
        return {'status': 'INVALID', 'valid': False, 'reason': str(e)}
