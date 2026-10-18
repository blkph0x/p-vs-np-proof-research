import importlib.util
from itertools import product
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("parameterized_edges", HERE / "parameterized_edges.py")
edges = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = edges
spec.loader.exec_module(edges)
engine_spec = importlib.util.spec_from_file_location("typed_engine", HERE / "engine.py")
typed_engine = importlib.util.module_from_spec(engine_spec)
sys.modules[engine_spec.name] = typed_engine
engine_spec.loader.exec_module(typed_engine)


def brute_distance(matrix):
    rows = [tuple(row) for row in matrix]
    k, n = len(rows), (len(rows[0]) if rows else 0)
    words = []
    for message in range(1, 1 << k):
        word = tuple(sum(((message >> i) & 1) * rows[i][j] for i in range(k)) % 2
                     for j in range(n))
        if any(word):
            words.append((sum(word), message, word))
    return min(words) if words else None


class ParameterizedEdgeTests(unittest.TestCase):
    def test_dimension_route_exactly_matches_bruteforce(self):
        matrices = (
            ((1, 0, 0), (0, 1, 0)),
            ((1, 1, 1),),
            ((1, 0, 1), (0, 1, 1), (1, 1, 0)),
            ((1, 0, 1), (1, 0, 1)),  # rank-deficient input is normalized
        )
        for matrix in matrices:
            result = edges.minimum_distance_by_dimension(matrix)
            expected = brute_distance(matrix)
            if expected is None:
                self.assertEqual(result["status"], "ZERO_CODE")
            else:
                self.assertEqual(result["status"], "EXACT")
                self.assertEqual(result["distance"], expected[0])
                self.assertEqual(result["word"].bit_count(), result["distance"])

    def test_distance_route_finds_and_excludes_small_supports(self):
        repetition = ((1, 1, 1),)
        above = edges.minimum_distance_by_weight(repetition, 2)
        self.assertEqual(above["status"], "CERTIFIED_ABOVE_BOUND")
        self.assertEqual(above["lower_bound"], 3)
        exact = edges.minimum_distance_by_weight(repetition, 3)
        self.assertEqual(exact["status"], "EXACT")
        self.assertEqual(exact["distance"], 3)
        self.assertEqual(exact["word"].bit_count(), 3)

    def test_distance_route_matches_dimension_route_on_small_matrices(self):
        for k in range(1, 3):
            for n in range(1, 5):
                for flat in product((0, 1), repeat=k * n):
                    matrix = tuple(tuple(flat[i * n + j] for j in range(n)) for i in range(k))
                    expected = edges.minimum_distance_by_dimension(matrix)
                    bound = edges.minimum_distance_by_weight(matrix, n)
                    self.assertEqual(expected["status"], bound["status"])
                    if expected["status"] == "EXACT":
                        self.assertEqual(expected["distance"], bound["distance"])

    def test_pair_status_is_conservative_and_labels_xp_correctly(self):
        self.assertEqual(edges.parameterized_pair_status("AFFINE", "CARDINALITY")["route"],
                         "KNOWN_NP_HARD")
        dim = edges.parameterized_pair_status("CARDINALITY", "AFFINE", code_dimension=5)
        self.assertEqual(dim["route"], "PARAMETERIZED_DIMENSION_ENUMERATION")
        self.assertEqual(dim["message_branches"], 31)
        xp = edges.parameterized_pair_status("AFFINE", "CARDINALITY", code_length=6,
                                             distance_bound=2)
        self.assertEqual(xp["route"], "XP_DISTANCE_SUPPORT_ENUMERATION")
        self.assertEqual(xp["supports"], 22)
        self.assertEqual(edges.parameterized_pair_status("HORN", "AFFINE")["route"],
                         "NOT_THIS_HARD_PAIR")
        integrated = typed_engine.assess_hard_merge(
            "AFFINE", "CARDINALITY", 0, 100, code_dimension=4)
        self.assertEqual(integrated["route"], "PARAMETERIZED_DIMENSION_ENUMERATION")

    def test_zero_dimension_and_empty_columns_are_sound(self):
        self.assertEqual(edges.minimum_distance_by_dimension(())["status"], "ZERO_CODE")
        self.assertEqual(edges.minimum_distance_by_weight((), 0)["status"], "ZERO_CODE")


if __name__ == "__main__":
    unittest.main()
