"""Independent fast-wrapper review over the frozen explicit-sum records."""
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
NIGHT = HERE.parent
spec = importlib.util.spec_from_file_location('_fast_review_module', HERE/'fast_recognition.py')
fast = importlib.util.module_from_spec(spec); sys.modules[spec.name] = fast; spec.loader.exec_module(fast)


def digest(path): return sha256(path.read_bytes()).hexdigest()


def val(message, word):
    if message['zero']: return Fraction(0)
    for mask, rhs in message['equations']:
        if (word & mask).bit_count() % 2 != rhs: return Fraction(0)
    sign = sum((word & mask) == mask for mask in message['phase']) % 2
    c = Fraction(*message['scalar'])
    return -c if sign else c


def direct_values(request):
    n = request['n']; ids = request['retained']; messages = request['messages']
    return [sum((val(m, word) for m in messages), Fraction(0)) for word in range(1 << n)]


def affine_support(values):
    support = {i for i, value in enumerate(values) if value}
    if not support: return True
    anchor = min(support)
    differences = {x ^ anchor for x in support}
    return all(a ^ b in differences for a in differences for b in differences)


def quadratic_sign(values):
    support = {i for i, value in enumerate(values) if value}
    if not support: return True
    anchor = min(support); directions = []
    span = {0}
    for x in sorted(support):
        delta = x ^ anchor
        if delta not in span:
            directions.append(delta); span |= {y ^ delta for y in list(span)}
    if span != {x ^ anchor for x in support}: return False
    # Evaluate signs on the affine coordinates and recover the degree<=2
    # Boolean Mobius coefficients directly from low-weight values.
    indexed = {0: values[anchor]}
    for mask in range(1, 1 << len(directions)):
        word = anchor
        for i, direction in enumerate(directions):
            if mask >> i & 1: word ^= direction
        indexed[mask] = values[word]
    magnitude = abs(indexed[0])
    if not magnitude or any(abs(v) != magnitude for v in indexed.values()): return False
    signs = {mask: int(indexed[mask] != indexed[0]) for mask in indexed}
    for mask in indexed:
        predicted = signs[0]
        for i in range(len(directions)):
            if mask >> i & 1: predicted ^= signs[1 << i]
        for i in range(len(directions)):
            for j in range(i+1, len(directions)):
                if mask >> i & 1 and mask >> j & 1:
                    # Mobius coefficient is the third finite difference over
                    # the two coordinate axes.
                    predicted ^= signs[(1 << i) | (1 << j)] ^ signs[1 << i] ^ signs[1 << j] ^ signs[0]
        if predicted != signs[mask]: return False
    return True


def direct_one_piece(values):
    if not any(values): return True
    return affine_support(values) and quadratic_sign(values)


def main():
    results_path = NIGHT/'affine_one_piece_lab'/'RESULTS.json'
    saved = json.loads(results_path.read_text())
    records = sum((saved[key] for key in ('named_controls','all_small_ternary_tables',
                                          'all_three_bit_sign_tables','seeded_explicit_sums')), [])
    assert len(records) == 494
    before = {name: digest(path) for name, path in {
        'fast_recognition.py': HERE/'fast_recognition.py',
        'one_piece.py': NIGHT/'affine_one_piece_lab'/'one_piece.py',
        'partition.py': NIGHT/'affine_partition_compression_lab'/'partition.py',
        'reference.py': NIGHT/'affine_boundary_reference'/'reference.py',
        'RESULTS.json': results_path,
    }.items()}
    status_counts = {'EXACT':0, 'UNSUPPORTED':0, 'UNKNOWN':0}
    mismatches = []; direct_checked = 0; mutation_rejects = 0; total_work = 0
    for index, record in enumerate(records):
        request = record['original_request']; expected = record.get('result', {}).get('status')
        # Every result is independently recomputed by the fast wrapper. For
        # n<=3, compare against a separate direct truth-table oracle.
        result = fast.recognize(request['n'], request['retained'], request['messages'])
        status_counts[result['status']] = status_counts.get(result['status'],0)+1
        total_work += result['stats']['work']
        checked = fast.verify_one_piece(request['n'], request['retained'], request['messages'], result)
        assert checked['valid'] or result['status']=='UNKNOWN', (index, checked)
        if result['status'] == 'UNSUPPORTED':
            assert expected != 'EXACT', (index, expected)
        if request['n'] <= 3:
            values = direct_values(request); direct_checked += 1
            direct = direct_one_piece(values)
            if direct and result['status']=='UNSUPPORTED': mismatches.append((index,'false rejection'))
            if not direct and result['status']=='EXACT': mismatches.append((index,'false acceptance'))
        if index < 12:
            bad = json.loads(json.dumps(result))
            if bad.get('certificate'):
                bad['certificate']['input_sha256'] = '0'*64
                mut = fast.verify_one_piece(request['n'], request['retained'], request['messages'], bad)
                assert not mut['valid']
                mutation_rejects += 1
    assert not mismatches, mismatches
    after = {name: digest(path) for name, path in {
        'fast_recognition.py': HERE/'fast_recognition.py',
        'one_piece.py': NIGHT/'affine_one_piece_lab'/'one_piece.py',
        'partition.py': NIGHT/'affine_partition_compression_lab'/'partition.py',
        'reference.py': NIGHT/'affine_boundary_reference'/'reference.py',
        'RESULTS.json': results_path,
    }.items()}
    assert before == after
    output = dict(status='VERIFIED_FAST_WRAPPER_REVIEW', source_hashes_before=before,
                  source_hashes_after=after, source_unchanged_during_review=True,
                  saved_requests=len(records), status_counts=status_counts,
                  direct_truth_table_cases=direct_checked, rejected_binding_mutations=mutation_rejects,
                  total_work=total_work,
                  scope='Fast negative probes are checked against a direct oracle for all n<=3 records. Larger records are checked for no false UNSUPPORTED on saved exact claims and for complete certificate replay. UNKNOWN is never promoted to a claim; this review does not prove a polynomial SAT algorithm.')
    (HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ('status','saved_requests','status_counts','direct_truth_table_cases','rejected_binding_mutations')}))


if __name__ == '__main__': main()
