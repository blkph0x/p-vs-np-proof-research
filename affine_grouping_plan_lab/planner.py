"""Occurrence-preserving complete-XOR3 clause grouping, never a SAT solver.

Discovery adapts the fixed-support bucket idea from the existing
proof_motif_candidate_lab/miner.py:detect_parity_blocks. Its verifier is not
used. Every proposal is independently rebound to all original clause IDs.
"""
from hashlib import sha256


LIMITS = dict(max_variables=1024, max_clauses=4096, max_literals=100000,
              max_blocks=1024, max_work=1000000)


class Exhausted(Exception):
    pass


class Meter:
    def __init__(self, caps):
        if set(caps)-set(LIMITS):
            raise ValueError('unknown planner cap')
        self.limits = {**LIMITS, **caps}
        if any(type(x) is not int or x < 0 for x in self.limits.values()):
            raise ValueError('planner caps must be nonnegative exact integers')
        self.stats = dict(work=0, clauses=0, literals=0, eligible_occurrences=0,
                          support_buckets=0, candidate_buckets=0,
                          rejected_buckets=0, blocks=0, grouped_occurrences=0)

    def tick(self, amount=1):
        self.stats['work'] += amount
        if self.stats['work'] > self.limits['max_work']:
            raise Exhausted('planner work cap')

    def block(self):
        self.stats['blocks'] += 1
        if self.stats['blocks'] > self.limits['max_blocks']:
            raise Exhausted('planner block cap')

    def ordered(self, values):
        values = list(values)
        self.tick(2*len(values)*max(1, len(values).bit_length()))
        return sorted(values)


def input_hash(n, clauses):
    h = sha256(b'xor3-occurrence-grouping-v1\0')
    def number(x):
        data = abs(x).to_bytes(max(1, (abs(x).bit_length()+7)//8), 'big')
        h.update(bytes([x < 0])+len(data).to_bytes(8, 'big')+data)
    number(n); number(len(clauses))
    for clause in clauses:
        number(len(clause))
        for literal in clause:
            number(literal)
    return h.hexdigest()


def checked_original(n, clauses, meter):
    if type(n) is not int or n < 0:
        raise ValueError('n must be a nonnegative exact integer')
    if n > meter.limits['max_variables']:
        raise Exhausted('planner variable cap')
    if type(clauses) not in (list, tuple):
        raise ValueError('explicit original clause list required')
    if len(clauses) > meter.limits['max_clauses']:
        raise Exhausted('planner clause cap')
    original = []
    for clause in clauses:
        meter.tick()
        meter.stats['clauses'] += 1
        if type(clause) not in (list, tuple):
            raise ValueError('explicit original clause required')
        copied = []
        for literal in clause:
            meter.tick(); meter.stats['literals'] += 1
            if meter.stats['literals'] > meter.limits['max_literals']:
                raise Exhausted('planner literal cap')
            if type(literal) is not int or literal == 0 or abs(literal) > n:
                raise ValueError('invalid original literal')
            copied.append(literal)
        original.append(copied)
    return original


def _discovery_buckets(clauses, meter):
    buckets = {}
    for index, clause in enumerate(clauses):
        meter.tick()
        if len(clause) != 3:
            continue
        support = tuple(sorted(abs(lit)-1 for lit in clause))
        meter.tick(6)  # bounded three-literal extraction/sort bookkeeping
        if len(set(support)) != 3:
            continue
        positions = {variable: j for j, variable in enumerate(support)}
        word = sum((int(lit < 0) << positions[abs(lit)-1]) for lit in clause)
        meter.tick(3)
        meter.stats['eligible_occurrences'] += 1
        buckets.setdefault(support, []).append((word, index))
    meter.stats['support_buckets'] = len(buckets)
    return buckets


def plan(n, clauses, **caps):
    meter = Meter(caps)
    binding = None
    try:
        original = checked_original(n, clauses, meter)
        binding = input_hash(n, original)
        buckets = _discovery_buckets(original, meter)
        groups, used = [], set()
        for support in meter.ordered(buckets):
            items = buckets[support]
            meter.tick(1+len(items))
            meter.stats['candidate_buckets'] += 1
            words = {word for word, index in items}
            parity = {word.bit_count() % 2 for word in words}
            if len(items) != 4 or len(words) != 4 or len(parity) != 1:
                meter.stats['rejected_buckets'] += 1
                continue
            meter.block()
            forbidden = next(iter(parity))
            ordered = [index for word, index in meter.ordered(items)]
            used.update(ordered)
            groups.append(dict(support=list(support), occurrence_ids=ordered,
                               forbidden_parity=forbidden, rhs=1-forbidden))
        ungrouped = [i for i in range(len(original)) if i not in used]
        order = [i for block in groups for i in block['occurrence_ids']] + ungrouped
        meter.tick(len(original))
        meter.stats['grouped_occurrences'] = len(used)
        certificate = dict(kind='complete-xor3-order-v1', input_sha256=binding,
                           groups=groups, ungrouped_ids=ungrouped, order=order)
        return dict(status='EXACT', order=order, certificate=certificate,
                    input_sha256=binding, stats=meter.stats)
    except Exhausted as exc:
        return dict(status='UNKNOWN', order=None, certificate=None, input_sha256=binding,
                    reason=str(exc), stats=meter.stats)


def verify_plan(n, clauses, result, **caps):
    """Independent occurrence proof; does not invoke candidate discovery."""
    meter = Meter(caps)
    try:
        original = checked_original(n, clauses, meter)
        if type(result) is not dict or result.get('status') != 'EXACT':
            return dict(valid=False, status='UNKNOWN', order=None, errors=['no exact proposal'], stats=meter.stats)
        binding = input_hash(n, original)
        cert = result['certificate']
        if (type(cert) is not dict or set(cert) != {'kind', 'input_sha256', 'groups', 'ungrouped_ids', 'order'}
                or cert['kind'] != 'complete-xor3-order-v1' or cert['input_sha256'] != binding
                or result.get('input_sha256') != binding):
            raise ValueError('wrong external original formula')
        groups = cert['groups']
        if type(groups) is not list:
            raise ValueError('explicit block list required')
        # Index eligible original occurrences independently; no truth labels or
        # proposed block IDs are used to establish these complete buckets.
        occurrence_sets = {}
        for index, clause in enumerate(original):
            meter.tick()
            if len(clause) == 3:
                variables = {abs(literal)-1 for literal in clause}
                meter.tick(3)
                if len(variables) == 3:
                    occurrence_sets.setdefault(frozenset(variables), set()).add(index)
                    meter.stats['eligible_occurrences'] += 1
        meter.stats['support_buckets'] = len(occurrence_sets)
        used, previous_support, ordered_blocks = set(), None, []
        for group in groups:
            meter.block(); meter.tick()
            if type(group) is not dict or set(group) != {'support', 'occurrence_ids', 'forbidden_parity', 'rhs'}:
                raise ValueError('malformed block')
            support, ids = group['support'], group['occurrence_ids']
            if (type(support) is not list or len(support) != 3
                    or any(type(v) is not int or not 0 <= v < n for v in support)
                    or support != sorted(set(support))):
                raise ValueError('block support must contain three distinct exact original IDs')
            if previous_support is not None and tuple(support) <= previous_support:
                raise ValueError('blocks must have distinct sorted supports')
            previous_support = tuple(support)
            if (type(ids) is not list or len(ids) != 4
                    or any(type(i) is not int or not 0 <= i < len(original) for i in ids)
                    or len(set(ids)) != 4 or used.intersection(ids)):
                raise ValueError('block must own four distinct unused original occurrence IDs')
            if occurrence_sets.get(frozenset(support), set()) != set(ids):
                raise ValueError('extra or missing eligible occurrences on the claimed support')
            forbidden = group['forbidden_parity']
            if type(forbidden) is not int or forbidden not in (0, 1) or type(group['rhs']) is not int or group['rhs'] != 1-forbidden:
                raise ValueError('invalid exact parity metadata')
            expected = {word for word in range(8) if word.bit_count() % 2 == forbidden}
            seen, words = set(), []
            for index in ids:
                clause = original[index]
                if len(clause) != 3:
                    raise ValueError('block clause does not have exactly three literals')
                signs = {}
                for literal in clause:
                    meter.tick()
                    variable = abs(literal)-1
                    if variable in signs:
                        raise ValueError('repeated variable in block clause')
                    signs[variable] = literal < 0
                if set(signs) != set(support):
                    raise ValueError('clause not on the claimed full support')
                word = sum(int(signs[v]) << j for j, v in enumerate(support))
                seen.add(word); words.append(word)
            if seen != expected or words != meter.ordered(expected):
                raise ValueError('block is not the complete ordered single-parity forbidden set')
            used.update(ids); ordered_blocks.extend(ids)
        ungrouped = cert['ungrouped_ids']
        expected_ungrouped = [i for i in range(len(original)) if i not in used]
        if (type(ungrouped) is not list or any(type(i) is not int for i in ungrouped)
                or ungrouped != expected_ungrouped):
            raise ValueError('ungrouped occurrences must be the complete original-order complement')
        expected_order = ordered_blocks + expected_ungrouped
        meter.tick(len(expected_order))
        for order in (cert['order'], result.get('order')):
            if (type(order) is not list or any(type(i) is not int for i in order)
                    or order != expected_order or meter.ordered(order) != list(range(len(original)))):
                raise ValueError('proposed order is not the exact complete occurrence permutation')
        meter.stats['grouped_occurrences'] = len(used)
        return dict(valid=True, status='VERIFIED', order=expected_order,
                    groups=[dict(group) for group in groups], errors=[], stats=meter.stats)
    except Exhausted as exc:
        return dict(valid=False, status='UNKNOWN', order=None, errors=[str(exc)], stats=meter.stats)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError) as exc:
        return dict(valid=False, status='INVALID', order=None, errors=[str(exc)], stats=meter.stats)


propose_order = plan
verify = verify_plan
