"""Source-bound streaming rewrites of compact real-affine sums.

No boundary truth tables are enumerated. Retained-size caps apply between
arrivals; actual live IDs and pending canonical objects are reported separately.
Failed-pair records preserve the sum but do not certify optimal irreducibility.
"""
from fractions import Fraction
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().parent.parent/'affine_boundary_lab'/'boundary.py'
_spec = importlib.util.spec_from_file_location('affine_sum_boundary', _path)
boundary = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = boundary
_spec.loader.exec_module(boundary)

LIMITS = dict(max_variables=4096, max_inputs=100000, max_generated=100000,
              max_live_pieces=4096, max_pairs=100000, max_steps=200000,
              max_work=4000000, max_scalar_bits=65536, max_rows=16384,
              max_terms=100000)


class Exhausted(Exception):
    pass


class Meter:
    def __init__(self, caps):
        if set(caps)-set(LIMITS):
            raise ValueError('unknown compression cap')
        self.limits = {**LIMITS, **caps}
        if any(type(v) is not int or v < 0 for v in self.limits.values()):
            raise ValueError('caps must be nonnegative exact integers')
        self.stats = dict(work=0, incoming_pieces=0, generated_pieces=0,
                          peak_live_pieces=0, peak_retained_pieces=0,
                          peak_pending_input_objects=0, peak_pending_generated_objects=0,
                          peak_live_plus_pending_objects=0, attempted_pairs=0,
                          failed_pairs=0, identity_tests=0, failed_identity_tests=0,
                          normalizations=0, steps=0, peak_scalar_bits=0)

    def tick(self, amount=1):
        self.stats['work'] += amount
        if self.stats['work'] > self.limits['max_work']:
            raise Exhausted('algebra work cap')

    def reserve(self, key, cap):
        self.stats[key] += 1
        if self.stats[key] > self.limits[cap]:
            raise Exhausted(cap)

    def scalar(self, value):
        bits = max(abs(value.numerator).bit_length(), value.denominator.bit_length())
        self.stats['peak_scalar_bits'] = max(self.stats['peak_scalar_bits'], bits)
        if bits > self.limits['max_scalar_bits']:
            raise Exhausted('coefficient bit cap')
        return value

    def observe(self, live, pending_input=0, pending_generated=0, settled=False):
        self.stats['peak_live_pieces'] = max(self.stats['peak_live_pieces'], live)
        self.stats['peak_pending_input_objects'] = max(self.stats['peak_pending_input_objects'], pending_input)
        self.stats['peak_pending_generated_objects'] = max(self.stats['peak_pending_generated_objects'], pending_generated)
        self.stats['peak_live_plus_pending_objects'] = max(self.stats['peak_live_plus_pending_objects'], live+pending_input+pending_generated)
        if settled:
            self.stats['peak_retained_pieces'] = max(self.stats['peak_retained_pieces'], live)
            if live > self.limits['max_live_pieces']:
                raise Exhausted('retained pieces cap after arrival processing')

    def boundary_caps(self):
        return {key: self.limits[key] for key in ('max_variables', 'max_rows', 'max_terms', 'max_scalar_bits')} | {
            'max_steps': 0, 'max_work': max(0, self.limits['max_work']-self.stats['work'])}

    def normalization_work(self, result):
        self.stats['normalizations'] += 1
        self.stats['peak_scalar_bits'] = max(self.stats['peak_scalar_bits'], result.get('stats', {}).get('peak_scalar_bits', 0))
        self.tick(result.get('stats', {}).get('work', 0))
        if result['status'] == 'UNKNOWN':
            raise Exhausted('boundary normalization cap')


def _header(n, retained, meter):
    if type(n) is not int or n < 0:
        raise ValueError('n must be a nonnegative exact integer')
    if n > meter.limits['max_variables']:
        raise Exhausted('coordinate dimension cap')
    if type(retained) not in (list, tuple) or any(type(i) is not int or not 0 <= i < n for i in retained) or len(set(retained)) != len(retained):
        raise ValueError('retained must be an ordered list of distinct original IDs')
    meter.tick(len(retained)+1)
    return list(retained)


def _equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(_equal(a[k], b[k]) for k in a)
    if type(a) in (list, tuple):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    return a == b


def _shape(message, n, retained):
    fields = {'n', 'retained', 'zero', 'equations', 'phase', 'scalar', 'free_ids'}
    if type(message) is not dict or set(message) != fields or type(message['n']) is not int or message['n'] != n:
        raise ValueError('invalid original canonical message')
    if not _equal(message['retained'], retained) or type(message['zero']) is not bool:
        raise ValueError('wrong original retained coordinates')
    if any(type(message[key]) is not list for key in ('equations', 'phase', 'scalar', 'free_ids')):
        raise ValueError('canonical message fields must be lists')


class Binding:
    def __init__(self, n, retained):
        self.hash = sha256(b'compact-affine-sum-rewrite-v1')
        self.integer(n); self.integer(len(retained))
        for i in retained:
            self.integer(i)

    def integer(self, value):
        data = abs(value).to_bytes(max(1, (abs(value).bit_length()+7)//8), 'little')
        self.hash.update(bytes([value < 0]))
        self.hash.update(len(data).to_bytes(8, 'little')); self.hash.update(data)

    def piece(self, index, message):
        self.integer(index); self.integer(int(message['zero']))
        for values in (message['equations'], message['phase'], message['scalar'], message['free_ids']):
            self.integer(len(values))
            for value in values:
                if type(value) is list:
                    self.integer(len(value))
                    for item in value:
                        self.integer(item)
                else:
                    self.integer(value)

    def finish(self, count):
        self.integer(count)
        return self.hash.hexdigest()


def _normalize(n, retained, rows, phase, scalar, meter):
    meter.scalar(scalar)
    result = boundary.normalize_message(n, retained, rows, sorted(phase), scalar, **meter.boundary_caps())
    meter.normalization_work(result)
    return result


def _verify_normalization(n, retained, rows, phase, scalar, proof, meter):
    meter.scalar(scalar)
    result = boundary.verify_marginal(n, retained, rows, sorted(phase), scalar, proof,
                                     active=retained, order=[], **meter.boundary_caps())
    meter.normalization_work(result)
    if not result['valid']:
        raise ValueError('invalid independently replayed normalization')
    return result['message']


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit
        mask ^= bit


def _toggle(poly, term):
    if term in poly:
        poly.remove(term)
    else:
        poly.add(term)


def _product(left, right, meter):
    out = set()
    for a in left:
        for b in right:
            _toggle(out, a | b)
            meter.tick()
    if len(out) > meter.limits['max_terms']:
        raise Exhausted('phase term cap')
    return out


def _pivots(message):
    return [i for i in message['retained'] if i not in message['free_ids']]


def _reduce_row(row, message, meter):
    mask, rhs = row
    for variable, (other, value) in zip(_pivots(message), message['equations']):
        if mask & (1 << variable):
            mask ^= other; rhs ^= value
        meter.tick()
    return mask, rhs


def _restrict_phase(poly, support, meter):
    out = set(poly)
    for variable, (mask, rhs) in zip(_pivots(support), support['equations']):
        bit = 1 << variable
        replacement = list(_bits(mask ^ bit)) + ([0] if rhs else [])
        changed = set()
        for term in out:
            if term & bit:
                for item in replacement:
                    _toggle(changed, (term ^ bit) | item)
                    meter.tick()
            else:
                _toggle(changed, term); meter.tick()
        out = changed
        if len(out) > meter.limits['max_terms']:
            raise Exhausted('restricted phase term cap')
    return out


def _discover(left, right, meter):
    c, d = boundary.ratio(left['scalar']), boundary.ratio(right['scalar'])
    difference = set(left['phase']) ^ set(right['phase'])
    meter.tick(len(left['phase'])+len(right['phase'])+len(left['equations'])+len(right['equations'])+1)

    def test():
        meter.stats['identity_tests'] += 1
        meter.tick()

    def failed():
        meter.stats['failed_identity_tests'] += 1

    test()
    if boundary.message_key(left) == boundary.message_key(right):
        return 'identical', {}, left['equations'], set(left['phase']), meter.scalar(c+d)
    failed(); test()
    if left['equations'] == right['equations'] and abs(c) == abs(d) and all(term.bit_count() <= 1 for term in difference):
        rows = left['equations'] + [[sum(difference), int(d == -c)]]
        return 'same_support', {}, rows, set(left['phase']), meter.scalar(2*c)
    failed(); test()
    if ([row[0] for row in left['equations']] == [row[0] for row in right['equations']]
            and left['equations'] != right['equations'] and abs(c) == abs(d)
            and all(term.bit_count() <= 1 for term in difference)):
        delta = [a[1] ^ b[1] for a, b in zip(left['equations'], right['equations'])]
        j = delta.index(1)
        pivot_mask, pivot_rhs = left['equations'][j]
        rows = [[mask ^ (pivot_mask if delta[i] else 0), rhs ^ (pivot_rhs if delta[i] else 0)]
                for i, (mask, rhs) in enumerate(left['equations']) if i != j]
        selector = set(_bits(pivot_mask)) | ({0} if pivot_rhs else set())
        if d == -c:
            difference ^= {0}
        phase = set(left['phase']) ^ _product(selector, difference, meter)
        return 'parallel', {'row': j}, rows, phase, c
    failed()
    for outer, a, inner in (('left', left, right), ('right', right, left)):
        test()
        if len(inner['equations']) != len(a['equations'])+1:
            failed(); continue
        if any(_reduce_row(row, inner, meter) != (0, 0) for row in a['equations']):
            failed(); continue
        row_index = next((i for i, row in enumerate(inner['equations']) if _reduce_row(row, a, meter) != (0, 0)), None)
        if row_index is None:
            failed(); continue
        restricted = _restrict_phase(set(a['phase']) ^ set(inner['phase']), inner, meter)
        ca, cb = boundary.ratio(a['scalar']), boundary.ratio(inner['scalar'])
        if restricted - {0} or cb != (-ca if not restricted else ca):
            failed(); continue
        mask, rhs = inner['equations'][row_index]
        return 'nested', {'outer': outer, 'row': row_index}, a['equations']+[[mask, rhs ^ 1]], set(a['phase']), ca
    return None


def _rank(vectors, meter):
    basis = {}
    for vector in vectors:
        while vector:
            pivot = vector.bit_length()-1
            meter.tick()
            if pivot in basis:
                vector ^= basis[pivot]
            else:
                basis[pivot] = vector
                break
    return len(basis)


def _checker_restriction(phase, support, meter):
    expressions = {}
    for variable, (mask, rhs) in zip(_pivots(support), support['equations']):
        expressions[1 << variable] = set(_bits(mask ^ (1 << variable))) | ({0} if rhs else set())
    result = set()
    for term in phase:
        current = {0}
        for bit in _bits(term):
            following = set()
            for x in current:
                for y in expressions.get(bit, {bit}):
                    _toggle(following, x | y); meter.tick()
            current = following
        for item in current:
            _toggle(result, item); meter.tick()
        if len(result) > meter.limits['max_terms']:
            raise Exhausted('checker phase term cap')
    return result


def _check_identity(n, left, right, rule, parameters, meter):
    if type(parameters) is not dict:
        raise ValueError('rewrite parameters must be a dictionary')
    meter.stats['identity_tests'] += 1
    meter.tick(len(left['phase'])+len(right['phase'])+len(left['equations'])+len(right['equations'])+1)
    c, d = boundary.ratio(left['scalar']), boundary.ratio(right['scalar'])
    phase0, phase1 = set(left['phase']), set(right['phase'])
    if rule == 'identical':
        if parameters or left['equations'] != right['equations'] or phase0 != phase1:
            raise ValueError('different canonical functions in identical addition')
        return left['equations'], phase0, meter.scalar(c+d)
    if rule in ('parallel', 'same_support'):
        if abs(c) != abs(d):
            raise ValueError('unequal magnitudes')
        difference = phase0 ^ phase1
        if any(term.bit_count() > 1 for term in difference):
            raise ValueError('phase difference is not affine in common coordinates')
        sigma = int(d != c)
        if rule == 'same_support':
            if parameters or left['equations'] != right['equations']:
                raise ValueError('supports are different')
            mask = 0
            for term in difference:
                mask ^= term; meter.tick()
            return left['equations']+[[mask, sigma]], phase0, meter.scalar(2*c)
        if set(parameters) != {'row'} or type(parameters['row']) is not int:
            raise ValueError('invalid union row selector')
        rows0, rows1 = left['equations'], right['equations']
        j = parameters['row']
        if len(rows0) != len(rows1) or not 0 <= j < len(rows0):
            raise ValueError('parallel rank or selector mismatch')
        if any(a[0] != b[0] for a, b in zip(rows0, rows1)) or rows0[j][1] == rows1[j][1]:
            raise ValueError('not distinct parallel cosets at chosen row')
        combined = []
        for i in range(len(rows0)):
            if i != j:
                mask, rhs = rows0[i]
                if rows0[i][1] != rows1[i][1]:
                    mask ^= rows0[j][0]; rhs ^= rows0[j][1]
                combined.append([mask, rhs])
            meter.tick()
        if sigma:
            difference ^= {0}
        phase = set(phase0)
        selector = list(_bits(rows0[j][0])) + ([0] if rows0[j][1] else [])
        for term in difference:
            for bit in selector:
                _toggle(phase, term | bit); meter.tick()
        return combined, phase, c
    if rule == 'nested':
        if set(parameters) != {'outer', 'row'} or parameters['outer'] not in ('left', 'right') or type(parameters['row']) is not int:
            raise ValueError('invalid nested parameters')
        a, inner = (left, right) if parameters['outer'] == 'left' else (right, left)
        j = parameters['row']
        if len(inner['equations']) != len(a['equations'])+1 or not 0 <= j < len(inner['equations']):
            raise ValueError('nested support must have codimension one')
        augmented_a = [mask | (rhs << n) for mask, rhs in a['equations']]
        augmented_b = [mask | (rhs << n) for mask, rhs in inner['equations']]
        if _rank(augmented_b+augmented_a, meter) != len(augmented_b):
            raise ValueError('inner support is not contained in outer support')
        if _rank(augmented_a+[augmented_b[j]], meter) != len(augmented_a)+1:
            raise ValueError('extra nested row is not independent')
        restricted0 = _checker_restriction(set(a['phase']), inner, meter)
        restricted1 = _checker_restriction(set(inner['phase']), inner, meter)
        difference = restricted0 ^ restricted1
        ca, cb = boundary.ratio(a['scalar']), boundary.ratio(inner['scalar'])
        if difference - {0} or cb != ca * (1 if 0 in difference else -1):
            raise ValueError('nested contributions do not cancel on the inner support')
        mask, rhs = inner['equations'][j]
        return a['equations']+[[mask, rhs ^ 1]], set(a['phase']), ca
    raise ValueError('unknown rewrite identity')


def compress(n, retained, messages, **caps):
    meter = Meter(caps)
    try:
        retained = _header(n, retained, meter)
        binding = Binding(n, retained)
        live, events, next_id = {}, [], 0
        def event(item):
            meter.reserve('steps', 'max_steps'); events.append(item)
        def discard_zero(index):
            if live[index]['zero']:
                event(dict(kind='drop_zero', id=index)); del live[index]
                return True
            return False
        for original in messages:
            meter.observe(len(live), settled=True)
            meter.reserve('incoming_pieces', 'max_inputs')
            meter.observe(len(live), pending_input=1)
            _shape(original, n, retained)
            proof = _normalize(n, retained, original['equations'], original['phase'], boundary.ratio(original['scalar']), meter)
            if not _equal(original, proof['message']):
                raise ValueError('incoming message is not canonical')
            input_index = meter.stats['incoming_pieces']-1
            binding.piece(input_index, original)
            pending = next_id; next_id += 1
            live[pending] = proof['message']
            meter.observe(len(live))
            event(dict(kind='input', index=input_index, id=pending, normalization=proof))
            if discard_zero(pending):
                meter.observe(len(live), settled=True); continue
            while True:
                replacement = None
                for other in sorted(live):
                    if other == pending:
                        continue
                    meter.reserve('attempted_pairs', 'max_pairs')
                    candidate = _discover(live[other], live[pending], meter)
                    if candidate is None:
                        meter.stats['failed_pairs'] += 1
                        event(dict(kind='failed_pair', left=other, right=pending))
                        continue
                    rule, parameters, rows, phase, scalar = candidate
                    meter.reserve('generated_pieces', 'max_generated')
                    meter.observe(len(live), pending_generated=1)
                    proof = _normalize(n, retained, rows, phase, scalar, meter)
                    replacement = next_id; next_id += 1
                    event(dict(kind='rewrite', left=other, right=pending, id=replacement,
                               rule=rule, parameters=parameters, normalization=proof))
                    del live[other]; del live[pending]
                    live[replacement] = proof['message']
                    meter.observe(len(live))
                    break
                if replacement is None:
                    break
                pending = replacement
                if discard_zero(pending):
                    break
            meter.observe(len(live), settled=True)
        ids = sorted(live)
        certificate = dict(kind='streamed-affine-sum-v1', input_sha256=binding.finish(meter.stats['incoming_pieces']),
                           events=events, final_ids=ids)
        return dict(status='EXACT', messages=[live[i] for i in ids], certificate=certificate, stats=meter.stats)
    except Exhausted as exc:
        return dict(status='UNKNOWN', messages=None, certificate=None, reason=str(exc), stats=meter.stats)


def verify_compression(n, retained, original_messages, result, **caps):
    meter = Meter(caps)
    try:
        retained = _header(n, retained, meter)
        if type(result) is not dict or result.get('status') != 'EXACT' or type(result.get('certificate')) is not dict:
            raise ValueError('expected an EXACT compression proof')
        cert = result['certificate']
        if set(cert) != {'kind', 'input_sha256', 'events', 'final_ids'} or cert['kind'] != 'streamed-affine-sum-v1' or type(cert['events']) is not list:
            raise ValueError('invalid compression proof format')
        if len(cert['events']) > meter.limits['max_steps']:
            raise Exhausted('proof event cap')
        source = iter(original_messages)
        sentinel = object()
        binding = Binding(n, retained)
        live, next_id = {}, 0
        def sources(step):
            left, right = step.get('left'), step.get('right')
            if type(left) is not int or type(right) is not int or left == right or left not in live or right not in live:
                raise ValueError('rewrite must consume two distinct currently live IDs')
            if live[left]['zero'] or live[right]['zero']:
                raise ValueError('zero pieces must be dropped explicitly')
            return left, right
        for step in cert['events']:
            meter.reserve('steps', 'max_steps'); meter.tick()
            if type(step) is not dict:
                raise ValueError('malformed event')
            kind = step.get('kind')
            if kind == 'input':
                meter.observe(len(live), settled=True)
                if set(step) != {'kind', 'index', 'id', 'normalization'} or type(step['index']) is not int or step['index'] != meter.stats['incoming_pieces'] or type(step['id']) is not int or step['id'] != next_id:
                    raise ValueError('original indices and fresh IDs must be complete and sequential')
                meter.reserve('incoming_pieces', 'max_inputs')
                original = next(source, sentinel)
                if original is sentinel:
                    raise ValueError('proof invents an original input piece')
                meter.observe(len(live), pending_input=1)
                _shape(original, n, retained)
                normalized = _verify_normalization(n, retained, original['equations'], original['phase'], boundary.ratio(original['scalar']), step['normalization'], meter)
                if not _equal(original, normalized):
                    raise ValueError('original message is not canonical')
                binding.piece(step['index'], original)
                live[next_id] = normalized; next_id += 1
                meter.observe(len(live))
            elif kind == 'drop_zero':
                if set(step) != {'kind', 'id'} or type(step['id']) is not int or step['id'] not in live or not live[step['id']]['zero']:
                    raise ValueError('only a current verified zero may be dropped')
                del live[step['id']]
            elif kind == 'failed_pair':
                if set(step) != {'kind', 'left', 'right'}:
                    raise ValueError('malformed failed-pair observation')
                sources(step)
                meter.reserve('attempted_pairs', 'max_pairs')
                meter.stats['failed_pairs'] += 1
                # This no-op is not a maximality certificate. All values remain
                # unchanged regardless of whether another identity could apply.
            elif kind == 'rewrite':
                if set(step) != {'kind', 'left', 'right', 'id', 'rule', 'parameters', 'normalization'} or type(step['id']) is not int or step['id'] != next_id:
                    raise ValueError('invalid rewrite or reused generated ID')
                left, right = sources(step)
                meter.reserve('attempted_pairs', 'max_pairs')
                rows, phase, scalar = _check_identity(n, live[left], live[right], step['rule'], step['parameters'], meter)
                meter.reserve('generated_pieces', 'max_generated')
                meter.observe(len(live), pending_generated=1)
                normalized = _verify_normalization(n, retained, rows, phase, scalar, step['normalization'], meter)
                del live[left]; del live[right]
                live[next_id] = normalized; next_id += 1
                meter.observe(len(live))
            else:
                raise ValueError('unknown proof event')
        if next(source, sentinel) is not sentinel:
            raise ValueError('proof omits original input pieces')
        if cert['input_sha256'] != binding.finish(meter.stats['incoming_pieces']):
            raise ValueError('wrong external original sum binding')
        meter.observe(len(live), settled=True)
        ids = sorted(live)
        if any(message['zero'] for message in live.values()) or not _equal(cert['final_ids'], ids):
            raise ValueError('wrong final live IDs or undropped zero')
        messages = [live[i] for i in ids]
        if not _equal(result.get('messages'), messages):
            raise ValueError('incorrect final sum')
        return dict(valid=True, status='VERIFIED', messages=messages, errors=[], stats=meter.stats)
    except Exhausted as exc:
        return dict(valid=False, status='UNKNOWN', messages=None, errors=[str(exc)], stats=meter.stats)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError) as exc:
        return dict(valid=False, status='INVALID', messages=None, errors=[str(exc)], stats=meter.stats)


reduce_sum = compress
verify_sum = verify_compression
