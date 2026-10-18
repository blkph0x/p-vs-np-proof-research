"""Independent source-bound replay of the five-piece / minimum-two controls."""
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,HERE/path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def point(message,word):
    if message['zero'] or any((mask&word).bit_count()%2!=rhs for mask,rhs in message['equations']):
        return Fraction(0)
    parity=sum((mask&word)==mask for mask in message['phase'])%2
    return Fraction(*message['scalar'])*(-1 if parity else 1)


def main():
    saved=json.loads((HERE/'AFFINE_RECOGNITION_LIMITS.json').read_text())
    paths=list(saved['source_sha256'])+['AFFINE_RECOGNITION_LIMITS.json',
          'AFFINE_RECOGNITION_LIMITS_REVIEW.py','AFFINE_RECOGNITION_LIMITS_REVIEW.md']
    before={path:sha256((HERE/path).read_bytes()).hexdigest() for path in paths}
    assert saved['source_unchanged'] is True
    assert all(before[path]==expected for path,expected in saved['source_sha256'].items())
    compression=load('limits_review_compression','affine_sum_compression_lab/compression.py')
    oracle=load('limits_review_oracle','affine_compression_review/review_oracles.py')
    assert [case['n'] for case in saved['cases']]==[3,16,64]
    rows=[]
    for case in saved['cases']:
        n,ids,originals,target=case['n'],case['retained'],case['originals'],case['target']
        assert ids==list(range(n)) and len(originals)==5 and len(target)==2
        # This checked dependency restriction lifts the eight-word table to all
        # 2**n assignments without enumerating the irrelevant coordinates.
        assert all(not message['phase'] and all(mask<8 for mask,_ in message['equations'])
                   for message in originals+target)
        values=[sum((point(message,word) for message in originals),Fraction(0)) for word in range(8)]
        assert values==[2,1,1,1,1,1,1,1]
        assert all(sum((point(message,word) for message in target),Fraction(0))==value
                   for word,value in enumerate(values))
        assert case['values_on_first_three_bits']==[int(value) for value in values]
        assert case['minimum_piece_count']==2
        checked=compression.verify_compression(n,ids,originals,case['local_compression'])
        assert checked['valid'] and len(checked['messages'])==5
        fresh=compression.compress(n,ids,originals)
        assert fresh['status']=='EXACT' and fresh['messages']==case['local_compression']['messages']
        assert json.loads(json.dumps(fresh['certificate']))==case['local_compression']['certificate']
        norm=oracle.verify_norm_identity(n,ids,originals,target,case['equality_norm'])
        assert norm['valid'] and norm['equal'] and norm['squared_norm']==[0,1]
        rows.append(dict(n=n,retained_width=len(ids),local_output_pieces=5,
                         verified_minimum_pieces=2,relevant_truth_words=8,
                         truth_values=[int(value) for value in values],
                         fresh_greedy_stats=fresh['stats'],compression_verification=checked,
                         norm_verification=norm,norm_products=case['equality_norm']['block_checks']))
    after={path:sha256((HERE/path).read_bytes()).hexdigest() for path in paths}
    assert before==after
    output=dict(verdict='VERIFIED',created_utc=datetime.now(timezone.utc).isoformat(),
                source_sha256=before,source_unchanged_during_review=True,cases=rows,
                totals=dict(cases=3,relevant_truth_words=24,norm_products=sum(row['norm_products'] for row in rows),
                            compression_proofs_replayed=3,fresh_greedy_runs=3,minimum_piece_count=2),
                minimum_argument='Full support and nonconstant absolute values exclude a single scalar times affine-support quadratic sign; the verified two-piece expression attains two.',
                scope='Three explicit local greedy traps, not a lower bound for arbitrary compression or SAT.')
    (HERE/'AFFINE_RECOGNITION_LIMITS_REVIEW.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output['totals']))


if __name__=='__main__':main()
