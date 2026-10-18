import json
from pathlib import Path
import unittest

from exact_oracle import apply, exceptional_stats, rank, score


HERE = Path(__file__).resolve().parent


class RankFiveArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((HERE / 'RANK5_RESULTS.json').read_text(encoding='utf-8'))

    def test_group_size_and_full_enumeration(self):
        self.assertEqual(self.payload['gl5_size'], 9_999_360)
        self.assertEqual(self.payload['case_count'], 4)
        for record in self.payload['records']:
            self.assertEqual(record['oracle']['transforms_evaluated'], 9_999_360)

    def test_saved_objectives_replay(self):
        for record in self.payload['records']:
            case = record['case']; rows = tuple(case['rows'])
            for kind in ('count_first', 'rank_first'):
                candidate = record['oracle'][kind]
                transform = tuple(candidate['row_transform'])
                self.assertEqual(rank(transform), 5)
                transformed = apply(rows, transform)
                stats = exceptional_stats(transformed, case['n'])
                self.assertEqual(candidate['exceptional_rank'], stats[1])
                self.assertEqual(candidate['exceptional_count'], stats[0])
                self.assertEqual(candidate['excess'], stats[2])
                self.assertEqual(candidate['total'], stats[3])
                expected = list(score(transformed, case['n'])) if kind == 'count_first' else [stats[1], stats[0], stats[2], stats[3]]
                self.assertEqual(candidate['objective'], expected)

    def test_downstream_rank_tradeoff(self):
        tradeoff = self.payload['records'][0]['native_tradeoff']
        self.assertEqual(tradeoff['count_first_state_count'], 4)
        self.assertEqual(tradeoff['rank_first_state_count'], 2)
        self.assertEqual(tradeoff['distance'], 2)


if __name__ == '__main__':
    unittest.main()
