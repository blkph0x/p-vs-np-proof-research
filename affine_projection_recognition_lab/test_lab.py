import copy
import json
import unittest
from itertools import product
from pathlib import Path

import engine
import verify


class AffineProjectionRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = engine.build_artifact()

    def test_selector_reduction(self):
        sat, unsat, empty = self.artifact["records"]
        self.assertEqual(sat["projection_bits"], [1] * 8)
        self.assertEqual(sat["projection_class"], "AFFINE")
        self.assertEqual(unsat["projection_bits"], [0, 1, 0, 1, 0, 1, 1, 1])
        self.assertEqual(unsat["projection_class"], "NON_AFFINE_OR_EMPTY")
        self.assertEqual(empty["projection_bits"], [1] * 8)

    def test_shared_width_is_constant(self):
        self.assertEqual(self.artifact["shared_width"], 3)
        self.assertTrue(all(row["shared_width"] == 3 for row in self.artifact["records"]))

    def test_independent_replay(self):
        self.assertTrue(all(verify.verify(row) for row in self.artifact["records"]))

    def test_exhaustive_two_variable_source_controls(self):
        pool = tuple(tuple((index + 1) * choice for index, choice in enumerate(choices) if choice)
                     for choices in product((-1, 0, 1), repeat=2)
                     if any(choices))
        self.assertEqual(len(pool), 8)
        for selector in range(1 << len(pool)):
            source = tuple(pool[index] for index in range(len(pool)) if selector & (1 << index))
            record = engine.exact_record(source, 2)
            self.assertTrue(verify.verify(record))
            self.assertEqual(record["projection_class"],
                             "AFFINE" if record["source_satisfiable"] else "NON_AFFINE_OR_EMPTY")

    def test_mutation_is_rejected(self):
        forged = copy.deepcopy(self.artifact["records"][0])
        forged["projection_bits"] = self.artifact["records"][1]["projection_bits"]
        self.assertFalse(verify.verify(forged))
        forged = copy.deepcopy(self.artifact["records"][1])
        forged["source_model_count"] += 1
        self.assertFalse(verify.verify(forged))

    def test_saved_artifact_replays(self):
        path = Path(__file__).with_name("RESULTS.json")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved, self.artifact)


if __name__ == "__main__":
    unittest.main(verbosity=2)
