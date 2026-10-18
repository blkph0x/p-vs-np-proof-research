"""Retain a five-piece local trap whose exact minimum is two pieces."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCES = ['affine_recognition_limits.py',
           'affine_compression_review/review_oracles.py',
           'affine_boundary_reference/reference.py',
           'affine_sum_compression_lab/compression.py',
           'affine_boundary_lab/boundary.py']


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE/relative)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def hashes():
    return {p: hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in SOURCES}


def main():
    before = hashes()
    oracle = module('recognition_limits_oracle', 'affine_compression_review/review_oracles.py')
    compression = module('recognition_limits_compression', 'affine_sum_compression_lab/compression.py')
    lines = [oracle.affine_span_message(pair) for pair in ([0, 1], [4, 6], [3, 7], [2, 5])]
    rows = []
    for n in (3, 16, 64):
        ids = list(range(n))
        originals = [oracle.canonical(n, ids, line['equations']) for line in lines]
        extra = oracle.canonical(n, ids, [[1, 0], [2, 0], [4, 0]])
        originals.append(extra)
        target = [oracle.canonical(n, ids), extra]
        reduced = compression.compress(n, ids, originals)
        checked = compression.verify_compression(n, ids, originals, reduced)
        assert reduced['status'] == 'EXACT' and checked['valid']
        assert len(reduced['messages']) == 5
        proof = oracle.norm_identity(n, ids, originals, target, save_proofs=True)
        norm_check = oracle.verify_norm_identity(n, ids, originals, target, proof)
        assert norm_check['valid'] and norm_check['equal']
        # All pieces depend on only the first three coordinates, so these
        # eight words exhaust the relevant truth table for every stated n.
        assert all(not any(mask >> 3 for mask, rhs in m['equations'])
                   and not m['phase'] for m in originals+target)
        values = [sum(oracle.point(m, word) for m in originals) for word in range(8)]
        assert values == [2, 1, 1, 1, 1, 1, 1, 1]
        rows.append(dict(n=n, retained=ids, originals=originals, target=target,
                         local_compression=reduced, local_verification=checked,
                         equality_norm=proof, norm_verification=norm_check,
                         values_on_first_three_bits=[int(v) for v in values],
                         minimum_piece_count=2,
                         minimum_proof='Equality norm verifies two pieces suffice. The function is nonzero on every input and has magnitudes 2 and 1, so no single affine quadratic piece can represent it.'))
    assert before == hashes()
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  source_sha256=before, source_unchanged=True, cases=rows,
                  scope='Five-piece local trap with exact minimum two. Whole-sum one-piece rejection is correct but does not find a compressible proper subgroup. No SAT lower bound.')
    (HERE/'AFFINE_RECOGNITION_LIMITS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'cases': len(rows), 'widths': [r['n'] for r in rows],
                      'local_output_pieces': 5, 'verified_minimum_pieces': 2,
                      'norm_products': sum(r['equality_norm']['block_checks'] for r in rows)}))


if __name__ == '__main__':
    main()
