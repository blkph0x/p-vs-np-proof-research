from hashlib import sha256
import json
from pathlib import Path

from capacity import dictionary_count, dictionary_product, enumerate_directions, existence_bound, small_two_piece_coverage

HERE = Path(__file__).resolve().parent
SOURCES = ['capacity.py', 'test_capacity.py', 'THEOREM.md', 'run_experiments.py']


def main():
    before = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}
    exact = []
    for n in range(5):
        data = enumerate_directions(n)
        assert len(data['directions']) == dictionary_count(n) == dictionary_product(n)
        exact.append({k: v for k, v in data.items() if k != 'directions'} | {'dictionary_count': len(data['directions'])})
    pair_controls = [small_two_piece_coverage(n) for n in range(4)]
    bounds = [existence_bound(n) for n in (4, 8, 16, 32, 64, 128)]
    after = {name: sha256((HERE/name).read_bytes()).hexdigest() for name in SOURCES}
    assert before == after
    out = dict(status='PASS', source_sha256=before, sources_unchanged_during_run=True,
               exact_dictionary_controls=exact, exact_small_pair_span_controls=pair_controls,
               arbitrary_truth_function_existence_bounds=bounds,
               conclusion='No succinct-CNF family or general SAT lower bound follows from this counting argument.')
    (HERE/'RESULTS.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'dictionary_counts': [r['dictionary_count'] for r in exact], 'pair_span_controls': pair_controls}, indent=2))


if __name__ == '__main__':
    main()
