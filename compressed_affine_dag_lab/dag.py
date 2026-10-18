"""Compressed sums of compact signed affine boundary messages.

Adapted from the frozen weighted_affine_dag_lab/dag.py, SHA-256
5693dfff8bba4b4ec0ba9735698eb209567bc0a4eff1c091bf90e49b70453368.
The original source is unchanged and remains the external baseline.

Source factors retain their original IDs. The structural factor tree and the
shared marginal-request DAG are both certified; equality of messages never
licenses omission of a source factor. This is an exponential worst-case method.
"""
from collections import Counter, defaultdict
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys


LIMITS = dict(max_terms=256, max_products=100000, max_nodes=4096,
              max_work=3000000, max_variables=1024, max_factors=4096,
              max_integer_bits=100000)

COMPRESSION_LIMITS = dict(max_variables=4096, max_inputs=100000,
    max_generated=100000, max_live_pieces=4096, max_pairs=100000,
    max_steps=200000, max_work=4000000, max_scalar_bits=65536,
    max_rows=16384, max_terms=100000)
COMPRESSION_COUNTERS = ('work', 'incoming_pieces', 'generated_pieces',
    'attempted_pairs', 'failed_pairs', 'identity_tests', 'failed_identity_tests',
    'normalizations', 'steps')
COMPRESSION_AGGREGATES = dict(max_inputs='incoming_pieces',
    max_generated='generated_pieces', max_pairs='attempted_pairs',
    max_steps='steps', max_work='work')
COMPRESSION_PEAKS = ('peak_live_pieces', 'peak_retained_pieces',
    'peak_pending_input_objects', 'peak_pending_generated_objects',
    'peak_live_plus_pending_objects', 'peak_scalar_bits')
_NO_COMPRESSION_CLAIM = object()


class Exhausted(Exception):
    pass


class Budget:
    def __init__(self, caps):
        if set(caps) - set(LIMITS):
            raise ValueError("unknown cap")
        self.limits = {**LIMITS, **caps}
        if any(type(x) is not int or x < 0 for x in self.limits.values()):
            raise ValueError("caps must be nonnegative exact integers")
        self.stats = dict(work=0, products=0, nodes=0, marginal_requests=0,
                          marginal_cache_hits=0, peak_terms=0, peak_integer_bits=0,
                          generated_input_terms=0, peak_generated_input_terms=0,
                          peak_output_terms=0)
        self.stats.update({'compression_'+key: 0 for key in COMPRESSION_COUNTERS})
        self.stats.update({'compression_'+key: 0 for key in COMPRESSION_PEAKS})

    def tick(self, amount=1):
        self.stats['work'] += amount
        if self.stats['work'] > self.limits['max_work']:
            raise Exhausted("work cap")

    def integer(self, value):
        bits = abs(value).bit_length()
        self.stats['peak_integer_bits'] = max(self.stats['peak_integer_bits'], bits)
        if bits > self.limits['max_integer_bits']:
            raise Exhausted("integer bit cap")

    def rational(self, value):
        self.integer(value.numerator)
        self.integer(value.denominator)
        return value

    def node(self):
        self.stats['nodes'] += 1
        if self.stats['nodes'] > self.limits['max_nodes']:
            raise Exhausted("combined structural/marginal node cap")

    def products(self, amount):
        self.stats['products'] += amount
        self.tick(amount)
        if self.stats['products'] > self.limits['max_products']:
            raise Exhausted("cross-product cap before merging")

    def terms(self, amount):
        self.stats['peak_terms'] = max(self.stats['peak_terms'], amount)
        if amount > self.limits['max_terms']:
            raise Exhausted("retained term cap")


def rational(value):
    if type(value) is int or type(value) is Fraction:
        return Fraction(value)
    if (type(value) in (list, tuple) and len(value) == 2
            and all(type(x) is int for x in value) and value[1] > 0):
        return Fraction(*value)
    raise ValueError("exact rational required")


def pack(value):
    value = rational(value)
    return [value.numerator, value.denominator]


def identical(first, second):
    """Typed equality: booleans/floats cannot impersonate proof integers."""
    return digest(first) == digest(second) and first == second


def add_free_variables(value, count, budget):
    if not value:
        return value
    denominator_twos = (value.denominator & -value.denominator).bit_length() - 1
    cancel = min(count, denominator_twos)
    shift = count - cancel
    if value.numerator.bit_length() + shift > budget.limits['max_integer_bits']:
        raise Exhausted("free-variable integer bit cap")
    return budget.rational(Fraction(value.numerator << shift, value.denominator >> cancel))


def digest(value):
    """Binary typed hash, including huge integers without decimal conversion."""
    h = sha256(b'weighted-affine-dag-v1\0')
    def emit(x):
        if type(x) is int:
            data = abs(x).to_bytes(max(1, (abs(x).bit_length()+7)//8), 'big')
            h.update(b'i' + bytes([x < 0]) + len(data).to_bytes(8, 'big') + data)
        elif type(x) is str:
            data = x.encode('utf-8'); h.update(b's' + len(data).to_bytes(8, 'big') + data)
        elif type(x) in (list, tuple):
            h.update(b'l'); emit(len(x))
            for y in x: emit(y)
        elif type(x) is dict:
            h.update(b'd'); emit(len(x))
            for key in sorted(x): emit(key); emit(x[key])
        elif type(x) is bool:
            h.update(b't' if x else b'f')
        elif x is None:
            h.update(b'n')
        else:
            raise ValueError("unhashable request object")
    emit(value)
    return h.hexdigest()


@lru_cache(None)
def boundary_module():
    path = Path(__file__).resolve().parent.parent/'affine_boundary_lab'/'boundary.py'
    spec = importlib.util.spec_from_file_location('_weighted_affine_boundary_dependency', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(None)
def compression_module():
    path = Path(__file__).resolve().parent.parent/'affine_sum_compression_lab'/'compression.py'
    spec = importlib.util.spec_from_file_location('_compressed_affine_sum_dependency', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CompressionMeter:
    """Cumulative compression limits, separate from per-message dimension caps."""
    def __init__(self, budget, caps):
        if caps is not None and type(caps) is not dict:
            raise ValueError("compression_caps must be a dictionary")
        caps = {} if caps is None else caps
        if set(caps) - set(COMPRESSION_LIMITS):
            raise ValueError("unknown compression cap")
        self.limits = {**COMPRESSION_LIMITS, **caps}
        if any(type(x) is not int or x < 0 for x in self.limits.values()):
            raise ValueError("compression caps must be nonnegative exact integers")
        self.budget = budget

    def reduce(self, n, retained, generated, claimed=_NO_COMPRESSION_CLAIM):
        budget = self.budget
        budget.stats['generated_input_terms'] += len(generated)
        budget.stats['peak_generated_input_terms'] = max(
            budget.stats['peak_generated_input_terms'], len(generated))
        # Preserve the old one-per-input merge bookkeeping unit, then charge
        # all additional compressor discovery, algebra and verification work.
        budget.tick(len(generated))
        caps = dict(self.limits)
        for limit, counter in COMPRESSION_AGGREGATES.items():
            caps[limit] = max(0, caps[limit] - budget.stats['compression_'+counter])
        caps['max_work'] = min(caps['max_work'], max(0, budget.limits['max_work']-budget.stats['work']))
        caps['max_live_pieces'] = min(caps['max_live_pieces'], budget.limits['max_terms'])
        caps['max_scalar_bits'] = min(caps['max_scalar_bits'], budget.limits['max_integer_bits'])
        caps['max_variables'] = min(caps['max_variables'], budget.limits['max_variables'])
        module = compression_module()
        if claimed is _NO_COMPRESSION_CLAIM:
            result = module.compress(n, retained, generated, **caps)
        else:
            result = module.verify_compression(n, retained, generated, claimed, **caps)
        stats = result['stats']
        for key in COMPRESSION_COUNTERS:
            amount = stats.get(key, 0)
            if type(amount) is not int or amount < 0:
                raise ValueError("invalid independently metered compression counter")
            budget.stats['compression_'+key] += amount
        for key in COMPRESSION_PEAKS:
            amount = stats.get(key, 0)
            if type(amount) is not int or amount < 0:
                raise ValueError("invalid independently metered compression peak")
            budget.stats['compression_'+key] = max(budget.stats['compression_'+key], amount)
        budget.stats['peak_terms'] = max(budget.stats['peak_terms'], stats.get('peak_retained_pieces', 0))
        budget.stats['peak_integer_bits'] = max(budget.stats['peak_integer_bits'], stats.get('peak_scalar_bits', 0))
        budget.tick(stats['work'])
        if result['status'] == 'UNKNOWN':
            raise Exhausted("sum compression cap: " + str(result.get('reason', result.get('errors', []))))
        if claimed is not _NO_COMPRESSION_CLAIM and not result['valid']:
            raise ValueError("invalid sum compression proof")
        if claimed is _NO_COMPRESSION_CLAIM and result['status'] != 'EXACT':
            raise ValueError("invalid sum compression result")
        for limit, counter in COMPRESSION_AGGREGATES.items():
            if budget.stats['compression_'+counter] > self.limits[limit]:
                raise Exhausted("aggregate compression " + limit)
        messages = result['messages']
        budget.terms(len(messages))
        budget.stats['peak_output_terms'] = max(budget.stats['peak_output_terms'], len(messages))
        for message in messages:
            budget.rational(rational(message['scalar']))
        return result, messages


def xor_phase(*phases):
    terms = set()
    for phase in phases:
        for term in phase:
            if term in terms: terms.remove(term)
            else: terms.add(term)
    return sorted(terms)


def checked_request(n, factors, order, budget):
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative exact integer")
    if n > budget.limits['max_variables']:
        raise Exhausted("variable cap")
    if type(factors) not in (list, tuple):
        raise ValueError("factor list required")
    if len(factors) > budget.limits['max_factors']:
        raise Exhausted("factor cap")
    checked = []
    for factor in factors:
        budget.tick()
        if type(factor) is not dict:
            raise ValueError("factor dictionary required")
        if factor.get('kind') == 'or' and set(factor) == {'kind', 'literals'}:
            literals = factor['literals']
            if (type(literals) not in (list, tuple)
                    or any(type(x) is not int or x == 0 or abs(x) > n for x in literals)):
                raise ValueError("invalid literal")
            checked.append({'kind': 'or', 'literals': list(literals)})
            budget.tick(len(literals))
        elif factor.get('kind') == 'affine' and set(factor) == {'kind', 'scope', 'equations', 'phase', 'scalar'}:
            scope = factor['scope']
            if (type(scope) not in (list, tuple)
                    or any(type(v) is not int or not 0 <= v < n for v in scope)
                    or len(set(scope)) != len(scope)):
                raise ValueError("invalid affine scope")
            mask = sum(1 << v for v in scope)
            rows = factor['equations']; phase = factor['phase']
            if type(rows) not in (list, tuple) or type(phase) not in (list, tuple):
                raise ValueError("explicit rows and phase required")
            for row in rows:
                if (type(row) not in (list, tuple) or len(row) != 2
                        or type(row[0]) is not int or row[0] < 0 or row[0] & ~mask
                        or type(row[1]) is not int or row[1] not in (0, 1)):
                    raise ValueError("invalid affine row")
            if any(type(t) is not int or t < 0 or t & ~mask or t.bit_count() > 2 for t in phase):
                raise ValueError("invalid quadratic phase")
            scale = budget.rational(rational(factor['scalar']))
            checked.append({'kind': 'affine', 'scope': list(scope),
                            'equations': [list(r) for r in rows], 'phase': list(phase), 'scalar': pack(scale)})
            budget.tick(len(rows) + len(phase) + len(scope))
        else:
            raise ValueError("unknown factor schema")
    m = len(checked)
    if order is not None and type(order) not in (list, tuple):
        raise ValueError("explicit factor order required")
    order = list(range(m)) if order is None else list(order)
    if (len(order) != m or any(type(i) is not int or not 0 <= i < m for i in order)
            or len(set(order)) != m):
        raise ValueError("order must cover every original factor exactly once")
    return checked, order


def source_terms(factor):
    """Exact local decomposition; scope means variables used after normalization."""
    if factor['kind'] == 'affine':
        return sorted(factor['scope']), [(factor['equations'], xor_phase(factor['phase']), rational(factor['scalar']))]
    literals = set(factor['literals'])
    if any(-x in literals for x in literals):
        return [], [([], [], Fraction(1))]
    if not literals:
        return [], []
    scope = sorted(abs(x)-1 for x in literals)
    violation = [[1 << (abs(x)-1), int(x < 0)]
                 for x in sorted(literals, key=lambda x: abs(x))]
    return scope, [([], [], Fraction(1)), (violation, [], Fraction(-1))]


def components(ids, scopes, budget):
    """Adapt the existing clause/component recurrence; no family labels."""
    parent = {i: i for i in ids}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    owners = {}
    for i in ids:
        for variable in scopes[i]:
            budget.tick()
            if variable in owners:
                parent[find(i)] = find(owners[variable])
            else:
                owners[variable] = i
    groups = defaultdict(list)
    for i in ids: groups[find(i)].append(i)
    return list(groups.values())


def _request_args(n, active, retained, equations, phase, scalar):
    return {'n': n, 'active': list(active), 'retained': list(retained),
            'equations': [list(row) for row in equations], 'phase': list(phase), 'scalar': pack(scalar)}


def solve_factors(n, factors, *, order=None, boundary_caps=None, compression_caps=None, **caps):
    budget = Budget(caps)
    compressor = CompressionMeter(budget, compression_caps)
    binding = None
    try:
        factors, order = checked_request(n, factors, order, budget)
        binding = digest({'n': n, 'factors': factors, 'order': order})
        source = [source_terms(factor) for factor in factors]
        scopes = [set(scope) for scope, terms in source]
        occurrences = Counter(v for scope in scopes for v in scope)
        records, marginal_cache, nodes = [], {}, []
        b = boundary_module()

        def project(active, retained, equations, phase, scalar):
            request = _request_args(n, active, retained, equations, phase, scalar)
            key = digest(request)
            if key in marginal_cache:
                index = marginal_cache[key]
                if records[index]['request'] == request:
                    budget.stats['marginal_cache_hits'] += 1
                    return index, records[index]['result']['message']
            budget.node()
            result = b.marginalize(n, retained, equations, phase, scalar,
                                   active=active, **(boundary_caps or {}))
            budget.tick(result.get('stats', {}).get('work', 0))
            if result['status'] != 'EXACT':
                raise Exhausted("boundary marginalization cap")
            index = len(records)
            records.append({'request': request, 'result': result})
            marginal_cache[key] = index
            budget.stats['marginal_requests'] += 1
            return index, result['message']

        def make(ids, children=None):
            budget.node()
            inside = Counter(v for i in ids for v in scopes[i])
            boundary = sorted(v for v in inside if inside[v] < occurrences[v])
            requests, generated = [], []
            if children is None:
                if ids:
                    active, terms = source[ids[0]]
                    kind = 'leaf'
                else:
                    active, terms, kind = [], [([], [], Fraction(1))], 'identity'
                for rows, phase, scalar in terms:
                    ref, message = project(active, boundary, rows, phase, scalar)
                    requests.append(ref); generated.append(message)
            else:
                kind = 'product'
                left, right = (nodes[i] for i in children)
                active = sorted(set(left['boundary']) | set(right['boundary']))
                budget.products(len(left['messages'])*len(right['messages']))
                for first in left['messages']:
                    for second in right['messages']:
                        rows = first['equations'] + second['equations']
                        phase = xor_phase(first['phase'], second['phase'])
                        scalar = budget.rational(rational(first['scalar'])*rational(second['scalar']))
                        ref, message = project(active, boundary, rows, phase, scalar)
                        requests.append(ref); generated.append(message)
            compression, messages = compressor.reduce(n, boundary, generated)
            node = {'kind': kind, 'factor_ids': sorted(ids), 'boundary': boundary,
                    'active': list(active), 'children': [] if children is None else list(children),
                    'requests': requests, 'compression': compression, 'messages': messages}
            nodes.append(node)
            return len(nodes)-1

        def tree(ids):
            if len(ids) <= 1: return make(ids)
            middle = len(ids)//2
            left = tree(ids[:middle]); right = tree(ids[middle:])
            return make(ids, [left, right])

        roots = [tree(group) for group in components(order, scopes, budget)]
        if not roots:
            root = tree([])
        else:
            while len(roots) > 1:
                next_roots = []
                for i in range(0, len(roots), 2):
                    if i+1 == len(roots): next_roots.append(roots[i]); continue
                    left, right = roots[i:i+2]
                    ids = nodes[left]['factor_ids'] + nodes[right]['factor_ids']
                    next_roots.append(make(ids, [left, right]))
                roots = next_roots
            root = roots[0]
        free = [v for v in range(n) if v not in occurrences]
        value = budget.rational(sum((rational(piece['scalar']) for piece in nodes[root]['messages']), Fraction(0)))
        value = add_free_variables(value, len(free), budget)
        certificate = {'format': 'compressed-affine-dag-v1', 'request_sha256': binding,
                       'root': root, 'nodes': nodes, 'marginals': records,
                       'free_variables': free, 'value': pack(value)}
        return {'status': 'EXACT', 'value': pack(value), 'count': None,
                'certificate': certificate, 'request_sha256': binding, 'stats': budget.stats}
    except Exhausted as exc:
        return {'status': 'UNKNOWN', 'value': None, 'count': None, 'certificate': None,
                'request_sha256': binding, 'reason': str(exc), 'stats': budget.stats}


def verify_factors(n, factors, result, *, order=None, boundary_caps=None, compression_caps=None, **caps):
    """Replay ownership, every pair, exact marginal proofs, merges and total."""
    budget = Budget(caps)
    compressor = CompressionMeter(budget, compression_caps)
    try:
        factors, order = checked_request(n, factors, order, budget)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return {'valid': False, 'status': 'UNKNOWN', 'errors': ['no exact result'], 'stats': budget.stats}
        binding = digest({'n': n, 'factors': factors, 'order': order})
        cert = result['certificate']
        if (cert['format'] != 'compressed-affine-dag-v1' or cert['request_sha256'] != binding
                or result['request_sha256'] != binding):
            raise ValueError("wrong external original request")
        nodes, records, root = cert['nodes'], cert['marginals'], cert['root']
        if type(nodes) is not list or type(records) is not list or not nodes:
            raise ValueError("invalid DAG arrays")
        if type(root) is not int or root != len(nodes)-1:
            raise ValueError("root must be last topological node")
        if len(nodes)+len(records) > budget.limits['max_nodes']:
            raise Exhausted("certificate node cap")
        source = [source_terms(factor) for factor in factors]
        scopes = [set(scope) for scope, terms in source]
        occurrences = Counter(v for scope in scopes for v in scope)
        verified_requests, used_nodes, verified_messages = {}, set(), []
        b = boundary_module()

        def project_reference(ref, request):
            if type(ref) is not int or not 0 <= ref < len(records):
                raise ValueError("invalid marginal reference")
            record = records[ref]
            if not identical(record['request'], request):
                raise ValueError("marginal request does not match original derived operands")
            if ref not in verified_requests:
                budget.node()
                checked = b.verify_marginal(n, request['retained'], request['equations'], request['phase'],
                                            request['scalar'], record['result'], active=request['active'],
                                            **(boundary_caps or {}))
                budget.tick(checked.get('stats', {}).get('work', 0))
                if checked['status'] == 'UNKNOWN': raise Exhausted("boundary verification cap")
                if not checked['valid']: raise ValueError("invalid marginal proof")
                verified_requests[ref] = checked['message']
                budget.stats['marginal_requests'] += 1
            else:
                budget.stats['marginal_cache_hits'] += 1
            return verified_requests[ref]

        for index, node in enumerate(nodes):
            budget.node()
            ids, children = node['factor_ids'], node['children']
            if (type(ids) is not list or any(type(i) is not int or not 0 <= i < len(factors) for i in ids)
                    or ids != sorted(set(ids)) or type(children) is not list):
                raise ValueError("invalid factor ownership")
            inside = Counter(v for i in ids for v in scopes[i])
            boundary = sorted(v for v in inside if inside[v] < occurrences[v])
            if not identical(node['boundary'], boundary): raise ValueError("wrong original boundary")
            expected_requests = []
            if node['kind'] in ('leaf', 'identity'):
                if children: raise ValueError("leaf with children")
                if node['kind'] == 'leaf':
                    if len(ids) != 1: raise ValueError("leaf must own one original factor")
                    active, terms = source[ids[0]]
                else:
                    if factors or ids or len(nodes) != 1: raise ValueError("identity only for empty original input")
                    active, terms = [], [([], [], Fraction(1))]
                expected_requests = [_request_args(n, active, boundary, rows, phase, scalar)
                                     for rows, phase, scalar in terms]
            elif node['kind'] == 'product':
                if (len(children) != 2 or any(type(c) is not int or not 0 <= c < index for c in children)
                        or children[0] == children[1]):
                    raise ValueError("invalid topological product children")
                left, right = (nodes[c] for c in children)
                left_ids, right_ids = set(left['factor_ids']), set(right['factor_ids'])
                if left_ids & right_ids or left_ids | right_ids != set(ids):
                    raise ValueError("children do not partition original factors")
                used_nodes.update(children)
                active = sorted(set(left['boundary']) | set(right['boundary']))
                left_messages, right_messages = (verified_messages[c] for c in children)
                budget.products(len(left_messages)*len(right_messages))
                for first in left_messages:
                    for second in right_messages:
                        coefficient = budget.rational(rational(first['scalar'])*rational(second['scalar']))
                        expected_requests.append(_request_args(n, active, boundary,
                            first['equations']+second['equations'], xor_phase(first['phase'], second['phase']), coefficient))
            else:
                raise ValueError("unknown node kind")
            if not identical(node['active'], list(active)): raise ValueError("wrong projected variable universe")
            refs = node['requests']
            if type(refs) is not list or len(refs) != len(expected_requests):
                raise ValueError("omitted or additional product/leaf terms")
            generated = [project_reference(ref, request) for ref, request in zip(refs, expected_requests)]
            checked_compression, merged = compressor.reduce(n, boundary, generated, node['compression'])
            if not identical(node['messages'], merged):
                raise ValueError("incorrect canonical coefficient merge")
            verified_messages.append(merged)
        if nodes[root]['factor_ids'] != list(range(len(factors))) or nodes[root]['boundary']:
            raise ValueError("root omits original factors or has a boundary")
        if used_nodes != set(range(len(nodes)-1)) or set(verified_requests) != set(range(len(records))):
            raise ValueError("unreachable structural or arithmetic nodes")
        free = [v for v in range(n) if v not in occurrences]
        if not identical(cert['free_variables'], free): raise ValueError("wrong original free variables")
        value = budget.rational(sum((rational(piece['scalar']) for piece in verified_messages[root]), Fraction(0)))
        value = add_free_variables(value, len(free), budget)
        if not identical(cert['value'], pack(value)) or not identical(result['value'], pack(value)):
            raise ValueError("wrong original contraction")
        return {'valid': True, 'status': 'VERIFIED', 'value': pack(value), 'errors': [], 'stats': budget.stats}
    except Exhausted as exc:
        return {'valid': False, 'status': 'UNKNOWN', 'errors': [str(exc)], 'stats': budget.stats}
    except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError, ZeroDivisionError) as exc:
        return {'valid': False, 'status': 'INVALID', 'errors': [str(exc)], 'stats': budget.stats}


def solve_formula(n, clauses, *, order=None, boundary_caps=None, compression_caps=None, **caps):
    if type(clauses) not in (list, tuple): raise ValueError("clause list required")
    result = solve_factors(n, [{'kind': 'or', 'literals': clause} for clause in clauses],
                           order=order, boundary_caps=boundary_caps, compression_caps=compression_caps, **caps)
    if result['status'] == 'EXACT':
        value = rational(result['value'])
        if value.denominator != 1 or value < 0: raise ArithmeticError("invalid original SAT count")
        result['count'] = value.numerator
    return result


def verify_formula(n, clauses, result, *, order=None, boundary_caps=None, compression_caps=None, **caps):
    if type(clauses) not in (list, tuple):
        return {'valid': False, 'status': 'INVALID', 'errors': ['clause list required']}
    checked = verify_factors(n, [{'kind': 'or', 'literals': clause} for clause in clauses], result,
                             order=order, boundary_caps=boundary_caps, compression_caps=compression_caps, **caps)
    if checked['valid']:
        value = rational(checked['value'])
        if value.denominator != 1 or value < 0 or type(result.get('count')) is not int or result['count'] != value.numerator:
            return {'valid': False, 'status': 'INVALID', 'errors': ['wrong original SAT count'], 'stats': checked['stats']}
    return checked
