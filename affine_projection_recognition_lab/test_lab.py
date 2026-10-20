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
        self.assertEqual(self.artifact["two_source_shared_width"], 4)

    def test_two_source_sat_unsat_reduction(self):
        rows = self.artifact["two_source_records"]
        self.assertEqual(len(rows), 4)
        classes = {(row["a_satisfiable"], row["b_satisfiable"]): row["projection_class"]
                   for row in rows}
        self.assertEqual(classes, {
            (True, True): "NON_AFFINE_OR_EMPTY",
            (True, False): "AFFINE",
            (False, True): "NON_AFFINE_OR_EMPTY",
            (False, False): "NON_AFFINE_OR_EMPTY",
        })
        masks = {(row["a_satisfiable"], row["b_satisfiable"]):
                 {index for index, bit in enumerate(row["projection_bits"]) if bit}
                 for row in rows}
        self.assertEqual(masks[(True, False)], set(range(8)))
        self.assertEqual(masks[(True, True)], set(range(9)))
        self.assertEqual(masks[(False, True)], {1, 3, 5, 6, 7, 8})
        self.assertEqual(masks[(False, False)], {1, 3, 5, 6, 7})

    def test_fixed_width_oracle_accounting(self):
        profiles = self.artifact["fixed_width_oracle_profiles"]
        self.assertEqual(profiles["one_source_width_three"]["oracle_queries"], 8)
        self.assertEqual(profiles["two_source_width_four"]["oracle_queries"], 16)
        for profile in profiles.values():
            self.assertEqual(profile["oracle_queries"], profile["postprocess_points"])
            self.assertEqual(profile["projection_class"], "AFFINE")

    def test_independent_replay(self):
        self.assertTrue(all(verify.verify(row) for row in self.artifact["records"]))
        self.assertTrue(all(verify.verify_two_source(row)
                            for row in self.artifact["two_source_records"]))

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
        forged = copy.deepcopy(self.artifact["two_source_records"][1])
        forged["projection_bits"][0] ^= 1
        self.assertFalse(verify.verify_two_source(forged))

    def test_saved_artifact_replays(self):
        path = Path(__file__).with_name("RESULTS.json")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved, self.artifact)


if __name__ == "__main__":
    unittest.main(verbosity=2)
